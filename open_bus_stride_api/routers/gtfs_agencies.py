import typing
import datetime
from textwrap import dedent

import pydantic
from fastapi import APIRouter

from open_bus_stride_db.db import get_session


router = APIRouter()


class GtfsAgencyPydanticModel(pydantic.BaseModel):
    date: datetime.date
    operator_ref: int
    agency_name: str


@router.get("/list", tags=['gtfs'], response_model=typing.List[GtfsAgencyPydanticModel])
def list_(limit: int = None, offset: int = None,
          date_from: datetime.date = None, date_to: datetime.date = None):
    with get_session() as session:
        if not limit or limit > 1000:
            limit = 1000
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
