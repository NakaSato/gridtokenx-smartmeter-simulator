import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

from smart_meter_simulator.services.cost_calculator_service import CostCalculatorService
from smart_meter_simulator.services.strategy_service import GridFinancials
from smart_meter_simulator.models.reading import EnergyReading
from smart_meter_simulator.transport.influx_mappers.mappers import map_operational_cost
from smart_meter_simulator.app import create_app
from smart_meter_simulator.core import app_state


def test_cost_calculator_direct_rates():
    """Test cost service calculations for each generator/consumer type."""
    service = CostCalculatorService()

    # Establish readings
    readings = [
        # Solar prosumer generating 10 kWh
        EnergyReading(
            meter_id="solar_meter",
            timestamp=datetime.now(timezone.utc),
            energy_generated=10.0,
            energy_consumed=2.0,
            surplus_energy=8.0,
            deficit_energy=0.0,
            location="Samui",
            meter_type="Solar_Prosumer",
            user_type="Residential",
        ),
        # BESS prosumer generating 5 kWh
        EnergyReading(
            meter_id="bess_meter",
            timestamp=datetime.now(timezone.utc),
            energy_generated=5.0,
            energy_consumed=1.0,
            surplus_energy=4.0,
            deficit_energy=0.0,
            location="Samui",
            meter_type="Battery_Storage",
            user_type="Residential",
        ),
        # Diesel generator producing 20 kWh
        EnergyReading(
            meter_id="TAO-GEN-DIESEL",
            timestamp=datetime.now(timezone.utc),
            energy_generated=20.0,
            energy_consumed=0.0,
            surplus_energy=20.0,
            deficit_energy=0.0,
            location="Tao",
            meter_type="Generator",
            user_type="Industrial",
        ),
        # General consumer importing 15 kWh
        EnergyReading(
            meter_id="consumer_meter",
            timestamp=datetime.now(timezone.utc),
            energy_generated=0.0,
            energy_consumed=15.0,
            surplus_energy=0.0,
            deficit_energy=15.0,
            location="Samui",
            meter_type="Residential",
            user_type="Residential",
            nodal_price=4.5,
            carbon_intensity=500.0,
        ),
    ]

    records = service.calculate_step_costs(readings, strategy_mode="PEAK_SHAVING")

    # We expect 4 records (Solar, BESS, Diesel, Grid)
    assert len(records) == 4

    # Verify Solar
    solar = next(r for r in records if r["source"] == "Solar")
    assert solar["cost_thb"] == 0.0
    assert solar["savings_thb"] == 130.0  # 10 kWh * 13.0
    assert solar["diesel_displaced_liters"] == 3.3  # 10 kWh * 0.33
    assert solar["carbon_offset_kg"] == 7.4  # 10 kWh * 0.74

    # Verify BESS
    bess = next(r for r in records if r["source"] == "BESS")
    assert bess["cost_thb"] == 17.5  # 5 kWh * 3.5
    assert bess["savings_thb"] == 47.5  # 5 kWh * (13.0 - 3.5)

    # Verify Diesel
    diesel = next(r for r in records if r["source"] == "Diesel")
    assert diesel["cost_thb"] == 260.0  # 20 kWh * 13.0
    assert diesel["carbon_tax_thb"] == 0.59  # 20 * 0.74 * 0.04 = 0.592

    # Verify Grid
    grid = next(r for r in records if r["source"] == "Grid")
    assert grid["cost_thb"] == 67.5  # 15 kWh * 4.5 nodal price
    assert grid["carbon_tax_thb"] == 0.30  # 15 * 0.5 * 0.04

    # Verify summary
    summary = service.get_savings_summary()
    assert summary["total_savings_thb"] == 177.5  # 130.0 + 47.5
    assert summary["diesel_displaced_liters"] == 4.95  # 3.3 + 1.65
    assert summary["carbon_offset_kg"] == 11.1  # 7.4 + 3.7


def test_analytics_endpoints_empty_engine():
    """Verify endpoints return default empty structure when engine is not initialized."""
    app = create_app()
    client = TestClient(app)

    # Explicitly clear engine state
    with patch.object(app_state, "engine", None):
        response_costs = client.get("/api/v1/analytics/costs")
        assert response_costs.status_code == 200
        assert response_costs.json() == []

        response_savings = client.get("/api/v1/analytics/savings/summary")
        assert response_savings.status_code == 200
        assert response_savings.json() == {
            "total_savings_thb": 0.0,
            "diesel_displaced_liters": 0.0,
            "carbon_offset_kg": 0.0,
        }


def test_influx_cost_mapping():
    """Assert mapper creates valid InfluxDB Point from operational cost record."""
    record = {
        "timestamp": "2026-05-31T12:00:00Z",
        "zone": "Samui",
        "source": "BESS",
        "cost_thb": 17.5,
        "savings_thb": 47.5,
        "carbon_tax_thb": 0.0,
        "strategy_mode": "PEAK_SHAVING",
        "meter_id": "test_bess_01",
    }
    point = map_operational_cost(record)
    assert point._name == "operational_costs"
    assert point._tags["zone"] == "Samui"
    assert point._tags["source"] == "BESS"
    assert point._tags["strategy_mode"] == "PEAK_SHAVING"
    assert point._tags["meter_id"] == "test_bess_01"
    assert point._fields["cost_thb"] == 17.5
    assert point._fields["savings_thb"] == 47.5
    assert point._fields["carbon_tax_thb"] == 0.0
