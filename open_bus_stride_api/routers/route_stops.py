import typing
import datetime

import pydantic
from fastapi import APIRouter

from open_bus_stride_db.model.route_stop import RouteStop

from . import common


router = APIRouter()


class RouteStopPydanticModel(pydantic.BaseModel):
    id: int
    stop_id: int
    route_id: int
    order: int = None
    is_from_gtfs: bool


@router.get("/list", tags=['route_stops'], response_model=typing.List[RouteStopPydanticModel])
def list_(limit: int = None, offset: int = None,
          stop_id: int = None, route_id: int = None, order: int = None, is_from_gtfs: bool = None):
    return common.get_list(
        RouteStop, limit, offset,
        [
            {'type': 'equals', 'field': RouteStop.stop_id, 'value': stop_id},
            {'type': 'equals', 'field': RouteStop.route_id, 'value': route_id},
            {'type': 'equals', 'field': RouteStop.order, 'value': order},
            {'type': 'equals', 'field': RouteStop.is_from_gtfs, 'value': is_from_gtfs},
        ]
    )


@router.get('/get', tags=['route_stops'], response_model=RouteStopPydanticModel)
def get_(id: int):
    return common.get_item(RouteStop, RouteStop.id, id)
