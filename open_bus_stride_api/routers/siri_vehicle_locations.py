import datetime
import functools
import math
import typing

import fastapi
import pydantic
import sqlalchemy
from open_bus_stride_db import model
from open_bus_stride_db.clickhouse import get_session
from open_bus_stride_db.clickhouse.models import SiriVehicleLocation
from open_bus_stride_db.db import get_session as get_postgres_session

from . import common

router = fastapi.APIRouter()


class SiriVehicleLocationPydanticModel(pydantic.BaseModel):
    id: str
    siri_snapshot_id: str
    siri_ride_stop_id: str
    recorded_at_time: datetime.datetime
    siri_stop_id: str
    siri_ride_id: str
    line_ref: typing.Optional[int]
    data_frame_ref: str
    dated_vehicle_journey_ref: str
    operator_ref: typing.Optional[int]
    origin_aimed_departure_time: datetime.datetime
    vehicle_location_longitude: typing.Optional[float]
    vehicle_location_latitude: typing.Optional[float]
    bearing: typing.Optional[int]
    velocity: typing.Optional[int]
    vehicle_ref: str
    stop_point_ref: str
    stop_order: typing.Optional[int]
    distance_from_stop: typing.Optional[int]
    journey_ref: str
    siri_route_id: str
    scheduled_start_time: datetime.datetime
    stop_code: str

    @pydantic.validator(
        'vehicle_location_longitude',
        'vehicle_location_latitude',
        'bearing',
        'velocity',
        'line_ref',
        'operator_ref',
        'stop_order',
        'distance_from_stop',
        pre=True,
    )
    def parse_number(cls, value, field):
        if value is None:
            return None
        try:
            number = float(value) if field.type_ is float else int(value)
            if not math.isfinite(number):
                return None
            return number
        except (TypeError, ValueError, OverflowError):
            return None

    @pydantic.validator('recorded_at_time', 'origin_aimed_departure_time', 'scheduled_start_time')
    def set_utc(cls, value):
        if value.tzinfo is None:
            return value.replace(tzinfo=datetime.timezone.utc)
        return value.astimezone(datetime.timezone.utc)


class SiriVehicleLocationCompatibleModel(SiriVehicleLocationPydanticModel):
    lon: typing.Optional[float] = None
    lat: typing.Optional[float] = None
    distance_from_journey_start: typing.Optional[int] = None
    distance_from_siri_ride_stop_meters: typing.Optional[int] = None
    siri_snapshot__snapshot_id: typing.Optional[str] = None
    siri_route__id: typing.Optional[int] = None
    siri_route__line_ref: typing.Optional[int] = None
    siri_route__operator_ref: typing.Optional[int] = None
    siri_ride__id: typing.Optional[int] = None
    siri_ride__journey_ref: typing.Optional[str] = None
    siri_ride__scheduled_start_time: typing.Optional[datetime.datetime] = None
    siri_ride__vehicle_ref: typing.Optional[str] = None
    siri_ride__first_vehicle_location_id: typing.Optional[int] = None
    siri_ride__last_vehicle_location_id: typing.Optional[int] = None
    siri_ride__duration_minutes: typing.Optional[int] = None
    siri_ride__gtfs_ride_id: typing.Optional[int] = None

    @pydantic.root_validator
    def add_compatible_fields(cls, values):
        values['lon'] = values.get('vehicle_location_longitude')
        values['lat'] = values.get('vehicle_location_latitude')
        values['siri_snapshot__snapshot_id'] = values.get('siri_snapshot_id')
        for source, target in (
            ('line_ref', 'siri_route__line_ref'),
            ('operator_ref', 'siri_route__operator_ref'),
        ):
            try:
                values[target] = int(values[source])
            except (ValueError, TypeError, KeyError):
                values[target] = None
        values['siri_ride__journey_ref'] = values.get('siri_ride__journey_ref') or values.get('journey_ref')
        values['siri_ride__scheduled_start_time'] = values.get('siri_ride__scheduled_start_time') or values.get('scheduled_start_time')
        values['siri_ride__vehicle_ref'] = values.get('siri_ride__vehicle_ref') or (str(values['vehicle_ref']) if values.get('vehicle_ref') is not None else None)
        return values


WHAT_SINGULAR = 'siri vehicle location'
WHAT_PLURAL = f'{WHAT_SINGULAR}s'
TAG = 'siri'
PYDANTIC_MODEL = SiriVehicleLocationPydanticModel
SQL_MODEL = SiriVehicleLocation


def _resolve_ride_ids(value):
    if value is None:
        return None
    ids = value.split(',')
    if len(ids) > 1000:
        raise fastapi.HTTPException(status_code=400, detail='Maximum 1000 ride IDs')
    numeric_ids = [int(item) for item in ids if item.isdecimal()]
    direct_ids = [item for item in ids if not item.isdecimal()]
    predicates = [SQL_MODEL.siri_ride_id.in_(direct_ids)] if direct_ids else []
    if numeric_ids:
        with get_postgres_session() as session:
            rides = (
                session.query(
                    model.SiriRoute.line_ref,
                    model.SiriRoute.operator_ref,
                    model.SiriRide.journey_ref,
                    model.SiriRide.vehicle_ref,
                )
                .join(model.SiriRoute, model.SiriRoute.id == model.SiriRide.siri_route_id)
                .filter(model.SiriRide.id.in_(numeric_ids))
                .all()
            )
            pairs = [(f'{line_ref};{operator_ref};{journey_ref}', vehicle_ref) for line_ref, operator_ref, journey_ref, vehicle_ref in rides if vehicle_ref is not None]
            if pairs:
                predicates.append(sqlalchemy.tuple_(SQL_MODEL.siri_ride_id, SQL_MODEL.vehicle_ref).in_(pairs))
    return sqlalchemy.or_(*predicates) if predicates else sqlalchemy.false()


def _resolve_route_ids(value):
    if value is None:
        return None
    ids = value.split(',')
    if len(ids) > 1000:
        raise fastapi.HTTPException(status_code=400, detail='Maximum 1000 route IDs')
    numeric_ids = [int(item) for item in ids if item.isdecimal()]
    resolved = [item for item in ids if not item.isdecimal()]
    if numeric_ids:
        with get_postgres_session() as session:
            routes = session.query(model.SiriRoute.line_ref, model.SiriRoute.operator_ref).filter(model.SiriRoute.id.in_(numeric_ids)).all()
            resolved.extend(f'{line_ref};{operator_ref}' for line_ref, operator_ref in routes)
    return resolved or ['']


def _enrich_locations(rows):
    if not rows:
        return rows
    # Match on the natural ride key, including vehicle_ref: PostgreSQL permits
    # more than one ride for a route and journey reference.
    keys = list({(str(row['line_ref']), str(row['operator_ref']), row['journey_ref'], str(row['vehicle_ref'])) for row in rows})
    rides_by_key = {}
    with get_postgres_session() as session:
        for start in range(0, len(keys), 500):
            batch = keys[start : start + 500]
            conditions = [sqlalchemy.and_(model.SiriRoute.line_ref == int(line), model.SiriRoute.operator_ref == int(operator), model.SiriRide.journey_ref == journey, model.SiriRide.vehicle_ref == vehicle) for line, operator, journey, vehicle in batch if line.isdecimal() and operator.isdecimal()]
            if not conditions:
                continue
            rides = session.query(model.SiriRide, model.SiriRoute).join(model.SiriRoute, model.SiriRide.siri_route_id == model.SiriRoute.id).filter(sqlalchemy.or_(*conditions)).all()
            for ride, route in rides:
                rides_by_key[(str(route.line_ref), str(route.operator_ref), ride.journey_ref, str(ride.vehicle_ref))] = (ride, route)
        for row in rows:
            key = (str(row['line_ref']), str(row['operator_ref']), row['journey_ref'], str(row['vehicle_ref']))
            match = rides_by_key.get(key)
            if match:
                ride, route = match
                row.update(
                    {
                        'siri_route__id': route.id,
                        'siri_ride__id': ride.id,
                        'siri_ride__journey_ref': ride.journey_ref,
                        'siri_ride__scheduled_start_time': ride.scheduled_start_time,
                        'siri_ride__vehicle_ref': ride.vehicle_ref,
                        'siri_ride__first_vehicle_location_id': ride.first_vehicle_location_id,
                        'siri_ride__last_vehicle_location_id': ride.last_vehicle_location_id,
                        'siri_ride__duration_minutes': ride.duration_minutes,
                        'siri_ride__gtfs_ride_id': ride.gtfs_ride_id,
                    }
                )
        # Distances are stored on the original PostgreSQL location record.
        keys = []
        for row in rows:
            if row.get('siri_ride__id') is not None:
                recorded = row['recorded_at_time']
                if recorded.tzinfo is None:
                    recorded = recorded.replace(tzinfo=datetime.timezone.utc)
                keys.append((row['siri_snapshot_id'], row['siri_ride__id'], recorded))
        distances = {}
        for start in range(0, len(keys), 500):
            batch = keys[start : start + 500]
            locations = (
                session.query(model.SiriSnapshot.snapshot_id, model.SiriRideStop.siri_ride_id, model.SiriVehicleLocation.recorded_at_time, model.SiriVehicleLocation.distance_from_journey_start, model.SiriVehicleLocation.distance_from_siri_ride_stop_meters)
                .join(model.SiriRideStop, model.SiriRideStop.id == model.SiriVehicleLocation.siri_ride_stop_id)
                .join(model.SiriSnapshot, model.SiriSnapshot.id == model.SiriVehicleLocation.siri_snapshot_id)
                .filter(sqlalchemy.tuple_(model.SiriSnapshot.snapshot_id, model.SiriRideStop.siri_ride_id, model.SiriVehicleLocation.recorded_at_time).in_(batch))
                .all()
            )
            for snapshot, ride_id, recorded, journey_distance, stop_distance in locations:
                if recorded.tzinfo is None:
                    recorded = recorded.replace(tzinfo=datetime.timezone.utc)
                distances[(snapshot, ride_id, recorded)] = (journey_distance, stop_distance)
        for row in rows:
            recorded = row['recorded_at_time']
            if recorded.tzinfo is None:
                recorded = recorded.replace(tzinfo=datetime.timezone.utc)
            values = distances.get((row['siri_snapshot_id'], row.get('siri_ride__id'), recorded))
            if values is not None:
                row['distance_from_journey_start'], row['distance_from_siri_ride_stop_meters'] = values
    return rows


# Keep the ClickHouse fields available during validation, but expose the original API fields.
_RESPONSE_FIELDS = {
    'id',
    'siri_snapshot_id',
    'siri_ride_stop_id',
    'recorded_at_time',
    'lon',
    'lat',
    'bearing',
    'velocity',
    'distance_from_journey_start',
    'distance_from_siri_ride_stop_meters',
    'siri_snapshot__snapshot_id',
    'siri_route__id',
    'siri_route__line_ref',
    'siri_route__operator_ref',
    'siri_ride__id',
    'siri_ride__journey_ref',
    'siri_ride__scheduled_start_time',
    'siri_ride__vehicle_ref',
    'siri_ride__first_vehicle_location_id',
    'siri_ride__last_vehicle_location_id',
    'siri_ride__duration_minutes',
    'siri_ride__gtfs_ride_id',
}


def _legacy_distance_order(order_by):
    fields = []
    for part in (order_by or '').split(','):
        tokens = part.strip().split()
        if not tokens:
            continue
        if len(tokens) > 2 or (len(tokens) == 2 and tokens[1].lower() not in ('asc', 'desc')):
            raise fastapi.HTTPException(status_code=400, detail='Invalid order_by')
        fields.append((tokens[0], len(tokens) == 2 and tokens[1].lower() == 'desc'))
    if not any(name in ('distance_from_journey_start', 'distance_from_siri_ride_stop_meters') for name, _ in fields):
        return None
    for name, _ in fields:
        if name not in SiriVehicleLocationCompatibleModel.__fields__:
            raise fastapi.HTTPException(status_code=400, detail='Invalid order_by field')
    if not any(name == 'id' for name, _ in fields):
        fields.append(('id', True))
    return fields


def _sort_legacy_locations(rows, fields):
    # Normalize ClickHouse strings and derived compatibility fields in the
    # same way as response validation before comparing values.
    normalized = {id(row): SiriVehicleLocationCompatibleModel.parse_obj(row).dict() for row in rows}

    def compare(left, right):
        for name, descending in fields:
            a, b = normalized[id(left)].get(name), normalized[id(right)].get(name)
            if a is None or b is None:
                result = (a is None) - (b is None)
            else:
                result = (a > b) - (a < b)
            if result:
                return -result if descending else result
        return 0

    rows.sort(key=functools.cmp_to_key(compare))


def _apply_numeric_order(query, order_by, limit):
    order_fields, _, _ = common.process_list_query_order_by_limit_offset(False, order_by, False, limit, None)
    aliases = {
        'lon': sqlalchemy.func.toFloat64OrNull(SQL_MODEL.vehicle_location_longitude),
        'lat': sqlalchemy.func.toFloat64OrNull(SQL_MODEL.vehicle_location_latitude),
        'velocity': sqlalchemy.func.toInt64OrNull(SQL_MODEL.velocity),
        'bearing': sqlalchemy.func.toInt64OrNull(SQL_MODEL.bearing),
    }
    ordering = []
    for direction, name in order_fields:
        field = aliases.get(name)
        if field is None:
            field = getattr(SQL_MODEL, name)
        ordering.append((sqlalchemy.desc if direction == 'desc' else sqlalchemy.asc)(field))
    return query.order_by(*ordering)


@router.get('/list', tags=[TAG], response_model=typing.List[SiriVehicleLocationCompatibleModel], response_model_include=_RESPONSE_FIELDS, description=f'List of {WHAT_PLURAL}.')
def list_(
    limit: int = common.param_limit(),
    offset: int = common.param_offset(),
    get_count: bool = common.param_get_count(),
    siri_vehicle_location_ids: str = common.doc_param('siri vehicle location id', filter_type='list'),
    siri_snapshot_ids: str = common.doc_param('siri snapshot id', filter_type='list'),
    siri_ride_stop_ids: str = common.doc_param('siri ride stop id', filter_type='list'),
    recorded_at_time_from: datetime.datetime = common.doc_param('recorded at time', filter_type='datetime_from'),
    recorded_at_time_to: datetime.datetime = common.doc_param('recorded at time', filter_type='datetime_to'),
    lon__greater_or_equal: float = common.doc_param('lon', filter_type='greater_or_equal'),
    lon__lower_or_equal: float = common.doc_param('lon', filter_type='lower_or_equal'),
    lat__greater_or_equal: float = common.doc_param('lat', filter_type='greater_or_equal'),
    lat__lower_or_equal: float = common.doc_param('lat', filter_type='lower_or_equal'),
    order_by: str = common.param_order_by(),
    siri_routes__line_ref: str = common.doc_param('siri route line ref', filter_type='equals'),
    siri_ride__vehicle_ref: str = common.doc_param('siri ride vehicle ref', filter_type='list'),
    siri_routes__operator_ref: str = common.doc_param('siri route operator ref', filter_type='equals'),
    siri_rides__ids: str = common.doc_param('siri ride id', filter_type='list'),
    siri_routes__ids: str = common.doc_param('siri route id', filter_type='list'),
    # --- Deprecated (misspelled) scheduled start time params ---
    # Kept for backward compatibility. Do not remove without a major version bump,
    # since existing consumers (including the hackathon repo) rely on this spelling.
    # NOTE: common.doc_param() does not currently support a `deprecated` kwarg,
    # so deprecation is communicated via the description text only.
    siri_rides__schedualed_start_time_from: typing.Optional[datetime.datetime] = common.doc_param(
        'siri ride scheduled start time',
        filter_type='datetime_from',
        description='[DEPRECATED] Misspelled parameter name, kept for backward compatibility. Use "siri_rides__scheduled_start_time_from" instead.',
    ),
    siri_rides__schedualed_start_time_to: typing.Optional[datetime.datetime] = common.doc_param(
        'siri ride scheduled start time',
        filter_type='datetime_to',
        description='[DEPRECATED] Misspelled parameter name, kept for backward compatibility. Use "siri_rides__scheduled_start_time_to" instead.',
    ),
    siri_rides__scheduled_start_time_from: typing.Optional[datetime.datetime] = common.doc_param(
        'siri ride scheduled start time',
        filter_type='datetime_from',
        description='Preferred parameter. Replaces the deprecated "siri_rides__schedualed_start_time_from".',
    ),
    siri_rides__scheduled_start_time_to: typing.Optional[datetime.datetime] = common.doc_param(
        'siri ride scheduled start time',
        filter_type='datetime_to',
        description='Preferred parameter. Replaces the deprecated "siri_rides__schedualed_start_time_to".',
    ),
):
    legacy_order = None if get_count else _legacy_distance_order(order_by)
    ride_filter = _resolve_ride_ids(siri_rides__ids)
    numeric_order = not get_count and not legacy_order and any(part.strip().split() and part.strip().split()[0] in ('lon', 'lat', 'velocity', 'bearing') for part in (order_by or '').split(','))

    def prepare_query(query):
        if ride_filter is not None:
            query = query.filter(ride_filter)
        if numeric_order:
            query = _apply_numeric_order(query, order_by, limit)
        return query

    with get_session() as session:
        query = common.get_list_query(
            session,
            SQL_MODEL,
            limit,
            offset,
            [
                {'type': 'equals', 'field': SQL_MODEL.line_ref, 'value': siri_routes__line_ref},
                {'type': 'equals', 'field': SQL_MODEL.operator_ref, 'value': siri_routes__operator_ref},
                {'type': 'in', 'field': SQL_MODEL.siri_route_id, 'value': _resolve_route_ids(siri_routes__ids)},
                {'type': 'in', 'field': SQL_MODEL.vehicle_ref, 'value': siri_ride__vehicle_ref},
                {'type': 'in', 'field': SQL_MODEL.id, 'value': siri_vehicle_location_ids},
                {'type': 'in', 'field': SQL_MODEL.siri_snapshot_id, 'value': siri_snapshot_ids},
                {'type': 'in', 'field': SQL_MODEL.siri_ride_stop_id, 'value': siri_ride_stop_ids},
                {'type': 'datetime_from', 'field': SQL_MODEL.recorded_at_time, 'value': recorded_at_time_from},
                {'type': 'datetime_to', 'field': SQL_MODEL.recorded_at_time, 'value': recorded_at_time_to},
                {'type': 'datetime_from', 'field': SQL_MODEL.scheduled_start_time, 'value': siri_rides__scheduled_start_time_from or siri_rides__schedualed_start_time_from},
                {'type': 'datetime_to', 'field': SQL_MODEL.scheduled_start_time, 'value': siri_rides__scheduled_start_time_to or siri_rides__schedualed_start_time_to},
                {'type': 'greater_or_equal', 'field': sqlalchemy.func.toFloat64OrNull(SQL_MODEL.vehicle_location_longitude), 'value': lon__greater_or_equal},
                {'type': 'lower_or_equal', 'field': sqlalchemy.func.toFloat64OrNull(SQL_MODEL.vehicle_location_longitude), 'value': lon__lower_or_equal},
                {'type': 'greater_or_equal', 'field': sqlalchemy.func.toFloat64OrNull(SQL_MODEL.vehicle_location_latitude), 'value': lat__greater_or_equal},
                {'type': 'lower_or_equal', 'field': sqlalchemy.func.toFloat64OrNull(SQL_MODEL.vehicle_location_latitude), 'value': lat__lower_or_equal},
            ],
            order_by=None if legacy_order or numeric_order else order_by,
            skip_order_by=numeric_order,
            get_count=get_count,
            pydantic_model=PYDANTIC_MODEL,
            post_session_query_hook=prepare_query,
        )
        if get_count:
            return fastapi.Response(content=str(query.count()), media_type='application/json')
        if legacy_order:
            # The legacy distances reside in PostgreSQL, so all matching rows
            # must be enriched and sorted before applying the requested page.
            query = query.limit(None).offset(None).order_by(None)
            rows = []
            batch = []
            for row in query:
                batch.append(row._asdict())
                if len(batch) == 500:
                    rows.extend(_enrich_locations(batch))
                    batch = []
            rows.extend(_enrich_locations(batch))
            _sort_legacy_locations(rows, legacy_order)
            start = offset or 0
            return rows[start : start + (limit or common.DEFAULT_LIMIT)]
        return _enrich_locations([row._asdict() for row in query])


@router.get(
    '/get',
    tags=[TAG],
    response_model=SiriVehicleLocationCompatibleModel,
    response_model_include=_RESPONSE_FIELDS,
    description=f'Return a single {WHAT_SINGULAR} based on id.',
)
def get_(id: str = common.param_get_id(WHAT_SINGULAR)):
    with get_session() as session:
        query = common.get_base_session_query(session, SQL_MODEL, PYDANTIC_MODEL)
        return _enrich_locations([query.filter(SQL_MODEL.id == id).one()._asdict()])[0]
