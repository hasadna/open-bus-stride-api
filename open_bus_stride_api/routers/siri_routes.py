import pydantic
from fastapi import APIRouter

from open_bus_stride_db.model.siri_route import SiriRoute

from . import common


router = APIRouter()


class SiriRoutePydanticModel(pydantic.BaseModel):
    id: int
    line_ref: int
    operator_ref: int


WHAT_SINGULAR = 'siri route'
WHAT_PLURAL = f'{WHAT_SINGULAR}s'
TAG = 'siri'
PYDANTIC_MODEL = SiriRoutePydanticModel
SQL_MODEL = SiriRoute


@common.router_list(router, TAG, PYDANTIC_MODEL, WHAT_PLURAL)
def list_(limit: int = common.param_limit(),
          offset: int = common.param_offset(),
          get_count: bool = common.param_get_count(),
          line_refs: str = common.doc_param('line ref', filter_type='list'),
          operator_refs: str = common.doc_param('operator ref', filter_type='list'),
          order_by: str = common.param_order_by()):
    return common.get_list(
        SQL_MODEL, limit, offset,
        [
            {'type': 'in', 'field': SiriRoute.line_ref, 'value': line_refs},
            {'type': 'in', 'field': SiriRoute.operator_ref, 'value': operator_refs},
        ],
        order_by=order_by,
        get_count=get_count,
    )


@common.router_get(router, TAG, PYDANTIC_MODEL, WHAT_SINGULAR)
def get_(id: int = common.param_get_id(WHAT_SINGULAR)):
    return common.get_item(SQL_MODEL, SQL_MODEL.id, id)
