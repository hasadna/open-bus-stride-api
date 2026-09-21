import pytest


EVIDENCE_FIELDS = [
    'siri_ride_id', 'vehicle_ref', 'journey_ref', 'first_seen', 'last_seen',
    'observed_stop_orders', 'max_stop_order', 'planned_stop_count', 'stop_coverage',
]


def find_route_with_rides(client):
    """Find an (operator_ref, line_ref, date) that actually has /rides_execution rows.

    Discovered from the API rather than hardcoded on purpose: CI runs against a
    production-like database while the local harness runs against a tiny seed, and
    neither one's ids exist in the other.
    """
    res = client.get('/gtfs_routes/list', params={'limit': 25})
    assert res.status_code == 200, res.text
    routes = res.json()
    assert routes, 'no gtfs_routes at all - cannot exercise /rides_execution'
    for route in routes:
        if route.get('operator_ref') is None or route.get('line_ref') is None or not route.get('date'):
            continue
        params = {
            'date_from': route['date'],
            'date_to': route['date'],
            'operator_ref': route['operator_ref'],
            'line_ref': route['line_ref'],
            'limit': 100,
        }
        res = client.get('/rides_execution/list', params=params)
        assert res.status_code == 200, res.text
        rows = res.json()
        if rows:
            return params, rows
    pytest.skip('none of the sampled gtfs_routes has planned or actual rides')


def test_rides_execution_evidence_fields(client):
    params, rows = find_route_with_rides(client)

    previous_planned = None
    for row in rows:
        for field in EVIDENCE_FIELDS:
            assert field in row, f'missing evidence field {field!r} in {row}'

        # every row is a planned ride, an actual ride, or both - never neither
        assert row['planned_start_time'] or row['actual_start_time'], row

        # the two sides come from the same subquery each, so they appear and vanish together
        assert (row['actual_start_time'] is None) == (row['siri_ride_id'] is None), row
        assert (row['planned_start_time'] is None) == (row['gtfs_ride_id'] is None), row

        # a ride with no actual side carries no evidence about one
        if row['siri_ride_id'] is None:
            for field in ['vehicle_ref', 'journey_ref', 'first_seen', 'last_seen',
                          'observed_stop_orders', 'max_stop_order']:
                assert row[field] is None, f'{field} set on a row with no siri_ride: {row}'

        # stop_coverage is exactly max_stop_order / planned_stop_count, or nothing at all
        if row['stop_coverage'] is None:
            assert row['max_stop_order'] is None or not row['planned_stop_count'], row
        else:
            assert row['max_stop_order'] is not None and row['planned_stop_count'], row
            expected = round(row['max_stop_order'] / row['planned_stop_count'], 3)
            assert abs(row['stop_coverage'] - expected) < 1e-9, row

        # the furthest stop reached cannot be behind the number of distinct stops reported
        if row['max_stop_order'] is not None and row['max_stop_order'] >= 1:
            assert 1 <= row['observed_stop_orders'] <= row['max_stop_order'], row

        # the enrichment fills first/last from min/max recorded_at_time of the same ride
        if row['first_seen'] and row['last_seen']:
            assert row['first_seen'] <= row['last_seen'], row

        # documented ordering: planned_start_time ascending, nulls last
        if row['planned_start_time']:
            assert previous_planned is None or previous_planned <= row['planned_start_time'], row
            previous_planned = row['planned_start_time']

    res = client.get('/rides_execution/list', params={**params, 'get_count': 'true'})
    assert res.status_code == 200, res.text
    assert int(res.text) >= len(rows)


def test_rides_execution_detects_an_announced_but_unmoved_ride(client):
    """A ride whose vehicle never progressed along the route must be distinguishable.

    This is the whole point of the evidence fields: before they existed, such a ride was
    indistinguishable from one that ran, because actual_start_time is a copy of the
    planned time. Asserts the shape of the signal on whatever data is present rather than
    requiring a phantom to exist.
    """
    _, rows = find_route_with_rides(client)
    scored = [r for r in rows if r['stop_coverage'] is not None]
    if not scored:
        pytest.skip('no ride on the sampled route has both a matched plan and observed stops')
    for row in scored:
        assert 0 < row['stop_coverage'] <= row['planned_stop_count'], row
        # a ride that was merely announced reaches at most the first stop
        if row['max_stop_order'] <= 1:
            assert row['stop_coverage'] <= 1 / row['planned_stop_count'] + 1e-9, row
