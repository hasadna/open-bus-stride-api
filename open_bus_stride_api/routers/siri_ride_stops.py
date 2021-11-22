import typing

import pydantic
from fastapi import APIRouter

from open_bus_stride_db.model.siri_ride_stop import SiriRideStop

from . import common


router = APIRouter()


class SiriRideStopPydanticModel(pydantic.BaseModel):
    id: int
    siri_stop_id: int
    siri_ride_id: int
    order: int


@router.get("/list", tags=['siri_ride_stops'], response_model=typing.List[SiriRideStopPydanticModel])
def list_(limit: int = None, offset: int = None,
          siri_stop_ids: str = None,
          siri_ride_ids: str = None,
          order_by: str = None):
    """
    * siri_stop_ids: comma-separated list
    * siri_ride_ids: comma-separated list
    * order_by: comma-separated list of order by fields, e.g.: "order asc,siri_stop_id desc"
    """
    return common.get_list(
        SiriRideStop, limit, offset,
        [
            {'type': 'in', 'field': SiriRideStop.siri_stop_id, 'value': siri_stop_ids},
            {'type': 'in', 'field': SiriRideStop.siri_ride_id, 'value': siri_ride_ids},
        ],
        order_by=order_by
    )


@router.get('/get', tags=['siri_ride_stops'], response_model=SiriRideStopPydanticModel)
def get_(id: int):
    return common.get_item(SiriRideStop, SiriRideStop.id, id)
