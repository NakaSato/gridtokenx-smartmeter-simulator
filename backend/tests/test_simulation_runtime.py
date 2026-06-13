"""Run-progress counters: tick count, simulated-clock elapsed, wall-clock runtime."""

from __future__ import annotations

import asyncio
from pathlib import Path

from smart_meter_simulator.core.engine import SimulationEngine

REFERENCE_GLM = Path("src/smart_meter_simulator/data/grids/grid_bus_network.glm")


def _engine(meters: int = 20) -> SimulationEngine:
    engine = SimulationEngine(grid_topology=f"glm:{REFERENCE_GLM}", num_meters=meters)
    engine.grid.initialize_network(engine.meters)
    return engine


def test_counters_start_at_zero():
    engine = _engine()
    assert engine.tick_count == 0
    assert engine.sim_elapsed_seconds() == 0.0
    assert engine.runtime_seconds() == 0.0


def test_tick_advances_count_and_sim_clock():
    engine = _engine()
    asyncio.run(engine.tick())
    asyncio.run(engine.tick())
    assert engine.tick_count == 2
    # Simulated elapsed == ticks * interval.
    assert engine.sim_elapsed_seconds() == 2 * engine.interval


def test_runtime_accumulates_then_freezes_on_stop(monkeypatch):
    engine = _engine()
    import smart_meter_simulator.core.engine as eng_mod

    # Arm the wall clock as start() would, then stop() should freeze + accumulate.
    engine.wall_clock_started_monotonic = 100.0  # fake monotonic origin
    monkeypatch.setattr(eng_mod.time, "monotonic", lambda: 105.0)  # 5s later
    asyncio.run(engine.stop())
    assert engine.runtime_seconds() == 5.0
    assert engine.wall_clock_started_monotonic is None
    # Frozen: a later clock does not advance a stopped engine.
    monkeypatch.setattr(eng_mod.time, "monotonic", lambda: 200.0)
    assert engine.runtime_seconds() == 5.0


def test_deterministic_reset_zeroes_counters():
    engine = _engine()
    asyncio.run(engine.tick())
    assert engine.tick_count == 1
    asyncio.run(engine.reset_deterministic(seed=7, autostart=False))
    assert engine.tick_count == 0
    assert engine.wall_clock_accumulated_s == 0.0
    assert engine.sim_elapsed_seconds() == 0.0
