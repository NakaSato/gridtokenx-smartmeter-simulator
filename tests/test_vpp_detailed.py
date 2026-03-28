"""
Virtual Power Plant (VPP) Detailed Tests

Tests for VPP cluster management, dispatch optimization, and grid services.

Note: VPP functionality is currently stubbed. These tests are marked with
the 'vpp' marker and can be skipped with: uv run pytest -m 'not vpp'

Run with:
    uv run pytest tests/test_vpp_detailed.py -v
    uv run pytest tests/test_vpp_detailed.py -v -m 'not vpp'  # Skip VPP tests

Fixtures:
    - sample_vpp_resources: Sample DER resources (from conftest.py)
    - sample_vpp_cluster: Sample VPP cluster (from conftest.py)
"""

import pytest
from unittest.mock import MagicMock
from datetime import datetime

from smart_meter_simulator.core.vpp import VPPCluster, DERResource, VPPManager

# Mark all tests in this module as VPP tests (currently stubbed)
pytestmark = pytest.mark.vpp


@pytest.mark.vpp
class TestVPPClusterProperties:
    """Tests for VPPCluster aggregate properties."""

    def test_cluster_capacity(self, sample_vpp_resources):
        """Verify total capacity calculation."""
        cluster = VPPCluster(cluster_id="F1", resources=sample_vpp_resources)
        assert cluster.total_capacity_kwh == 15.0
        assert cluster.current_stored_kwh == 9.0

    def test_cluster_flexibility(self, sample_vpp_resources):
        """Verify flexibility up/down calculations."""
        cluster = VPPCluster(cluster_id="F1", resources=sample_vpp_resources)
        assert cluster.max_flexibility_up_kw == 15.0
        assert cluster.max_flexibility_down_kw == 15.0

    def test_cluster_soc_calculation(self, sample_vpp_resources):
        """Verify state of charge calculation."""
        cluster = VPPCluster(cluster_id="F1", resources=sample_vpp_resources)
        # SOC = current_stored / total_capacity = 9.0 / 15.0 = 0.6
        soc = cluster.current_stored_kwh / cluster.total_capacity_kwh
        assert abs(soc - 0.6) < 0.01


class TestVPPHealthScore:
    """Tests for VPP cluster health score calculation."""

    def test_health_score_basic(self, sample_vpp_resources):
        """Verify basic health score calculation."""
        cluster = VPPCluster(cluster_id="F1", resources=sample_vpp_resources)
        score = cluster.calculate_health_score()
        assert 0 <= score <= 100

    def test_health_score_low_reputation(self, sample_vpp_resources):
        """Verify health score penalty for low reputation."""
        cluster = VPPCluster(cluster_id="F1", resources=sample_vpp_resources)
        baseline_score = cluster.calculate_health_score()

        # Reduce reputation score
        sample_vpp_resources["M1"].reputation_score = 0.5
        low_rep_score = cluster.calculate_health_score()

        assert low_rep_score < baseline_score

    def test_health_score_low_soc(self, sample_vpp_resources):
        """Verify health score reflects low state of charge."""
        cluster = VPPCluster(cluster_id="F1", resources=sample_vpp_resources)
        baseline_score = cluster.calculate_health_score()

        # Reduce SOC
        sample_vpp_resources["M1"].current_soc = 1.0
        sample_vpp_resources["M2"].current_soc = 0.5
        low_soc_score = cluster.calculate_health_score()

        assert low_soc_score < baseline_score


class TestVPPManagerRegistration:
    """Tests for VPP manager meter registration."""

    def test_meter_registration(self):
        """Verify meter registration creates cluster."""
        manager = VPPManager()
        manager.register_meter(
            "M1",
            {
                "feeder_id": "F1",
                "has_battery": True,
                "battery_capacity": 10.0,
                "max_power_kw": 5.0,
            },
            {"battery_level": 5.0},
        )

        assert "F1" in manager.clusters
        assert "M1" in manager.clusters["F1"].resources
        assert manager.meter_map["M1"] == "F1"

    def test_meter_update(self):
        """Verify meter state update."""
        manager = VPPManager()
        manager.register_meter(
            "M1",
            {
                "feeder_id": "F1",
                "has_battery": True,
                "battery_capacity": 10.0,
                "max_power_kw": 5.0,
            },
            {"battery_level": 5.0},
        )

        # Update battery level
        manager.update_meter_state("M1", 7.5)

        resource = manager.clusters["F1"].resources["M1"]
        assert resource.current_soc == 7.5
        assert len(resource.history) >= 1


class TestVPPAnomalyDetection:
    """Tests for VPP anomaly detection and security."""

    def test_anomaly_detection_impossible_jump(self, caplog):
        """Verify detection of impossible battery state jumps."""
        manager = VPPManager()
        manager.register_meter(
            "M1",
            {
                "feeder_id": "F1",
                "has_battery": True,
                "battery_capacity": 10.0,
                "max_power_kw": 5.0,
            },
            {"battery_level": 5.0},
        )

        # First update
        manager.update_meter_state("M1", 5.0)
        assert len(manager.clusters["F1"].resources["M1"].history) == 1

        # Impossible jump: 5kW max power in 15min = 1.25kWh max change
        # Jump from 5.0 to 10.0 (5kWh) is impossible
        with caplog.at_level("WARNING"):
            manager.update_meter_state("M1", 10.0)
            assert any(
                "VPP SECURITY ALERT" in record.message
                for record in caplog.records
            )
            assert (
                manager.clusters["F1"].resources["M1"].reputation_score < 1.0
            )


class TestAFRRResponse:
    """Tests for automatic frequency restoration reserve (AFRR)."""

    def test_under_frequency_response(self, sample_vpp_resources):
        """Verify VPP responds to under-frequency by injecting power."""
        manager = VPPManager()
        manager.clusters["F1"] = VPPCluster(
            cluster_id="F1", resources=sample_vpp_resources
        )

        # Under-frequency: 49.8Hz -> should inject (positive)
        response = manager.calculate_afrr_response("F1", 49.8)
        assert response > 0

    def test_over_frequency_response(self, sample_vpp_resources):
        """Verify VPP responds to over-frequency by absorbing power."""
        manager = VPPManager()
        manager.clusters["F1"] = VPPCluster(
            cluster_id="F1", resources=sample_vpp_resources
        )

        # Over-frequency: 50.2Hz -> should absorb (negative)
        response = manager.calculate_afrr_response("F1", 50.2)
        assert response < 0

    def test_frequency_deadband(self, sample_vpp_resources):
        """Verify no response within frequency deadband."""
        manager = VPPManager()
        manager.clusters["F1"] = VPPCluster(
            cluster_id="F1", resources=sample_vpp_resources
        )

        # Within deadband (50.0 ± 0.02Hz)
        response = manager.calculate_afrr_response("F1", 50.01)
        assert response == 0.0


class TestDispatchOptimization:
    """Tests for VPP dispatch optimization."""

    def test_discharge_dispatch(self, sample_vpp_resources):
        """Verify discharge dispatch distributes across resources."""
        manager = VPPManager()
        manager.clusters["F1"] = VPPCluster(
            cluster_id="F1", resources=sample_vpp_resources
        )
        manager.meter_map = {"M1": "F1", "M2": "F1"}

        # Target 5kW discharge
        dispatches = manager.dispatch_cluster("F1", 5.0)
        assert sum(dispatches.values()) == pytest.approx(5.0)
        assert dispatches["M1"] > 0
        assert dispatches["M2"] > 0

    def test_charge_dispatch(self, sample_vpp_resources):
        """Verify charge dispatch distributes across resources."""
        manager = VPPManager()
        manager.clusters["F1"] = VPPCluster(
            cluster_id="F1", resources=sample_vpp_resources
        )
        manager.meter_map = {"M1": "F1", "M2": "F1"}

        # Target 5kW charge
        dispatches = manager.dispatch_cluster("F1", -5.0)
        assert sum(dispatches.values()) == pytest.approx(-5.0)
        assert dispatches["M1"] < 0
        assert dispatches["M2"] < 0

    def test_dispatch_with_nodal_prices(self, sample_vpp_resources):
        """Verify dispatch prioritizes high-price nodes for discharge."""
        manager = VPPManager()
        manager.clusters["F1"] = VPPCluster(
            cluster_id="F1", resources=sample_vpp_resources
        )
        manager.meter_map = {"M1": "F1", "M2": "F1"}

        # Discharge: M1 has high price, M2 has low price
        nodal_prices = {"M1": 0.50, "M2": 0.10}
        dispatches = manager.dispatch_cluster(
            "F1", 5.0, nodal_prices=nodal_prices
        )
        assert dispatches["M1"] > dispatches["M2"]

    def test_dispatch_with_carbon_intensity(self, sample_vpp_resources):
        """Verify dispatch considers carbon intensity."""
        manager = VPPManager()
        manager.clusters["F1"] = VPPCluster(
            cluster_id="F1", resources=sample_vpp_resources
        )
        manager.meter_map = {"M1": "F1", "M2": "F1"}

        # High carbon intensity should encourage discharge
        dispatches = manager.dispatch_cluster(
            "F1", 5.0, carbon_intensity=500.0
        )
        assert sum(dispatches.values()) == pytest.approx(5.0)


class TestVPPIntegration:
    """Integration tests for VPP system."""

    def test_full_dispatch_cycle(self, sample_vpp_resources):
        """Test complete dispatch cycle with updates."""
        manager = VPPManager()
        manager.clusters["F1"] = VPPCluster(
            cluster_id="F1", resources=sample_vpp_resources
        )
        manager.meter_map = {"M1": "F1", "M2": "F1"}

        # Initial state
        initial_soc = (
            manager.clusters["F1"].current_stored_kwh
            / manager.clusters["F1"].total_capacity_kwh
        )
        assert initial_soc > 0

        # Discharge cycle
        dispatches = manager.dispatch_cluster("F1", 5.0)
        assert sum(dispatches.values()) == 5.0

        # Update states
        for meter_id, dispatch in dispatches.items():
            old_soc = manager.clusters["F1"].resources[meter_id].current_soc
            # Simplified: assume 15-min interval
            new_soc = old_soc - (dispatch * 0.25)
            manager.update_meter_state(meter_id, max(0, new_soc))

        # SOC should decrease after discharge
        final_soc = (
            manager.clusters["F1"].current_stored_kwh
            / manager.clusters["F1"].total_capacity_kwh
        )
        assert final_soc < initial_soc

    def test_multi_cluster_management(self):
        """Test VPP managing multiple clusters."""
        manager = VPPManager()

        # Register meters to different feeders
        manager.register_meter(
            "M1",
            {
                "feeder_id": "F1",
                "has_battery": True,
                "battery_capacity": 10.0,
                "max_power_kw": 5.0,
            },
            {"battery_level": 5.0},
        )
        manager.register_meter(
            "M2",
            {
                "feeder_id": "F2",
                "has_battery": True,
                "battery_capacity": 8.0,
                "max_power_kw": 4.0,
            },
            {"battery_level": 4.0},
        )

        assert len(manager.clusters) == 2
        assert "F1" in manager.clusters
        assert "F2" in manager.clusters
        assert manager.meter_map["M1"] == "F1"
        assert manager.meter_map["M2"] == "F2"
