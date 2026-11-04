import datetime
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import sqlalchemy
import pydantic
from fastapi.encoders import jsonable_encoder
from fastapi import HTTPException
from sqlalchemy.orm import sessionmaker

from open_bus_stride_api.routers import common, siri_stops
from open_bus_stride_api.routers import siri_vehicle_locations as locations


class CompatibilityTests(unittest.TestCase):
    def setUp(self):
        self.session = MagicMock()
        self.context = MagicMock()
        self.context.__enter__.return_value = self.session

    def test_route_ids_are_resolved_and_unknown_ids_do_not_match_all(self):
        self.session.query.return_value.filter.return_value.all.return_value = [(12, 3)]
        with patch.object(locations, 'get_postgres_session', return_value=self.context):
            self.assertEqual(locations._resolve_route_ids('42,missing'), ['missing', '12;3'])
            self.session.query.return_value.filter.return_value.all.return_value = []
            self.assertEqual(locations._resolve_route_ids('999'), [''])

    def test_vehicle_filter_accepts_multiple_references(self):
        query = MagicMock()
        result = common.get_list_query_filter_in(
            query,
            [],
            {
                'field': locations.SQL_MODEL.vehicle_ref,
                'value': '123,456',
            },
        )
        self.assertIs(result, query.filter.return_value)
        expression = query.filter.call_args.args[0]
        self.assertEqual(list(expression.right.value), ['123', '456'])

    def test_ride_filter_keeps_vehicle_pairs_and_direct_ids_distinct(self):
        self.session.query.return_value.join.return_value.filter.return_value.all.return_value = [
            (12, 3, 'journey', '123'), (12, 3, 'other', '456'),
        ]
        with patch.object(locations, 'get_postgres_session', return_value=self.context):
            condition = locations._resolve_ride_ids('42,43,12;3;direct')
        engine = sqlalchemy.create_engine('sqlite://')
        metadata = sqlalchemy.MetaData()
        table = sqlalchemy.Table('siri_vehicle_location', metadata,
                                 sqlalchemy.Column('siri_ride_id', sqlalchemy.String),
                                 sqlalchemy.Column('vehicle_ref', sqlalchemy.String))
        metadata.create_all(engine)
        with engine.begin() as connection:
            connection.execute(table.insert(), [
                {'siri_ride_id': '12;3;journey', 'vehicle_ref': '123'},
                {'siri_ride_id': '12;3;journey', 'vehicle_ref': '456'},
                {'siri_ride_id': '12;3;other', 'vehicle_ref': '456'},
                {'siri_ride_id': '12;3;direct', 'vehicle_ref': '789'},
            ])
            rows = connection.execute(sqlalchemy.select(locations.SQL_MODEL.siri_ride_id,
                                                        locations.SQL_MODEL.vehicle_ref).where(condition)).fetchall()
        self.assertEqual([(row.siri_ride_id, row.vehicle_ref) for row in rows], [
            ('12;3;journey', '123'), ('12;3;other', '456'), ('12;3;direct', '789'),
        ])
        engine.dispose()

    def test_coordinate_order_uses_numeric_clickhouse_expressions(self):
        query = MagicMock()
        locations._apply_numeric_order(query, 'lon asc,lat desc', 10)
        order = query.order_by.call_args.args
        self.assertIn('toFloat64OrNull(siri_vehicle_location.vehicle_location_longitude) ASC', str(order[0]))
        self.assertIn('toFloat64OrNull(siri_vehicle_location.vehicle_location_latitude) DESC', str(order[1]))

    def test_velocity_and_bearing_order_are_numeric(self):
        engine = sqlalchemy.create_engine('sqlite://')
        connection = engine.raw_connection()
        connection.create_function('toInt64OrNull', 1, lambda value: int(value) if value and value.isdecimal() else None)
        connection.execute('CREATE TABLE siri_vehicle_location (id TEXT, velocity TEXT, bearing TEXT)')
        connection.executemany('INSERT INTO siri_vehicle_location VALUES (?, ?, ?)', [
            ('a', '100', '20'), ('b', '20', '100'), ('c', '3', '3'),
        ])
        connection.commit()
        connection.close()
        with sessionmaker(bind=engine)() as session:
            query = session.query(locations.SQL_MODEL.id)
            rows = locations._apply_numeric_order(query, 'velocity asc,bearing desc', 10).all()
            self.assertEqual([row.id for row in rows], ['c', 'b', 'a'])
            rows = locations._apply_numeric_order(query, 'bearing desc', 10).all()
            self.assertEqual([row.id for row in rows], ['b', 'a', 'c'])
        engine.dispose()

    def test_list_and_get_use_same_response_fields(self):
        routes = {route.path: route for route in locations.router.routes}
        self.assertEqual(routes['/list'].response_model_include, locations._RESPONSE_FIELDS)
        self.assertEqual(routes['/get'].response_model_include, locations._RESPONSE_FIELDS)
        response_item = pydantic.create_model('ResponseItem', id=(str, ...), lon=(float, ...), vehicle_ref=(str, ...))
        data = [response_item(id='id', lon=34.0, vehicle_ref='internal')]
        self.assertEqual(jsonable_encoder(data, include=routes['/list'].response_model_include),
                         [{'id': 'id', 'lon': 34.0}])

    def test_legacy_ride_and_distance_fields_are_restored(self):
        time = datetime.datetime(2026, 1, 1, 12, 0)
        ride = SimpleNamespace(id=7, journey_ref='journey', vehicle_ref='123', scheduled_start_time=time, first_vehicle_location_id=9, last_vehicle_location_id=10, duration_minutes=11, gtfs_ride_id=12)
        route = SimpleNamespace(id=8, line_ref=12, operator_ref=3)
        first = MagicMock()
        first.join.return_value.filter.return_value.all.return_value = [(ride, route)]
        second = MagicMock()
        second.join.return_value.join.return_value.filter.return_value.all.return_value = [
            ('2026/01/01/12/00', 7, time, 100, 20),
        ]
        self.session.query.side_effect = [first, second]
        row = {'line_ref': '12', 'operator_ref': '3', 'journey_ref': 'journey', 'vehicle_ref': '123', 'siri_snapshot_id': '2026/01/01/12/00', 'recorded_at_time': time}
        with patch.object(locations, 'get_postgres_session', return_value=self.context):
            result = locations._enrich_locations([row])[0]
        self.assertEqual(result['siri_route__id'], 8)
        self.assertEqual(result['siri_ride__id'], 7)
        self.assertEqual(result['siri_ride__first_vehicle_location_id'], 9)
        self.assertEqual(result['siri_ride__duration_minutes'], 11)
        self.assertEqual(result['distance_from_journey_start'], 100)
        self.assertEqual(result['distance_from_siri_ride_stop_meters'], 20)

    def test_stops_derive_distinct_ids_and_codes_from_vehicle_locations(self):
        engine = sqlalchemy.create_engine('sqlite://')
        metadata = sqlalchemy.MetaData()
        table = sqlalchemy.Table(
            'siri_vehicle_location', metadata,
            sqlalchemy.Column('siri_stop_id', sqlalchemy.String),
            sqlalchemy.Column('stop_code', sqlalchemy.String),
        )
        metadata.create_all(engine)
        with engine.begin() as connection:
            connection.execute(table.insert(), [
                {'siri_stop_id': '123', 'stop_code': '123'},
                {'siri_stop_id': '123', 'stop_code': '123'},
                {'siri_stop_id': '456', 'stop_code': '456'},
            ])
        with patch.object(siri_stops, 'get_session', sessionmaker(bind=engine)):
            result = siri_stops.list_(limit=10, offset=0, get_count=False, codes=None, order_by='id asc')
            self.assertEqual(result, [{'id': '123', 'code': '123'}, {'id': '456', 'code': '456'}])
            filtered = siri_stops.list_(limit=10, offset=0, get_count=False, codes='456', order_by='id asc')
            self.assertEqual(filtered, [{'id': '456', 'code': '456'}])
            self.assertEqual(siri_stops.get_('123'), {'id': '123', 'code': '123'})
            with self.assertRaises(HTTPException) as error:
                siri_stops.get_('missing')
            self.assertEqual(error.exception.status_code, 404)
        engine.dispose()

    def test_legacy_distance_order_sorts_before_page_selection(self):
        now = datetime.datetime(2026, 1, 1)
        base = {
            'siri_snapshot_id': 'snapshot',
            'siri_ride_stop_id': 'stop',
            'recorded_at_time': now,
            'siri_stop_id': 'stop',
            'siri_ride_id': 'ride',
            'line_ref': '12',
            'data_frame_ref': 'frame',
            'dated_vehicle_journey_ref': 'journey',
            'operator_ref': '3',
            'origin_aimed_departure_time': now,
            'vehicle_location_longitude': '34',
            'vehicle_location_latitude': '32',
            'bearing': '0',
            'velocity': '0',
            'vehicle_ref': '123',
            'stop_point_ref': 'stop',
            'stop_order': '0',
            'distance_from_stop': '0',
            'journey_ref': 'journey',
            'siri_route_id': '12;3',
            'scheduled_start_time': now,
            'stop_code': 'stop',
        }
        rows = [dict(base, id='a', distance_from_siri_ride_stop_meters=10), dict(base, id='b', distance_from_siri_ride_stop_meters=30), dict(base, id='c', distance_from_siri_ride_stop_meters=20)]
        order = locations._legacy_distance_order('distance_from_siri_ride_stop_meters desc')
        locations._sort_legacy_locations(rows, order)
        self.assertEqual([row['id'] for row in rows[1:3]], ['c', 'a'])


if __name__ == '__main__':
    unittest.main()
