import typing
import datetime

import pydantic
from fastapi import APIRouter

from open_bus_stride_db.model.route import Route

from . import common


router = APIRouter()


class RoutePydanticModel(pydantic.BaseModel):
    id: int
    min_date: datetime.date
    max_date: datetime.date
    line_ref: int
    operator_ref: int
    siri_published_line_name: str = None
    gtfs_route_short_name: str = None
    gtfs_route_long_name: str = None
    gtfs_route_mkt: str = None
    gtfs_route_direction: str = None
    gtfs_route_alternative: str = None
    gtfs_agency_name: str = None
    gtfs_route_type: str = None
    is_from_gtfs: bool


@router.get("/list", tags=['routes'], response_model=typing.List[RoutePydanticModel])
def list_(limit: int = None, offset: int = None,
          valid_for_date: datetime.date = None, line_ref: int = None, operator_ref: int = None,
          is_from_gtfs: bool = None):
    return common.get_list(
        Route, limit, offset,
        [
            {'type': 'date_in_range', 'fields': (Route.min_date, Route.max_date), 'value': valid_for_date},
            {'type': 'equals', 'field': Route.line_ref, 'value': line_ref},
            {'type': 'equals', 'field': Route.operator_ref, 'value': operator_ref},
            {'type': 'equals', 'field': Route.is_from_gtfs, 'value': is_from_gtfs},
        ]
    )


@router.get('/get', tags=['routes'], response_model=RoutePydanticModel)
def get_(id: int):
    return common.get_item(Route, Route.id, id)
