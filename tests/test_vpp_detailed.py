import pytest
from unittest.mock import MagicMock
from datetime import datetime
from smart_meter_simulator.core.vpp import VPPCluster, DERResource, VPPManager

@pytest.fixture
def sample_resources():
    r1 = DERResource(
        meter_id="M1", feeder_id="F1", max_charge_kw=10.0, max_discharge_kw=10.0,
        current_soc=5.0, capacity_kwh=10.0, is_controllable=True
    )
    r2 = DERResource(
        meter_id="M2", feeder_id="F1", max_charge_kw=5.0, max_discharge_kw=5.0,
        current_soc=4.0, capacity_kwh=5.0, is_controllable=True
    )
    return {"M1": r1, "M2": r2}

def test_cluster_properties(sample_resources):
    cluster = VPPCluster(cluster_id="F1", resources=sample_resources)
    assert cluster.total_capacity_kwh == 15.0
    assert cluster.current_stored_kwh == 9.0
    assert cluster.max_flexibility_up_kw == 15.0
    assert cluster.max_flexibility_down_kw == 15.0

def test_health_score_calculation(sample_resources):
    cluster = VPPCluster(cluster_id="F1", resources=sample_resources)
    score = cluster.calculate_health_score()
    assert 0 <= score <= 100
    
    # Test low reputation penalty
    sample_resources["M1"].reputation_score = 0.5
    score_low_rep = cluster.calculate_health_score()
    assert score_low_rep < score

def test_vpp_manager_registration():
    manager = VPPManager()
    manager.register_meter("M1", {"feeder_id": "F1", "has_battery": True, "battery_capacity": 10.0, "max_power_kw": 5.0}, {"battery_level": 5.0})
    assert "F1" in manager.clusters
    assert "M1" in manager.clusters["F1"].resources
    assert manager.meter_map["M1"] == "F1"

def test_anomaly_detection(caplog):
    manager = VPPManager()
    manager.register_meter("M1", {"feeder_id": "F1", "has_battery": True, "battery_capacity": 10.0, "max_power_kw": 5.0}, {"battery_level": 5.0})
    
    # First update
    manager.update_meter_state("M1", 5.0)
    assert len(manager.clusters["F1"].resources["M1"].history) == 1
    
    # Impossible jump: 5kW max power in 15min tick is 1.25kWh. Jump of 5kWh is impossible.
    with caplog.at_level("WARNING"):
        manager.update_meter_state("M1", 10.0) # 5 -> 10 = 5kWh delta
        assert any("VPP SECURITY ALERT" in record.message for record in caplog.records)
        assert manager.clusters["F1"].resources["M1"].reputation_score < 1.0

def test_afrr_response(sample_resources):
    manager = VPPManager()
    manager.clusters["F1"] = VPPCluster(cluster_id="F1", resources=sample_resources)
    
    # Under-frequency: 49.8Hz -> should inject (positive return)
    resp = manager.calculate_afrr_response("F1", 49.8)
    assert resp > 0
    
    # Over-frequency: 50.2Hz -> should absorb (negative return)
    resp = manager.calculate_afrr_response("F1", 50.2)
    assert resp < 0
    
    # Deadband
    assert manager.calculate_afrr_response("F1", 50.01) == 0.0

def test_dispatch_optimization(sample_resources):
    manager = VPPManager()
    manager.clusters["F1"] = VPPCluster(cluster_id="F1", resources=sample_resources)
    manager.meter_map = {"M1": "F1", "M2": "F1"}
    
    # Target 5kW discharge
    dispatches = manager.dispatch_cluster("F1", 5.0)
    assert sum(dispatches.values()) == pytest.approx(5.0)
    assert dispatches["M1"] > 0
    assert dispatches["M2"] > 0
    
    # Target 5kW charge
    dispatches = manager.dispatch_cluster("F1", -5.0)
    assert sum(dispatches.values()) == pytest.approx(-5.0)
    assert dispatches["M1"] < 0
    assert dispatches["M2"] < 0

def test_dispatch_with_nodal_prices(sample_resources):
    manager = VPPManager()
    manager.clusters["F1"] = VPPCluster(cluster_id="F1", resources=sample_resources)
    manager.meter_map = {"M1": "F1", "M2": "F1"}
    
    # Discharge: M1 has high price, M2 has low price
    # M1 should get more dispatch
    nodal_prices = {"M1": 0.50, "M2": 0.10}
    dispatches = manager.dispatch_cluster("F1", 5.0, nodal_prices=nodal_prices)
    assert dispatches["M1"] > dispatches["M2"]

def test_dispatch_with_carbon(sample_resources):
    manager = VPPManager()
    manager.clusters["F1"] = VPPCluster(cluster_id="F1", resources=sample_resources)
    manager.meter_map = {"M1": "F1", "M2": "F1"}
    
    # High carbon -> Prefer discharge (displace grid)
    # This is hard to compare without baseline, but we can verify it doesn't crash
    dispatches = manager.dispatch_cluster("F1", 5.0, carbon_intensity=500.0)
    assert sum(dispatches.values()) == pytest.approx(5.0)
