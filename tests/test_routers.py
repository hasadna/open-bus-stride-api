import datetime

import pytest

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


def group_by_agg(client, params):
    res = client.get('/gtfs_rides_agg/group_by', params=params)
    assert res.status_code == 200, res.text
    return res.json()


def find_agg_date_with_groups(client, group_by, minimum):
    """Params for a recent date which actually has `minimum` groups, so the assertions below
    describe real data on whatever database the suite runs against."""
    for minus_days in range(1, 15):
        date = (datetime.datetime.now() - datetime.timedelta(days=minus_days)).date().isoformat()
        params = {'date_from': date, 'date_to': date, 'group_by': group_by}
        groups = group_by_agg(client, params)
        if len(groups) >= minimum:
            return params, groups
    pytest.skip(f'no date in the last 14 days has {minimum} "{group_by}" groups to test with')


def test_gtfs_rides_agg_group_by_order_by_limit(client):
    params, groups = find_agg_date_with_groups(client, 'operator_ref', 2)
    limit = len(groups) - 1

    top = group_by_agg(client, {**params, 'order_by': 'total_planned_rides desc', 'limit': limit})

    assert len(top) == limit
    assert [g['total_planned_rides'] for g in top] \
        == sorted((g['total_planned_rides'] for g in groups), reverse=True)[:limit]


def test_gtfs_rides_agg_group_by_unordered_by_default(client):
    # every existing consumer fetches without order_by/limit and expects the whole grouping
    params, groups = find_agg_date_with_groups(client, 'operator_ref', 2)
    assert len(group_by_agg(client, params)) == len(groups)


def test_gtfs_rides_agg_group_by_get_count(client):
    params, groups = find_agg_date_with_groups(client, 'operator_ref', 1)
    res = client.get('/gtfs_rides_agg/group_by', params={**params, 'get_count': 'true'})
    assert res.status_code == 200
    assert int(res.text) == len(groups)


@pytest.mark.parametrize('order_by,expected_error', [
    ('line_ref', 'Invalid order_by field'),
    ('total_routes desc; drop table gtfs_route --', 'Invalid order_by element'),
    ('total_routes sideways', 'Invalid order_by direction'),
])
def test_gtfs_rides_agg_group_by_rejects_invalid_order_by(client, order_by, expected_error):
    # a name which is not one of this request's own output fields is refused before any query
    # runs, so it reads as a message about order_by rather than as a database error
    with pytest.raises(AssertionError, match=expected_error):
        client.get('/gtfs_rides_agg/group_by', params={
            'date_from': '2026-01-01', 'date_to': '2026-01-01',
            'group_by': 'operator_ref', 'order_by': order_by,
        })


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
