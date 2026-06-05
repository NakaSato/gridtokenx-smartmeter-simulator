from datetime import datetime, timezone
from pathlib import Path

import pytest

from smart_meter_simulator.adapters.reference_grid_loader import (
    load_reference_grid_topology,
)
from smart_meter_simulator.core.telemetry_source import (
    ReferenceGridReplaySource,
    build_telemetry_source,
)
from smart_meter_simulator.core.topology_factory import load_topology_spec
from smart_meter_simulator.devices.ami import SmartMeter
from smart_meter_simulator.meter_registry import (
    build_meter_configs,
    load_meter_registry,
)

REFERENCE_GRID_DIR = Path("data/80_bus_rural_reference_grid")


def test_reference_grid_topology_loads_csv_folder():
    topology = load_topology_spec(f"reference-grid:{REFERENCE_GRID_DIR}")

    assert topology.source == "reference-grid"
    assert len(topology.buses) == 80
    assert len(topology.lines) == 79
    assert len(topology.loads) == 32
    assert len(topology.pvs) == 0
    assert topology.get_substation_bus() == "ref_lv_bus_1"
    assert topology.validate().is_valid
    assert topology.summary()["static_load_kw"] == pytest.approx(32.715, abs=0.001)


def test_reference_grid_loader_preserves_branch_length_and_impedance():
    topology = load_reference_grid_topology(REFERENCE_GRID_DIR)
    line = topology.lines[0]

    z_base_ohm = (0.23**2) / 0.015967
    expected_r_ohm_per_km = 0.0157048256741581 * z_base_ohm / 0.0433594955305194
    expected_x_ohm_per_km = 0.0010689935743038 * z_base_ohm / 0.0433594955305194

    assert line.name == "Line_0"
    assert line.from_bus == "ref_lv_bus_35"
    assert line.to_bus == "ref_lv_bus_36"
    assert line.length == pytest.approx(0.0433594955305194)
    assert line.length_unit == "km"
    assert line.resistance_ohm_per_km == pytest.approx(expected_r_ohm_per_km)
    assert line.reactance_ohm_per_km == pytest.approx(expected_x_ohm_per_km)


def test_reference_grid_registry_pins_load_buses_to_matching_meter_ids():
    topology = load_topology_spec(f"reference-grid:{REFERENCE_GRID_DIR}")
    entries = load_meter_registry(f"reference-grid:{REFERENCE_GRID_DIR}")
    configs = build_meter_configs(entries, topology)

    assert len(entries) == 32
    assert entries[0].meter_id == "ref_lv_bus_8"
    assert entries[0].bus == "ref_lv_bus_8"
    assert entries[0].has_solar is False
    assert configs[0]["meter_id"] == "ref_lv_bus_8"
    assert configs[0]["bus_name"] == "ref_lv_bus_8"
    assert configs[0]["bus_idx"] == 7


def test_reference_grid_replay_source_converts_wide_load_files_to_meter_frames():
    source = ReferenceGridReplaySource(REFERENCE_GRID_DIR)
    frame = source.poll(datetime(2026, 1, 1, 0, 15, tzinfo=timezone.utc))

    assert len(frame) == 32
    assert frame["ref_lv_bus_8"].cons_kw == pytest.approx(2.547)
    assert frame["ref_lv_bus_8"].gen_kw is None
    assert frame["ref_lv_bus_8"].reactive_kvar == pytest.approx(0.025)
    assert frame["ref_lv_bus_80"].cons_kw == pytest.approx(0.519)
    assert frame["ref_lv_bus_80"].reactive_kvar == pytest.approx(0.084)


def test_build_telemetry_source_accepts_reference_grid_spec():
    source = build_telemetry_source(f"reference-grid:{REFERENCE_GRID_DIR}")

    assert isinstance(source, ReferenceGridReplaySource)


def test_meter_reading_can_carry_replayed_reactive_power():
    topology = load_topology_spec(f"reference-grid:{REFERENCE_GRID_DIR}")
    entries = load_meter_registry(f"reference-grid:{REFERENCE_GRID_DIR}")[:1]
    config = build_meter_configs(entries, topology)[0]
    meter = SmartMeter(config)

    reading = meter.generate_reading(
        datetime(2021, 1, 1, tzinfo=timezone.utc),
        override_cons=2.547,
        override_gen=0.0,
        override_reactive_kvar=0.025,
        interval_seconds=3600,
    )

    assert reading.energy_consumed == pytest.approx(2.547)
    assert reading.energy_generated == pytest.approx(0.0)
    assert reading.reactive_power_kvar == pytest.approx(0.025)
