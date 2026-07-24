"""Tests for the /gtfs_agencies/list endpoint.

Self-validating: they discover which dates actually hold data (so they pass both against
the local seed and against the prod-like CI DB) and assert invariants rather than fixed rows.
"""

# A range wide enough to span all real data; date_to is needed because date_from alone means
# "just that day". Ordered by date asc, so the sample starts at the earliest populated dates.
WIDE = {'date_from': '2000-01-01', 'date_to': '2100-01-01'}


def _sample_rows(client):
    # Raw per-date rows (merge=false) give us real (date, operator_ref) pairs to build cases from.
    res = client.get('/gtfs_agencies/list', params={**WIDE, 'merge': 'false', 'limit': 200})
    assert res.status_code == 200
    rows = res.json()
    assert rows, 'no gtfs agency data available in the test DB'
    return rows


def test_date_from_is_required(client):
    # A bare call - previously an all-time full-table scan - is now rejected.
    assert client.get('/gtfs_agencies/list').status_code == 422
    # date_to alone is not enough either.
    assert client.get('/gtfs_agencies/list', params={'date_to': '2024-01-01'}).status_code == 422


def test_merged_list_has_one_row_per_operator(client):
    dates = sorted({row['date'] for row in _sample_rows(client)})
    date_from, date_to = dates[0], dates[-1]
    res = client.get('/gtfs_agencies/list',
                     params={'date_from': date_from, 'date_to': date_to, 'merge': 'true'})
    assert res.status_code == 200
    operator_refs = [row['operator_ref'] for row in res.json()]
    # The whole point of the merge: no operator appears twice across the date range.
    assert len(operator_refs) == len(set(operator_refs)), \
        'merged agency list must not contain duplicate operator_ref values'


def test_date_from_without_date_to_is_a_single_day(client):
    day = sorted({row['date'] for row in _sample_rows(client)})[0]
    res = client.get('/gtfs_agencies/list', params={'date_from': day})
    assert res.status_code == 200
    rows = res.json()
    assert rows, 'expected agencies on a known-populated date'
    assert all(row['date'] == day for row in rows), \
        'date_from without date_to must return only that single day'
    operator_refs = [row['operator_ref'] for row in rows]
    assert len(operator_refs) == len(set(operator_refs))
    # On a single day, merged and un-merged describe the same set of operators.
    unmerged = client.get('/gtfs_agencies/list',
                          params={'date_from': day, 'date_to': day, 'merge': 'false'})
    assert unmerged.status_code == 200
    assert set(operator_refs) == {row['operator_ref'] for row in unmerged.json()}


def test_merge_collapses_rows_relative_to_raw(client):
    dates = sorted({row['date'] for row in _sample_rows(client)})
    if len(dates) < 2:
        return  # need a multi-day range for this comparison to be meaningful
    date_from, date_to = dates[0], dates[-1]
    common = {'date_from': date_from, 'date_to': date_to}
    merged = client.get('/gtfs_agencies/list', params={**common, 'merge': 'true'}).json()
    raw = client.get('/gtfs_agencies/list', params={**common, 'merge': 'false', 'limit': 5000}).json()
    # Every merged operator is a real operator seen in the raw rows, and merging never adds rows.
    assert {r['operator_ref'] for r in merged} <= {r['operator_ref'] for r in raw}
    assert len(merged) <= len(raw)
