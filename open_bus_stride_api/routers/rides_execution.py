import datetime
from textwrap import dedent

import pydantic
from fastapi import APIRouter

from . import common
from ..common import sql_route

router = APIRouter()


class RideExecutionPydanticModel(pydantic.BaseModel):
    planned_start_time: datetime.datetime = None
    actual_start_time: datetime.datetime = None
    gtfs_ride_id: int = None

DEFAULT_LIMIT = 100
WHAT_PLURAL = """A comparison between the planned and actual rides of a specific route between the given dates.
Currently, the "actual_rides_count", will be either None (no actual ride) or equal to the "planned_rides_count"""
TAG = 'user cases'
PYDANTIC_MODEL = RideExecutionPydanticModel

@common.router_list(router, TAG, PYDANTIC_MODEL, WHAT_PLURAL)
def list_(limit: int = common.param_limit(default_limit=DEFAULT_LIMIT),
          offset: int = common.param_offset(),
          get_count: bool = common.param_get_count(),
          date_from: datetime.date = common.doc_param('date', filter_type='date_from', default=...),
          date_to: datetime.date = common.doc_param('date', filter_type='date_to', default=...),
          operator_ref: int = common.doc_param('operator_ref', filter_type='equals', description="Line operator ref."),
          line_ref: int = common.doc_param('line_ref', filter_type='equals', description="Line ref.")):
    sql = """
        select actual_rides.start_time actual_start_time, planned_rides.start_time planned_start_time, planned_rides.gtfs_ride_id gtfs_ride_id from (
(select siri_ride.scheduled_start_time start_time from siri_ride
join siri_route sr on siri_ride.siri_route_id = sr.id
where sr.operator_ref= :operator_ref and sr.line_ref= :line_ref and date_trunc('day', siri_ride.scheduled_start_time) between :date_from and :date_to)
              ) actual_rides
full outer join
(select gtfs_ride.start_time start_time, gtfs_ride.id gtfs_ride_id from gtfs_ride
    join gtfs_route gr on gtfs_ride.gtfs_route_id = gr.id
where gr.operator_ref= :operator_ref and gr.line_ref= :line_ref and date_trunc('day', gtfs_ride.start_time) between :date_from and :date_to ) planned_rides
on actual_rides.start_time=planned_rides.start_time
    """
    sql_params = {
        'date_from': date_from,
        'date_to': date_to,
        'operator_ref': operator_ref,
        'line_ref': line_ref,
    }

    return sql_route.list_(dedent(sql), sql_params, DEFAULT_LIMIT, limit, offset, get_count, 'planned_start_time asc, actual_start_time asc', False)
