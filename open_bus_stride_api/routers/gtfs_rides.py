import datetime
import pydantic
from fastapi import APIRouter

from open_bus_stride_db import model

from . import common, gtfs_routes


router = APIRouter()


class GtfsRidePydanticModel(pydantic.BaseModel):
    id: int
    gtfs_route_id: int
    journey_ref: str = None
    start_time: datetime.datetime = None
    end_time: datetime.datetime = None


WHAT_SINGULAR = 'gtfs ride'
WHAT_PLURAL = f'{WHAT_SINGULAR}s'
TAG = 'gtfs'
PYDANTIC_MODEL = GtfsRidePydanticModel
SQL_MODEL = model.GtfsRide


gtfs_route_related_model = common.PydanticRelatedModel(
    'gtfs_route__', gtfs_routes.GtfsRoutePydanticModel, ['id']
)


GtfsRideWithRelatedPydanticModel = common.pydantic_create_model_with_related(
    'GtfsRideWithRelatedPydanticModel',
    GtfsRidePydanticModel,
    gtfs_route_related_model,
)


def _post_session_query_hook(session_query):
    session_query = session_query.select_from(model.GtfsRide)
    session_query = gtfs_route_related_model.add_session_query_entities(model.GtfsRoute, session_query)
    return (
        session_query
        .join(model.GtfsRoute, model.GtfsRide.gtfs_route_id == model.GtfsRoute.id)
    )


gtfs_ride_filter_params = [
    common.RouteParam(
        'gtfs_route_id', int, common.DocParam('gtfs route id', filter_type='equals'),
        {'type': 'equals', 'field': model.GtfsRide.gtfs_route_id},
    ),
    common.RouteParam(
        'journey_ref_prefix', str, common.DocParam('journey ref', filter_type='prefix'),
        {'type': 'prefix', 'field': model.GtfsRide.journey_ref}
    ),
    common.RouteParam(
        'start_time_from', datetime.datetime, common.DocParam('start time from', filter_type='datetime_from'),
        {'type': 'datetime_from', 'field': model.GtfsRide.start_time},
    ),
    common.RouteParam(
        'start_time_to', datetime.datetime, common.DocParam('start time to', filter_type='datetime_to'),
        {'type': 'datetime_to', 'field': model.GtfsRide.end_time},
    ),
]


gtfs_ride_filter_params_with_related = [
    *gtfs_ride_filter_params,
    *common.get_route_params_with_prefix(
        'gtfs_route__', "related gtfs route's",
        gtfs_routes.gtfs_route_filter_params
    ),
]


gtfs_ride_list_params = [
    common.param_limit(as_RouteParam=True),
    common.param_offset(as_RouteParam=True),
    common.param_get_count(as_RouteParam=True),
    *gtfs_ride_filter_params_with_related,
    common.param_order_by(as_RouteParam=True),
]


@common.add_api_router_list(router, TAG, GtfsRideWithRelatedPydanticModel, WHAT_PLURAL, gtfs_ride_list_params)
def list_(**kwargs):
    return common.get_list(
        SQL_MODEL, kwargs['limit'], kwargs['offset'],
        [
            route_param.get_filter(kwargs)
            for route_param in gtfs_ride_filter_params_with_related
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
