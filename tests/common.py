from open_bus_stride_api.routers.common import DEFAULT_LIMIT


def assert_router_list(client, path, params=None, get_get_count_params=None):
    res = client.get(path, params=params)
    assert res.status_code == 200
    items = res.json()
    assert 1 <= len(items) <= DEFAULT_LIMIT
    if get_get_count_params:
        get_count_params = {**get_get_count_params(items), 'get_count': 'true'}
        res = client.get(path, params={**(params if params else {}), **get_count_params})
        assert res.status_code == 200
        assert int(res.text) > 0
    return items


def assert_router_list_get(client, base_path, params=None, get_get_count_params=None):
    items = assert_router_list(client, base_path + '/list', params=params, get_get_count_params=get_get_count_params)
    first_item = items[0]
    first_item_id = first_item['id']
    res = client.get(base_path + '/get', params={'id': first_item_id})
    assert res.status_code == 200
    assert isinstance(res.json(), dict)
    return items
