import datetime
from typing import List, Optional

import pydantic
from fastapi import APIRouter, HTTPException, Query
from open_bus_stride_db.clickhouse import get_session
from sqlalchemy import text

TAG = 'siri'
QUERY = """
    WITH parsed AS (
        SELECT toFloat64OrNull(vehicle_location_longitude) AS lon,
               toFloat64OrNull(vehicle_location_latitude) AS lat,
               toFloat64OrNull(velocity) AS speed,
               recorded_at_time
        FROM siri_vehicle_location
        WHERE recorded_at_time BETWEEN :recorded_from AND :recorded_to
    ), rounded AS (
        SELECT
            if(lon * :scale + 0.5 >= 0, floor(lon * :scale + 1), ceil(lon * :scale)) / :scale AS rounded_lon,
            if(lat * :scale + 0.5 >= 0, floor(lat * :scale + 1), ceil(lat * :scale)) / :scale AS rounded_lat,
            speed, recorded_at_time
        FROM parsed
        WHERE isFinite(lon) AND isFinite(lat) AND isFinite(speed)
          AND speed > :velocity_min AND speed < :velocity_max
          AND lon BETWEEN :lon_min AND :lon_max
          AND lat BETWEEN :lat_min AND :lat_max
    ), rolling AS (
        SELECT rounded_lon, rounded_lat,
               avg(speed) OVER (
                   PARTITION BY rounded_lon, rounded_lat
                   ORDER BY recorded_at_time
                   ROWS BETWEEN 2 PRECEDING AND 2 FOLLOWING
               ) AS rolling_average
        FROM rounded
    )
    SELECT rounded_lon, rounded_lat, count() AS total_sample_count,
           avg(rolling_average) AS average_rolling_avg,
           if(count() > 1, stddevSamp(rolling_average), NULL) AS stddev_rolling_avg
    FROM rolling
    GROUP BY rounded_lon, rounded_lat
    ORDER BY rounded_lon, rounded_lat
"""
VELOCITY_MIN = 0
VELOCITY_MAX = 200


class SiriVelocityAggregationPydanticModel(pydantic.BaseModel):
    rounded_lon: float
    rounded_lat: float
    total_sample_count: int
    average_rolling_avg: Optional[float]
    stddev_rolling_avg: Optional[float]


router = APIRouter()


@router.get(
    '/siri_velocity_aggregation',
    tags=[TAG],
    response_model=List[SiriVelocityAggregationPydanticModel],
)
def siri_velocity_aggregation(
    recorded_from: datetime.datetime = Query(..., description='start of recorded_at_time range, inclusive'),
    lon_min: float = Query(34.25, description='minimum longitude bound'),
    lon_max: float = Query(35.70, description='maximum longitude bound'),
    lat_min: float = Query(29.50, description='minimum latitude bound'),
    lat_max: float = Query(33.33, description='maximum latitude bound'),
    rounding_precision: int = Query(2, ge=0, le=10, description='lon/lat scaling factor, in powers of 2'),
) -> List[SiriVelocityAggregationPydanticModel]:
    sql = text(QUERY)
    params = {
        'scale': 2**rounding_precision,
        'velocity_min': VELOCITY_MIN,
        'velocity_max': VELOCITY_MAX,
        'lon_min': lon_min,
        'lon_max': lon_max,
        'lat_min': lat_min,
        'lat_max': lat_max,
        'recorded_from': recorded_from.astimezone(datetime.timezone.utc).replace(tzinfo=None) if recorded_from.tzinfo else recorded_from,
    }
    params['recorded_to'] = params['recorded_from'] + datetime.timedelta(days=1)
    try:
        with get_session() as session:
            result = session.execute(sql, params)
            return list(result.fetchall())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
