import time
import subprocess

import pytest
import stride
import stride.config
from fastapi.testclient import TestClient

from open_bus_stride_api.main import app


@pytest.fixture(scope='session')
def client():
    return TestClient(app)


@pytest.fixture(scope='function')
def stride_client():
    stride.config.STRIDE_API_BASE_URL = 'http://localhost:8000'
    process = subprocess.Popen(['uvicorn', 'open_bus_stride_api.main:app'])
    try:
        ok = False
        for i in range(10):
            time.sleep(1)
            try:
                if stride.get('/', {})['ok']:
                    ok = True
                    break
            except:
                pass
        assert ok
        yield stride
    finally:
        process.terminate()
        process.wait()
