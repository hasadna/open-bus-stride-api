import pytest
from fastapi.testclient import TestClient

from open_bus_stride_api.main import app


@pytest.fixture(scope='session')
def client():
    return TestClient(app)

