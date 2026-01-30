import pytest
import pandapower as pp
import numpy as np
import pandas as pd
from app.adapters.state_estimator import StateEstimator, EstimationAlgorithm
from app.adapters.topology_builder import TopologyBuilder
from app.core.meter import SmartMeter
from app.config import MeterType

def test_state_estimator_accuracy_metrics():
    """Test StateEstimator accuracy metrics with a valid converged case."""
    net = pp.create_empty_network()
    b1 = pp.create_bus(net, vn_kv=0.4)
    b2 = pp.create_bus(net, vn_kv=0.4)
    pp.create_ext_grid(net, bus=b1)
    pp.create_line_from_parameters(net, from_bus=b1, to_bus=b2, length_km=0.1, r_ohm_per_km=0.1, x_ohm_per_km=0.1, c_nf_per_km=100, max_i_ka=1.0)
    pp.create_load(net, bus=b2, p_mw=0.01, q_mvar=0.003)
    
    # Add enough measurements for observability (Nodal P, Q at bus 1 and 2, and V at 1 and 2)
    pp.create_measurement(net, "v", "bus", 1.0, 0.01, b1)
    pp.create_measurement(net, "v", "bus", 1.0, 0.01, b2)
    pp.create_measurement(net, "p", "bus", 0.0, 0.001, b1)
    pp.create_measurement(net, "q", "bus", 0.0, 0.001, b1)
    pp.create_measurement(net, "p", "bus", -0.01, 0.001, b2) # Load is negative injection
    pp.create_measurement(net, "q", "bus", -0.003, 0.001, b2)
    
    estimator = StateEstimator(algorithm=EstimationAlgorithm.WLS)
    results = estimator.run_estimation(net)
    
    assert results.converged is True
    
    # Test accuracy metrics method
    metrics = estimator.validate_ansi_c12_20(net, tolerance_percent=5.0)
    assert len(metrics) > 0

def test_topology_builder_radial_feeder():
    """Test TopologyBuilder with radial feeder configuration."""
    builder = TopologyBuilder()
    net = builder.build_radial_network(num_buses=5)
    
    # build_radial_network(num_buses=5) creates 5 buses.
    assert len(net.bus) == 5 
    assert len(net.line) == 4

def test_state_estimator_large_network():
    """Test StateEstimator with a larger network to hit more branches."""
    builder = TopologyBuilder()
    # Create 2 feeders with 2 buses each = 4 buses + 1 substation = 5 buses
    net = builder.build_feeder_network(num_feeders=2, buses_per_feeder=2)
    
    # Add measurements for all buses for observability
    for i in net.bus.index:
        pp.create_measurement(net, "v", "bus", 1.0, 0.01, int(i))
        pp.create_measurement(net, "p", "bus", 0.0, 0.001, int(i))
        pp.create_measurement(net, "q", "bus", 0.0, 0.001, int(i))
        
    estimator = StateEstimator()
    results = estimator.run_estimation(net)
    assert results.converged is True
    assert results.num_measurements > 0
