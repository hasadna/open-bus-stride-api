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


LIST_MAX_LIMIT = 100
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
    return (
        session_query
        .select_from(model.SiriVehicleLocation)
        .add_entity(model.SiriSnapshot)
        .add_entity(model.SiriRide)
        .add_entity(model.SiriRoute)
        .join(model.SiriRideStop, model.SiriRideStop.id == model.SiriVehicleLocation.siri_ride_stop_id)
        .join(model.SiriRide, model.SiriRide.id == model.SiriRideStop.siri_ride_id)
        .join(model.SiriRoute, model.SiriRoute.id == model.SiriRide.siri_route_id)
        .join(model.SiriSnapshot, model.SiriSnapshot.id == model.SiriVehicleLocation.siri_snapshot_id)
    )

def _convert_to_dict(obj: model.SiriVehicleLocation):
    siri_vehicle_location, siri_snapshot, siri_ride, siri_route = obj
    res = siri_vehicle_location.__dict__
    siri_snapshot_related_model.add_orm_obj_to_dict_res(siri_snapshot, res)
    siri_route_related_model.add_orm_obj_to_dict_res(siri_route, res)
    siri_ride_related_model.add_orm_obj_to_dict_res(siri_ride, res)
    return res

@common.router_list(router, TAG, SiriVehicleLocationWithRelatedPydanticModel, WHAT_PLURAL)
def list_(limit: int = common.param_limit(LIST_MAX_LIMIT),
          offset: int = common.param_offset(),
          siri_vehicle_location_ids: str = common.param_filter_list('siri vehicle location id'),
          siri_snapshot_ids: str = common.param_filter_list('siri snapshot id'),
          siri_ride_stop_ids: str = common.param_filter_list('siri ride stop id'),
          recorded_at_time_from: datetime.datetime = common.param_filter_datetime_from('recorded at time'),
          recorded_at_time_to: datetime.datetime = common.param_filter_datetime_to('recorded at time'),
          order_by: str = common.param_order_by(),
          siri_routes__line_ref: str = common.param_filter_equals('siri route line ref'),
          siri_routes__operator_ref: str = common.param_filter_equals('siri route operator ref'),
          siri_rides__schedualed_start_time_from: datetime.datetime = common.param_filter_datetime_from('siri ride scheduled start time'),
          siri_rides__schedualed_start_time_to: datetime.datetime = common.param_filter_datetime_to('siri ride scheduled start time'),
          siri_rides__ids: str = common.param_filter_list('siri ride id'),
          siri_routes__ids: str = common.param_filter_list('siri route id'),
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
        ],
        order_by=order_by,
        post_session_query_hook=_post_session_query_hook,
        convert_to_dict=_convert_to_dict,
        max_limit=LIST_MAX_LIMIT
    )


@common.router_get(router, TAG, PYDANTIC_MODEL, WHAT_SINGULAR)
def get_(id: int = common.param_get_id(WHAT_SINGULAR)):
    return common.get_item(SQL_MODEL, SQL_MODEL.id, id)
