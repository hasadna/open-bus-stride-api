import typing

import pydantic
from fastapi import APIRouter

from open_bus_stride_db.model.siri_stop import SiriStop

from . import common


router = APIRouter()


class SiriStopPydanticModel(pydantic.BaseModel):
    id: int
    code: int


@router.get("/list", tags=['siri_stops'], response_model=typing.List[SiriStopPydanticModel])
def list_(limit: int = None, offset: int = None,
          codes: str = None,
          order_by: str = None):
    """
    * codes: comma-separated list
    * order_by: comma-separated list of order by fields, e.g.: "code asc"
    """
    return common.get_list(
        SiriStop, limit, offset,
        [
            {'type': 'in', 'field': SiriStop.code, 'value': codes},
        ],
        order_by=order_by
    )


@router.get('/get', tags=['siri_stops'], response_model=SiriStopPydanticModel)
def get_(id: int):
    return common.get_item(SiriStop, SiriStop.id, id)
