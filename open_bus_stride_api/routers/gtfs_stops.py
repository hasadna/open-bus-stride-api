import datetime

import pydantic
from fastapi import APIRouter

from open_bus_stride_db.model.gtfs_stop import GtfsStop

from . import common


router = APIRouter()


class GtfsStopPydanticModel(pydantic.BaseModel):
    id: int
    date: datetime.date
    code: int
    lat: float = None
    lon: float = None
    name: str = None
    city: str = None


WHAT_SINGULAR = 'gtfs stop'
WHAT_PLURAL = f'{WHAT_SINGULAR}s'
TAG = 'gtfs'
PYDANTIC_MODEL = GtfsStopPydanticModel
SQL_MODEL = GtfsStop


# This is only used by other routers to include the stop filters
# TODO: Refactor the router_list below to use this variable
gtfs_stop_filter_params = [
    common.RouteParam(
        'date_from', datetime.date, common.DocParam('date', filter_type='date_from'),
        {'type': 'datetime_from', 'field': GtfsStop.date},
    ),
    common.RouteParam(
        'date_to', datetime.date, common.DocParam('date', filter_type='date_to'),
        {'type': 'datetime_to', 'field': GtfsStop.date},
    ),
    common.RouteParam(
        'code', int, common.DocParam('code', filter_type='equals'),
        {'type': 'equals', 'field': GtfsStop.code},
    ),
    common.RouteParam(
        'city', str, common.DocParam('city', filter_type='equals'),
        {'type': 'equals', 'field': GtfsStop.city},
    ),
]


@common.router_list(router, TAG, PYDANTIC_MODEL, WHAT_PLURAL)
def list_(limit: int = common.param_limit(),
          offset: int = common.param_offset(),
          get_count: bool = common.param_get_count(),
          date_from: datetime.date = common.doc_param('date', filter_type='date_from'),
          date_to: datetime.date = common.doc_param('date', filter_type='date_to'),
          code: int = common.doc_param('code', filter_type='equals'),
          city: str = common.doc_param('city', filter_type='equals')):
    return common.get_list(
        GtfsStop, limit, offset,
        [
            {'type': 'datetime_from', 'field': GtfsStop.date, 'value': date_from},
            {'type': 'datetime_to', 'field': GtfsStop.date, 'value': date_to},
            {'type': 'equals', 'field': GtfsStop.code, 'value': code},
            {'type': 'equals', 'field': GtfsStop.city, 'value': city},
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
