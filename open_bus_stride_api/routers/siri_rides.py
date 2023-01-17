import datetime

import pydantic
from fastapi import APIRouter
import sqlalchemy.orm

from open_bus_stride_db import model

from . import common, gtfs_rides, gtfs_routes, siri_routes


router = APIRouter()


class SiriRidePydanticModel(pydantic.BaseModel):
    id: int
    siri_route_id: int
    journey_ref: str
    scheduled_start_time: datetime.datetime
    vehicle_ref: str = None
    updated_first_last_vehicle_locations: datetime.datetime = None
    first_vehicle_location_id: int = None
    last_vehicle_location_id: int = None
    updated_duration_minutes: datetime.datetime = None
    duration_minutes: int = None
    journey_gtfs_ride_id: int = None
    route_gtfs_ride_id: int = None
    gtfs_ride_id: int = None


WHAT_SINGULAR = 'siri ride'
WHAT_PLURAL = f'{WHAT_SINGULAR}s'
TAG = 'siri'
PYDANTIC_MODEL = SiriRidePydanticModel
SQL_MODEL = model.SiriRide


siri_route_related_model = common.PydanticRelatedModel(
    'siri_route__', siri_routes.SiriRoutePydanticModel, ['id']
)
gtfs_ride_related_model = common.PydanticRelatedModel(
    'gtfs_ride__', gtfs_rides.GtfsRidePydanticModel, ['id']
)
gtfs_route_related_model = common.PydanticRelatedModel(
    'gtfs_route__', gtfs_routes.GtfsRoutePydanticModel, ['id']
)


SiriRideWithRelatedPydanticModel = common.pydantic_create_model_with_related(
    'SiriRideWithRelatedPydanticModel',
    SiriRidePydanticModel,
    siri_route_related_model,
    gtfs_ride_related_model,
    gtfs_route_related_model,
)


def _post_session_query_hook(session_query: sqlalchemy.orm.Query):
    session_query = session_query.select_from(model.SiriRide)
    session_query = siri_route_related_model.add_session_query_entities(model.SiriRoute, session_query)
    session_query = gtfs_ride_related_model.add_session_query_entities(model.GtfsRide, session_query)
    session_query = gtfs_route_related_model.add_session_query_entities(model.GtfsRoute, session_query)
    return (
        session_query
        .join(model.SiriRoute, model.SiriRide.siri_route_id == model.SiriRoute.id)
        .join(model.GtfsRide, model.SiriRide.gtfs_ride_id == model.GtfsRide.id)
        .join(model.GtfsRoute, model.GtfsRide.gtfs_route_id == model.GtfsRoute.id)
    )


siri_ride_filter_params = [
    common.RouteParam(
        'siri_route_ids', str, common.DocParam('siri route ids', filter_type='list'),
        {'type': 'in', 'field': model.SiriRide.siri_route_id},
    ),
    common.RouteParam(
        'siri_route__line_refs', str, common.DocParam('siri route line refs', filter_type='list'),
        {'type': 'in', 'field': model.SiriRoute.line_ref},
    ),
    common.RouteParam(
        'siri_route__operator_refs', str, common.DocParam('siri route operator refs', filter_type='list'),
        {'type': 'in', 'field': model.SiriRoute.operator_ref},
    ),
    common.RouteParam(
        'journey_ref_prefix', str, common.DocParam('journey ref', filter_type='prefix'),
        {'type': 'prefix', 'field': model.SiriRide.journey_ref},
    ),
    common.RouteParam(
        'journey_refs', str, common.DocParam('journey ref', filter_type='list'),
        {'type': 'in', 'field': model.SiriRide.journey_ref},
    ),
    common.RouteParam(
        'vehicle_refs', str, common.DocParam('vehicle ref', filter_type='list'),
        {'type': 'in', 'field': model.SiriRide.vehicle_ref},
    ),
    common.RouteParam(
        'scheduled_start_time_from', datetime.datetime, common.DocParam('scheduled start time', filter_type='datetime_from'),
        {'type': 'datetime_from', 'field': model.SiriRide.scheduled_start_time},
    ),
    common.RouteParam(
        'scheduled_start_time_to', datetime.datetime, common.DocParam('scheduled start time', filter_type='datetime_to'),
        {'type': 'datetime_to', 'field': model.SiriRide.scheduled_start_time},
    ),
]


siri_ride_filter_params_with_related = [
    *common.get_route_params_with_prefix(
        'gtfs_route__', "related gtfs route's",
        gtfs_routes.gtfs_route_filter_params
    ),
    *common.get_route_params_with_prefix(
        'gtfs_ride__', "related gtfs ride's",
        gtfs_rides.gtfs_ride_filter_params,
    ),
    *siri_ride_filter_params,
]


siri_ride_list_params = [
    common.param_limit(as_RouteParam=True),
    common.param_offset(as_RouteParam=True),
    common.param_get_count(as_RouteParam=True),
    *siri_ride_filter_params_with_related,
    common.param_order_by(as_RouteParam=True),
]


@common.add_api_router_list(router, TAG, SiriRideWithRelatedPydanticModel, WHAT_PLURAL, siri_ride_list_params)
def list_(**kwargs):
    return common.get_list(
        SQL_MODEL, kwargs['limit'], kwargs['offset'],
        [
            route_param.get_filter(kwargs)
            for route_param in siri_ride_filter_params_with_related
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
