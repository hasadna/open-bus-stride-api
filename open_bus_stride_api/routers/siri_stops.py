import typing

import pydantic
from fastapi import APIRouter

from open_bus_stride_db.model.siri_stop import SiriStop

from . import common


router = APIRouter()


class SiriStopPydanticModel(pydantic.BaseModel):
    id: int
    code: int


LIST_MAX_LIMIT = 100
WHAT_SINGULAR = 'siri stop'
WHAT_PLURAL = f'{WHAT_SINGULAR}s'
TAG = 'siri'
PYDANTIC_MODEL = SiriStopPydanticModel
SQL_MODEL = SiriStop


@common.router_list(router, TAG, PYDANTIC_MODEL, WHAT_PLURAL)
def list_(limit: int = common.param_limit(LIST_MAX_LIMIT),
          offset: int = common.param_offset(),
          codes: str = common.param_filter_list('stop code'),
          order_by: str = common.param_order_by()):
    return common.get_list(
        SiriStop, limit, offset,
        [
            {'type': 'in', 'field': SiriStop.code, 'value': codes},
        ],
        order_by=order_by,
        max_limit=LIST_MAX_LIMIT
    )


@common.router_get(router, TAG, PYDANTIC_MODEL, WHAT_SINGULAR)
def get_(id: int = common.param_get_id(WHAT_SINGULAR)):
    return common.get_item(SQL_MODEL, SQL_MODEL.id, id)
