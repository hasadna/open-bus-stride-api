import datetime
from textwrap import dedent

import typing
import fastapi
import pydantic
from fastapi import APIRouter

from . import common
from ..common import sql_route


router = APIRouter()


class GtfsRidesAggPydanticModel(pydantic.BaseModel):
    gtfs_route_id: int
    gtfs_route_date: datetime.date
    num_planned_rides: int
    num_actual_rides: int
    operator_ref: int


class GtfsRidesAggGroupByPydanticModel(pydantic.BaseModel):
    gtfs_route_date: typing.Optional[datetime.date]
    operator_ref: typing.Optional[int]
    day_of_week: typing.Optional[str]
    total_routes: int
    total_planned_rides: int
    total_actual_rides: int


WHAT_SINGULAR = 'gtfs rides aggregation'
WHAT_PLURAL = 'gtfs rides aggregations'
TAG = 'aggregations'
PYDANTIC_MODEL = GtfsRidesAggPydanticModel
GROUP_BY_PYDANTIC_MODEL = GtfsRidesAggGroupByPydanticModel
DEFAULT_LIMIT = 1000
ALLOWED_GROUP_BY_FIELDS = ['gtfs_route_date', 'operator_ref', 'day_of_week', 'clustername']


@common.router_list(router, TAG, PYDANTIC_MODEL, WHAT_PLURAL)
def list_(limit: int = common.param_limit(default_limit=DEFAULT_LIMIT),
          offset: int = common.param_offset(),
          get_count: bool = common.param_get_count(),
          date_from: datetime.date = common.doc_param('date', filter_type='date_from', default=...),
          date_to: datetime.date = common.doc_param('date', filter_type='date_to', default=...)):
    sql = dedent("""
        select
            agg.gtfs_route_id,
            agg.gtfs_route_date,
            agg.num_planned_rides,
            agg.num_actual_rides,
            rt.operator_ref
        from gtfs_rides_agg agg, gtfs_route rt
        where
            agg.gtfs_route_id = rt.id
            and agg.gtfs_route_date >= :date_from
            and agg.gtfs_route_date <= :date_to
    """)
    sql_params = {
        'date_from': date_from,
        'date_to': date_to,
    }
    return sql_route.list_(sql, sql_params, DEFAULT_LIMIT, limit, offset, get_count, 'gtfs_route_date asc, gtfs_route_id asc', False)


@router.get("/group_by", tags=[TAG], response_model=typing.List[GROUP_BY_PYDANTIC_MODEL], description=f'{WHAT_SINGULAR} grouped by given fields.')
def group_by_(date_from: datetime.date = common.doc_param('date', filter_type='date_from', default=...),
              date_to: datetime.date = common.doc_param('date', filter_type='date_to', default=...),
              group_by: str = fastapi.Query(..., description=f'Comma-separated list of fields to group by. Valid values: {", ".join(ALLOWED_GROUP_BY_FIELDS)}.')
              ):
    group_by = [f.strip() for f in group_by.split(',') if f.strip()]
    assert all(f in ALLOWED_GROUP_BY_FIELDS for f in group_by), f'Invalid group_by fields: {group_by}. Valid values: {", ".join(ALLOWED_GROUP_BY_FIELDS)}.'
    select_fields = []
    group_by_fields = []
    for fieldname in group_by:
        if fieldname == 'gtfs_route_date':
            full_fieldname = 'agg.gtfs_route_date'
        elif fieldname == 'day_of_week':
            full_fieldname = "trim(lower(to_char(agg.gtfs_route_date, 'DAY')))"
        else:
            full_fieldname = f'rt.{fieldname}'
        select_fields.append(f'{full_fieldname} as {fieldname}')
        group_by_fields.append(full_fieldname)
    sql = dedent(f"""
        select
            {', '.join(select_fields)},
            count(1) as total_routes,
            sum(agg.num_planned_rides) as total_planned_rides,
            sum(agg.num_actual_rides) as total_actual_rides
        from gtfs_rides_agg agg, gtfs_route rt join clustertoline c on rt.line_ref = c.officelineid
        where
            agg.gtfs_route_id = rt.id
            and agg.gtfs_route_date >= :date_from
            and agg.gtfs_route_date <= :date_to
        group by {', '.join(group_by_fields)}
    """)
    sql_params = {
        'date_from': date_from,
        'date_to': date_to,
    }
    return sql_route.list_(sql, sql_params, None, None, None, None, None, True)
