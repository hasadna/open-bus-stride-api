import typing
import datetime

import pydantic
from fastapi import APIRouter

from open_bus_stride_db.model.stop import Stop

from . import common


router = APIRouter()


class StopPydanticModel(pydantic.BaseModel):
    id: int
    min_date: datetime.date
    max_date: datetime.date
    code: int
    lat: float = None
    lon: float = None
    name: str = None
    city: str = None
    is_from_gtfs: bool


@router.get("/list", tags=['stops'], response_model=typing.List[StopPydanticModel])
def list_(limit: int = None, offset: int = None,
          valid_for_date: datetime.date = None, code: int = None, is_from_gtfs: bool = None):
    return common.get_list(
        Stop, limit, offset,
        [
            {'type': 'date_in_range', 'fields': (Stop.min_date, Stop.max_date), 'value': valid_for_date},
            {'type': 'equals', 'field': Stop.code, 'value': code},
            {'type': 'equals', 'field': Stop.is_from_gtfs, 'value': is_from_gtfs},
        ]
    )


@router.get('/get', tags=['stops'], response_model=StopPydanticModel)
def get_(id: int):
    return common.get_item(Stop, Stop.id, id)
