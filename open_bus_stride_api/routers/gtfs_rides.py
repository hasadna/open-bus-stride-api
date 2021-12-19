import typing
import datetime

import pydantic
from fastapi import APIRouter

from open_bus_stride_db.model.gtfs_ride import GtfsRide

from . import common


router = APIRouter()


class GtfsRidePydanticModel(pydantic.BaseModel):
    id: int
    gtfs_route_id: int
    journey_ref: str
    scheduled_start_time: datetime.datetime
    vehicle_ref: str = None


@router.get("/list", tags=['gtfs_rides'], response_model=typing.List[GtfsRidePydanticModel])
def list_(limit: int = None, offset: int = None,
          gtfs_route_id: int = None, journey_ref_prefix: str = None, vehicle_ref: str = None,
          scheduled_start_time_from: datetime.datetime = None, scheduled_start_time_to: datetime.datetime = None):
    return common.get_list(
        GtfsRide, limit, offset,
        [
            {'type': 'equals', 'field': GtfsRide.gtfs_route_id, 'value': gtfs_route_id},
            {'type': 'prefix', 'field': GtfsRide.journey_ref, 'value': journey_ref_prefix},
            {'type': 'equals', 'field': GtfsRide.vehicle_ref, 'value': vehicle_ref},
            {'type': 'datetime_from', 'field': GtfsRide.scheduled_start_time, 'value': scheduled_start_time_from},
            {'type': 'datetime_to', 'field': GtfsRide.scheduled_start_time, 'value': scheduled_start_time_to},
        ]
    )


@router.get('/get', tags=['gtfs_rides'], response_model=GtfsRidePydanticModel)
def get_(id: int):
    return common.get_item(GtfsRide, GtfsRide.id, id)
