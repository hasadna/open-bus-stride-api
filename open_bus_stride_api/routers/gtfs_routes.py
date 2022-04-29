import typing
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


LIST_MAX_LIMIT = 100
WHAT_SINGULAR = 'gtfs route'
WHAT_PLURAL = f'{WHAT_SINGULAR}s'
TAG = 'gtfs'
PYDANTIC_MODEL = GtfsRoutePydanticModel
SQL_MODEL = GtfsRoute


@common.router_list(router, TAG, PYDANTIC_MODEL, WHAT_PLURAL)
def list_(limit: int = common.param_limit(LIST_MAX_LIMIT),
          offset: int = common.param_offset(),
          get_count: bool = common.param_get_count(),
          date_from: datetime.date = common.param_filter_date_from('date'),
          date_to: datetime.date = common.param_filter_date_to('date'),
          line_refs: str = common.param_filter_list('line ref'),
          operator_refs: str = common.param_filter_list('operator ref'),
          route_short_name: str = common.param_filter_equals('route short name'),
          route_long_name_contains: str = common.param_filter_contains('route long name'),
          route_mkt: str = common.param_filter_equals('route mkt'),
          route_direction: str = common.param_filter_equals('route direction'),
          route_alternative: str = common.param_filter_equals('route alternative'),
          agency_name: str = common.param_filter_equals('agency name'),
          route_type: str = common.param_filter_equals('route type'),
          order_by: str = common.param_order_by()):
    return common.get_list(
        GtfsRoute, limit, offset,
        [
            {'type': 'datetime_from', 'field': GtfsRoute.date, 'value': date_from},
            {'type': 'datetime_to', 'field': GtfsRoute.date, 'value': date_to},
            {'type': 'in', 'field': GtfsRoute.line_ref, 'value': line_refs},
            {'type': 'in', 'field': GtfsRoute.operator_ref, 'value': operator_refs},
            {'type': 'equals', 'field': GtfsRoute.route_short_name, 'value': route_short_name},
            {'type': 'contains', 'field': GtfsRoute.route_long_name, 'value': route_long_name_contains},
            {'type': 'equals', 'field': GtfsRoute.route_mkt, 'value': route_mkt},
            {'type': 'equals', 'field': GtfsRoute.route_direction, 'value': route_direction},
            {'type': 'equals', 'field': GtfsRoute.route_alternative, 'value': route_alternative},
            {'type': 'equals', 'field': GtfsRoute.agency_name, 'value': agency_name},
            {'type': 'equals', 'field': GtfsRoute.route_type, 'value': route_type},
        ],
        order_by=order_by,
        max_limit=LIST_MAX_LIMIT,
        get_count=get_count,
    )


@common.router_get(router, TAG, PYDANTIC_MODEL, WHAT_SINGULAR)
def get_(id: int = common.param_get_id(WHAT_SINGULAR)):
    return common.get_item(SQL_MODEL, SQL_MODEL.id, id)
