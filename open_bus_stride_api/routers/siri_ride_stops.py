import datetime

import pydantic
from fastapi import APIRouter
import sqlalchemy.orm

from open_bus_stride_db import model

from . import common
from . import siri_rides, siri_stops, gtfs_stops, siri_vehicle_locations, gtfs_ride_stops


router = APIRouter()


class SiriRideStopPydanticModel(pydantic.BaseModel):
    id: int
    siri_stop_id: int
    siri_ride_id: int
    order: int
    gtfs_stop_id: int = None
    nearest_siri_vehicle_location_id: int = None


LIST_MAX_LIMIT = 100
WHAT_SINGULAR = 'siri ride stop'
WHAT_PLURAL = f'{WHAT_SINGULAR}s'
TAG = 'siri'
PYDANTIC_MODEL = SiriRideStopPydanticModel
SQL_MODEL = model.SiriRideStop


siri_stop_related_model = common.PydanticRelatedModel(
    'siri_stop__', siri_stops.SiriStopPydanticModel, ['id']
)
siri_ride_related_model = common.PydanticRelatedModel(
    'siri_ride__', siri_rides.SiriRidePydanticModel, ['id']
)
gtfs_stop_related_model = common.PydanticRelatedModel(
    'gtfs_stop__', gtfs_stops.GtfsStopPydanticModel, ['id']
)
nearest_siri_vehicle_location_related_model = common.PydanticRelatedModel(
    'nearest_siri_vehicle_location__', siri_vehicle_locations.SiriVehicleLocationPydanticModel, ['id']
)
gtfs_ride_stop_related_model = common.PydanticRelatedModel(
    'gtfs_ride_stop__', gtfs_ride_stops.GtfsRideStopPydanticModel, ['id']
)

SiriRideStopWithRelatedPydanticModel = common.pydantic_create_model_with_related(
    'SiriRideStopWithRelatedPydanticModel',
    SiriRideStopPydanticModel,
    siri_stop_related_model,
    siri_ride_related_model,
    gtfs_stop_related_model,
    nearest_siri_vehicle_location_related_model,
    gtfs_ride_stop_related_model
)


def _post_session_query_hook(session_query: sqlalchemy.orm.Query):
    return (
        session_query
        .select_from(model.SiriRideStop)
        .add_entity(model.SiriRide)
        .add_entity(model.SiriStop)
        .add_entity(model.GtfsStop)
        .add_entity(model.SiriVehicleLocation)
        .add_entity(model.GtfsRideStop)
        .add_entity(model.GtfsRide)
        .join(model.SiriRide)
        .join(model.SiriStop)
        .outerjoin(model.GtfsStop, model.SiriRideStop.gtfs_stop_id == model.GtfsStop.id)
        .outerjoin(model.SiriVehicleLocation, model.SiriRideStop.nearest_siri_vehicle_location_id == model.SiriVehicleLocation.id)
        .outerjoin(model.GtfsRide, model.SiriRide.gtfs_ride_id == model.GtfsRide.id)
        .outerjoin(
            model.GtfsRideStop,
            sqlalchemy.sql.and_(model.GtfsRideStop.gtfs_stop_id == model.GtfsStop.id,
                                model.GtfsRideStop.gtfs_ride_id == model.GtfsRide.id)
        )
    )


def _convert_to_dict(obj: model.SiriRideStop):
    siri_ride_stop, siri_ride, siri_stop, gtfs_stop, nearest_siri_vehicle_location, gtfs_ride_stop, gtfs_ride = obj
    res = siri_ride_stop.__dict__
    siri_stop_related_model.add_orm_obj_to_dict_res(siri_stop, res)
    siri_ride_related_model.add_orm_obj_to_dict_res(siri_ride, res)
    gtfs_stop_related_model.add_orm_obj_to_dict_res(gtfs_stop, res)
    nearest_siri_vehicle_location_related_model.add_orm_obj_to_dict_res(nearest_siri_vehicle_location, res)
    gtfs_ride_stop_related_model.add_orm_obj_to_dict_res(gtfs_ride_stop, res)
    return res


@common.router_list(router, TAG, SiriRideStopWithRelatedPydanticModel, WHAT_PLURAL)
def list_(limit: int = common.param_limit(LIST_MAX_LIMIT),
          offset: int = common.param_offset(),
          siri_stop_ids: str = common.param_filter_list('siri stop id'),
          siri_ride_ids: str = common.param_filter_list('siri ride id'),
          siri_vehicle_location__lon__greater_or_equal: float = common.param_filter_greater_or_equal(
              'siri vehicle location lon', 34.808),
          siri_vehicle_location__lon__lower_or_equal: float = common.param_filter_lower_or_equal(
              'siri vehicle location lon', 34.808),
          siri_vehicle_location__lat__greater_or_equal: float = common.param_filter_greater_or_equal(
              'siri vehicle location lat', 31.961),
          siri_vehicle_location__lat__lower_or_equal: float = common.param_filter_lower_or_equal(
              'siri vehicle location lat', 31.961),
          siri_vehicle_location__recorded_at_time_from: datetime.datetime = common.param_filter_datetime_from(
              'siri vehicle location recorded at time'),
          siri_vehicle_location__recorded_at_time_to: datetime.datetime = common.param_filter_datetime_to(
              'siri vehicle location recorded at time'),
          order_by: str = common.param_order_by(),
          ):
    return common.get_list(
        model.SiriRideStop, limit, offset,
        [
            {'type': 'in', 'field': model.SiriRideStop.siri_stop_id, 'value': siri_stop_ids},
            {'type': 'in', 'field': model.SiriRideStop.siri_ride_id, 'value': siri_ride_ids},
            {'type': 'greater_or_equal', 'field': model.SiriVehicleLocation.lon, 'value': siri_vehicle_location__lon__greater_or_equal},
            {'type': 'lower_or_equal', 'field': model.SiriVehicleLocation.lon, 'value': siri_vehicle_location__lon__lower_or_equal},
            {'type': 'greater_or_equal', 'field': model.SiriVehicleLocation.lat, 'value': siri_vehicle_location__lat__greater_or_equal},
            {'type': 'lower_or_equal', 'field': model.SiriVehicleLocation.lat, 'value': siri_vehicle_location__lat__lower_or_equal},
            {'type': 'datetime_from', 'field': model.SiriVehicleLocation.recorded_at_time, 'value': siri_vehicle_location__recorded_at_time_from},
            {'type': 'datetime_to', 'field': model.SiriVehicleLocation.recorded_at_time, 'value': siri_vehicle_location__recorded_at_time_to},
        ],
        order_by=order_by,
        post_session_query_hook=_post_session_query_hook,
        convert_to_dict=_convert_to_dict,
        max_limit=LIST_MAX_LIMIT
    )


@common.router_get(router, TAG, PYDANTIC_MODEL, WHAT_SINGULAR)
def get_(id: int = common.param_get_id(WHAT_SINGULAR)):
    return common.get_item(SQL_MODEL, SQL_MODEL.id, id)
