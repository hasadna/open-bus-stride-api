import typing
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


LIST_MAX_LIMIT = 100
WHAT_SINGULAR = 'gtfs stop'
WHAT_PLURAL = f'{WHAT_SINGULAR}s'
TAG = 'gtfs'
PYDANTIC_MODEL = GtfsStopPydanticModel
SQL_MODEL = GtfsStopPydanticModel


@common.router_list(router, TAG, PYDANTIC_MODEL, WHAT_PLURAL)
def list_(limit: int = common.param_limit(LIST_MAX_LIMIT),
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
        max_limit=LIST_MAX_LIMIT,
        get_count=get_count,
    )


@common.router_get(router, TAG, PYDANTIC_MODEL, WHAT_SINGULAR)
def get_(id: int = common.param_get_id(WHAT_SINGULAR)):
    return common.get_item(SQL_MODEL, SQL_MODEL.id, id)
