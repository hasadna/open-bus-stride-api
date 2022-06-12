import typing
import datetime

import pydantic
from fastapi import APIRouter

from open_bus_stride_db import model

from . import common


router = APIRouter()


class GtfsRideStopPydanticModel(pydantic.BaseModel):
    id: int
    gtfs_stop_id: int
    gtfs_ride_id: int
    arrival_time: datetime.datetime = None
    departure_time: datetime.datetime = None
    stop_sequence: int = None
    pickup_type: int = None
    drop_off_type: int = None
    shape_dist_traveled: int = None


LIST_MAX_LIMIT = 100
WHAT_SINGULAR = 'gtfs ride stop'
WHAT_PLURAL = f'{WHAT_SINGULAR}s'
TAG = 'gtfs'
PYDANTIC_MODEL = GtfsRideStopPydanticModel
SQL_MODEL = model.GtfsRideStop


@common.router_list(router, TAG, PYDANTIC_MODEL, WHAT_PLURAL)
def list_(limit: int = common.param_limit(LIST_MAX_LIMIT),
          offset: int = common.param_offset(),
          get_count: bool = common.param_get_count(),
          gtfs_stop_ids: str = common.doc_param('gtfs stop id', filter_type='list'),
          gtfs_ride_ids: str = common.doc_param('gtfs ride id', filter_type='list')):
    return common.get_list(
        model.GtfsRideStop, limit, offset,
        [
            {'type': 'in', 'field': model.GtfsRideStop.gtfs_stop_id, 'value': gtfs_stop_ids},
            {'type': 'in', 'field': model.GtfsRideStop.gtfs_ride_id, 'value': gtfs_ride_ids},
        ],
        max_limit=LIST_MAX_LIMIT,
        get_count=get_count,
    )


@common.router_get(router, TAG, PYDANTIC_MODEL, WHAT_SINGULAR)
def get_(id: int = common.param_get_id(WHAT_SINGULAR)):
    return common.get_item(SQL_MODEL, SQL_MODEL.id, id)
