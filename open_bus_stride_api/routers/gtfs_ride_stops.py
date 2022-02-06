import typing
import datetime

import pydantic
from fastapi import APIRouter

from open_bus_stride_db import model

from . import common


router = APIRouter()


class GtfsRideStopPydanticModel(pydantic.BaseModel):
    id: int
    gtfs_stop_id: int
    gtfs_ride_id: int
    arrival_time: datetime.datetime = None
    departure_time: datetime.datetime = None
    stop_sequence: int = None
    pickup_type: int = None
    drop_off_type: int = None
    shape_dist_traveled: int = None


@router.get("/list", tags=['gtfs'], response_model=typing.List[GtfsRideStopPydanticModel])
def list_(limit: int = None, offset: int = None,
          gtfs_stop_ids: str = None, gtfs_ride_ids: str = None):
    return common.get_list(
        model.GtfsRideStop, limit, offset,
        [
            {'type': 'in', 'field': model.GtfsRideStop.gtfs_stop_id, 'value': gtfs_stop_ids},
            {'type': 'in', 'field': model.GtfsRideStop.gtfs_ride_id, 'value': gtfs_ride_ids},
        ]
    )


@router.get('/get', tags=['gtfs'], response_model=GtfsRideStopPydanticModel)
def get_(id: int):
    return common.get_item(model.GtfsRideStop, model.GtfsRideStop.id, id)
