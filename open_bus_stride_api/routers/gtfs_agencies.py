import datetime
from textwrap import dedent

import pydantic
from fastapi import APIRouter

from open_bus_stride_db.db import get_session

from . import common


router = APIRouter()


class GtfsAgencyPydanticModel(pydantic.BaseModel):
    date: datetime.date
    operator_ref: int
    agency_name: str


LIST_MAX_LIMIT = 100
WHAT_SINGULAR = 'gtfs agency'
WHAT_PLURAL = 'gtfs agencies'
TAG = 'gtfs'
PYDANTIC_MODEL = GtfsAgencyPydanticModel


@common.router_list(router, TAG, PYDANTIC_MODEL, WHAT_PLURAL)
def list_(limit: int = common.param_limit(LIST_MAX_LIMIT),
          offset: int = common.param_offset(),
          date_from: datetime.date = common.doc_param('date', filter_type='date_from'),
          date_to: datetime.date = common.doc_param('date', filter_type='date_to')):
    with get_session() as session:
        if not limit:
            limit = LIST_MAX_LIMIT
        assert limit <= LIST_MAX_LIMIT, f'max allowed limit is {LIST_MAX_LIMIT}'
        if not offset:
            offset = 0
        res = []
        wheres = []
        if date_from:
            wheres.append("date >= '{}'".format(date_from.strftime('%Y-%m-%d')))
        if date_to:
            wheres.append("date <= '{}'".format(date_to.strftime('%Y-%m-%d')))
        if len(wheres) > 0:
            where = 'where ' + ' and '.join(wheres)
        else:
            where = ''
        for row in session.execute(dedent("""
            select date, operator_ref, agency_name
            from gtfs_route
            {where}
            group by date, operator_ref, agency_name
            order by date, agency_name
            limit :limit offset :offset
        """.format(where=where)), dict(limit=limit, offset=offset)):
            res.append(GtfsAgencyPydanticModel(
                date=row[0],
                operator_ref=row[1],
                agency_name=row[2]
            ))
        return res
