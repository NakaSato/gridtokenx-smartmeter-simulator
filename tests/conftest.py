"""
Pytest Configuration and Shared Fixtures

This module provides shared fixtures and configuration for the test suite.
Fixtures are organized by category:
- API/HTTP client fixtures
- Mock engine/fixtures
- Pandapower network fixtures
- VPP/market fixtures
"""

import pandas as pd
import pandapower as pp
import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from smart_meter_simulator.config import SimulatorConfig
from smart_meter_simulator.core.meter import SmartMeter
from smart_meter_simulator.core.vpp import VPPCluster, DERResource


# ============================================================================
# Pytest Marker Registration
# ============================================================================

def pytest_configure(config):
    """Register custom markers to avoid warnings with --strict-markers."""
    config.addinivalue_line(
        "markers",
        "unit: Unit tests (fast, isolated)",
    )
    config.addinivalue_line(
        "markers",
        "integration: Integration tests (multiple components, require server)",
    )
    config.addinivalue_line(
        "markers",
        "slow: Slow running tests (>1 second)",
    )
    config.addinivalue_line(
        "markers",
        "phase1: Phase 1 tests (AMI Foundation)",
    )
    config.addinivalue_line(
        "markers",
        "phase2: Phase 2 tests (Grid Integration)",
    )
    config.addinivalue_line(
        "markers",
        "phase3: Phase 3 tests (State Estimation)",
    )
    config.addinivalue_line(
        "markers",
        "phase4: Phase 4 tests (Data Management)",
    )
    config.addinivalue_line(
        "markers",
        "phase5: Phase 5 tests (Co-Simulation)",
    )
    config.addinivalue_line(
        "markers",
        "vpp: VPP-related tests (currently stubbed, skip with -m 'not vpp')",
    )
    config.addinivalue_line(
        "markers",
        "market: Market-related tests",
    )
    config.addinivalue_line(
        "markers",
        "grid: Grid topology tests",
    )
    config.addinivalue_line(
        "markers",
        "crypto: Cryptography tests",
    )
    config.addinivalue_line(
        "markers",
        "api: API endpoint tests",
    )
    config.addinivalue_line(
        "markers",
        "e2e: End-to-end tests",
    )


# ============================================================================
# API Client Fixtures
# ============================================================================

@pytest.fixture
def mock_config():
    """Create a mock configuration to avoid real connections during tests."""
    config = MagicMock(spec=SimulatorConfig)
    config.database_url = "postgresql://user:pass@localhost/db"
    config.api_gateway_url = "http://localhost:8080"
    config.api_key = "test_key"
    config.kafka_servers = None
    config.influxdb_token = None
    config.num_meters = 1
    config.autostart_simulation = False
    config.c2c_api_key = "gridtokenx_c2c_live_feed"
    return config


@pytest.fixture
def client(mock_config):
    """
    Create a TestClient with mocked dependencies.
    
    Provides:
    - Mocked engine with basic meter setup
    - Mocked market with tariff manager
    - Mocked grid topology
    
    Yields:
        tuple: (TestClient, mock_engine)
    """
    from fastapi.testclient import TestClient
    from smart_meter_simulator.app import app
    from smart_meter_simulator.core import app_state

    with patch('smart_meter_simulator.app.get_config', return_value=mock_config):
        with patch('smart_meter_simulator.core.app_state.engine') as mock_engine:
            # Setup mock engine
            mock_engine.meters = [
                MagicMock(
                    meter_id="M1",
                    config={
                        "meter_type": "solar_prosumer",
                        "location": "Zone_1",
                        "phase": "A",
                        "has_battery": True,
                        "battery_capacity": 10.0,
                    },
                    battery_level=5.0,
                )
            ]
            mock_engine.meter_to_bus = {"M1": 0}
            mock_engine.current_sim_time = datetime.now(timezone.utc)
            mock_engine.running = True
            mock_engine.paused = False
            mock_engine.last_estimation_results = None

            # Setup mock market
            mock_engine.market = MagicMock()
            mock_engine.market.current_mcp = 0.25
            mock_engine.market.history = []
            mock_engine.market.tariff_manager.get_current_tariff.return_value = MagicMock(
                import_rate=0.28,
                export_rate=0.15,
            )

            # Setup mock VPP
            mock_engine.vpp = MagicMock()
            mock_engine.vpp.get_all_cluster_statuses.return_value = []

            # Setup mock grid topology
            net = _create_mock_pandapower_net()
            mock_engine.net = net

            # Patch dependencies
            with patch(
                'smart_meter_simulator.routers.dependencies.app_state',
                MagicMock(engine=mock_engine),
            ):
                with patch(
                    'smart_meter_simulator.app.mapbox_matcher',
                    create=True,
                ) as mock_matcher:
                    mock_matcher.match_route.return_value = (
                        [[100.6, 13.7], [100.7, 13.8]],
                        15000.0,
                    )
                    with TestClient(app) as test_client:
                        yield test_client, mock_engine


# ============================================================================
# Pandapower Network Fixtures
# ============================================================================

@pytest.fixture
def simple_radial_net():
    """
    Create a simple radial network for testing.
    
    Network topology:
        Bus 0 (Substation) -- Line --> Bus 1 (Load)
    
    Returns:
        pandapowerNet: Simple 2-bus radial network
    """
    net = pp.create_empty_network()
    b0 = pp.create_bus(net, vn_kv=11.0, name="Substation")
    b1 = pp.create_bus(net, vn_kv=11.0, name="Feeder 1")
    pp.create_ext_grid(net, bus=b0)
    pp.create_line_from_parameters(
        net,
        from_bus=b0,
        to_bus=b1,
        length_km=1.0,
        r_ohm_per_km=0.1,
        x_ohm_per_km=0.1,
        c_nf_per_km=0.0,
        max_i_ka=1.0,
    )
    pp.create_load(net, bus=b1, p_mw=0.1, q_mvar=0.02)
    return net


@pytest.fixture
def three_bus_net():
    """
    Create a 3-bus radial network for state estimation testing.
    
    Network topology:
        Bus 0 (Substation) -- Line --> Bus 1 (Load) -- Line --> Bus 2 (Load)
    
    Returns:
        pandapowerNet: 3-bus radial network with measurements
    """
    net = pp.create_empty_network()
    b0 = pp.create_bus(net, vn_kv=11.0, name="Substation")
    b1 = pp.create_bus(net, vn_kv=11.0, name="Feeder 1")
    b2 = pp.create_bus(net, vn_kv=11.0, name="Feeder 2")

    pp.create_ext_grid(net, bus=b0)

    # Lines
    pp.create_line_from_parameters(
        net,
        from_bus=b0,
        to_bus=b1,
        length_km=1.0,
        r_ohm_per_km=0.1,
        x_ohm_per_km=0.1,
        c_nf_per_km=0.0,
        max_i_ka=1.0,
        name="Line 0-1",
    )
    pp.create_line_from_parameters(
        net,
        from_bus=b1,
        to_bus=b2,
        length_km=1.5,
        r_ohm_per_km=0.1,
        x_ohm_per_km=0.1,
        c_nf_per_km=0.0,
        max_i_ka=1.0,
        name="Line 1-2",
    )

    # Loads
    pp.create_load(net, bus=b1, p_mw=0.05, q_mvar=0.01, name="Load 1")
    pp.create_load(net, bus=b2, p_mw=0.05, q_mvar=0.01, name="Load 2")

    # Run power flow
    pp.runpp(net)

    return net


@pytest.fixture
def measured_three_bus_net(three_bus_net):
    """
    Create a 3-bus network with measurements for state estimation.
    
    Adds voltage and power flow measurements to the 3-bus network.
    
    Returns:
        pandapowerNet: 3-bus network with measurements
    """
    net = three_bus_net

    # Add voltage measurements
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

    # Add line flow measurements
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

    return net


# ============================================================================
# VPP Fixtures
# ============================================================================

@pytest.fixture
def sample_vpp_resources():
    """
    Create sample VPP resources for testing.
    
    Returns:
        dict: Dictionary of DERResource objects
    """
    r1 = DERResource(
        meter_id="M1",
        feeder_id="F1",
        max_charge_kw=10.0,
        max_discharge_kw=10.0,
        current_soc=5.0,
        capacity_kwh=10.0,
        is_controllable=True,
    )
    r2 = DERResource(
        meter_id="M2",
        feeder_id="F1",
        max_charge_kw=5.0,
        max_discharge_kw=5.0,
        current_soc=4.0,
        capacity_kwh=5.0,
        is_controllable=True,
    )
    return {"M1": r1, "M2": r2}


@pytest.fixture
def sample_vpp_cluster(sample_vpp_resources):
    """
    Create a sample VPP cluster.
    
    Returns:
        VPPCluster: VPP cluster with sample resources
    """
    return VPPCluster(cluster_id="F1", resources=sample_vpp_resources)


# ============================================================================
# Mock Transport Fixtures
# ============================================================================

@pytest.fixture
def mock_transport():
    """
    Create a mock transport layer for testing.
    
    Returns:
        MagicMock: Mocked transport with async methods
    """
    transport = MagicMock()
    transport.connect = AsyncMock()
    transport.disconnect = AsyncMock()
    transport.send_readings = AsyncMock()
    transport.send_batch = AsyncMock()
    transport.send_auction_bid = AsyncMock()
    transport.send_alert = AsyncMock()
    return transport


# ============================================================================
# Smart Meter Fixtures
# ============================================================================

@pytest.fixture
def sample_meter_config():
    """
    Create a sample smart meter configuration.
    
    Returns:
        dict: Meter configuration dictionary
    """
    return {
        "meter_id": "M1",
        "meter_type": "Residential",
        "has_battery": True,
        "battery_capacity": 10.0,
        "has_solar": False,
        "location": "Zone_1",
    }


@pytest.fixture
def sample_solar_meter_config():
    """
    Create a sample solar prosumer meter configuration.
    
    Returns:
        dict: Solar prosumer configuration dictionary
    """
    return {
        "meter_id": "M2",
        "meter_type": "Solar Prosumer",
        "has_battery": True,
        "battery_capacity": 15.0,
        "has_solar": True,
        "solar_capacity_kwp": 5.0,
        "location": "Zone_2",
    }


@pytest.fixture
def sample_meter(sample_meter_config):
    """
    Create a sample smart meter instance.
    
    Returns:
        SmartMeter: Smart meter instance
    """
    return SmartMeter(sample_meter_config)


@pytest.fixture
def sample_solar_meter(sample_solar_meter_config):
    """
    Create a sample solar prosumer meter instance.
    
    Returns:
        SmartMeter: Solar prosumer meter instance
    """
    return SmartMeter(sample_solar_meter_config)


# ============================================================================
# Helper Functions
# ============================================================================

def _create_mock_pandapower_net():
    """Create a mock pandapower network for API testing."""
    net = MagicMock()
    net.bus = pd.DataFrame(
        {
            "name": ["Bus 0", "Bus 1"],
            "vn_kv": [0.4, 0.4],
            "type": ["b", "b"],
        },
        index=[0, 1],
    )
    net.line = pd.DataFrame(
        {
            "name": ["Line 0"],
            "from_bus": [0],
            "to_bus": [1],
            "length_km": [0.1],
            "max_i_ka": [0.2],
            "vn_kv": [0.4],
        },
        index=[0],
    )
    net.load = pd.DataFrame({"bus": [0]}, index=[0])
    net.sgen = pd.DataFrame({"bus": [1]}, index=[1])
    net.ext_grid = pd.DataFrame({"bus": [0]}, index=[0])
    net.res_bus = pd.DataFrame({"vm_pu": [1.0, 1.0]}, index=[0, 1])
    net.res_line = pd.DataFrame(
        {"loading_percent": [10.0], "i_ka": [0.01]}, index=[0]
    )
    net.bus_geocoord = pd.DataFrame(
        {"x": [100.6, 100.7], "y": [13.7, 13.8]}, index=[0, 1]
    )
    return net
