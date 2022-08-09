import typing
import datetime
import sqlalchemy

import pydantic
from fastapi import APIRouter

from open_bus_stride_db.model.siri_vehicle_location import SiriVehicleLocation
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
