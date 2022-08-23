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


@common.router_list(router, TAG, GtfsRideWithRelatedPydanticModel, WHAT_PLURAL)
def list_(limit: int = common.param_limit(),
          offset: int = common.param_offset(),
          get_count: bool = common.param_get_count(),
          gtfs_route_id: int = common.doc_param('gtfs route id', filter_type='equals'),
          journey_ref_prefix: str = common.doc_param('journey ref', filter_type='prefix'),
          start_time_from: datetime.datetime = common.doc_param('start time from', filter_type='datetime_from'),
          start_time_to: datetime.datetime = common.doc_param('start time to', filter_type='datetime_to'),
          gtfs_route__date_from: datetime.date = common.doc_param('gtfs_route date', filter_type='date_from'),
          gtfs_route__date_to: datetime.date = common.doc_param('gtfs_route date', filter_type='date_to'),
          gtfs_route__line_refs: str = common.doc_param('gtfs_route line ref', filter_type='list'),
          gtfs_route__operator_refs: str = common.doc_param('gtfs_route operator ref', 'list', description='Agency identifier. To get it, first query gtfs_agencies.', example="3 for Eged"),
          gtfs_route__route_short_name: str = common.doc_param('gtfs_route short name', 'equals', description='Line number.', example="480"),
          gtfs_route__route_long_name_contains: str = common.doc_param('gtfs_route long name', filter_type='contains'),
          gtfs_route__route_mkt: str = common.doc_param('gtfs_route mkt', filter_type='equals'),
          gtfs_route__route_direction: str = common.doc_param('gtfs_route direction', filter_type='equals'),
          gtfs_route__route_alternative: str = common.doc_param('gtfs_route alternative', filter_type='equals'),
          gtfs_route__agency_name: str = common.doc_param('gtfs_route agency name', filter_type='equals'),
          gtfs_route__route_type: str = common.doc_param('gtfs_route type', filter_type='equals'),
          order_by: str = common.param_order_by()):
    return common.get_list(
        SQL_MODEL, limit, offset,
        [
            {'type': 'equals', 'field': model.GtfsRide.gtfs_route_id, 'value': gtfs_route_id},
            {'type': 'prefix', 'field': model.GtfsRide.journey_ref, 'value': journey_ref_prefix},
            {'type': 'datetime_from', 'field': model.GtfsRide.start_time, 'value': start_time_from},
            {'type': 'datetime_to', 'field': model.GtfsRide.end_time, 'value': start_time_to},
            {'type': 'datetime_from', 'field': model.GtfsRoute.date, 'value': gtfs_route__date_from},
            {'type': 'datetime_to', 'field': model.GtfsRoute.date, 'value': gtfs_route__date_to},
            {'type': 'in', 'field': model.GtfsRoute.line_ref, 'value': gtfs_route__line_refs},
            {'type': 'in', 'field': model.GtfsRoute.operator_ref, 'value': gtfs_route__operator_refs},
            {'type': 'equals', 'field': model.GtfsRoute.route_short_name, 'value': gtfs_route__route_short_name},
            {'type': 'contains', 'field': model.GtfsRoute.route_long_name, 'value': gtfs_route__route_long_name_contains},
            {'type': 'equals', 'field': model.GtfsRoute.route_mkt, 'value': gtfs_route__route_mkt},
            {'type': 'equals', 'field': model.GtfsRoute.route_direction, 'value': gtfs_route__route_direction},
            {'type': 'equals', 'field': model.GtfsRoute.route_alternative, 'value': gtfs_route__route_alternative},
            {'type': 'equals', 'field': model.GtfsRoute.agency_name, 'value': gtfs_route__agency_name},
            {'type': 'equals', 'field': model.GtfsRoute.route_type, 'value': gtfs_route__route_type},
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
