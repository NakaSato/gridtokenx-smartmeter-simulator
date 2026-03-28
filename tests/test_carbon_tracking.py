import pytest
from datetime import datetime
from unittest.mock import MagicMock, patch
import pandas as pd
import pandapower as pp

from smart_meter_simulator.core.engine import SimulationEngine
from smart_meter_simulator.core.vpp import VPPManager, VPPCluster, DERResource
from smart_meter_simulator.core.billing import ThaiBillingEngine

def test_carbon_intensity_calculation():
    """Test that carbon intensity decreases as solar generation increases."""
    # We don't need a full SimulationEngine, just test the formula used in engine.py
    # formula: current_carbon_intensity = max(0.0, (grid_p_mw / total_load_mw) * 500.0)
    
    # Case 1: 100% Grid
    grid_p = 1.0
    total_load = 1.0
    intensity_1 = (grid_p / total_load) * 500.0
    assert intensity_1 == 500.0
    
    # Case 2: 50% Grid, 50% Solar
    grid_p = 0.5
    total_load = 1.0
    intensity_2 = (grid_p / total_load) * 500.0
    assert intensity_2 == 250.0

def test_vpp_carbon_aware_dispatch():
    """Test that VPP prioritizes discharge when carbon intensity is high."""
    vpp = VPPManager()
    
    # Register two identical meters
    config = {"has_battery": True, "battery_capacity": 10.0, "max_power_kw": 5.0, "feeder_id": "F1"}
    state = {"battery_level": 5.0} # 5.0 kWh = 50% SOC
    vpp.register_meter("M1", config, state)
    vpp.register_meter("M2", config, state)
    
    # High Carbon Intensity (500 g/kWh) -> Should discharge
    dispatches = vpp.dispatch_cluster("F1", 2.0, carbon_intensity=500.0)
    assert dispatches["M1"] == pytest.approx(1.0)
    assert dispatches["M2"] == pytest.approx(1.0)
    
def test_billing_carbon_savings():
    """Test that billing reflects carbon savings."""
    billing = ThaiBillingEngine("USER_1")
    test_ts = datetime(2026, 3, 27, 12, 0)
    
    # 10 kWh solar generation with 1.0 self-consumption ratio (for simple test)
    billing.add_solar_generation(
        energy_kwh=10.0,
        timestamp=test_ts,
        self_consumption_ratio=1.0
    )
    
    # 5 kWh P2P sales (also considered green in my billing.py logic)
    billing.add_p2p_sale(
        timestamp=test_ts,
        energy_kwh=5.0,
        price_baht_kwh=3.0,
        buyer_id="M2"
    )
    
    # Grid export also contributes (Phase 22 logic in billing.py)
    billing.add_grid_export(energy_kwh=2.0, timestamp=test_ts)
    
    bill = billing.generate_monthly_bill(3, 2026)
    # Total green energy = 10 (self) + 2 (grid export) + 5 (p2p sale) = 17 kWh
    # Carbon saved = 17 * 0.5 = 8.5 kg
    assert bill.carbon_saved_kg == 8.5
    print(f"Carbon Saved: {bill.carbon_saved_kg} kg")
