import datetime
from typing import List, Optional

import pydantic
from fastapi import APIRouter, Query, HTTPException
from sqlalchemy import text

from . import common

TAG = 'siri'
QUERY = """
    WITH RollingAvg AS (
        SELECT 
            ROUND(CAST(lon AS NUMERIC), :rounding_precision) AS rounded_lon,
            ROUND(CAST(lat AS NUMERIC), :rounding_precision) AS rounded_lat,
            AVG(velocity) OVER (
                PARTITION BY 
                    ROUND(CAST(lon AS NUMERIC), :rounding_precision),
                    ROUND(CAST(lat AS NUMERIC), :rounding_precision)
                ORDER BY 
                    recorded_at_time 
                ROWS BETWEEN 2 PRECEDING AND 2 FOLLOWING
            ) AS rolling_average
        FROM 
            siri_vehicle_location
        WHERE 
            velocity > :velocity_min
            AND velocity < :velocity_max 
            AND lon BETWEEN :lon_min AND :lon_max
            AND lat BETWEEN :lat_min AND :lat_max
            AND recorded_at_time BETWEEN :recorded_from AND :recorded_to
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

class SiriTimeAggregationPydanticModel(pydantic.BaseModel):
    rounded_lon: float
    rounded_lat: float
    total_sample_count: int
    average_rolling_avg: Optional[float]
    stddev_rolling_avg: Optional[float]

router = APIRouter()

@router.get("/siri_time_aggregation", tags=[TAG], response_model=List[SiriTimeAggregationPydanticModel])
def siri_time_aggregation(
    recorded_from: datetime.datetime = Query(..., description="start of recorded_at_time range, inclusive"),
    lon_min: float = Query(34.25, description="minimum longitude bound"),
    lon_max: float = Query(35.70, description="maximum longitude bound"),
    lat_min: float = Query(29.50, description="minimum latitude bound"),
    lat_max: float = Query(33.33, description="maximum latitude bound"),
    rounding_precision: int = Query(2, ge=0, le=6, description="number of decimals to round lon/lat"),
) -> List[SiriTimeAggregationPydanticModel]:
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
        "recorded_to": recorded_from + datetime.timedelta(days=1),
    }

    try:
        with common.get_session() as session:
            result = session.execute(sql, params)
            rows: List[SiriTimeAggregationPydanticModel] = [
                {
                    "rounded_lon": float(r["rounded_lon"]),
                    "rounded_lat": float(r["rounded_lat"]),
                    "total_sample_count": int(r["total_sample_count"]),
                    "average_rolling_avg": None if r["average_rolling_avg"] is None else float(r["average_rolling_avg"]),
                    "stddev_rolling_avg": None if r["stddev_rolling_avg"] is None else float(r["stddev_rolling_avg"]),
                }
                for r in result.fetchall()
            ]
            return rows
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
