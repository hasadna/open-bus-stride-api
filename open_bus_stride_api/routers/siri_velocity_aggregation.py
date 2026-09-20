import datetime
from typing import List, Optional

import pydantic
from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import JSONResponse
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
        -- velocity is an integer column, so AVG and STDDEV return numeric, which the driver
        -- has to materialise as a Decimal per row. Cast back to float8 - the response field
        -- is a float either way.
        AVG(rolling_average)::DOUBLE PRECISION AS average_rolling_avg,
        STDDEV(rolling_average)::DOUBLE PRECISION AS stddev_rolling_avg
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
) -> JSONResponse:
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
            # A nationwide request at rounding_precision=10 returns over 100k cells, and
            # re-validating every one of them against response_model costs more than the
            # query. The query already selects exactly the response fields, in order, with
            # the right types, so serialise the rows directly and let FastAPI pass the
            # response through untouched. response_model still documents the schema.
            return JSONResponse([dict(row._mapping) for row in result])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
