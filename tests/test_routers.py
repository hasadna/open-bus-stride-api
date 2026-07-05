import datetime

from . import common


def test_gtfs_agencies(client):
    common.assert_router_list(client, '/gtfs_agencies/list')


def test_gtfs_ride_stops(client):
    common.assert_router_list_get(
        client, '/gtfs_ride_stops',
        params={'arrival_time_from': '2023-05-22T02:12:50+00:00', 'arrival_time_to': '2023-05-22T02:18:59+00:00'},
        get_get_count_params=lambda items: {'gtfs_ride_ids': str(items[0]['gtfs_ride_id'])}
    )


def test_gtfs_ride_stops_list_bad_arrival_time_range(client):
    res = client.get(
        '/gtfs_ride_stops/list',
        params={'arrival_time_from': '2023-01-01T00:00:00+00:00', 'arrival_time_to': '2023-03-01T00:00:00+00:00'},
    )
    assert res.status_code == 400, f'expected 400, got {res.status_code}'
    assert res.json() == {'detail': 'Time range is longer than 30 days'}


def test_gtfs_rides(client):
    common.assert_router_list_get(
        client, '/gtfs_rides',
        get_get_count_params=lambda items: {'journey_ref_prefix': str(items[0]['journey_ref']),
                                            'gtfs_route_id': str(items[0]['gtfs_route_id'])}
    )


def test_gtfs_routes(client):
    common.assert_router_list_get(
        client, '/gtfs_routes',
        get_get_count_params=lambda items: {'line_refs': str(items[0]['line_ref']),
                                            'operator_refs': str(items[0]['operator_ref'])}
    )


def test_gtfs_stops(client):
    common.assert_router_list_get(
        client, '/gtfs_stops',
        get_get_count_params=lambda items: {'code': str(items[0]['code']),
                                            'city': str(items[0]['city'])}
    )


def test_route_timetable(client):
    gtfs_route = client.get('/gtfs_routes/list', params={'limit': 1}).json()[0]
    line_ref = gtfs_route['line_ref']
    date = gtfs_route['date']
    date_to = (datetime.datetime.strptime(date, '%Y-%m-%d') + datetime.timedelta(days=1)).strftime('%Y-%m-%d')
    params = {
        'line_refs': str(line_ref),
        'planned_start_time_date_from': f'{date}T00:00:00+02:00',
        'planned_start_time_date_to': f'{date_to}T00:00:00+02:00',
    }
    common.assert_router_list(
        client, '/route_timetable/list',
        params=params,
        get_get_count_params=lambda items: {}
    )


def test_siri_ride_stops(client):
    common.assert_router_list_get(
        client, '/siri_ride_stops',
        params={'siri_ride_ids': '107208369'},
        get_get_count_params=lambda items: {'siri_ride_ids': str(items[0]['siri_ride_id']),
                                            'siri_stop_ids': str(items[0]['siri_stop_id'])}
    )


def test_siri_rides(client):
    common.assert_router_list_get(
        client, '/siri_rides',
        get_get_count_params=lambda items: {'siri_route_ids': str(items[0]['siri_route_id'])}
    )


def test_siri_routes(client):
    common.assert_router_list_get(
        client, '/siri_routes',
        get_get_count_params=lambda items: {'line_refs': str(items[0]['line_ref']),
                                            'operator_refs': str(items[0]['operator_ref'])}
    )


def test_siri_snapshots(client):
    common.assert_router_list_get(
        client, '/siri_snapshots',
        get_get_count_params=lambda items: {'snapshot_id_prefix': str(items[0]['snapshot_id'])}
    )


def test_siri_stops(client):
    common.assert_router_list_get(
        client, '/siri_stops',
        get_get_count_params=lambda items: {'codes': str(items[0]['code'])}
    )


def test_siri_vehicle_locations(client):
    common.assert_router_list_get(
        client, '/siri_vehicle_locations',
        get_get_count_params=lambda items: {'siri_vehicle_location_ids': str(items[0]['id'])}
    )


def test_siri_vehicle_locations_distinct(client):
    # The SIRI ETL re-stamps a vehicle which has not moved with the same GPS fix on every
    # per-minute snapshot, so the raw endpoint returns many rows sharing
    # (siri_ride__vehicle_ref, recorded_at_time, lat, lon). The opt-in distinct=true param must
    # collapse those to a single representative row while leaving order_by / limit / get_count intact.
    from collections import Counter

    def key(loc):
        return (loc['siri_ride__vehicle_ref'], loc['recorded_at_time'], loc['lat'], loc['lon'])

    # pick a ride that actually has vehicle locations, then compare raw vs de-duplicated for it
    recent = client.get('/siri_vehicle_locations/list', params={'limit': 500, 'order_by': 'id desc'}).json()
    assert recent, 'no siri vehicle locations available to test against'
    ride_id = Counter(loc['siri_ride__id'] for loc in recent).most_common(1)[0][0]

    ride_params = {'siri_rides__ids': str(ride_id), 'limit': 15000, 'order_by': 'recorded_at_time asc'}
    raw = client.get('/siri_vehicle_locations/list', params=ride_params).json()
    distinct = client.get('/siri_vehicle_locations/list', params={**ride_params, 'distinct': 'true'}).json()

    # each (vehicle_ref, recorded_at_time, lat, lon) appears at most once - the core invariant
    distinct_keys = [key(loc) for loc in distinct]
    assert len(distinct_keys) == len(set(distinct_keys)), 'distinct=true returned duplicate fixes'
    # de-dup never invents or drops fixes
    assert len(distinct) <= len(raw)
    if len(raw) < ride_params['limit']:  # only when neither side was truncated by the limit
        assert set(distinct_keys) == {key(loc) for loc in raw}
        assert len(distinct) == len({key(loc) for loc in raw})
    # the public order_by is preserved through the inner DISTINCT ON re-sort
    times = [loc['recorded_at_time'] for loc in distinct]
    assert times == sorted(times), 'distinct=true broke the requested order_by'

    # get_count must count the de-duplicated rows, not the raw ones
    count_params = {'siri_rides__ids': str(ride_id), 'get_count': 'true'}
    raw_count = int(client.get('/siri_vehicle_locations/list', params=count_params).text)
    distinct_count = int(client.get('/siri_vehicle_locations/list', params={**count_params, 'distinct': 'true'}).text)
    assert distinct_count <= raw_count
