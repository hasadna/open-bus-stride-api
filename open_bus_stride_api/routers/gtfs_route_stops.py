import typing

import pydantic
from fastapi import APIRouter

from open_bus_stride_db.model.gtfs_route_stop import GtfsRouteStop

from . import common


router = APIRouter()


class GtfsRouteStopPydanticModel(pydantic.BaseModel):
    id: int
    gtfs_stop_id: int
    gtfs_route_id: int
    order: int = None


@router.get("/list", tags=['gtfs_route_stops'], response_model=typing.List[GtfsRouteStopPydanticModel])
def list_(limit: int = None, offset: int = None,
          gtfs_stop_id: int = None, gtfs_route_id: int = None, order: int = None):
    return common.get_list(
        GtfsRouteStop, limit, offset,
        [
            {'type': 'equals', 'field': GtfsRouteStop.gtfs_stop_id, 'value': gtfs_stop_id},
            {'type': 'equals', 'field': GtfsRouteStop.gtfs_route_id, 'value': gtfs_route_id},
            {'type': 'equals', 'field': GtfsRouteStop.order, 'value': order},
        ]
    )


@router.get('/get', tags=['gtfs_route_stops'], response_model=GtfsRouteStopPydanticModel)
def get_(id: int):
    return common.get_item(GtfsRouteStop, GtfsRouteStop.id, id)
