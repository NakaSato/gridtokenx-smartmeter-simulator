"""HTTP-level tests for GET /grid/flows (trading-UI map flow contract).

Raw-refs form per gridtokenx-trading docs/MAP_REAL_DATA_API.md §3:
{"flows": [{"from_meter_id", "to_zone_id", "power_kw", "description"}]}
— one flow per meter with non-trivial net power (|net| > 0.1 kW), signed
positive for surplus (meter→zone) and negative for deficit (zone→meter).
"""

from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from smart_meter_simulator.core import app_state
from smart_meter_simulator.routers.grid_v1 import router


class _FakeReading:
    def __init__(self, generated_kwh: float, consumed_kwh: float, interval_s: int = 15):
        self.energy_generated = generated_kwh
        self.energy_consumed = consumed_kwh
        self.interval_seconds = interval_s


class _FakeMeter:
    def __init__(self, meter_id: str, zone_code: int, reading: _FakeReading | None):
        self.meter_id = meter_id
        self.config = {
            "zone_code": zone_code,
            "location_name": f"Loc {meter_id}",
        }
        self.last_reading = reading


def _client(meters) -> TestClient:
    class _FakeEngine:
        def __init__(self):
            self.meters = meters

    app_state.engine = _FakeEngine()
    app = FastAPI()
    app.include_router(router, prefix="/api/v1")
    return TestClient(app)


@pytest.fixture(autouse=True)
def _restore_engine():
    saved = app_state.engine
    yield
    app_state.engine = saved


def test_flows_surplus_and_deficit_signed():
    # 15 s interval: 0.01 kWh -> 2.4 kW. Exporter nets +2.4, importer -2.4.
    meters = [
        _FakeMeter("m-export", 3, _FakeReading(0.01, 0.0)),
        _FakeMeter("m-import", 5, _FakeReading(0.0, 0.01)),
    ]
    resp = _client(meters).get("/api/v1/grid/flows")
    assert resp.status_code == 200
    flows = {f["from_meter_id"]: f for f in resp.json()["flows"]}
    assert set(flows) == {"m-export", "m-import"}

    export = flows["m-export"]
    assert export["to_zone_id"] == 3
    assert export["power_kw"] == pytest.approx(2.4)
    assert "export" in export["description"]

    imp = flows["m-import"]
    assert imp["to_zone_id"] == 5
    assert imp["power_kw"] == pytest.approx(-2.4)
    assert "import" in imp["description"]


def test_trivial_and_missing_readings_excluded():
    meters = [
        # |net| = 0.024 kW — below the 0.1 kW floor.
        _FakeMeter("m-noise", 1, _FakeReading(0.0001, 0.0)),
        # Balanced meter — net 0.
        _FakeMeter("m-balanced", 1, _FakeReading(0.005, 0.005)),
        # No reading yet (before first tick).
        _FakeMeter("m-cold", 1, None),
    ]
    resp = _client(meters).get("/api/v1/grid/flows")
    assert resp.status_code == 200
    assert resp.json() == {"flows": []}


def test_no_engine_returns_empty_flows():
    app_state.engine = None
    app = FastAPI()
    app.include_router(router, prefix="/api/v1")
    resp = TestClient(app).get("/api/v1/grid/flows")
    assert resp.status_code == 200
    assert resp.json() == {"flows": []}


def test_unzoned_meter_flows_to_zone_zero():
    meters = [_FakeMeter("m-unzoned", 0, _FakeReading(0.01, 0.0))]
    meters[0].config["zone_code"] = None
    resp = _client(meters).get("/api/v1/grid/flows")
    flows = resp.json()["flows"]
    assert len(flows) == 1
    assert flows[0]["to_zone_id"] == 0
