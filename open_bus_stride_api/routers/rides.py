import typing
import datetime

import pydantic
from fastapi import APIRouter

from open_bus_stride_db.model.ride import Ride

from . import common


router = APIRouter()


class RidePydanticModel(pydantic.BaseModel):
    id: int
    route_id: int
    journey_ref: str
    scheduled_start_time: datetime.datetime
    vehicle_ref: str = None
    is_from_gtfs: bool


@router.get("/list", tags=['rides'], response_model=typing.List[RidePydanticModel])
def list_(limit: int = None, offset: int = None,
          route_id: int = None, journey_ref_prefix: str = None, vehicle_ref: str = None, is_from_gtfs: bool = None,
          scheduled_start_time_from: datetime.datetime = None, scheduled_start_time_to: datetime.datetime = None):
    return common.get_list(
        Ride, limit, offset,
        [
            {'type': 'equals', 'field': Ride.route_id, 'value': route_id},
            {'type': 'prefix', 'field': Ride.journey_ref, 'value': journey_ref_prefix},
            {'type': 'equals', 'field': Ride.vehicle_ref, 'value': vehicle_ref},
            {'type': 'equals', 'field': Ride.is_from_gtfs, 'value': is_from_gtfs},
            {'type': 'datetime_from', 'field': Ride.scheduled_start_time, 'value': scheduled_start_time_from},
            {'type': 'datetime_to', 'field': Ride.scheduled_start_time, 'value': scheduled_start_time_to},
        ]
    )


@router.get('/get', tags=['rides'], response_model=RidePydanticModel)
def get_(id: int):
    return common.get_item(Ride, Ride.id, id)
