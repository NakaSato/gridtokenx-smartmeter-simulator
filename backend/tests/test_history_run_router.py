"""HTTP-level tests for the InfluxDB run time-series endpoints in history_v1.

Covers ``/history/run/current``, ``/history/runs``, ``/history/run/series`` against
a fake influx store — no live InfluxDB. Pins the dependency wiring (503 when the
store is disabled, 400 when no run_id resolves, and aggregate-vs-per-meter dispatch).
"""

from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from smart_meter_simulator.core import app_state
from smart_meter_simulator.routers.history_v1 import router


class _FakeInflux:
    """Stand-in for InfluxReadingStore: records calls, returns canned series."""

    def __init__(self):
        self.calls: list[tuple] = []

    async def list_runs(self):
        return ["seed42-20260610T080000-i15-m80", "seed7-20260101T000000-i900-m10"]

    async def aggregate_series(self, run_id: str):
        self.calls.append(("aggregate", run_id))
        return [
            {"time": "2026-06-10T08:00:00+00:00", "energy_generated": 100.0,
             "energy_consumed": 40.0, "net": 60.0, "frequency": 50.0},
        ]

    async def meter_series(self, run_id: str, meter_id: str):
        self.calls.append(("meter", run_id, meter_id))
        return [
            {"time": "2026-06-10T08:00:00+00:00", "energy_generated": 1.4,
             "energy_consumed": 0.5, "voltage": 230.0},
        ]


class _FakeEngine:
    def __init__(self, *, run_id="seed42-20260610T080000-i15-m80", influx=None):
        self.run_id = run_id
        self.influx_store = influx


def _client(engine):
    app = FastAPI()
    app.include_router(router, prefix="/api/v1")
    return TestClient(app)


@pytest.fixture
def influx():
    return _FakeInflux()


@pytest.fixture
def client(monkeypatch, influx):
    monkeypatch.setattr(app_state, "engine", _FakeEngine(influx=influx))
    return _client(None)


def test_current_run_returns_engine_run_id(client):
    resp = client.get("/api/v1/history/run/current")
    assert resp.status_code == 200
    assert resp.json() == {"run_id": "seed42-20260610T080000-i15-m80"}


def test_list_runs(client):
    resp = client.get("/api/v1/history/runs")
    assert resp.status_code == 200
    body = resp.json()
    assert body["count"] == 2
    assert "seed42-20260610T080000-i15-m80" in body["runs"]


def test_series_defaults_to_current_run_aggregate(client, influx):
    resp = client.get("/api/v1/history/run/series")
    assert resp.status_code == 200
    body = resp.json()
    assert body["run_id"] == "seed42-20260610T080000-i15-m80"
    assert body["meter_id"] is None
    assert body["count"] == 1
    assert influx.calls == [("aggregate", "seed42-20260610T080000-i15-m80")]


def test_series_explicit_run_id(client, influx):
    resp = client.get("/api/v1/history/run/series", params={"run_id": "seed7-x"})
    assert resp.status_code == 200
    assert resp.json()["run_id"] == "seed7-x"
    assert influx.calls == [("aggregate", "seed7-x")]


def test_series_per_meter_dispatch(client, influx):
    resp = client.get(
        "/api/v1/history/run/series",
        params={"run_id": "seed7-x", "meter_id": "meter-3"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["meter_id"] == "meter-3"
    assert body["series"][0]["voltage"] == 230.0
    assert influx.calls == [("meter", "seed7-x", "meter-3")]


def test_series_400_when_no_run_id_resolves(monkeypatch, influx):
    monkeypatch.setattr(app_state, "engine", _FakeEngine(run_id=None, influx=influx))
    resp = _client(None).get("/api/v1/history/run/series")
    assert resp.status_code == 400


def test_runs_503_when_influx_disabled(monkeypatch):
    monkeypatch.setattr(app_state, "engine", _FakeEngine(influx=None))
    resp = _client(None).get("/api/v1/history/runs")
    assert resp.status_code == 503
    assert "INFLUX_ENABLED" in resp.text


def test_series_503_when_influx_disabled(monkeypatch):
    monkeypatch.setattr(app_state, "engine", _FakeEngine(influx=None))
    resp = _client(None).get("/api/v1/history/run/series")
    assert resp.status_code == 503


def test_current_run_503_when_engine_uninitialized(monkeypatch):
    monkeypatch.setattr(app_state, "engine", None)
    resp = _client(None).get("/api/v1/history/run/current")
    assert resp.status_code == 503
