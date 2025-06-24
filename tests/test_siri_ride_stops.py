import datetime

import pytest


def get_query_params():
    date = datetime.date(2022, 6, 21)
    min_lon, min_lat, max_lon, max_lat = 34.732918, 31.988688, 34.876007, 32.202171
    start_hour, end_hour = 8, 12
    recorded_at_time_from = datetime.datetime.combine(date, datetime.time(start_hour), datetime.timezone.utc)
    recorded_at_time_to = datetime.datetime.combine(date, datetime.time(end_hour, 59, 59), datetime.timezone.utc)
    return {
        'gtfs_stop__lat__greater_or_equal': min_lat,
        'gtfs_stop__lat__lower_or_equal': max_lat,
        'gtfs_stop__lon__greater_or_equal': min_lon,
        'gtfs_stop__lon__lower_or_equal': max_lon,
        'gtfs_date_from': date,
        'gtfs_date_to': date,
        'siri_vehicle_location__recorded_at_time_from': recorded_at_time_from,
        'siri_vehicle_location__recorded_at_time_to': recorded_at_time_to,
        'siri_ride__scheduled_start_time_from': recorded_at_time_from - datetime.timedelta(hours=10),
        'siri_ride__scheduled_start_time_to': recorded_at_time_to + datetime.timedelta(hours=10),
        'limit': -1,
    }


@pytest.mark.skip(reason="This test relies on specific GTFS data that is not always available")
def test_urbanaccess_fake_gtfs_data_query(stride_client):
    """Tests a query which is used by stride client urbanaccess"""
    start_time = datetime.datetime.now()
    first_item_time = None
    for item in stride_client.iterate('/siri_ride_stops/list', get_query_params(), limit=None):
        first_item_time = datetime.datetime.now()
        _ = item['nearest_siri_vehicle_location__recorded_at_time'].strftime("%H:%M:%S")
        _ = f'{item["gtfs_stop__city"]}: {item["gtfs_stop__name"]}'
        _ = item['gtfs_stop_id']
        _ = f'{item["gtfs_stop__lat"]}, {item["gtfs_stop__lon"]}'
        _ = item['gtfs_ride__gtfs_route_id']
        _ = item["gtfs_route__route_short_name"]
        _ = item['siri_ride__gtfs_ride_id']
        _ = item["order"]
        break
    seconds_to_first_item = (first_item_time - start_time).total_seconds()
    print(f'seconds_to_first_item={seconds_to_first_item}')
