import pytest
from fastapi.testclient import TestClient

from app.main import create_app


@pytest.fixture
def client() -> TestClient:
    # raise_server_exceptions=False: we assert on the HTTP response, not on a re-raised exception.
    return TestClient(create_app(), raise_server_exceptions=False)
