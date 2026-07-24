import datetime
from textwrap import dedent

import fastapi
import pydantic
from fastapi import APIRouter

from open_bus_stride_db.db import get_session

from . import common


router = APIRouter()


class GtfsAgencyPydanticModel(pydantic.BaseModel):
    date: datetime.date
    operator_ref: int
    agency_name: str


WHAT_SINGULAR = 'gtfs agency'
WHAT_PLURAL = 'gtfs agencies'
TAG = 'gtfs'
PYDANTIC_MODEL = GtfsAgencyPydanticModel


@common.router_list(router, TAG, PYDANTIC_MODEL, WHAT_PLURAL)
def list_(limit: int = common.param_limit(),
          offset: int = common.param_offset(),
          date_from: datetime.date = fastapi.Query(
              ...,
              description='Required. ' + common.FILTER_DOCS['date_from'].format(what_singular='date')),
          date_to: datetime.date = common.doc_param('date', filter_type='date_to'),
          merge: bool = fastapi.Query(
              True,
              description='When true (the default), return a de-duplicated list with a single row '
                         'per operator_ref for the requested date range, carrying the agency name '
                         'from the latest date in the range. When false, return the raw per-date '
                         'rows (one row per operator per date) - useful for tracking agency '
                         'presence and renames over time. A date_from without date_to is treated '
                         'as that single day.')):
    with get_session() as session:
        # date_from is required; a missing date_to means "just that one day".
        if not date_to:
            date_to = date_from
        if not offset:
            offset = 0
        if not limit:
            # A merged result holds at most one row per operator (a few dozen), so it needs no
            # default cap; only the un-merged (operators x dates) mode keeps the safety limit.
            limit = None if merge else common.DEFAULT_LIMIT

        where = "where date >= '{}' and date <= '{}'".format(
            date_from.strftime('%Y-%m-%d'), date_to.strftime('%Y-%m-%d'))

        params = {'offset': offset}
        limit_offset = ''
        if limit is not None:
            limit_offset += 'limit :limit '
            params['limit'] = limit
        limit_offset += 'offset :offset'

        if merge:
            # DISTINCT ON (operator_ref) ordered by date desc keeps, per operator, its most recent
            # row in the range; the inner query is then re-sorted by the public order in the outer.
            query = dedent("""
                select date, operator_ref, agency_name from (
                    select distinct on (operator_ref) date, operator_ref, agency_name
                    from gtfs_route
                    {where}
                    order by operator_ref, date desc, agency_name
                ) as merged
                order by date, agency_name
                {limit_offset}
            """).format(where=where, limit_offset=limit_offset)
        else:
            query = dedent("""
                select date, operator_ref, agency_name
                from gtfs_route
                {where}
                group by date, operator_ref, agency_name
                order by date, agency_name
                {limit_offset}
            """).format(where=where, limit_offset=limit_offset)

        res = []
        for row in session.execute(query, params):
            res.append(GtfsAgencyPydanticModel(
                date=row[0],
                operator_ref=row[1],
                agency_name=row[2]
            ))
        return res
