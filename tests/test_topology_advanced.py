"""
Grid Topology and State Estimation Tests

Tests for:
- TopologyBuilder (radial, feeder networks)
- StateEstimator (WLS, Iwamoto, bad data detection)
- Sanitized estimation with bad data removal

Run with:
    uv run pytest tests/test_topology_advanced.py -v

Fixtures:
    - simple_radial_net: 2-bus radial network (from conftest.py)
    - three_bus_net: 3-bus radial network (from conftest.py)
    - measured_three_bus_net: 3-bus network with measurements (from conftest.py)
"""

import pytest
import pandapower as pp
from unittest.mock import MagicMock, patch

from smart_meter_simulator.adapters.topology_builder import TopologyBuilder
from smart_meter_simulator.adapters.state_estimator import StateEstimator


class TestTopologyBuilderRadial:
    """Tests for radial network topology construction."""

    def test_build_radial_network(self):
        """Verify radial network construction."""
        builder = TopologyBuilder(network_name="Test Radial")
        net = builder.build_radial_network(num_buses=5)

        assert len(net.bus) == 5
        assert len(net.line) == 4  # n-1 lines for radial
        assert len(net.ext_grid) == 1

    def test_build_radial_network_with_loads(self):
        """Verify radial network with load distribution."""
        builder = TopologyBuilder(network_name="Test Radial Loads")
        net = builder.build_radial_network(num_buses=5)
        
        # Add loads manually
        import pandapower as pp
        for i in range(len(net.bus)):
            pp.create_load(net, bus=i, p_mw=0.05, q_mvar=0.01, name=f"load_{i}")

        assert len(net.bus) == 5
        assert len(net.load) == 5

    def test_radial_network_power_flow(self):
        """Verify radial network converges with power flow."""
        builder = TopologyBuilder(network_name="Test Radial PF")
        net = builder.build_radial_network(num_buses=5)

        # Run power flow
        pp.runpp(net)

        # Check results exist
        assert net.res_bus is not None
        assert len(net.res_bus) == 5
        assert all(net.res_bus.vm_pu.notna())


class TestTopologyBuilderFeeder:
    """Tests for feeder network topology construction."""

    def test_build_feeder_network(self):
        """Verify feeder network construction."""
        builder = TopologyBuilder(network_name="Test Feeder")
        net = builder.build_feeder_network(
            num_feeders=2, buses_per_feeder=3
        )

        # 1 substation + 2 feeders * 3 buses = 7 total
        assert len(net.bus) == 7
        assert len(net.ext_grid) == 1

    def test_build_feeder_network_structure(self):
        """Verify feeder network has correct structure."""
        builder = TopologyBuilder(network_name="Test Feeder Structure")
        net = builder.build_feeder_network(
            num_feeders=2, buses_per_feeder=3
        )

        # Check main lines from substation
        main_lines = net.line[net.line.from_bus == 0]
        assert len(main_lines) == 2  # One per feeder

    def test_feeder_network_power_flow(self):
        """Verify feeder network converges with power flow."""
        builder = TopologyBuilder(network_name="Test Feeder PF")
        net = builder.build_feeder_network(
            num_feeders=2, buses_per_feeder=3
        )

        # Run power flow
        pp.runpp(net)

        # Check results exist
        assert net.res_bus is not None
        assert all(net.res_bus.vm_pu.notna())


class TestStateEstimatorSuccess:
    """Tests for successful state estimation."""

    def test_wls_estimation_convergence(self, measured_three_bus_net):
        """Verify WLS estimation converges with good measurements."""
        estimator = StateEstimator()
        results = estimator.run_estimation(measured_three_bus_net)

        assert results.converged is True
        assert results.iterations > 0

    def test_estimation_state_vector(self, measured_three_bus_net):
        """Verify state vector has correct dimensions."""
        estimator = StateEstimator()
        results = estimator.run_estimation(measured_three_bus_net)

        # State vector is a DataFrame with vm_pu and va_degree columns
        # Should have one row per bus
        n_buses = len(measured_three_bus_net.bus)
        assert results.state_vector is not None
        assert len(results.state_vector) == n_buses  # 3 buses
        assert 'vm_pu' in results.state_vector.columns
        assert 'va_degree' in results.state_vector.columns

    def test_estimation_residuals(self, measured_three_bus_net):
        """Verify residuals are computed."""
        estimator = StateEstimator()
        results = estimator.run_estimation(measured_three_bus_net)

        assert results.residuals is not None
        assert len(results.residuals) > 0


class TestBadDataDetection:
    """Tests for bad data detection algorithms."""

    def test_chi_squared_test(self, three_bus_net):
        """Verify Chi-squared test for bad data detection."""
        net = three_bus_net

        # Add measurements with one bad data
        for i in range(len(net.bus)):
            pp.create_measurement(
                net,
                "v",
                "bus",
                value=net.res_bus.vm_pu.iloc[i],
                std_dev=0.001,
                element=i,
                name=f"v{i}",
            )

        # Add bad voltage measurement (extreme outlier)
        pp.create_measurement(
            net, "v", "bus", value=2.0, std_dev=0.001, element=2, name="v_bad"
        )

        estimator = StateEstimator()
        bad_data = estimator.detect_bad_data(net)

        assert "v_bad" in bad_data

    def test_normalized_residuals_test(self, measured_three_bus_net):
        """Verify normalized residuals identify bad data."""
        net = measured_three_bus_net

        # Add bad data
        pp.create_measurement(
            net,
            "p",
            "line",
            value=10.0,  # Extreme value
            std_dev=0.01,
            element=0,
            side="from",
            name="p_bad",
        )

        estimator = StateEstimator()

        # Run estimation first
        estimator.run_estimation(net)

        # Detect bad data
        bad_data = estimator.detect_bad_data(net)
        assert "p_bad" in bad_data

    def test_bad_data_removal(self, three_bus_net):
        """Verify bad data removal from measurement table."""
        import pandapower as pp
        net = three_bus_net

        # Add good voltage measurements at all buses
        for i in range(len(net.bus)):
            pp.create_measurement(
                net,
                "v",
                "bus",
                value=net.res_bus.vm_pu.iloc[i],
                std_dev=0.001,
                element=i,
                name=f"v{i}",
            )

        # Add power flow measurements for redundancy (needed for observability)
        for i in range(len(net.line)):
            pp.create_measurement(
                net,
                "p",
                "line",
                value=net.res_line.p_from_mw.iloc[i],
                std_dev=0.01,
                element=i,
                side="from",
                name=f"p_line{i}",
            )
            pp.create_measurement(
                net,
                "q",
                "line",
                value=net.res_line.q_from_mvar.iloc[i],
                std_dev=0.01,
                element=i,
                side="from",
                name=f"q_line{i}",
            )

        # Add bad data (extreme voltage at bus 2)
        pp.create_measurement(
            net, "v", "bus", value=10.0, std_dev=0.001, element=2, name="v_bad"
        )

        estimator = StateEstimator()
        results = estimator.run_sanitized_estimation(net)

        # Should converge after removing bad data
        assert results.converged is True
        assert "v_bad" in results.bad_data_detected
        assert "v_bad" not in net.measurement.name.values


class TestSanitizedEstimation:
    """Tests for sanitized state estimation with bad data removal."""

    def test_sanitized_estimation_convergence(self, three_bus_net):
        """Verify sanitized estimation converges after removing bad data."""
        net = three_bus_net

        # Add measurements
        for i in range(len(net.bus)):
            pp.create_measurement(
                net,
                "v",
                "bus",
                value=net.res_bus.vm_pu.iloc[i],
                std_dev=0.001,
                element=i,
                name=f"v{i}",
            )

        # Add line measurements
        for i in range(len(net.line)):
            pp.create_measurement(
                net,
                "p",
                "line",
                value=net.res_line.p_from_mw.iloc[i],
                std_dev=0.01,
                element=i,
                side="from",
                name=f"p_line_f{i}",
            )
            pp.create_measurement(
                net,
                "q",
                "line",
                value=net.res_line.q_from_mvar.iloc[i],
                std_dev=0.01,
                element=i,
                side="from",
                name=f"q_line_f{i}",
            )

        # Add multiple bad data points
        pp.create_measurement(
            net, "v", "bus", value=10.0, std_dev=0.001, element=2, name="v_bad1"
        )
        pp.create_measurement(
            net,
            "p",
            "line",
            value=100.0,
            std_dev=0.01,
            element=0,
            side="from",
            name="p_bad",
        )

        estimator = StateEstimator()
        results = estimator.run_sanitized_estimation(net)

        assert results.converged is True
        assert len(results.bad_data_detected) >= 1

    def test_sanitized_estimation_accuracy(self, three_bus_net):
        """Verify sanitized estimation produces accurate results."""
        import pandapower as pp
        net = three_bus_net

        # Add accurate voltage measurements at all buses
        for i in range(len(net.bus)):
            pp.create_measurement(
                net,
                "v",
                "bus",
                value=net.res_bus.vm_pu.iloc[i],
                std_dev=0.001,
                element=i,
                name=f"v{i}",
            )

        # Add power flow measurements for redundancy (needed for observability)
        for i in range(len(net.line)):
            pp.create_measurement(
                net,
                "p",
                "line",
                value=net.res_line.p_from_mw.iloc[i],
                std_dev=0.01,
                element=i,
                side="from",
                name=f"p_line{i}",
            )
            pp.create_measurement(
                net,
                "q",
                "line",
                value=net.res_line.q_from_mvar.iloc[i],
                std_dev=0.01,
                element=i,
                side="from",
                name=f"q_line{i}",
            )

        # Add one bad measurement
        pp.create_measurement(
            net, "v", "bus", value=2.0, std_dev=0.001, element=1, name="v_bad"
        )

        estimator = StateEstimator()
        results = estimator.run_sanitized_estimation(net)

        # Should converge after removing bad data
        assert results.converged is True
        assert results.state_vector is not None
        
        # Estimated voltages should be close to true values (excluding bad data)
        for i in range(len(net.bus)):
            estimated_v = results.state_vector['vm_pu'].iloc[i]
            true_v = net.res_bus.vm_pu.iloc[i]
            # Allow 5% tolerance
            assert abs(estimated_v - true_v) < 0.05


class TestMeasurementRedundancy:
    """Tests for measurement redundancy and observability."""

    def test_observability_check(self, three_bus_net):
        """Verify observability check passes with sufficient measurements."""
        net = three_bus_net

        # Add voltage measurements at all buses
        for i in range(len(net.bus)):
            pp.create_measurement(
                net,
                "v",
                "bus",
                value=net.res_bus.vm_pu.iloc[i],
                std_dev=0.001,
                element=i,
                name=f"v{i}",
            )

        # Add injection measurements
        for i in range(len(net.bus)):
            pp.create_measurement(
                net,
                "p",
                "bus",
                value=0.05,
                std_dev=0.01,
                element=i,
                name=f"p_inj{i}",
            )

        estimator = StateEstimator()
        is_observable = estimator.check_observability(net)

        assert is_observable is True

    def test_unobservable_network(self, three_bus_net):
        """Verify unobservable network detection."""
        net = three_bus_net

        # Add only one measurement (insufficient)
        pp.create_measurement(
            net,
            "v",
            "bus",
            value=1.0,
            std_dev=0.001,
            element=0,
            name="v_single",
        )

        estimator = StateEstimator()
        is_observable = estimator.check_observability(net)

        # Network should be unobservable with single measurement
        assert is_observable is False


class TestIntegration:
    """Integration tests for topology and estimation."""

    def test_full_estimation_workflow(self, three_bus_net):
        """Test complete estimation workflow from setup to results."""
        import pandapower as pp
        net = three_bus_net

        # Step 1: Add measurements (need m > 2n for chi-squared test)
        # For 3 buses: 6 state variables, need at least 7 measurements
        for i in range(len(net.bus)):
            pp.create_measurement(
                net,
                "v",
                "bus",
                value=net.res_bus.vm_pu.iloc[i],
                std_dev=0.001,
                element=i,
                name=f"v{i}",
            )

        # Add power flow measurements on all lines (both from and to for redundancy)
        for i in range(len(net.line)):
            pp.create_measurement(
                net,
                "p",
                "line",
                value=net.res_line.p_from_mw.iloc[i],
                std_dev=0.01,
                element=i,
                side="from",
                name=f"p_line{i}_from",
            )
            pp.create_measurement(
                net,
                "p",
                "line",
                value=net.res_line.p_to_mw.iloc[i],
                std_dev=0.01,
                element=i,
                side="to",
                name=f"p_line{i}_to",
            )
            pp.create_measurement(
                net,
                "q",
                "line",
                value=net.res_line.q_from_mvar.iloc[i],
                std_dev=0.01,
                element=i,
                side="from",
                name=f"q_line{i}_from",
            )

        # Step 2: Run estimation
        estimator = StateEstimator()
        results = estimator.run_estimation(net)

        # Step 3: Verify convergence
        assert results.converged is True

        # Step 4: Check results quality
        assert results.chi_squared_test is not None

    def test_topology_with_distributed_generation(self):
        """Test estimation with distributed generation."""
        import pandapower as pp
        builder = TopologyBuilder(network_name="Test DG")
        net = builder.build_radial_network(num_buses=5)

        # Add load and solar generation
        pp.create_load(net, bus=2, p_mw=0.05, q_mvar=0.01)
        pp.create_sgen(net, bus=3, p_mw=0.08, q_mvar=0.0)

        # Run power flow
        pp.runpp(net)

        # Add measurements (need m > 2n-1 = 9 for 5 buses)
        for i in range(len(net.bus)):
            pp.create_measurement(
                net,
                "v",
                "bus",
                value=net.res_bus.vm_pu.iloc[i],
                std_dev=0.001,
                element=i,
                name=f"v{i}",
            )

        # Add power flow measurements for redundancy
        for i in range(len(net.line)):
            pp.create_measurement(
                net,
                "p",
                "line",
                value=net.res_line.p_from_mw.iloc[i],
                std_dev=0.01,
                element=i,
                side="from",
                name=f"p_line{i}",
            )
            pp.create_measurement(
                net,
                "q",
                "line",
                value=net.res_line.q_from_mvar.iloc[i],
                std_dev=0.01,
                element=i,
                side="from",
                name=f"q_line{i}",
            )

        # Run estimation
        estimator = StateEstimator()
        results = estimator.run_estimation(net)

        assert results.converged is True
        assert results.state_vector is not None
