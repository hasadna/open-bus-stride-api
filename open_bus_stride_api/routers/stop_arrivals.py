import typing
import datetime

import pydantic
import sqlalchemy
from fastapi import APIRouter

from open_bus_stride_db.model.gtfs_stop import GtfsStop
from open_bus_stride_db import model

from . import common


router = APIRouter()


class StopArrivalPydanticModel(pydantic.BaseModel):
    actual_arrival_time: datetime.datetime = None

LIST_MAX_LIMIT = 100
WHAT_PLURAL = """the actual arrival times to a specific stop.
Currently, only planned time (gtfs) is returned for every stop"""
TAG = 'user cases'
PYDANTIC_MODEL = StopArrivalPydanticModel


def get_base_session_query(session):
    return session.query(
        *[getattr(model.SiriVehicleLocation, f) for f in ['recorded_at_time']]
    )

def _post_session_query_hook(session_query: sqlalchemy.orm.Query):
    return (
        session_query
        .select_from(model.GtfsStop)
        .add_entity(model.SiriVehicleLocation)
        .join(model.SiriRideStop, model.SiriRideStop.gtfs_stop_id == model.GtfsStop.id)
        .join(model.SiriVehicleLocation, model.SiriVehicleLocation.id == model.SiriRideStop.nearest_siri_vehicle_location_id)
        .join(model.SiriRide, model.SiriRide.id == model.SiriRideStop.siri_ride_id)
        .order_by((sqlalchemy.asc)(model.SiriVehicleLocation.recorded_at_time))
    )


def _convert_to_dict(obj):
    gtfs_stop, siri_vehicle_location = obj
    return StopArrivalPydanticModel(actual_arrival_time=siri_vehicle_location.recorded_at_time).__dict__


@common.router_list(router, TAG, PYDANTIC_MODEL, WHAT_PLURAL)
def list_(limit: int = common.param_limit(LIST_MAX_LIMIT),
          offset: int = common.param_offset(),
          get_count: bool = common.param_get_count(),
          gtfs_stop_id: int = common.doc_param('gtfs_stop_id', 'equals', description='To get a line ref, first query gtfs_routes'),
          gtfs_ride_ids: str = common.doc_param('line_ref', 'list', description='To get a line ref, first query gtfs_routes')):
    return common.get_list(
        GtfsStop, limit, offset,
        [
            {'type': 'equals', 'field': model.GtfsStop.id, 'value': gtfs_stop_id},
            {'type': 'in', 'field': model.SiriRide.route_gtfs_ride_id, 'value': gtfs_ride_ids},
        ],
        post_session_query_hook=_post_session_query_hook,
        convert_to_dict=_convert_to_dict,
        get_count=get_count,
        skip_order_by=True,
        get_base_session_query_callback=get_base_session_query,
    )
