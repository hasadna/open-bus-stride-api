def test_large_response_is_compressed(client):
    res = client.get('/openapi.json', headers={'Accept-Encoding': 'gzip'})
    assert res.status_code == 200
    assert res.headers['content-encoding'] == 'gzip'
    # The test client decodes the body transparently, so content-length is the
    # size on the wire and res.content is the size without compression.
    assert int(res.headers['content-length']) < len(res.content)


def test_response_is_not_compressed_unless_asked(client):
    res = client.get('/openapi.json', headers={'Accept-Encoding': 'identity'})
    assert res.status_code == 200
    assert 'content-encoding' not in res.headers


def test_small_response_is_not_compressed(client):
    res = client.get('/', headers={'Accept-Encoding': 'gzip'})
    assert res.status_code == 200
    assert 'content-encoding' not in res.headers
