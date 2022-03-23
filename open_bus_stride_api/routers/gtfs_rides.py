import typing

import pydantic
from fastapi import APIRouter

from open_bus_stride_db.model.gtfs_ride import GtfsRide

from . import common


router = APIRouter()


class GtfsRidePydanticModel(pydantic.BaseModel):
    id: int
    gtfs_route_id: int
    journey_ref: str


LIST_MAX_LIMIT = 100
WHAT_SINGULAR = 'gtfs ride'
WHAT_PLURAL = f'{WHAT_SINGULAR}s'
TAG = 'gtfs'
PYDANTIC_MODEL = GtfsRidePydanticModel
SQL_MODEL = GtfsRide


@common.router_list(router, TAG, PYDANTIC_MODEL, WHAT_PLURAL)
def list_(limit: int = common.param_limit(LIST_MAX_LIMIT),
          offset: int = common.param_offset(),
          gtfs_route_id: int = common.param_filter_equals('gtfs route id'),
          journey_ref_prefix: str = common.param_filter_prefix('journey ref')):
    return common.get_list(
        GtfsRide, limit, offset,
        [
            {'type': 'equals', 'field': GtfsRide.gtfs_route_id, 'value': gtfs_route_id},
            {'type': 'prefix', 'field': GtfsRide.journey_ref, 'value': journey_ref_prefix},
        ],
        max_limit=LIST_MAX_LIMIT
    )


@common.router_get(router, TAG, PYDANTIC_MODEL, WHAT_SINGULAR)
def get_(id: int = common.param_get_id(WHAT_SINGULAR)):
    return common.get_item(SQL_MODEL, SQL_MODEL.id, id)
