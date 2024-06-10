import datetime

import pydantic
from fastapi import APIRouter

from open_bus_stride_db import model
from pydantic.fields import Undefined

from . import common, gtfs_rides, gtfs_stops, gtfs_routes


router = APIRouter()


class GtfsRideStopPydanticModel(pydantic.BaseModel):
    id: int
    gtfs_stop_id: int
    gtfs_ride_id: int
    arrival_time: datetime.datetime = None
    departure_time: datetime.datetime = None
    stop_sequence: int = None
    pickup_type: int = None
    drop_off_type: int = None
    shape_dist_traveled: int = None


WHAT_SINGULAR = 'gtfs ride stop'
WHAT_PLURAL = f'{WHAT_SINGULAR}s'
TAG = 'gtfs'
PYDANTIC_MODEL = GtfsRideStopPydanticModel
SQL_MODEL = model.GtfsRideStop


gtfs_ride_related_model = common.PydanticRelatedModel(
    'gtfs_ride__', gtfs_rides.GtfsRidePydanticModel, ['id']
)
gtfs_stop_related_model = common.PydanticRelatedModel(
    'gtfs_stop__', gtfs_stops.GtfsStopPydanticModel, ['id']
)
gtfs_route_related_model = common.PydanticRelatedModel(
    'gtfs_route__', gtfs_routes.GtfsRoutePydanticModel, ['id']
)


GtfsRideStopWithRelatedPydanticModel = common.pydantic_create_model_with_related(
    'GtfsRideStopWithRelatedPydanticModel',
    GtfsRideStopPydanticModel,
    gtfs_ride_related_model,
    gtfs_stop_related_model,
    gtfs_route_related_model,
)


def _post_session_query_hook(session_query):
    session_query = session_query.select_from(model.GtfsRideStop)
    session_query = gtfs_ride_related_model.add_session_query_entities(model.GtfsRide, session_query)
    session_query = gtfs_stop_related_model.add_session_query_entities(model.GtfsStop, session_query)
    session_query = gtfs_route_related_model.add_session_query_entities(model.GtfsRoute, session_query)
    return (
        session_query
        .join(model.GtfsRide, model.GtfsRideStop.gtfs_ride_id == model.GtfsRide.id)
        .join(model.GtfsStop, model.GtfsRideStop.gtfs_stop_id == model.GtfsStop.id)
        .join(model.GtfsRoute, model.GtfsRide.gtfs_route_id == model.GtfsRoute.id)
    )


gtfs_ride_stop_filter_params = [
    common.RouteParam(
        'arrival_time_from', datetime.datetime,
        common.DocParam('arrival time from', filter_type='datetime_from', default=Undefined),
        {'type': 'datetime_from', 'field': model.GtfsRideStop.arrival_time},
    ),
    common.RouteParam(
        'arrival_time_to', datetime.datetime,
        common.DocParam('arrival time to', filter_type='datetime_to', default=Undefined),
        {'type': 'datetime_to', 'field': model.GtfsRideStop.arrival_time},
    ),
    common.RouteParam(
        'gtfs_stop_ids', str, common.DocParam('gtfs stop id', filter_type='list'),
        {'type': 'in', 'field': model.GtfsRideStop.gtfs_stop_id},
    ),
    common.RouteParam(
        'gtfs_ride_ids', str, common.DocParam('gtfs ride id', filter_type='list'),
        {'type': 'in', 'field': model.GtfsRideStop.gtfs_ride_id},
    ),
]


gtfs_ride_stop_filter_params_with_related = [
    *gtfs_ride_stop_filter_params,
    *common.get_route_params_with_prefix(
        'gtfs_ride__', "related gtfs ride's",
        gtfs_rides.gtfs_ride_filter_params
    ),
    *common.get_route_params_with_prefix(
        'gtfs_stop__', "related gtfs stop's",
        gtfs_stops.gtfs_stop_filter_params
    ),
    *common.get_route_params_with_prefix(
        'gtfs_route__', "related gtfs route's",
        gtfs_routes.gtfs_route_filter_params
    ),
]


gtfs_ride_stop_list_params = [
    common.param_limit(as_RouteParam=True),
    common.param_offset(as_RouteParam=True),
    common.param_get_count(as_RouteParam=True),
    *gtfs_ride_stop_filter_params_with_related,
    common.param_order_by(as_RouteParam=True),
]


@common.add_api_router_list(router, TAG, GtfsRideStopWithRelatedPydanticModel, WHAT_PLURAL, gtfs_ride_stop_list_params)
def list_(**kwargs):
    return common.get_list(
        SQL_MODEL, kwargs['limit'], kwargs['offset'],
        [
            route_param.get_filter(kwargs)
            for route_param in gtfs_ride_stop_filter_params_with_related
        ],
        order_by=kwargs['order_by'],
        post_session_query_hook=_post_session_query_hook,
        get_count=kwargs['get_count'],
        pydantic_model=PYDANTIC_MODEL,
    )


@common.router_get(router, TAG, PYDANTIC_MODEL, WHAT_SINGULAR)
def get_(id: int = common.param_get_id(WHAT_SINGULAR)):
    return common.get_item(
        SQL_MODEL, SQL_MODEL.id, id,
        pydantic_model=PYDANTIC_MODEL,
    )
