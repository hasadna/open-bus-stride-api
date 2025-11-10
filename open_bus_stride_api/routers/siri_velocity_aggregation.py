import datetime
from typing import List, Optional

import pydantic
from fastapi import APIRouter, Query, HTTPException
from sqlalchemy import text

from . import common

TAG = "siri"
QUERY = """
    WITH RollingAvg AS (
        with RoundedLonLat as (
            SELECT 
                (CAST(lon AS NUMERIC) * POWER(2, :rounding_precision) + 0.5)::INT / POWER(2, :rounding_precision) AS rounded_lon,
                (CAST(lat AS NUMERIC) * POWER(2, :rounding_precision) + 0.5)::INT / POWER(2, :rounding_precision) AS rounded_lat,
                velocity,
                recorded_at_time
            FROM 
                siri_vehicle_location
            WHERE 
                velocity > :velocity_min
                AND velocity < :velocity_max 
                AND lon BETWEEN :lon_min AND :lon_max
                AND lat BETWEEN :lat_min AND :lat_max
                AND recorded_at_time BETWEEN :recorded_from AND (:recorded_from + INTERVAL '1 day')
        )
        SELECT 
            rounded_lon,
            rounded_lat,
            AVG(velocity) OVER (
                PARTITION BY 
                    rounded_lon,
                    rounded_lat
                ORDER BY 
                    recorded_at_time
                ROWS BETWEEN 2 PRECEDING AND 2 FOLLOWING
            ) AS rolling_average
        FROM 
            RoundedLonLat
    )
    SELECT 
        rounded_lon::DOUBLE PRECISION AS rounded_lon,
        rounded_lat::DOUBLE PRECISION AS rounded_lat,
        COUNT(*) AS total_sample_count,
        AVG(rolling_average) AS average_rolling_avg,
        STDDEV(rolling_average) AS stddev_rolling_avg
    FROM
        RollingAvg
    GROUP BY
        rounded_lon, 
        rounded_lat
    ORDER BY
        rounded_lon, rounded_lat
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
    "/siri_velocity_aggregation",
    tags=[TAG],
    response_model=List[SiriVelocityAggregationPydanticModel],
)
def siri_velocity_aggregation(
    recorded_from: datetime.datetime = Query(
        ..., description="start of recorded_at_time range, inclusive"
    ),
    lon_min: float = Query(34.25, description="minimum longitude bound"),
    lon_max: float = Query(35.70, description="maximum longitude bound"),
    lat_min: float = Query(29.50, description="minimum latitude bound"),
    lat_max: float = Query(33.33, description="maximum latitude bound"),
    rounding_precision: int = Query(
        2, ge=0, le=10, description="lon/lat scaling factor, in powers of 2"
    ),
) -> List[SiriVelocityAggregationPydanticModel]:
    sql = text(QUERY)
    params = {
        "rounding_precision": rounding_precision,
        "velocity_min": VELOCITY_MIN,
        "velocity_max": VELOCITY_MAX,
        "lon_min": lon_min,
        "lon_max": lon_max,
        "lat_min": lat_min,
        "lat_max": lat_max,
        "recorded_from": recorded_from,
    }
    try:
        with common.get_session() as session:
            result = session.execute(sql, params)
            return list(result.fetchall())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
