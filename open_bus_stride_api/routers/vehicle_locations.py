import typing
import datetime

import pydantic
from fastapi import APIRouter

from open_bus_stride_db.model.vehicle_location import VehicleLocation

from . import common


router = APIRouter()


class VehicleLocationPydanticModel(pydantic.BaseModel):
    id: int
    siri_snapshot_id: int
    ride_id: int
    route_stop_id: int
    recorded_at_time: datetime.datetime
    lon: float
    lat: float
    bearing: int
    velocity: int
    distance_from_journey_start: int


@router.get("/list", tags=['vehicle_locations'], response_model=typing.List[VehicleLocationPydanticModel])
def list_(limit: int = None, offset: int = None,
          siri_snapshot_id: int = None, route_stop_id: int = None, ride_id: int = None,
          recorded_at_time_from: datetime.datetime = None, recorded_at_time_to: datetime.datetime = None):
    return common.get_list(
        VehicleLocation, limit, offset,
        [
            {'type': 'equals', 'field': VehicleLocation.siri_snapshot_id, 'value': siri_snapshot_id},
            {'type': 'equals', 'field': VehicleLocation.route_stop_id, 'value': route_stop_id},
            {'type': 'equals', 'field': VehicleLocation.ride_id, 'value': ride_id},
            {'type': 'datetime_from', 'field': VehicleLocation.recorded_at_time, 'value': recorded_at_time_from},
            {'type': 'datetime_to', 'field': VehicleLocation.recorded_at_time, 'value': recorded_at_time_to},
        ]
    )


@router.get('/get', tags=['vehicle_locations'], response_model=VehicleLocationPydanticModel)
def get_(id: int):
    return common.get_item(VehicleLocation, VehicleLocation.id, id)
