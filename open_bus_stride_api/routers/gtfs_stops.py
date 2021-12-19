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


@router.get("/list", tags=['gtfs_stops'], response_model=typing.List[GtfsStopPydanticModel])
def list_(limit: int = None, offset: int = None,
          date_from: datetime.date = None, date_to: datetime.date = None,
          code: int = None):
    return common.get_list(
        GtfsStop, limit, offset,
        [
            {'type': 'datetime_from', 'field': GtfsStop.date, 'value': date_from},
            {'type': 'datetime_to', 'field': GtfsStop.date, 'value': date_to},
            {'type': 'equals', 'field': GtfsStop.code, 'value': code},
        ]
    )


@router.get('/get', tags=['gtfs_stops'], response_model=GtfsStopPydanticModel)
def get_(id: int):
    return common.get_item(GtfsStop, GtfsStop.id, id)
