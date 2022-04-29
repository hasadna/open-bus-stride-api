import datetime

import pydantic
from fastapi import APIRouter
import sqlalchemy.orm

from open_bus_stride_db import model

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
    journey_gtfs_ride_id: int = None
    route_gtfs_ride_id: int = None
    gtfs_ride_id: int = None


LIST_MAX_LIMIT = 100
WHAT_SINGULAR = 'siri ride'
WHAT_PLURAL = f'{WHAT_SINGULAR}s'
TAG = 'siri'
PYDANTIC_MODEL = SiriRidePydanticModel
SQL_MODEL = model.SiriRide


def _post_session_query_hook(session_query: sqlalchemy.orm.Query):
    return session_query.join(model.SiriRoute, model.SiriRoute.id == model.SiriRide.siri_route_id)


@common.router_list(router, TAG, PYDANTIC_MODEL, WHAT_PLURAL)
def list_(limit: int = common.param_limit(max_limit=LIST_MAX_LIMIT),
          offset: int = common.param_offset(),
          get_count: bool = common.param_get_count(),
          siri_route_ids: str = common.param_filter_list('siri route ids'),
          siri_route__line_refs: str = common.param_filter_list('siri route line refs'),
          siri_route__operator_refs: str = common.param_filter_list('siri route operator refs'),
          journey_ref_prefix: str = common.param_filter_prefix('journey ref'),
          journey_refs: str = common.param_filter_list('journey ref'),
          vehicle_refs: str = common.param_filter_list('vehicle ref'),
          scheduled_start_time_from: datetime.datetime = common.param_filter_datetime_from('scheduled start time'),
          scheduled_start_time_to: datetime.datetime = common.param_filter_datetime_to('scheduled start time'),
          order_by: str = common.param_order_by('siri_route_id asc,vehicle_ref desc')):
    return common.get_list(
        SQL_MODEL, limit, offset,
        [
            {'type': 'in', 'field': model.SiriRide.siri_route_id, 'value': siri_route_ids},
            {'type': 'in', 'field': model.SiriRoute.line_ref, 'value': siri_route__line_refs},
            {'type': 'in', 'field': model.SiriRoute.operator_ref, 'value': siri_route__operator_refs},
            {'type': 'prefix', 'field': model.SiriRide.journey_ref, 'value': journey_ref_prefix},
            {'type': 'in', 'field': model.SiriRide.journey_ref, 'value': journey_refs},
            {'type': 'in', 'field': model.SiriRide.vehicle_ref, 'value': vehicle_refs},
            {'type': 'datetime_from', 'field': model.SiriRide.scheduled_start_time, 'value': scheduled_start_time_from},
            {'type': 'datetime_to', 'field': model.SiriRide.scheduled_start_time, 'value': scheduled_start_time_to},
        ],
        order_by=order_by,
        post_session_query_hook=_post_session_query_hook,
        max_limit=LIST_MAX_LIMIT,
        get_count=get_count,
    )


@common.router_get(router, TAG, PYDANTIC_MODEL, WHAT_SINGULAR)
def get_(id: int = common.param_get_id(WHAT_SINGULAR)):
    return common.get_item(SQL_MODEL, SQL_MODEL.id, id)
