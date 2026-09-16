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
    gtfs_route_hour: datetime.date
    num_planned_rides: int
    num_actual_rides: int
    operator_ref: int


class GtfsRidesAggGroupByPydanticModel(pydantic.BaseModel):
    gtfs_route_date: typing.Optional[datetime.date]
    gtfs_route_hour: typing.Optional[datetime.date]
    operator_ref: typing.Optional[int]
    day_of_week: typing.Optional[str]
    line_ref: typing.Optional[int]
    route_short_name: typing.Optional[str]
    route_long_name: typing.Optional[str]
    total_routes: int
    total_planned_rides: int
    total_actual_rides: int


WHAT_SINGULAR = 'gtfs rides aggregation'
WHAT_PLURAL = 'gtfs rides aggregations'
TAG = 'aggregations'
PYDANTIC_MODEL = GtfsRidesAggPydanticModel
GROUP_BY_PYDANTIC_MODEL = GtfsRidesAggGroupByPydanticModel
DEFAULT_LIMIT = 1000
ALLOWED_GROUP_BY_FIELDS = ['gtfs_route_date', 'gtfs_route_hour', 'operator_ref', 'day_of_week', 'line_ref']
AGG_VIEW_FIELDS = ['gtfs_route_date', 'gtfs_route_hour']
AGGREGATE_FIELDS = ['total_routes', 'total_planned_rides', 'total_actual_rides']
LINE_REF_FIELDS = ['route_short_name', 'route_long_name']


@common.router_list(router, TAG, PYDANTIC_MODEL, WHAT_PLURAL)
def list_(limit: int = common.param_limit(default_limit=DEFAULT_LIMIT),
          offset: int = common.param_offset(),
          get_count: bool = common.param_get_count(),
          date_from: datetime.date = common.doc_param('date', filter_type='date_from', default=...),
          date_to: datetime.date = common.doc_param('date', filter_type='date_to', default=...),
          exclude_hours_from: int = common.doc_param('hour', filter_type='hour_from', description="Hours to exclude from search, currently used to filter out edge cases."),
          exclude_hours_to: int = common.doc_param('hour', filter_type='hour_to', description="Hours to exclude from search, currently used to filter out edge cases.")):
    sql = """
        select
            agg.gtfs_route_id,
            agg.gtfs_route_hour,
            agg.num_planned_rides,
            agg.num_actual_rides,
            rt.operator_ref
        from gtfs_rides_agg_by_hour agg, gtfs_route rt
        where
            agg.gtfs_route_id = rt.id
            and agg.gtfs_route_date >= :date_from
            and agg.gtfs_route_date <= :date_to
            and rt.date >= :rt_date_from
            and rt.date <= :rt_date_to
    """
    sql_params = {
        'date_from': date_from,
        'date_to': date_to,
        'rt_date_from': date_from - datetime.timedelta(days=30),
        'rt_date_to': date_from + datetime.timedelta(days=30),
    }

    if exclude_hours_from:
        sql += " and not date_part('hour', agg.gtfs_route_hour) >= :exclude_hour_from"
        sql_params['exclude_hour_from'] = exclude_hours_from
    if exclude_hours_to:
        sql += " and not date_part('hour', agg.gtfs_route_hour) <= :exclude_hour_to"
        sql_params['exclude_hour_to'] = exclude_hours_to

    return sql_route.list_(dedent(sql), sql_params, DEFAULT_LIMIT, limit, offset, get_count, 'gtfs_route_hour asc, gtfs_route_id asc', False)


def assert_valid_group_by_order_by(order_by, selected_fields):
    """Validate order_by against the fields this request selects.

    sql_route interpolates the field name into the SQL instead of binding it, so restricting
    it to names this particular grouping produces is what turns a typo, or a field belonging
    to a different group_by, into a readable message rather than a postgres error.
    """
    for element in order_by.split(','):
        parts = element.split()
        assert parts, f'Empty order_by element in: "{order_by}".'
        assert len(parts) <= 2, f'Invalid order_by element: "{element.strip()}". Expected "<field> [asc|desc]".'
        assert parts[0] in selected_fields, \
            f'Invalid order_by field: {parts[0]}. Valid values for this group_by: {", ".join(selected_fields)}.'
        if len(parts) == 2:
            assert parts[1] in ('asc', 'desc'), f'Invalid order_by direction: {parts[1]}. Valid values: asc, desc.'


@router.get("/group_by", tags=[TAG], response_model=typing.List[GROUP_BY_PYDANTIC_MODEL], description=f'{WHAT_SINGULAR} grouped by given fields.')
def group_by_(date_from: datetime.date = common.doc_param('date', filter_type='date_from', default=...),
              date_to: datetime.date = common.doc_param('date', filter_type='date_to', default=...),
              exclude_hours_from: int = common.doc_param('hour', filter_type='hour_from', description="Hours to exclude from search, currently used to filter out edge cases."),
              exclude_hours_to: int = common.doc_param('hour', filter_type='hour_to', description="Hours to exclude from search, currently used to filter out edge cases."),
              group_by: str = fastapi.Query(..., description=f'Comma-separated list of fields to group by. Valid values: {", ".join(ALLOWED_GROUP_BY_FIELDS)}.'),
              order_by: str = fastapi.Query(None, description=f'Comma-separated list of "<field> [asc|desc]" to order the groups by. '
                                                              f'Valid fields are the ones this request groups by, {", ".join(AGGREGATE_FIELDS)}, '
                                                              f'and {", ".join(LINE_REF_FIELDS)} when grouping by line_ref. '
                                                              f'Combine with limit to fetch only the top groups instead of every one of them.'),
              limit: int = fastapi.Query(None, description='Limit the number of returned groups. If not specified, every group is returned.'),
              offset: int = common.param_offset(),
              get_count: bool = common.param_get_count()
              ):
    group_by = [f.strip() for f in group_by.split(',') if f.strip()]
    assert all(f in ALLOWED_GROUP_BY_FIELDS for f in group_by), f'Invalid group_by fields: {group_by}. Valid values: {", ".join(ALLOWED_GROUP_BY_FIELDS)}.'
    select_fields = []
    group_by_fields = []
    for fieldname in group_by:
        if fieldname in AGG_VIEW_FIELDS:
            full_fieldname = f'agg.{fieldname}'
        elif fieldname == 'day_of_week':
            full_fieldname = "trim(lower(to_char(agg.gtfs_route_hour, 'DAY')))"
        elif fieldname == 'line_ref':
            full_fieldname = f'rt.{fieldname}'
            select_fields.append(f'json_agg(distinct rt.route_short_name)::text as route_short_name')
            select_fields.append(f'json_agg(distinct rt.route_long_name)::text as route_long_name')
        else:
            full_fieldname = f'rt.{fieldname}'
        select_fields.append(f'{full_fieldname} as {fieldname}')
        group_by_fields.append(full_fieldname)

    if order_by:
        selected_fields = [*group_by, *AGGREGATE_FIELDS]
        if 'line_ref' in group_by:
            selected_fields += LINE_REF_FIELDS
        assert_valid_group_by_order_by(order_by, selected_fields)

    sql = dedent(f"""
        select
            {', '.join(select_fields)},
            count(1) as total_routes,
            sum(agg.num_planned_rides) as total_planned_rides,
            sum(agg.num_actual_rides) as total_actual_rides
        from gtfs_rides_agg_by_hour agg, gtfs_route rt
        where
            agg.gtfs_route_id = rt.id
            and agg.gtfs_route_date >= :date_from
            and agg.gtfs_route_date <= :date_to
            and rt.date >= :rt_date_from
            and rt.date <= :rt_date_to
    """)
    sql_params = {
        'date_from': date_from,
        'date_to': date_to,
        'rt_date_from': date_from - datetime.timedelta(days=30),
        'rt_date_to': date_from + datetime.timedelta(days=30),
    }

    if exclude_hours_from:
        sql += " and not date_part('hour', agg.gtfs_route_hour) >= :exclude_hour_from"
        sql_params['exclude_hour_from'] = exclude_hours_from
    if exclude_hours_to:
        sql += " and not date_part('hour', agg.gtfs_route_hour) <= :exclude_hour_to"
        sql_params['exclude_hour_to'] = exclude_hours_to

    sql += f" group by {', '.join(group_by_fields)}"
    # skip_order_by stays True without an order_by: sql_route builds a bare "order by" from an
    # empty field list, which postgres rejects.
    return sql_route.list_(sql, sql_params, None, limit, offset, get_count, order_by, not order_by,
                           allow_no_limit=True)
