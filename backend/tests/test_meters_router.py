"""HTTP-level tests for the meters_v1 router.

Regression: `GET /meters/count` must be matched by its own handler, not
swallowed by the `GET /meters/{meter_id}` route (which previously returned
404 "Meter count not found" because "count" was parsed as a meter id).
"""

from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from smart_meter_simulator.core import app_state
from smart_meter_simulator.routers.meters_v1 import router


class _FakeMeter:
    def __init__(self, meter_id: str):
        self.meter_id = meter_id
        self.config = {"meter_type": "Grid_Consumer"}
        self.last_reading = None


class _FakeEngine:
    def __init__(self, n: int):
        self.meters = [_FakeMeter(f"meter-{i}") for i in range(n)]


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(app_state, "engine", _FakeEngine(3))
    app = FastAPI()
    app.include_router(router, prefix="/api/v1")
    return TestClient(app)


def test_meter_count_endpoint_returns_count(client):
    resp = client.get("/api/v1/meters/count")
    assert resp.status_code == 200
    assert resp.json() == {"count": 3}


def test_count_not_swallowed_by_meter_id_route(client):
    """`count` must hit the count handler, never the {meter_id} 404."""
    resp = client.get("/api/v1/meters/count")
    assert resp.status_code != 404
    assert "not found" not in resp.text.lower()


def test_unknown_meter_id_still_404(client):
    resp = client.get("/api/v1/meters/does-not-exist")
    assert resp.status_code == 404
