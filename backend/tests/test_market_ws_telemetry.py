"""WS /ws pushes a `meter.telemetry` frame alongside `grid_status`.

Map contract (gridtokenx-trading docs/MAP_REAL_DATA_API.md §4): per-meter
live kW values derived from the last tick's readings so map markers update
between REST polls.
"""

from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from smart_meter_simulator.core import app_state
from smart_meter_simulator.routers.market_ws import router


class _FakeReading:
    def __init__(self, meter_id: str, generated_kwh: float, consumed_kwh: float):
        self.meter_id = meter_id
        self.energy_generated = generated_kwh
        self.energy_consumed = consumed_kwh
        self.interval_seconds = 15


class _FakeEngine:
    def __init__(self):
        self.meters = [object(), object()]
        self.last_tick_summary = {
            "total_generation_kwh": 1.0,
            "total_consumption_kwh": 0.5,
            "net_energy_kwh": 0.5,
            "frequency_hz": 50.0,
            "timestamp": "2026-07-06T00:00:00+00:00",
        }
        self.last_readings = [
            _FakeReading("m-1", 0.01, 0.0),  # 2.4 kW surplus
            _FakeReading("m-2", 0.0, 0.005),  # 1.2 kW deficit
        ]


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(app_state, "engine", _FakeEngine())
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


def test_ws_emits_grid_status_then_meter_telemetry(client):
    with client.websocket_connect("/ws") as ws:
        first = ws.receive_json()
        second = ws.receive_json()

    assert first["type"] == "grid_status"
    assert second["type"] == "meter.telemetry"

    by_id = {entry["meter_id"]: entry for entry in second["data"]}
    assert set(by_id) == {"m-1", "m-2"}

    surplus = by_id["m-1"]
    assert surplus["generation_kw"] == pytest.approx(2.4)
    assert surplus["consumption_kw"] == pytest.approx(0.0)
    assert surplus["surplus_kw"] == pytest.approx(2.4)
    assert surplus["deficit_kw"] == pytest.approx(0.0)
    assert surplus["status"] == "active"

    deficit = by_id["m-2"]
    assert deficit["surplus_kw"] == pytest.approx(0.0)
    assert deficit["deficit_kw"] == pytest.approx(1.2)
