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
    # Evidence about the actual ride. A siri_ride row only proves that an operator
    # announced a vehicle for the slot, so these let a consumer tell "the bus ran" from
    # "a vehicle was announced" instead of inferring it from actual_start_time.
    siri_ride_id: int = None
    vehicle_ref: str = None
    journey_ref: str = None
    first_seen: datetime.datetime = None
    last_seen: datetime.datetime = None
    observed_stop_orders: int = None
    max_stop_order: int = None
    planned_stop_count: int = None
    stop_coverage: float = None

DEFAULT_LIMIT = 100
WHAT_PLURAL = """A comparison between the planned and actual rides of a specific route between the given dates.

A row's "actual" side comes from a siri_ride, which exists as soon as the MOT SIRI feed named a
vehicle for that slot - typically 30 or 5 minutes before the scheduled departure, while the vehicle
is still parked. An actual_start_time therefore means "a vehicle was announced", NOT "a bus ran",
and it is a copy of the scheduled time rather than an observation.

The remaining fields expose the evidence behind the actual side so that the two can be told apart:

* "first_seen" / "last_seen" - the recorded_at_time of the ride's first and last GPS ping. Both are
  NULL unless the siri_ride first/last vehicle location enrichment has run for that date, so treat
  NULL as "unknown", never as "no data existed".
* "observed_stop_orders" / "max_stop_order" - how many distinct stops along the route the vehicle was
  reported approaching, and the furthest one it reached. These come from the SIRI MonitoredCall
  order, which is on the same 1-based scale as the GTFS stop_sequence.
* "planned_stop_count" - the number of stops in the matched planned ride.
* "stop_coverage" - max_stop_order / planned_stop_count, i.e. the fraction of the route the vehicle
  was observed to progress along. NULL when the ride matched no planned ride or was never observed.
  A ride that was announced and then vanished has a coverage near 0; a ride that ran has one near 1.
  Coverage uses the furthest stop reached rather than the count of reported stops, so that gaps in
  SIRI reporting along the way do not look like a shorter ride.

Note that "stop_coverage" is evidence, not a verdict: a bus that ran with a broken GPS unit and a bus
that never departed both produce a low coverage, and a low-coverage ride is often a trip that did run
under a different vehicle's record. Check whether another vehicle covered the same route in the same
window before reporting a ride as missing."""
TAG = 'user cases'
PYDANTIC_MODEL = RideExecutionPydanticModel

@common.router_list(router, TAG, PYDANTIC_MODEL, WHAT_PLURAL)
def list_(limit: int = common.param_limit(default_limit=DEFAULT_LIMIT),
          offset: int = common.param_offset(),
          get_count: bool = common.param_get_count(),
          date_from: datetime.date = common.doc_param('date', filter_type='date_from', default=...),
          date_to: datetime.date = common.doc_param('date', filter_type='date_to', default=...),
          operator_ref: int = common.doc_param('operator_ref', filter_type='equals', description="Line operator ref.", default=...),
          line_ref: int = common.doc_param('line_ref', filter_type='equals', description="Line ref.", default=...),):
    # The stop aggregates are lateral rather than grouped joins on purpose: siri_ride_stop and
    # gtfs_ride_stop are among the largest tables in the database, and a lateral keeps each
    # aggregate an index lookup on the parent ride id instead of letting the planner hash the
    # whole table against the ride set.
    sql = """
    select
        actual_rides.start_time::timestamptz as actual_start_time,
        planned_rides.start_time::timestamptz as planned_start_time,
        planned_rides.gtfs_ride_id,
        actual_rides.siri_ride_id,
        actual_rides.vehicle_ref,
        actual_rides.journey_ref,
        actual_rides.first_seen::timestamptz as first_seen,
        actual_rides.last_seen::timestamptz as last_seen,
        actual_rides.observed_stop_orders,
        actual_rides.max_stop_order,
        planned_rides.planned_stop_count,
        case
            when planned_rides.planned_stop_count > 0
            then round(actual_rides.max_stop_order::numeric / planned_rides.planned_stop_count, 3)
        end as stop_coverage
    from
        (
            (select
                siri_ride.id as siri_ride_id,
                siri_ride.scheduled_start_time as start_time,
                siri_ride.vehicle_ref as vehicle_ref,
                siri_ride.journey_ref as journey_ref,
                first_location.recorded_at_time as first_seen,
                last_location.recorded_at_time as last_seen,
                actual_stops.observed_stop_orders as observed_stop_orders,
                actual_stops.max_stop_order as max_stop_order
            from
                siri_ride
                join siri_route sr on siri_ride.siri_route_id = sr.id
                left join siri_vehicle_location first_location
                    on first_location.id = siri_ride.first_vehicle_location_id
                left join siri_vehicle_location last_location
                    on last_location.id = siri_ride.last_vehicle_location_id
                left join lateral (
                    select
                        count(distinct siri_ride_stop."order") as observed_stop_orders,
                        max(siri_ride_stop."order") as max_stop_order
                    from siri_ride_stop
                    where siri_ride_stop.siri_ride_id = siri_ride.id
                ) actual_stops on true
            where
                sr.operator_ref = :operator_ref
                and sr.line_ref = :line_ref
                and date_trunc('day', siri_ride.scheduled_start_time AT TIME ZONE 'UTC' AT TIME ZONE 'Asia/Jerusalem') between :date_from and :date_to
            ) actual_rides
        full outer join
            (select
                gtfs_ride.start_time as start_time,
                gtfs_ride.id as gtfs_ride_id,
                planned_stops.planned_stop_count as planned_stop_count
            from
                gtfs_ride
                join gtfs_route gr on gtfs_ride.gtfs_route_id = gr.id
                left join lateral (
                    select count(1) as planned_stop_count
                    from gtfs_ride_stop
                    where gtfs_ride_stop.gtfs_ride_id = gtfs_ride.id
                ) planned_stops on true
            where
                gr.operator_ref = :operator_ref
                and gr.line_ref = :line_ref
                and date_trunc('day', gtfs_ride.start_time AT TIME ZONE 'UTC' AT TIME ZONE 'Asia/Jerusalem') between :date_from and :date_to
            ) planned_rides
        on
            actual_rides.start_time = planned_rides.start_time
    )
    """
    sql_params = {
        'date_from': date_from,
        'date_to': date_to,
        'operator_ref': operator_ref,
        'line_ref': line_ref,
    }

    return sql_route.list_(dedent(sql), sql_params, DEFAULT_LIMIT, limit, offset, get_count, 'planned_start_time asc, actual_start_time asc', False)
