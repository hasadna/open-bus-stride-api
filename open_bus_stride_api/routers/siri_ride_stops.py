import typing

import pydantic
from fastapi import APIRouter
import sqlalchemy.orm

from open_bus_stride_db import model

from . import common
from . import siri_rides, siri_stops, gtfs_stops, siri_vehicle_locations, gtfs_ride_stops


router = APIRouter()


class SiriRideStopPydanticModel(pydantic.BaseModel):
    id: int
    siri_stop_id: int
    siri_ride_id: int
    order: int
    gtfs_stop_id: int = None
    nearest_siri_vehicle_location_id: int = None


siri_stop_related_model = common.PydanticRelatedModel(
    'siri_stop__', siri_stops.SiriStopPydanticModel, ['id']
)
siri_ride_related_model = common.PydanticRelatedModel(
    'siri_ride__', siri_rides.SiriRidePydanticModel, ['id']
)
gtfs_stop_related_model = common.PydanticRelatedModel(
    'gtfs_stop__', gtfs_stops.GtfsStopPydanticModel, ['id']
)
nearest_siri_vehicle_location_related_model = common.PydanticRelatedModel(
    'nearest_siri_vehicle_location__', siri_vehicle_locations.SiriVehicleLocationPydanticModel, ['id']
)
gtfs_ride_stop_related_model = common.PydanticRelatedModel(
    'gtfs_ride_stop__', gtfs_ride_stops.GtfsRideStopPydanticModel, ['id']
)

SiriRideStopWithRelatedPydanticModel = common.pydantic_create_model_with_related(
    'SiriRideStopWithRelatedPydanticModel',
    SiriRideStopPydanticModel,
    siri_stop_related_model,
    siri_ride_related_model,
    gtfs_stop_related_model,
    nearest_siri_vehicle_location_related_model,
    gtfs_ride_stop_related_model
)


def _post_session_query_hook(session_query: sqlalchemy.orm.Query):
    return (
        session_query
        .select_from(model.SiriRideStop)
        .add_entity(model.SiriRide)
        .add_entity(model.SiriStop)
        .add_entity(model.GtfsStop)
        .add_entity(model.SiriVehicleLocation)
        .add_entity(model.GtfsRideStop)
        .add_entity(model.GtfsRide)
        .join(model.SiriRide)
        .join(model.SiriStop)
        .outerjoin(model.GtfsStop, model.SiriRideStop.gtfs_stop_id == model.GtfsStop.id)
        .outerjoin(model.SiriVehicleLocation, model.SiriRideStop.nearest_siri_vehicle_location_id == model.SiriVehicleLocation.id)
        .outerjoin(model.GtfsRide, model.SiriRide.gtfs_ride_id == model.GtfsRide.id)
        .outerjoin(
            model.GtfsRideStop,
            sqlalchemy.sql.and_(model.GtfsRideStop.gtfs_stop_id == model.GtfsStop.id,
                                model.GtfsRideStop.gtfs_ride_id == model.GtfsRide.id)
        )
    )


def _convert_to_dict(obj: model.SiriRideStop):
    siri_ride_stop, siri_ride, siri_stop, gtfs_stop, nearest_siri_vehicle_location, gtfs_ride_stop, gtfs_ride = obj
    res = siri_ride_stop.__dict__
    siri_stop_related_model.add_orm_obj_to_dict_res(siri_stop, res)
    siri_ride_related_model.add_orm_obj_to_dict_res(siri_ride, res)
    gtfs_stop_related_model.add_orm_obj_to_dict_res(gtfs_stop, res)
    nearest_siri_vehicle_location_related_model.add_orm_obj_to_dict_res(nearest_siri_vehicle_location, res)
    gtfs_ride_stop_related_model.add_orm_obj_to_dict_res(gtfs_ride_stop, res)
    return res


@router.get("/list", tags=['siri'], response_model=typing.List[SiriRideStopWithRelatedPydanticModel])
def list_(limit: int = None, offset: int = None,
          siri_stop_ids: str = None,
          siri_ride_ids: str = None,
          order_by: str = None):
    """
    * siri_stop_ids: comma-separated list
    * siri_ride_ids: comma-separated list
    * order_by: comma-separated list of order by fields, e.g.: "order asc,siri_stop_id desc"
    """
    return common.get_list(
        model.SiriRideStop, limit, offset,
        [
            {'type': 'in', 'field': model.SiriRideStop.siri_stop_id, 'value': siri_stop_ids},
            {'type': 'in', 'field': model.SiriRideStop.siri_ride_id, 'value': siri_ride_ids},
        ],
        order_by=order_by,
        post_session_query_hook=_post_session_query_hook,
        convert_to_dict=_convert_to_dict
    )


@router.get('/get', tags=['siri'], response_model=SiriRideStopPydanticModel)
def get_(id: int):
    return common.get_item(model.SiriRideStop, model.SiriRideStop.id, id)
