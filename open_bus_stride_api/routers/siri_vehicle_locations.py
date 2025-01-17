import typing
import datetime
import sqlalchemy

import pydantic
from fastapi import APIRouter
from textwrap import dedent

from open_bus_stride_db.model.siri_vehicle_location import SiriVehicleLocation
from open_bus_stride_db.db import get_session
from open_bus_stride_db import model

from . import siri_rides, siri_routes, siri_snapshots
from . import common


router = APIRouter()


class SiriVehicleLocationPydanticModel(pydantic.BaseModel):
    id: int
    siri_snapshot_id: int
    siri_ride_stop_id: int
    recorded_at_time: datetime.datetime
    lon: float
    lat: float
    bearing: int
    velocity: int
    distance_from_journey_start: int
    distance_from_siri_ride_stop_meters: typing.Optional[int]


WHAT_SINGULAR = 'siri vehicle location'
WHAT_PLURAL = f'{WHAT_SINGULAR}s'
TAG = 'siri'
PYDANTIC_MODEL = SiriVehicleLocationPydanticModel
SQL_MODEL = model.SiriVehicleLocation


siri_route_related_model = common.PydanticRelatedModel(
    'siri_route__', siri_routes.SiriRoutePydanticModel
)
siri_ride_related_model = common.PydanticRelatedModel(
    'siri_ride__', siri_rides.SiriRidePydanticModel, [
        'siri_route_id', 'updated_first_last_vehicle_locations', 'updated_duration_minutes',
        'journey_gtfs_ride_id', 'route_gtfs_ride_id'
    ]
)
siri_snapshot_related_model = common.PydanticRelatedModel(
    'siri_snapshot__', siri_snapshots.SiriSnapshotPydanticModel,
    include_field_names=['snapshot_id']
)


SiriVehicleLocationWithRelatedPydanticModel = common.pydantic_create_model_with_related(
    'SiriVehicleLocationWithRelatedPydanticModel',
    SiriVehicleLocationPydanticModel,
    siri_snapshot_related_model,
    siri_route_related_model,
    siri_ride_related_model,
)


def _post_session_query_hook(session_query: sqlalchemy.orm.Query):
    session_query = session_query.select_from(model.SiriVehicleLocation)
    session_query = siri_snapshot_related_model.add_session_query_entities(model.SiriSnapshot, session_query)
    session_query = siri_ride_related_model.add_session_query_entities(model.SiriRide, session_query)
    session_query = siri_route_related_model.add_session_query_entities(model.SiriRoute, session_query)
    return (
        session_query
        .join(model.SiriRideStop, model.SiriRideStop.id == model.SiriVehicleLocation.siri_ride_stop_id)
        .join(model.SiriRide, model.SiriRide.id == model.SiriRideStop.siri_ride_id)
        .join(model.SiriRoute, model.SiriRoute.id == model.SiriRide.siri_route_id)
        .join(model.SiriSnapshot, model.SiriSnapshot.id == model.SiriVehicleLocation.siri_snapshot_id)
    )


@common.router_list(router, TAG, SiriVehicleLocationWithRelatedPydanticModel, WHAT_PLURAL)
def list_(limit: int = common.param_limit(),
          offset: int = common.param_offset(),
          get_count: bool = common.param_get_count(),
          siri_vehicle_location_ids: str = common.doc_param('siri vehicle location id', filter_type='list'),
          siri_snapshot_ids: str = common.doc_param('siri snapshot id', filter_type='list'),
          siri_ride_stop_ids: str = common.doc_param('siri ride stop id', filter_type='list'),
          recorded_at_time_from: datetime.datetime = common.doc_param('recorded at time', filter_type='datetime_from'),
          recorded_at_time_to: datetime.datetime = common.doc_param('recorded at time', filter_type='datetime_to'),
          lon__greater_or_equal: float = common.doc_param('lon', filter_type='greater_or_equal', example='34.808'),
          lon__lower_or_equal: float = common.doc_param('lon', filter_type='lower_or_equal', example='34.808'),
          lat__greater_or_equal: float = common.doc_param('lat', filter_type='greater_or_equal', example='31.961'),
          lat__lower_or_equal: float = common.doc_param('lat', filter_type='lower_or_equal', example='31.961'),
          order_by: str = common.param_order_by(),
          siri_routes__line_ref: str = common.doc_param('siri route line ref', filter_type='equals'),
          siri_routes__operator_ref: str = common.doc_param('siri route operator ref', filter_type='equals'),
          siri_rides__schedualed_start_time_from: datetime.datetime = common.doc_param('siri ride scheduled start time', filter_type='datetime_from'),
          siri_rides__schedualed_start_time_to: datetime.datetime = common.doc_param('siri ride scheduled start time', filter_type='datetime_to'),
          siri_rides__ids: str = common.doc_param('siri ride id', filter_type='list'),
          siri_routes__ids: str = common.doc_param('siri route id', filter_type='list'),
          ):
    return common.get_list(
        SiriVehicleLocation, limit, offset,
        [
            {'type': 'equals', 'field': model.SiriRoute.line_ref, 'value': siri_routes__line_ref},
            {'type': 'equals', 'field': model.SiriRoute.operator_ref, 'value': siri_routes__operator_ref},
            {'type': 'in', 'field': model.SiriRoute.id, 'value': siri_routes__ids},
            {'type': 'datetime_to', 'field': model.SiriRide.scheduled_start_time, 'value': siri_rides__schedualed_start_time_to},
            {'type': 'datetime_from', 'field': model.SiriRide.scheduled_start_time, 'value': siri_rides__schedualed_start_time_from},
            {'type': 'in', 'field': model.SiriRide.id, 'value': siri_rides__ids},
            {'type': 'in', 'field': SiriVehicleLocation.id, 'value': siri_vehicle_location_ids},
            {'type': 'in', 'field': SiriVehicleLocation.siri_snapshot_id, 'value': siri_snapshot_ids},
            {'type': 'in', 'field': SiriVehicleLocation.siri_ride_stop_id, 'value': siri_ride_stop_ids},
            {'type': 'datetime_from', 'field': SiriVehicleLocation.recorded_at_time, 'value': recorded_at_time_from},
            {'type': 'datetime_to', 'field': SiriVehicleLocation.recorded_at_time, 'value': recorded_at_time_to},
            {'type': 'greater_or_equal', 'field': model.SiriVehicleLocation.lon, 'value': lon__greater_or_equal},
            {'type': 'lower_or_equal', 'field': model.SiriVehicleLocation.lon, 'value': lon__lower_or_equal},
            {'type': 'greater_or_equal', 'field': model.SiriVehicleLocation.lat, 'value': lat__greater_or_equal},
            {'type': 'lower_or_equal', 'field': model.SiriVehicleLocation.lat, 'value': lat__lower_or_equal},
        ],
        order_by=order_by,
        post_session_query_hook=_post_session_query_hook,
        get_count=get_count,
        pydantic_model=PYDANTIC_MODEL,
    )


@common.router_get(router, TAG, PYDANTIC_MODEL, WHAT_SINGULAR)
def get_(id: int = common.param_get_id(WHAT_SINGULAR)):
    return common.get_item(
        SQL_MODEL, SQL_MODEL.id, id,
        pydantic_model=PYDANTIC_MODEL,
    )



class SIRI_AGG_VELOCITY_STATS_PYDANTIC_MODEL(pydantic.BaseModel):
    lon_round: float
    lat_round: float
    date: datetime.date
    stddev_hourly_avg: typing.Optional[float]
    avg_hourly_avg: float
    sample_number: int
    median_hourly_avg: float
    last_used: typing.Optional[datetime.datetime]

@router.get(
    "/siri-agg-velocity-stats",
    tags=[TAG],
    response_model=typing.List[SIRI_AGG_VELOCITY_STATS_PYDANTIC_MODEL],
    description="Retrieve aggregated velocity stats for a given date (with cache mechanism).",
)
def get_or_insert_agg_velocity_stats(
    date: datetime.date = common.doc_param("date", filter_type="date", default=...)
):
    """
    Fetch aggregated velocity stats for the given date. If not found, calculate them.
    """
    # Query the database for the given date
    sql = dedent("""
        SELECT
            siri_agg_velocity_stats.lat_round,
            lon_round,
            date,
            stddev_hourly_avg,
            avg_hourly_avg,
            sample_number,
            median_hourly_avg,
            last_used
        FROM siri_agg_velocity_stats
        WHERE date = :date
    """)
    sql_params = {"date": date}
    with get_session() as db:
        results = db.execute(sql, sql_params).fetchall()

        # If no results, calculate and insert new data
        if not results:
            calculate_sql = dedent("""
                WITH HourlyAverages AS (
                    SELECT
                        trunc(lon * 500 + .5) / 500 AS lon_round,
                        trunc(lat * 500 + .5) / 500 AS lat_round,
                        DATE(recorded_at_time) AS date,
                        DATE_PART('hour', recorded_at_time) AS hour,
                        AVG(velocity) AS hourly_avg,
                        COUNT(1) AS sample_number
                    FROM siri_vehicle_location svl
                    WHERE
                        velocity > 0 AND velocity < 200
                        AND lon > 0 AND lat > 0
                        AND DATE(recorded_at_time) = :date
                    GROUP BY lon_round, lat_round, date, hour
                    HAVING COUNT(1) > 5
                )
                SELECT
                    lon_round,
                    lat_round,
                    date,
                    STDDEV(hourly_avg) AS stddev_hourly_avg,
                    AVG(hourly_avg) AS avg_hourly_avg,
                    SUM(sample_number) AS sample_number,
                    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY hourly_avg) AS median_hourly_avg
                FROM HourlyAverages
                WHERE date = :date
                GROUP BY lon_round, lat_round, date
            """)
            new_data = db.execute(calculate_sql, sql_params).fetchall()

            if new_data:
                # delete old data (inserted 10,000 records ago)
                delete_old_sql = dedent("""
                    with delete_from as (
                        select last_used
                        from siri_agg_velocity_stats
                        order by last_used
                        limit 1
                        offset 10000
                    )
                    delete from siri_agg_velocity_stats
                    where last_used < (select last_used from delete_from)
                """)
                insert_sql = dedent("""
                    INSERT INTO siri_agg_velocity_stats (
                        lon_round, lat_round, date,
                        stddev_hourly_avg, avg_hourly_avg,
                        sample_number, median_hourly_avg,
                        last_used
                    )
                    VALUES (
                        :lon_round, :lat_round, :date,
                        :stddev_hourly_avg, :avg_hourly_avg,
                        :sample_number, :median_hourly_avg,
                        NOW()
                    )
                """)
                for row in new_data:
                    db.execute(insert_sql, dict(row))
                db.commit()

            # Refresh the results after insertion
            results = db.execute(sql, sql_params).fetchall()

        # Return the results as a response
        return [
            {
                "lon_round": result.lon_round,
                "lat_round": result.lat_round,
                "date": result.date,
                "stddev_hourly_avg": result.stddev_hourly_avg,
                "avg_hourly_avg": result.avg_hourly_avg,
                "sample_number": result.sample_number,
                "median_hourly_avg": result.median_hourly_avg,
                "last_used": result.last_used,
            }
            for result in results
        ]
