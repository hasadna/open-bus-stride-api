import typing

import pydantic
from fastapi import APIRouter

from open_bus_stride_db.model.siri_route import SiriRoute

from . import common


router = APIRouter()


class SiriRoutePydanticModel(pydantic.BaseModel):
    id: int
    line_ref: int
    operator_ref: int


@router.get("/list", tags=['siri'], response_model=typing.List[SiriRoutePydanticModel])
def list_(limit: int = None, offset: int = None,
          line_refs: str = None, operator_refs: str = None,
          order_by: str = None):
    """
    * limit: limit the number of results, if not specified will limit to 1000 results
    * offset: row number to start returning results from (for pagination)
    * line_refs: comma-separated list
    * operator_refs: comma-separated list
    * order_by: comma-separated list of order by fields, e.g.: "line_ref desc,operator_ref asc"
    """
    return common.get_list(
        SiriRoute, limit, offset,
        [
            {'type': 'in', 'field': SiriRoute.line_ref, 'value': line_refs},
            {'type': 'in', 'field': SiriRoute.operator_ref, 'value': operator_refs},
        ],
        order_by=order_by
    )


@router.get('/get', tags=['siri'], response_model=SiriRoutePydanticModel)
def get_(id: int):
    return common.get_item(SiriRoute, SiriRoute.id, id)
