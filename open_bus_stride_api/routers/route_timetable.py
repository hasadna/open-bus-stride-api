import typing
import datetime

import pydantic
import sqlalchemy
from fastapi import APIRouter

from open_bus_stride_db.model.gtfs_stop import GtfsStop
from open_bus_stride_db import model

from . import common


router = APIRouter()


class RouteTimetablePydanticModel(pydantic.BaseModel):
    id: int
    name: str = None
    city: str = None
    lon: float = None
    lat: float = None
    planned_arrival_time: datetime.datetime = None
    gtfs_line_ref: str = None
    gtfs_line_start_time: datetime.datetime = None
    gtfs_ride_id: str = None

LIST_MAX_LIMIT = 100
WHAT_PLURAL = """the stops timetable of a given bus.
Currently, only planned time (gtfs) is returned for every stop"""
TAG = 'user cases'
PYDANTIC_MODEL = RouteTimetablePydanticModel

def _post_session_query_hook(session_query: sqlalchemy.orm.Query):
    return (
        session_query
        .select_from(model.GtfsStop)
        .add_entity(model.GtfsRideStop)
        .add_entity(model.GtfsRide)
        .add_entity(model.GtfsRoute)
        .join(model.GtfsRideStop, model.GtfsRideStop.gtfs_stop_id == model.GtfsStop.id)
        .join(model.GtfsRide, model.GtfsRide.id == model.GtfsRideStop.gtfs_ride_id)
        .join(model.GtfsRoute, model.GtfsRoute.id == model.GtfsRide.gtfs_route_id)
        .order_by((sqlalchemy.asc)(model.GtfsRideStop.arrival_time))
    )

def _convert_to_dict(obj):
    gtfs_stop, gtfs_ride_stop, gtfs_ride, gtfs_route = obj
    return RouteTimetablePydanticModel(id=gtfs_stop.id, name=gtfs_stop.name, city=gtfs_stop.city, lat=gtfs_stop.lat,
                                       lon=gtfs_stop.lon, planned_arrival_time=gtfs_ride_stop.arrival_time,
                                       gtfs_line_ref=gtfs_route.line_ref, gtfs_line_start_time=gtfs_ride.start_time,
                                       gtfs_ride_id=gtfs_ride.id).__dict__

@common.router_list(router, TAG, PYDANTIC_MODEL, WHAT_PLURAL)
def list_(limit: int = common.param_limit(LIST_MAX_LIMIT),
          offset: int = common.param_offset(),
          get_count: bool = common.param_get_count(),
          planned_start_time_date_from: datetime.datetime = common.doc_param('planned_start_time', 'datetime_from', description='Set a time range to get the timetable of a specific ride'),
          planned_start_time_date_to: datetime.datetime = common.doc_param('planned_start_time', 'datetime_to', description='Set a time range to get the time table of a specific ride'),
          line_refs: str = common.doc_param('line_ref', 'list', description='To get a line ref, first query gtfs_routes')):
    return common.get_list(
        GtfsStop, limit, offset,
        [
            {'type': 'datetime_from', 'field': model.GtfsRide.start_time, 'value': planned_start_time_date_from},
            {'type': 'datetime_to', 'field': model.GtfsRide.start_time, 'value': planned_start_time_date_to},
            {'type': 'in', 'field': model.GtfsRoute.line_ref, 'value': line_refs},
        ],
        post_session_query_hook=_post_session_query_hook,
        convert_to_dict=_convert_to_dict,
        max_limit=LIST_MAX_LIMIT,
        get_count=get_count,
        skip_order_by=True,
    )
