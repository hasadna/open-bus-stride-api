import datetime

import pydantic
from fastapi import APIRouter
import sqlalchemy.orm

from open_bus_stride_db import model

from . import common
from . import siri_rides, siri_stops, gtfs_stops, siri_vehicle_locations, gtfs_ride_stops, gtfs_rides, gtfs_routes


router = APIRouter()


class SiriRideStopPydanticModel(pydantic.BaseModel):
    id: int
    siri_stop_id: int
    siri_ride_id: int
    order: int
    gtfs_stop_id: int = None
    nearest_siri_vehicle_location_id: int = None


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
gtfs_ride_related_model = common.PydanticRelatedModel(
    'gtfs_ride__', gtfs_rides.GtfsRidePydanticModel, ['id']
)
gtfs_route_related_model = common.PydanticRelatedModel(
    'gtfs_route__', gtfs_routes.GtfsRoutePydanticModel, ['id']
)


SiriRideStopWithRelatedPydanticModel = common.pydantic_create_model_with_related(
    'SiriRideStopWithRelatedPydanticModel',
    SiriRideStopPydanticModel,
    siri_stop_related_model,
    siri_ride_related_model,
    gtfs_stop_related_model,
    nearest_siri_vehicle_location_related_model,
    gtfs_ride_stop_related_model,
    gtfs_ride_related_model,
    gtfs_route_related_model,
)


def _post_session_query_hook(session_query: sqlalchemy.orm.Query):
    session_query = session_query.select_from(model.SiriRideStop)
    session_query = siri_ride_related_model.add_session_query_entities(model.SiriRide, session_query)
    session_query = siri_stop_related_model.add_session_query_entities(model.SiriStop, session_query)
    session_query = gtfs_stop_related_model.add_session_query_entities(model.GtfsStop, session_query)
    session_query = nearest_siri_vehicle_location_related_model.add_session_query_entities(model.SiriVehicleLocation, session_query)
    session_query = gtfs_ride_stop_related_model.add_session_query_entities(model.GtfsRideStop, session_query)
    session_query = gtfs_ride_related_model.add_session_query_entities(model.GtfsRide, session_query)
    session_query = gtfs_route_related_model.add_session_query_entities(model.GtfsRoute, session_query)
    return (
        session_query
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
        .outerjoin(model.GtfsRoute, model.GtfsRide.gtfs_route_id == model.GtfsRoute.id)
    )


@common.router_list(router, TAG, SiriRideStopWithRelatedPydanticModel, WHAT_PLURAL)
def list_(limit: int = common.param_limit(),
          offset: int = common.param_offset(),
          get_count: bool = common.param_get_count(),
          siri_stop_ids: str = common.doc_param('siri stop id', filter_type='list'),
          siri_ride_ids: str = common.doc_param('siri ride id', filter_type='list'),
          siri_vehicle_location__lon__greater_or_equal: float = common.doc_param(
              'siri vehicle location lon', filter_type='greater_or_equal', example='34.808'),
          siri_vehicle_location__lon__lower_or_equal: float = common.doc_param(
              'siri vehicle location lon', filter_type='lower_or_equal', example='34.808'),
          siri_vehicle_location__lat__greater_or_equal: float = common.doc_param(
              'siri vehicle location lat', filter_type='greater_or_equal', example='31.961'),
          siri_vehicle_location__lat__lower_or_equal: float = common.doc_param(
              'siri vehicle location lat', filter_type='lower_or_equal', example='31.961'),
          siri_vehicle_location__recorded_at_time_from: datetime.datetime = common.doc_param(
              'siri vehicle location recorded at time', filter_type='datetime_from'),
          siri_vehicle_location__recorded_at_time_to: datetime.datetime = common.doc_param(
              'siri vehicle location recorded at time', filter_type='datetime_to'),
          siri_ride__scheduled_start_time_from: datetime.datetime = common.doc_param(
              'siri ride scheduled start time', filter_type='datetime_from'),
          siri_ride__scheduled_start_time_to: datetime.datetime = common.doc_param(
              'siri ride scheduled start time', filter_type='datetime_to'),
          gtfs_stop__lat__greater_or_equal: float = common.doc_param(
              'gtfs stop lat', filter_type='greater_or_equal', example='31.961'),
          gtfs_stop__lat__lower_or_equal: float = common.doc_param(
              'gtfs stop lat', filter_type='lower_or_equal', example='31.961'),
          gtfs_stop__lon__greater_or_equal: float = common.doc_param(
              'gtfs stop lon', filter_type='greater_or_equal', example='34.808'),
          gtfs_stop__lon__lower_or_equal: float = common.doc_param(
              'gtfs stop lon', filter_type='lower_or_equal', example='34.808'),
          gtfs_date_from: datetime.date = common.doc_param(
              'gtfs date', filter_type='date_from',
              description='filter all gtfs related records on this date'),
          gtfs_date_to: datetime.date = common.doc_param(
              'gtfs date', filter_type='date_to',
              description='filter all gtfs related records on this date'),
          order_by: str = common.param_order_by(default=''),
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
            {'type': 'greater_or_equal', 'field': model.GtfsStop.lat, 'value': gtfs_stop__lat__greater_or_equal},
            {'type': 'lower_or_equal', 'field': model.GtfsStop.lat, 'value': gtfs_stop__lat__lower_or_equal},
            {'type': 'greater_or_equal', 'field': model.GtfsStop.lon, 'value': gtfs_stop__lon__greater_or_equal},
            {'type': 'lower_or_equal', 'field': model.GtfsStop.lon, 'value': gtfs_stop__lon__lower_or_equal},
            {'type': 'datetime_from', 'field': model.GtfsRoute.date, 'value': gtfs_date_from},
            {'type': 'datetime_to', 'field': model.GtfsRoute.date, 'value': gtfs_date_to},
            {'type': 'datetime_from', 'field': model.GtfsStop.date, 'value': gtfs_date_from},
            {'type': 'datetime_to', 'field': model.GtfsStop.date, 'value': gtfs_date_to},
            {'type': 'datetime_from', 'field': model.SiriRide.scheduled_start_time, 'value': siri_ride__scheduled_start_time_from},
            {'type': 'datetime_to', 'field': model.SiriRide.scheduled_start_time, 'value': siri_ride__scheduled_start_time_to},
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
