"""Bounded run window: explicit end_time and week/month/year range presets."""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from pathlib import Path

import pytest

from smart_meter_simulator.core.engine import SimulationEngine

REFERENCE_GLM = Path("src/smart_meter_simulator/data/grids/grid_bus_network.glm")
START = "2026-06-10T08:00:00+00:00"


def _engine() -> SimulationEngine:
    engine = SimulationEngine(grid_topology=f"glm:{REFERENCE_GLM}", num_meters=20)
    engine.grid.initialize_network(engine.meters)
    return engine


def _reset(engine, **kwargs):
    kwargs.setdefault("start_time", START)
    return asyncio.run(engine.reset_deterministic(autostart=False, **kwargs))


def test_no_window_is_open_ended():
    engine = _engine()
    _reset(engine)
    assert engine.sim_end_time is None
    assert engine.sim_progress() is None
    assert engine._reached_end() is False


def test_end_time_sets_window_and_is_reached_after_ticks():
    engine = _engine()
    out = _reset(engine, end_time="2026-06-10T08:01:00+00:00", interval=15)
    assert out["end_time"] == "2026-06-10T08:01:00+00:00"
    assert engine.sim_end_time == datetime(2026, 6, 10, 8, 1, tzinfo=timezone.utc)
    # 60s window / 15s interval = 4 ticks to reach the end.
    for _ in range(3):
        asyncio.run(engine.tick())
        assert engine._reached_end() is False
    asyncio.run(engine.tick())
    assert engine._reached_end() is True
    assert engine.sim_progress() == pytest.approx(1.0)


def test_time_range_week():
    engine = _engine()
    _reset(engine, time_range="week")
    assert engine.sim_end_time == datetime(2026, 6, 17, 8, 0, tzinfo=timezone.utc)


def test_time_range_year():
    engine = _engine()
    _reset(engine, time_range="year")
    assert engine.sim_end_time == datetime(2027, 6, 10, 8, 0, tzinfo=timezone.utc)


def test_time_range_month_clamps_day():
    # Jan 31 + 1 month -> Feb 28 (2026 is not a leap year).
    engine = _engine()
    _reset(engine, start_time="2026-01-31T08:00:00+00:00", time_range="month")
    assert engine.sim_end_time == datetime(2026, 2, 28, 8, 0, tzinfo=timezone.utc)


def test_end_before_start_rejected():
    engine = _engine()
    with pytest.raises(ValueError):
        _reset(engine, end_time="2026-06-10T07:00:00+00:00")


def test_end_time_and_range_mutually_exclusive():
    engine = _engine()
    with pytest.raises(ValueError):
        _reset(engine, end_time="2026-06-11T08:00:00+00:00", time_range="day")


def test_invalid_range_rejected():
    engine = _engine()
    with pytest.raises(ValueError):
        _reset(engine, time_range="fortnight")
