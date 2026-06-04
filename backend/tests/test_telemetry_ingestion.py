"""Tests for real-telemetry ingestion: registry, replay source, and engine override."""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone

import pytest

from smart_meter_simulator.core.engine import SimulationEngine
from smart_meter_simulator.core.telemetry_source import (
    ReplaySource,
    SyntheticSource,
    build_telemetry_source,
    parse_telemetry_spec,
)
from smart_meter_simulator.core.topology_factory import load_configured_topology
from smart_meter_simulator.devices.ami import SmartMeter
from smart_meter_simulator.meter_registry import (
    MeterRegistryEntry,
    build_meter_configs,
    load_meter_registry,
)

TS = datetime(2026, 6, 5, 8, 0, 0, tzinfo=timezone.utc)


# --------------------------------------------------------------------------- specs
def test_parse_telemetry_spec_variants():
    assert parse_telemetry_spec("") == ("synthetic", "")
    assert parse_telemetry_spec("synthetic") == ("synthetic", "")
    assert parse_telemetry_spec("replay:data/t.csv") == ("replay", "data/t.csv")
    assert parse_telemetry_spec("data/t.csv") == ("replay", "data/t.csv")
    with pytest.raises(ValueError):
        parse_telemetry_spec("kafka")


def test_synthetic_source_yields_empty_frame():
    assert SyntheticSource().poll(TS) == {}
    assert build_telemetry_source("synthetic").name == "synthetic"


# ------------------------------------------------------------------------- registry
def test_load_meter_registry_csv(tmp_path):
    csv_path = tmp_path / "registry.csv"
    csv_path.write_text(
        "meter_id,bus,meter_type,has_solar,solar_capacity_kw,phase\n"
        "MTR-1,node_2,solar_prosumer,true,8.0,A\n"
        "MTR-2,node_2,grid_consumer,false,0,B\n",
        encoding="utf-8",
    )
    entries = load_meter_registry(csv_path)
    assert [e.meter_id for e in entries] == ["MTR-1", "MTR-2"]
    assert entries[0].has_solar and entries[0].solar_capacity_kw == 8.0
    assert entries[1].meter_type == "grid_consumer" and not entries[1].has_solar


def test_build_meter_configs_pins_to_bus():
    topology = load_configured_topology()
    bus0 = topology.buses[0].name
    entries = [
        MeterRegistryEntry(meter_id="MTR-1", bus=bus0, meter_type="grid_consumer")
    ]
    configs = build_meter_configs(entries, topology)
    assert configs[0]["meter_id"] == "MTR-1"
    assert configs[0]["bus_name"] == bus0
    assert configs[0]["bus_idx"] == 0


# --------------------------------------------------------------------------- replay
def test_replay_source_hold_last_value(tmp_path):
    csv_path = tmp_path / "telemetry.csv"
    csv_path.write_text(
        "meter_id,timestamp,energy_consumed,energy_generated\n"
        "MTR-1,2026-06-05T08:00:00+00:00,0.05,0.0\n"
        "MTR-1,2026-06-05T08:15:00+00:00,0.10,0.0\n",
        encoding="utf-8",
    )
    src = ReplaySource(csv_path, interval_seconds=900)  # 15 min -> kWh == kW

    # At first sample: 0.05 kWh over 900s -> 0.2 kW.
    early = src.poll(datetime(2026, 6, 5, 8, 0, tzinfo=timezone.utc))
    assert early["MTR-1"].cons_kw == pytest.approx(0.2)
    # Between samples: hold the 08:00 value.
    assert src.poll(datetime(2026, 6, 5, 8, 10, tzinfo=timezone.utc))[
        "MTR-1"
    ].cons_kw == pytest.approx(0.2)
    # At/after second sample: 0.10 kWh -> 0.4 kW.
    assert src.poll(datetime(2026, 6, 5, 8, 20, tzinfo=timezone.utc))[
        "MTR-1"
    ].cons_kw == pytest.approx(0.4)
    # Before first sample: earliest frame.
    assert src.poll(datetime(2026, 6, 5, 7, 0, tzinfo=timezone.utc))[
        "MTR-1"
    ].cons_kw == pytest.approx(0.2)


# ----------------------------------------------------------------------- end-to-end
def test_engine_tick_uses_real_telemetry(tmp_path):
    """A replayed consumption value should flow through to the meter's reading."""
    topology = load_configured_topology()
    bus0 = topology.buses[0].name

    entries = [
        MeterRegistryEntry(meter_id="MTR-1", bus=bus0, meter_type="grid_consumer"),
        MeterRegistryEntry(meter_id="MTR-2", bus=bus0, meter_type="grid_consumer"),
    ]
    meters = [SmartMeter(c) for c in build_meter_configs(entries, topology)]

    csv_path = tmp_path / "telemetry.csv"
    # MTR-1 gets real data; MTR-2 is absent -> stays synthetic (hybrid).
    csv_path.write_text(
        "meter_id,timestamp,energy_consumed,energy_generated\n"
        "MTR-1,2026-06-05T08:00:00+00:00,0.05,0.0\n",
        encoding="utf-8",
    )

    engine = SimulationEngine(meters=meters, topology=topology)
    engine.interval = 900
    engine.telemetry_source = ReplaySource(csv_path, interval_seconds=900)
    engine.grid.initialize_network(engine.meters)
    engine.current_sim_time = TS

    readings = asyncio.run(engine.tick())
    by_id = {r.meter_id: r for r in readings}

    # Real injection round-trips exactly: 0.05 kWh consumed.
    assert by_id["MTR-1"].energy_consumed == pytest.approx(0.05, abs=1e-6)
    # The grid mapper pinned MTR-1 to its registry bus.
    assert engine.grid.meter_to_bus["MTR-1"] == bus0
    # MTR-2 had no telemetry -> synthetic (non-negative, independent of the injection).
    assert by_id["MTR-2"].energy_consumed >= 0.0
