import datetime

import pydantic
from fastapi import APIRouter

from open_bus_stride_db.model.gtfs_route import GtfsRoute

from . import common


router = APIRouter()


class GtfsRoutePydanticModel(pydantic.BaseModel):
    id: int
    date: datetime.date
    line_ref: int
    operator_ref: int
    route_short_name: str = None
    route_long_name: str = None
    route_mkt: str = None
    route_direction: str = None
    route_alternative: str = None
    agency_name: str = None
    route_type: str = None


WHAT_SINGULAR = 'gtfs route'
WHAT_PLURAL = f'{WHAT_SINGULAR}s'
TAG = 'gtfs'
PYDANTIC_MODEL = GtfsRoutePydanticModel
SQL_MODEL = GtfsRoute


gtfs_route_filter_params = [
    common.RouteParam(
        'date_from', datetime.date, common.DocParam('date', filter_type='date_from'),
        {'type': 'datetime_from', 'field': GtfsRoute.date}
    ),
    common.RouteParam(
        'date_to', datetime.date, common.DocParam('date', filter_type='date_to'),
        {'type': 'datetime_to', 'field': GtfsRoute.date}
    ),
    common.RouteParam(
        'line_refs', str, common.DocParam('line ref', filter_type='list'),
        {'type': 'in', 'field': GtfsRoute.line_ref},
    ),
    common.RouteParam(
        'operator_refs', str, common.DocParam('operator ref', 'list', description='Agency identifier. To get it, first query gtfs_agencies.', example="3 for Eged"),
        {'type': 'in', 'field': GtfsRoute.operator_ref},
    ),
    common.RouteParam(
        'route_short_name', str, common.DocParam('route short name', 'equals', description='Line number.', example="480"),
        {'type': 'equals', 'field': GtfsRoute.route_short_name},
    ),
    common.RouteParam(
        'route_long_name_contains', str, common.DocParam('route long name', filter_type='contains'),
        {'type': 'contains', 'field': GtfsRoute.route_long_name},
    ),
    common.RouteParam(
        'route_mkt', str, common.DocParam('route mkt', filter_type='equals'),
        {'type': 'equals', 'field': GtfsRoute.route_mkt},
    ),
    common.RouteParam(
        'route_direction', str, common.DocParam('route direction', filter_type='equals'),
        {'type': 'equals', 'field': GtfsRoute.route_direction}
    ),
    common.RouteParam(
        'route_alternative', str, common.DocParam('route alternative', filter_type='equals'),
        {'type': 'equals', 'field': GtfsRoute.route_alternative},
    ),
    common.RouteParam(
        'agency_name', str, common.DocParam('agency name', filter_type='equals'),
        {'type': 'equals', 'field': GtfsRoute.agency_name},
    ),
    common.RouteParam(
        'route_type', str, common.DocParam('route type', filter_type='equals'),
        {'type': 'equals', 'field': GtfsRoute.route_type},
    ),
]


gtfs_route_list_params = [
    common.param_limit(as_RouteParam=True),
    common.param_offset(as_RouteParam=True),
    common.param_get_count(as_RouteParam=True),
    *gtfs_route_filter_params,
    common.param_order_by(as_RouteParam=True),
]


@common.add_api_router_list(router, TAG, PYDANTIC_MODEL, WHAT_PLURAL, gtfs_route_list_params)
def list_(**kwargs):
    return common.get_list(
        GtfsRoute, kwargs['limit'], kwargs['offset'],
        [
            route_param.get_filter(kwargs)
            for route_param in gtfs_route_filter_params
        ],
        order_by=kwargs['order_by'],
        get_count=kwargs['get_count'],
        pydantic_model=PYDANTIC_MODEL,
    )


@common.router_get(router, TAG, PYDANTIC_MODEL, WHAT_SINGULAR)
def get_(id: int = common.param_get_id(WHAT_SINGULAR)):
    return common.get_item(
        SQL_MODEL, SQL_MODEL.id, id,
        pydantic_model=PYDANTIC_MODEL,
    )
