import pytest
import pandapower as pp
from unittest.mock import MagicMock, patch
from smart_meter_simulator.adapters.topology_builder import TopologyBuilder
from smart_meter_simulator.adapters.state_estimator import StateEstimator

@pytest.fixture
def base_net():
    net = pp.create_empty_network()
    # Create a simple radial grid: Bus 0 -> Line -> Bus 1
    b0 = pp.create_bus(net, vn_kv=11.0, name="Substation")
    b1 = pp.create_bus(net, vn_kv=11.0, name="Feeder 1")
    pp.create_ext_grid(net, bus=b0)
    pp.create_line_from_parameters(net, from_bus=b0, to_bus=b1, length_km=1.0, r_ohm_per_km=0.1, x_ohm_per_km=0.1, c_nf_per_km=0.0, max_i_ka=1.0)
    pp.create_load(net, bus=b1, p_mw=0.1, q_mvar=0.02)
    return net

def test_topology_builder_radial():
    builder = TopologyBuilder(network_name="Test Radial")
    net = builder.build_radial_network(num_buses=5)
    
    assert len(net.bus) == 5
    assert len(net.line) == 4
    assert len(net.ext_grid) == 1

def test_topology_builder_feeder():
    builder = TopologyBuilder(network_name="Test Feeder")
    net = builder.build_feeder_network(num_feeders=2, buses_per_feeder=3)
    
    # 1 substation + 2 feeders * 3 buses = 7 total
    assert len(net.bus) == 7
    assert len(net.line) == 2 + 2 * 2 # 2 main + 4 internal = 6
    assert len(net.ext_grid) == 1

def test_state_estimator_success():
    builder = TopologyBuilder(network_name="Estimator Test")
    net = builder.build_radial_network(num_buses=3)
    pp.create_load(net, bus=1, p_mw=0.05, q_mvar=0.01)
    pp.create_load(net, bus=2, p_mw=0.05, q_mvar=0.01)
    
    pp.runpp(net)
    
    # Add measurements
    for i in range(len(net.bus)):
        pp.create_measurement(net, "v", "bus", value=net.res_bus.vm_pu.iloc[i], std_dev=0.001, element=i, name=f"v{i}")
    
    # Add line flow measurements (more robust for observability)
    for i in range(len(net.line)):
        pp.create_measurement(net, "p", "line", value=net.res_line.p_from_mw.iloc[i], std_dev=0.01, element=i, side="from", name=f"p_line{i}")
        pp.create_measurement(net, "q", "line", value=net.res_line.q_from_mvar.iloc[i], std_dev=0.01, element=i, side="from", name=f"q_line{i}")

    estimator = StateEstimator()
    results = estimator.run_estimation(net)
    assert results.converged

def test_state_estimator_bad_data():
    builder = TopologyBuilder(network_name="Bad Data Test")
    # Same setup as success
    net = builder.build_radial_network(num_buses=3)
    pp.create_load(net, bus=1, p_mw=0.05, q_mvar=0.01)
    pp.runpp(net)
    
    for i in range(len(net.bus)):
        pp.create_measurement(net, "v", "bus", value=net.res_bus.vm_pu.iloc[i], std_dev=0.001, element=i, name=f"v{i}")
    for i in range(len(net.line)):
        pp.create_measurement(net, "p", "line", value=net.res_line.p_from_mw.iloc[i], std_dev=0.01, element=i, side="from", name=f"p_line{i}")
    
    # Inject bad data
    pp.create_measurement(net, "v", "bus", value=2.0, std_dev=0.001, element=2, name="v_bad")
    
    estimator = StateEstimator()
    bad_data = estimator.detect_bad_data(net)
    assert "v_bad" in bad_data

def test_state_estimator_sanitization():
    builder = TopologyBuilder(network_name="Sanitization Test")
    net = builder.build_radial_network(num_buses=3)
    pp.create_load(net, bus=1, p_mw=0.05, q_mvar=0.01)
    pp.create_load(net, bus=2, p_mw=0.05, q_mvar=0.01)
    pp.runpp(net)
    
    # Add MANY redundant measurements
    for i in range(len(net.bus)):
        pp.create_measurement(net, "v", "bus", value=net.res_bus.vm_pu.iloc[i], std_dev=0.001, element=i, name=f"v{i}")
    
    for i in range(len(net.line)):
        # Both ends of the line
        pp.create_measurement(net, "p", "line", value=net.res_line.p_from_mw.iloc[i], std_dev=0.01, element=i, side="from", name=f"p_line_f{i}")
        pp.create_measurement(net, "q", "line", value=net.res_line.q_from_mvar.iloc[i], std_dev=0.01, element=i, side="from", name=f"q_line_f{i}")
        pp.create_measurement(net, "p", "line", value=net.res_line.p_to_mw.iloc[i], std_dev=0.01, element=i, side="to", name=f"p_line_t{i}")
        pp.create_measurement(net, "q", "line", value=net.res_line.q_to_mvar.iloc[i], std_dev=0.01, element=i, side="to", name=f"q_line_t{i}")

    # Add bad data (Extreme outlier)
    pp.create_measurement(net, "v", "bus", value=10.0, std_dev=0.001, element=2, name="v_bad")
    
    estimator = StateEstimator()
    results = estimator.run_sanitized_estimation(net)
    assert results.converged
    assert "v_bad" in results.bad_data_detected
    assert "v_bad" not in net.measurement.name.values
