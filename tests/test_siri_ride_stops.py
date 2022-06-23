import datetime

import pytest

from .common import get_last_weekday_date


@pytest.mark.skip('slow, data dependant')
def test_urbanaccess_fake_gtfs_data_query(stride_client):
    """Tests a query which is used by stride client urbanaccess"""
    date = get_last_weekday_date()
    min_lon, min_lat, max_lon, max_lat = 34.8, 31.96, 34.81, 31.97
    start_hour, end_hour = 8, 12
    num_items = 0
    for item in stride_client.iterate('/siri_ride_stops/list', {
        'gtfs_stop__lat__greater_or_equal': min_lat,
        'gtfs_stop__lat__lower_or_equal': max_lat,
        'gtfs_stop__lon__greater_or_equal': min_lon,
        'gtfs_stop__lon__lower_or_equal': max_lon,
        'gtfs_route__date_from': date,
        'gtfs_route__date_to': date,
        'siri_vehicle_location__recorded_at_time_from': datetime.datetime.combine(date, datetime.time(start_hour), datetime.timezone.utc),
        'siri_vehicle_location__recorded_at_time_to': datetime.datetime.combine(date, datetime.time(end_hour, 59, 59), datetime.timezone.utc),
        'limit': -1,
    }, limit=None):
        _ = item['nearest_siri_vehicle_location__recorded_at_time'].strftime("%H:%M:%S")
        _ = f'{item["gtfs_stop__city"]}: {item["gtfs_stop__name"]}'
        _ = item['gtfs_stop_id']
        _ = f'{item["gtfs_stop__lat"]}, {item["gtfs_stop__lon"]}'
        _ = item['gtfs_ride__gtfs_route_id']
        _ = item["gtfs_route__route_short_name"]
        _ = item['siri_ride__gtfs_ride_id']
        _ = item["order"]
        num_items += 1
        assert num_items < 10000
    assert num_items > 0
