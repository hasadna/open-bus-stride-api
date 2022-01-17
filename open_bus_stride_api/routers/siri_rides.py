import typing
import datetime

import pydantic
from fastapi import APIRouter

from open_bus_stride_db.model.siri_ride import SiriRide

from . import common


router = APIRouter()


class SiriRidePydanticModel(pydantic.BaseModel):
    id: int
    siri_route_id: int
    journey_ref: str
    scheduled_start_time: datetime.datetime
    vehicle_ref: str = None
    updated_first_last_vehicle_locations: datetime.datetime = None
    first_vehicle_location_id: int = None
    last_vehicle_location_id: int = None
    updated_duration_minutes: datetime.datetime = None
    duration_minutes: int = None


@router.get("/list", tags=['siri'], response_model=typing.List[SiriRidePydanticModel])
def list_(limit: int = None, offset: int = None,
          siri_route_ids: str = None,
          journey_ref_prefix: str = None,
          journey_refs: str = None,
          vehicle_refs: str = None,
          scheduled_start_time_from: datetime.datetime = None,
          scheduled_start_time_to: datetime.datetime = None,
          order_by: str = None):
    """
    * limit: limit the number of results, if not specified will limit to 1000 results
    * offset: row number to start returning results from (for pagination)
    * siri_route_ids: comma-separated list
    * journey_refs: comma-separated list
    * vehicle_refs: comma-separated list
    * scheduled_start_time_from / scheduled_start_time_to: YYYY-MM-DDTHH:MM:SS+Z (e.g. 2021-11-33T55:48:49+00:00)
    * order_by: comma-separated list of order by fields, e.g.: "siri_route_id asc,vehicle_ref desc"
    """
    return common.get_list(
        SiriRide, limit, offset,
        [
            {'type': 'in', 'field': SiriRide.siri_route_id, 'value': siri_route_ids},
            {'type': 'prefix', 'field': SiriRide.journey_ref, 'value': journey_ref_prefix},
            {'type': 'in', 'field': SiriRide.journey_ref, 'value': journey_refs},
            {'type': 'in', 'field': SiriRide.vehicle_ref, 'value': vehicle_refs},
            {'type': 'datetime_from', 'field': SiriRide.scheduled_start_time, 'value': scheduled_start_time_from},
            {'type': 'datetime_to', 'field': SiriRide.scheduled_start_time, 'value': scheduled_start_time_to},
        ],
        order_by=order_by
    )


@router.get('/get', tags=['siri'], response_model=SiriRidePydanticModel)
def get_(id: int):
    return common.get_item(SiriRide, SiriRide.id, id)
