import pydantic
from fastapi import APIRouter

from open_bus_stride_db.model.gtfs_ride import GtfsRide

from . import common


router = APIRouter()


class GtfsRidePydanticModel(pydantic.BaseModel):
    id: int
    gtfs_route_id: int
    journey_ref: str


WHAT_SINGULAR = 'gtfs ride'
WHAT_PLURAL = f'{WHAT_SINGULAR}s'
TAG = 'gtfs'
PYDANTIC_MODEL = GtfsRidePydanticModel
SQL_MODEL = GtfsRide


@common.router_list(router, TAG, PYDANTIC_MODEL, WHAT_PLURAL)
def list_(limit: int = common.param_limit(),
          offset: int = common.param_offset(),
          get_count: bool = common.param_get_count(),
          gtfs_route_id: int = common.doc_param('gtfs route id', filter_type='equals'),
          journey_ref_prefix: str = common.doc_param('journey ref', filter_type='prefix')):
    return common.get_list(
        GtfsRide, limit, offset,
        [
            {'type': 'equals', 'field': GtfsRide.gtfs_route_id, 'value': gtfs_route_id},
            {'type': 'prefix', 'field': GtfsRide.journey_ref, 'value': journey_ref_prefix},
        ],
        get_count=get_count,
        pydantic_model=PYDANTIC_MODEL,
    )


@common.router_get(router, TAG, PYDANTIC_MODEL, WHAT_SINGULAR)
def get_(id: int = common.param_get_id(WHAT_SINGULAR)):
    return common.get_item(
        SQL_MODEL, SQL_MODEL.id, id,
        pydantic_model=PYDANTIC_MODEL,
    )
