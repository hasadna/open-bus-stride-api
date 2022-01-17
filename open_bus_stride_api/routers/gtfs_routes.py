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
          line_ref: int = None, operator_ref: int = None):
    return common.get_list(
        GtfsRoute, limit, offset,
        [
            {'type': 'datetime_from', 'field': GtfsRoute.date, 'value': date_from},
            {'type': 'datetime_to', 'field': GtfsRoute.date, 'value': date_to},
            {'type': 'equals', 'field': GtfsRoute.line_ref, 'value': line_ref},
            {'type': 'equals', 'field': GtfsRoute.operator_ref, 'value': operator_ref},
        ]
    )


@router.get('/get', tags=['gtfs'], response_model=GtfsRoutePydanticModel)
def get_(id: int):
    return common.get_item(GtfsRoute, GtfsRoute.id, id)
