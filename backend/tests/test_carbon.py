"""Carbon-offset model + REST surface.

Unit tests pin the pure ``compute_offset`` math; HTTP tests drive the carbon
router and the per-meter route against a fake engine.
"""

from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from smart_meter_simulator.core import app_state
from smart_meter_simulator.emissions import compute_offset

GRID = 0.5
SOLAR = 0.04


def test_pure_import_only_emits_and_no_offset():
    off = compute_offset(import_kwh=100, export_kwh=0, grid_intensity=GRID)
    assert off.grid_emissions_kg == pytest.approx(50.0)
    assert off.offset_kg == 0.0
    assert off.net_emissions_kg == pytest.approx(50.0)
    assert off.trees_equivalent == 0.0


def test_offset_nets_pv_lifecycle_and_can_go_negative():
    off = compute_offset(
        import_kwh=10,
        export_kwh=100,
        grid_intensity=GRID,
        solar_intensity=SOLAR,
        kg_per_tree_year=20.0,
    )
    # gross offset ignores PV footprint; net deducts it.
    assert off.gross_offset_kg == pytest.approx(50.0)
    assert off.offset_kg == pytest.approx(100 * (GRID - SOLAR))  # 46.0
    assert off.net_emissions_kg == pytest.approx(5.0 - 46.0)  # carbon-negative
    assert off.trees_equivalent == pytest.approx(46.0 / 20.0)


def test_solar_above_grid_clamps_offset_non_negative():
    off = compute_offset(
        import_kwh=0, export_kwh=10, grid_intensity=0.1, solar_intensity=0.2
    )
    assert off.offset_kg == 0.0


def test_negative_energy_rejected():
    with pytest.raises(ValueError):
        compute_offset(import_kwh=-1, export_kwh=0)


class _FakeMeter:
    def __init__(self, meter_id: str, imp: float, exp: float):
        self.meter_id = meter_id
        self.cumulative_import_kwh = imp
        self.cumulative_export_kwh = exp


class _FakeEngine:
    def __init__(self):
        self.meters = [
            _FakeMeter("meter-0", 100.0, 0.0),
            _FakeMeter("meter-1", 20.0, 80.0),
        ]


@pytest.fixture
def client(monkeypatch):
    from smart_meter_simulator.routers.api_v1 import router

    monkeypatch.setattr(app_state, "engine", _FakeEngine())
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


def test_factors_endpoint(client):
    resp = client.get("/api/v1/carbon/factors")
    assert resp.status_code == 200
    body = resp.json()
    assert body["grid_intensity"] == 0.4999
    assert body["unit"] == "kg_co2e_per_kwh"


def test_quote_endpoint(client):
    resp = client.post(
        "/api/v1/carbon/quote",
        json={"import_kwh": 100, "export_kwh": 0, "grid_intensity": 0.5},
    )
    assert resp.status_code == 200
    assert resp.json()["grid_emissions_kg"] == pytest.approx(50.0)


def test_per_meter_carbon(client):
    resp = client.get("/api/v1/meters/meter-1/carbon")
    assert resp.status_code == 200
    body = resp.json()
    assert body["meter_id"] == "meter-1"
    assert body["import_kwh"] == 20.0
    assert body["export_kwh"] == 80.0
    assert body["unit"] == "kg_co2e"


def test_per_meter_carbon_unknown_404(client):
    assert client.get("/api/v1/meters/nope/carbon").status_code == 404


def test_fleet_summary_aggregates(client):
    resp = client.get("/api/v1/carbon/summary")
    assert resp.status_code == 200
    body = resp.json()
    assert body["meter_count"] == 2
    assert body["import_kwh"] == pytest.approx(120.0)
    assert body["export_kwh"] == pytest.approx(80.0)
