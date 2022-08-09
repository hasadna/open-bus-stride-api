import typing
import datetime

import pydantic
from fastapi import APIRouter

from open_bus_stride_db.model.siri_snapshot import SiriSnapshot, SiriSnapshotEtlStatusEnum

from . import common


router = APIRouter()


class SiriSnapshotPydanticModel(pydantic.BaseModel):
    id: int
    snapshot_id: str
    etl_status: SiriSnapshotEtlStatusEnum
    etl_start_time: datetime.datetime = None
    etl_end_time: datetime.datetime = None
    error: str = None
    num_successful_parse_vehicle_locations: int = None
    num_failed_parse_vehicle_locations: int = None
    num_added_siri_rides: int = None
    num_added_siri_ride_stops: int = None
    num_added_siri_routes: int = None
    num_added_siri_stops: int = None
    last_heartbeat: datetime.datetime = None
    created_by: str = None


WHAT_SINGULAR = 'siri snapshot'
WHAT_PLURAL = f'{WHAT_SINGULAR}s'
TAG = 'siri'
PYDANTIC_MODEL = SiriSnapshotPydanticModel
SQL_MODEL = SiriSnapshot


@common.router_list(router, TAG, PYDANTIC_MODEL, WHAT_PLURAL)
def list_(limit: int = common.param_limit(),
          offset: int = common.param_offset(),
          get_count: bool = common.param_get_count(),
          snapshot_id_prefix: str = common.doc_param('snapshot id', filter_type='prefix'),
          order_by: str = common.param_order_by()):
    return common.get_list(
        SiriSnapshot, limit, offset,
        [
            {'type': 'prefix', 'field': SiriSnapshot.snapshot_id, 'value': snapshot_id_prefix},
        ],
        order_by=order_by,
        get_count=get_count,
        pydantic_model=PYDANTIC_MODEL,
    )


@common.router_get(router, TAG, PYDANTIC_MODEL, WHAT_SINGULAR)
def get_(id: int = common.param_get_id(WHAT_SINGULAR)):
    return common.get_item(SQL_MODEL, SQL_MODEL.id, id, pydantic_model=PYDANTIC_MODEL,)
