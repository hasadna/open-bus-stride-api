import pydantic
import sqlalchemy
from fastapi import APIRouter, HTTPException, Response
from open_bus_stride_db.clickhouse import get_session
from open_bus_stride_db.clickhouse.models import SiriVehicleLocation

from . import common

router = APIRouter()


class SiriStopPydanticModel(pydantic.BaseModel):
    id: str
    code: str


def _query(session):
    return session.query(
        SiriVehicleLocation.siri_stop_id.label('id'),
        SiriVehicleLocation.stop_code.label('code'),
    ).distinct()


@common.router_list(router, 'siri', SiriStopPydanticModel, 'siri stops')
def list_(
    limit: int = common.param_limit(),
    offset: int = common.param_offset(),
    get_count: bool = common.param_get_count(),
    codes: str = common.doc_param('stop code', filter_type='list'),
    order_by: str = common.param_order_by(),
):
    with get_session() as session:
        query = _query(session)
        if codes is not None:
            values = codes.split(',')
            if len(values) > 1000:
                raise HTTPException(status_code=400, detail='Maximum 1000 stop codes')
            query = query.filter(SiriVehicleLocation.stop_code.in_(values))
        if get_count:
            return Response(content=str(query.count()), media_type='application/json')
        limit = limit or common.DEFAULT_LIMIT
        if not 0 < limit <= 15000 or (offset is not None and offset < 0):
            raise HTTPException(status_code=400, detail='Invalid limit or offset')
        fields = {'id': SiriVehicleLocation.siri_stop_id, 'code': SiriVehicleLocation.stop_code}
        ordering = []
        for item in (order_by or 'id asc').split(','):
            parts = item.strip().split()
            if not parts or len(parts) > 2 or parts[0] not in fields or (len(parts) == 2 and parts[1].lower() not in ('asc', 'desc')):
                raise HTTPException(status_code=400, detail='Invalid order_by')
            ordering.append((sqlalchemy.desc if len(parts) == 2 and parts[1].lower() == 'desc' else sqlalchemy.asc)(fields[parts[0]]))
        return [row._asdict() for row in query.order_by(*ordering).limit(limit).offset(offset or 0)]


@common.router_get(router, 'siri', SiriStopPydanticModel, 'siri stop')
def get_(id: str = common.param_get_id('siri stop')):
    with get_session() as session:
        rows = _query(session).filter(SiriVehicleLocation.siri_stop_id == id).limit(2).all()
        if not rows:
            raise HTTPException(status_code=404, detail='Siri stop not found')
        if len(rows) > 1:
            raise HTTPException(status_code=409, detail='Siri stop has multiple codes')
        return rows[0]._asdict()
