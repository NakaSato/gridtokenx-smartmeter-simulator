import pytest
from fastapi.testclient import TestClient
from app.app import app

@pytest.fixture
def client():
    """Reusable TestClient fixture for API testing."""
    with TestClient(app) as c:
        yield c
