import typing
import datetime

import pydantic
from fastapi import APIRouter

from open_bus_stride_db.model.siri_vehicle_location import SiriVehicleLocation

from . import common


router = APIRouter()


class SiriVehicleLocationPydanticModel(pydantic.BaseModel):
    id: int
    siri_snapshot_id: int
    siri_ride_stop_id: int
    recorded_at_time: datetime.datetime
    lon: float
    lat: float
    bearing: int
    velocity: int
    distance_from_journey_start: int


@router.get("/list", tags=['siri_vehicle_locations'], response_model=typing.List[SiriVehicleLocationPydanticModel])
def list_(limit: int = None, offset: int = None,
          siri_snapshot_ids: str = None, siri_ride_stop_ids: str = None,
          recorded_at_time_from: datetime.datetime = None, recorded_at_time_to: datetime.datetime = None,
          order_by: str = None):
    """
    * siri_snapshot_ids: comma-separated list
    * siri_ride_stop_ids: comma-separated list
    * recorded_at_time_from / recorded_at_time_to: YYYY-MM-DDTHH:MM:SS
    * order_by: comma-separated list of order by fields, e.g.: "siri_snapshot_id desc,recorded_at_time asc"
    """
    return common.get_list(
        SiriVehicleLocation, limit, offset,
        [
            {'type': 'in', 'field': SiriVehicleLocation.siri_snapshot_id, 'value': siri_snapshot_ids},
            {'type': 'in', 'field': SiriVehicleLocation.siri_ride_stop_id, 'value': siri_ride_stop_ids},
            {'type': 'datetime_from', 'field': SiriVehicleLocation.recorded_at_time, 'value': recorded_at_time_from},
            {'type': 'datetime_to', 'field': SiriVehicleLocation.recorded_at_time, 'value': recorded_at_time_to},
        ],
        order_by=order_by
    )


@router.get('/get', tags=['siri_vehicle_locations'], response_model=SiriVehicleLocationPydanticModel)
def get_(id: int):
    return common.get_item(SiriVehicleLocation, SiriVehicleLocation.id, id)
