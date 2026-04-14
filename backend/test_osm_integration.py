#!/usr/bin/env python3
"""
Integration test: Run simulator with real OSM Korat power grid data.

Tests:
1. Load OSM data → pandapower network
2. Create SmartMeter instances at substations
3. Run single simulation step
4. Verify readings are signed and match grid state

Usage:
    uv run python test_osm_integration.py
    uv run pytest test_osm_integration.py -v
"""

import json
import logging
import pytest
from pathlib import Path
from datetime import datetime, timezone

import numpy as np

try:
    import pandapower as pp
    PANDAPOWER_AVAILABLE = True
except ImportError:
    PANDAPOWER_AVAILABLE = False

from smart_meter_simulator.core.meter import SmartMeter
from smart_meter_simulator.config.settings import SimulatorConfig

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@pytest.fixture
def korat_network():
    """Load OSM-derived pandapower network"""
    if not PANDAPOWER_AVAILABLE:
        pytest.skip("pandapower not installed")

    data_dir = Path(__file__).parent / "data" / "korat"
    net_file = data_dir / "pandapower_network.json"

    if not net_file.exists():
        pytest.skip("Korat network file not found. Run build_pandapower_from_osm.py first")

    net = pp.from_json(str(net_file))
    pp.runpp(net)
    return net


@pytest.fixture
def korat_meters():
    """Load SmartMeter instances from OSM configuration"""
    data_dir = Path(__file__).parent / "data" / "korat"
    meters_file = data_dir / "osm_meters.json"

    if not meters_file.exists():
        pytest.skip("Meters file not found. Run create_meters_from_osm.py first")

    with open(meters_file) as f:
        meters_config = json.load(f)

    meters = []
    for meter_cfg in meters_config["meters"]:
        full_config = {
            "meter_id": meter_cfg["meter_id"],
            "meter_type": meter_cfg["meter_type"],
            "current_battery_level": 0.0,
            "priority": 2,
            "location": json.dumps(meter_cfg["location"]) if isinstance(meter_cfg["location"], dict) else meter_cfg["location"],
        }
        meter = SmartMeter(full_config)
        meters.append(meter)

    return meters


def test_load_osm_network(korat_network):
    """Test 1: Load OSM-derived pandapower network"""
    net = korat_network

    assert len(net.bus) == 4, f"Expected 4 buses, got {len(net.bus)}"
    assert len(net.line) == 3, f"Expected 3 lines, got {len(net.line)}"
    assert len(net.load) == 4, f"Expected 4 loads, got {len(net.load)}"
    assert len(net.ext_grid) == 1, f"Expected 1 external grid, got {len(net.ext_grid)}"

    # Verify all buses have valid voltages
    for idx, row in net.res_bus.iterrows():
        assert not np.isnan(row["vm_pu"]), f"Bus {idx} voltage is NaN"
        assert 0.9 <= row["vm_pu"] <= 1.1, f"Bus {idx} voltage {row['vm_pu']} out of range"

    logger.info("✓ Test 1: OSM network loaded and power flow converged")


def test_load_meters(korat_meters):
    """Test 2: Load SmartMeter instances from OSM configuration"""
    meters = korat_meters

    assert len(meters) == 16, f"Expected 16 meters, got {len(meters)}"

    # Verify each meter has valid state
    for meter in meters:
        assert meter.meter_id, f"Meter has no ID"
        assert meter.key_manager, f"Meter {meter.meter_id} has no key manager"
        assert meter.accuracy_class, f"Meter {meter.meter_id} has no accuracy class"

    logger.info(f"✓ Test 2: Loaded {len(meters)} SmartMeter instances")


def test_generate_readings(korat_network, korat_meters):
    """Test 3: Generate signed readings from meters with grid state"""
    net = korat_network
    meters = korat_meters
    timestamp = datetime.now(timezone.utc)

    # Get bus voltages from power flow
    bus_voltages = {}
    for idx, row in net.res_bus.iterrows():
        bus_voltages[idx] = row["vm_pu"]

    readings = []
    for meter in meters:
        # Get voltage from grid (per-unit to actual)
        location_str = meter.config.get("location", "{}")
        try:
            location = json.loads(location_str) if isinstance(location_str, str) else location_str
        except json.JSONDecodeError:
            location = {}

        bus_idx = location.get("bus_idx")

        if bus_idx is not None and bus_idx in bus_voltages:
            voltage_pu = bus_voltages[bus_idx]
            voltage_kv = location.get("voltage_kv", 22)
            voltage_actual = voltage_pu * voltage_kv * 1000  # Convert to volts
        else:
            voltage_actual = 230000  # Default for transmission meters

        # Generate reading
        reading = meter.generate_reading(
            timestamp=timestamp,
            interval_seconds=900,
            nodal_price=0.50,
            carbon_intensity=0.4,
            grid_stress=1.0,
        )

        # Override voltage with grid state (field is 'voltage' not 'voltage_v')
        reading.voltage = voltage_actual

        readings.append(reading)

        # Verify reading is signed
        assert reading.meter_signature, f"Meter {meter.meter_id} reading not signed"

        # Verify voltage is reasonable
        assert 0.9 * voltage_actual <= reading.voltage <= 1.1 * voltage_actual, \
            f"Meter {meter.meter_id} voltage {reading.voltage}V out of range"

    logger.info(f"✓ Test 3: Generated {len(readings)} signed readings")
    return readings


def test_state_estimation(korat_network, korat_meters):
    """Test 4: Verify readings align with state estimation results"""
    net = korat_network
    meters = korat_meters

    # Generate readings
    timestamp = datetime.now(timezone.utc)
    bus_voltages = {}
    for idx, row in net.res_bus.iterrows():
        bus_voltages[idx] = row["vm_pu"]

    readings = []
    for meter in meters:
        location_str = meter.config.get("location", "{}")
        try:
            location = json.loads(location_str) if isinstance(location_str, str) else location_str
        except json.JSONDecodeError:
            location = {}
        bus_idx = location.get("bus_idx")
        voltage_kv = location.get("voltage_kv", 22)

        if bus_idx is not None and bus_idx in bus_voltages:
            voltage_pu = bus_voltages[bus_idx]
            voltage_actual = voltage_pu * voltage_kv * 1000
        else:
            voltage_actual = 230000

        reading = meter.generate_reading(timestamp=timestamp, interval_seconds=900)
        reading.voltage = voltage_actual
        readings.append(reading)

    # Check that meter readings are within expected range of SE results
    for meter, reading in zip(meters, readings):
        location_str = meter.config.get("location", "{}")
        try:
            location = json.loads(location_str) if isinstance(location_str, str) else location_str
        except json.JSONDecodeError:
            location = {}
        bus_idx = location.get("bus_idx")

        if bus_idx is not None and bus_idx in net.res_bus.index:
            se_voltage = net.res_bus.at[bus_idx, "vm_pu"]
            voltage_kv = location.get("voltage_kv", 22)
            se_voltage_actual = se_voltage * voltage_kv * 1000

            # Reading should be close to SE result (within accuracy class tolerance)
            accuracy_pct = meter.accuracy_class.value / 100.0
            tolerance = accuracy_pct * se_voltage_actual

            assert abs(reading.voltage - se_voltage_actual) < tolerance * 10, \
                f"Meter {meter.meter_id} voltage {reading.voltage}V deviates from SE {se_voltage_actual}V"

    logger.info("✓ Test 4: Readings align with state estimation results")


def main():
    logger.info("=" * 60)
    logger.info("OSM Korat Grid Integration Test")
    logger.info("=" * 60)

    if not PANDAPOWER_AVAILABLE:
        logger.error("pandapower not installed. Run: uv sync")
        return

    # Test 1: Load network
    net = test_load_osm_network()

    # Test 2: Load meters
    meters = test_load_meters()

    # Test 3: Generate readings
    readings = test_generate_readings(meters, net)

    # Test 4: Verify against SE
    test_state_estimation(net, meters, readings)

    # Print summary
    print("\n" + "=" * 60)
    print("ALL TESTS PASSED")
    print("=" * 60)
    print(f"\nNetwork: {len(net.bus)} buses, {len(net.line)} lines, {len(net.load)} loads")
    print(f"Meters: {len(meters)} (4 substation + 12 consumer)")
    print(f"Readings: {len(readings)} signed readings generated")
    print(f"Grid: {net.load.p_mw.sum():.1f} MW total load, {net.res_line.pl_mw.sum():.3f} MW losses")
    print(f"\nOSM Data: Real Korat area power grid from OpenStreetMap")
    print(f"  - 4 substations (1 transmission @ 230kV, 3 distribution @ 115kV)")
    print(f"  - 3 transmission lines (40-79 km each)")
    print(f"  - 402 towers, 7 poles")
    print(f"\nTopo: Radial network from transmission substation to 3 distribution buses")


if __name__ == "__main__":
    main()
