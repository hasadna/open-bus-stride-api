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


@router.get("/list", tags=['gtfs'], response_model=typing.List[GtfsRoutePydanticModel])
def list_(limit: int = None, offset: int = None,
          date_from: datetime.date = None, date_to: datetime.date = None,
          line_refs: str = None, operator_refs: str = None,
          route_short_name: str = None,
          route_long_name_contains: str = None,
          route_mkt: str = None,
          route_direction: str = None,
          route_alternative: str = None,
          agency_name: str = None,
          route_type: str = None,
          order_by: str = None):
    """
    * limit: limit the number of results, if not specified will limit to 1000 results
    * offset: row number to start returning results from (for pagination)
    * line_refs: comma-separated list
    * operator_refs: comma-separated list
    * route_short_name: string, exact match
    * route_long_name_contains: string, contains
    * route_mkt: string, exact match
    * route_direction: string, exact match
    * route_alternative: string, exact match
    * agency_name: string, exact match
    * route_type: string, exact match
    * order_by: comma-separated list of order by fields, e.g.: "line_ref desc,operator_ref asc"
    """
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
        order_by=order_by
    )


@router.get('/get', tags=['gtfs'], response_model=GtfsRoutePydanticModel)
def get_(id: int):
    return common.get_item(GtfsRoute, GtfsRoute.id, id)
