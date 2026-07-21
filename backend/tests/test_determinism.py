"""Determinism guarantees: same RANDOM_SEED (+ pinned clock) => identical runs.

Locks the behaviour added for reproducible simulation:
  * meter fleet generation (ids, serials, base loads) is seed-driven,
  * every meter's per-tick noise is seed-driven and drawn from its own stream,
  * SIMULATION_START_TIME pins the sim clock,
  * dropping a meter does not shift any other meter's readings.
"""

from __future__ import annotations

import asyncio

import pytest

from smart_meter_simulator.config import settings
from smart_meter_simulator.core.engine import SimulationEngine

PINNED_START = "2026-06-10T12:00:00+00:00"
NUM_METERS = 6


def _build_engine(monkeypatch, *, seed=42, start=PINNED_START):
    """Construct an engine under a fresh, isolated config singleton."""
    monkeypatch.setenv("RANDOM_SEED", str(seed))
    if start is None:
        monkeypatch.delenv("SIMULATION_START_TIME", raising=False)
    else:
        monkeypatch.setenv("SIMULATION_START_TIME", start)
    # Drop the cached singleton so the new env is picked up.
    settings._config_instance = None
    return SimulationEngine(num_meters=NUM_METERS)


def _fleet_signature(engine):
    return [
        (
            m.config.get("meter_id"),
            m.config.get("serial_number"),
            round(float(m.config.get("base_consumption", 0.0)), 9),
            round(float(m.config.get("base_generation", 0.0)), 9),
        )
        for m in engine.meters
    ]


def _tick_signature(engine, ticks=3):
    async def _run():
        out = []
        for _ in range(ticks):
            readings = await engine.tick()
            for r in readings:
                out.append(
                    (
                        r.meter_id,
                        round(r.energy_consumed, 9),
                        round(r.energy_generated, 9),
                        round(r.temperature, 6) if r.temperature is not None else None,
                        round(r.voltage, 6) if r.voltage is not None else None,
                    )
                )
        return out

    return asyncio.run(_run())


@pytest.fixture(autouse=True)
def _restore_config():
    """Reset the config singleton after each test so we don't leak env state."""
    yield
    settings._config_instance = None


# --- T1: fleet determinism ------------------------------------------------


def test_same_seed_produces_identical_fleet(monkeypatch):
    a = _fleet_signature(_build_engine(monkeypatch, seed=42))
    b = _fleet_signature(_build_engine(monkeypatch, seed=42))
    assert a == b
    assert a  # fleet is non-empty (sized to the GLM topology buses)


# --- T2: tick-noise determinism -------------------------------------------


def test_same_seed_produces_identical_tick_noise(monkeypatch):
    a = _tick_signature(_build_engine(monkeypatch, seed=42))
    b = _tick_signature(_build_engine(monkeypatch, seed=42))
    assert a == b


# --- T3: seed sensitivity (proves the seed is actually wired) -------------


def test_different_seed_changes_output(monkeypatch):
    fleet_42 = _fleet_signature(_build_engine(monkeypatch, seed=42))
    fleet_99 = _fleet_signature(_build_engine(monkeypatch, seed=99))
    assert fleet_42 != fleet_99

    noise_42 = _tick_signature(_build_engine(monkeypatch, seed=42))
    noise_99 = _tick_signature(_build_engine(monkeypatch, seed=99))
    assert noise_42 != noise_99


# --- T4: sim-clock pin -----------------------------------------------------


def test_simulation_start_time_pins_clock(monkeypatch):
    engine = _build_engine(monkeypatch, start=PINNED_START)
    assert engine.current_sim_time.isoformat() == PINNED_START


def test_unset_start_time_falls_back_to_0800(monkeypatch):
    engine = _build_engine(monkeypatch, start=None)
    ts = engine.current_sim_time
    assert (ts.hour, ts.minute, ts.second, ts.microsecond) == (8, 0, 0, 0)


def test_invalid_start_time_falls_back(monkeypatch):
    import datetime as dt

    engine = _build_engine(monkeypatch, start="not-a-timestamp")
    ts = engine.current_sim_time
    now = dt.datetime.now(dt.timezone.utc)
    default_start = now.replace(hour=8, minute=0, second=0, microsecond=0)
    if default_start <= now:
        # 08:00 UTC has already passed today — the invalid value falls back to it.
        assert (ts.hour, ts.minute, ts.second, ts.microsecond) == (8, 0, 0, 0)
    else:
        # Run before 08:00 UTC: the 08:00 fallback is still in the future, so
        # _initial_sim_time clamps it to now (a clock that outruns wall-clock
        # starves the aggregator's billing bins). Covered end-to-end by
        # test_future_start_time_clamps_to_now.
        assert abs((ts - now).total_seconds()) < 5


def test_future_start_time_clamps_to_now(monkeypatch):
    import datetime as dt

    future = (dt.datetime.now(dt.timezone.utc) + dt.timedelta(hours=2)).isoformat()
    before = dt.datetime.now(dt.timezone.utc)
    engine = _build_engine(monkeypatch, start=future)
    after = dt.datetime.now(dt.timezone.utc)
    assert before <= engine.current_sim_time <= after


# --- T5: per-meter isolation ----------------------------------------------


def test_dropping_a_meter_does_not_shift_others(monkeypatch):
    # Frequency-watt droop is a deliberate global coupling: system frequency is
    # derived from the whole fleet's gen/load balance, so removing any meter
    # shifts every other meter's next-tick droop response (and, through the
    # value-conditional noise draws in calculate_electrical_params, their RNG
    # stream positions). Disable it so this test pins what it is about — that
    # each meter's *random stream* is keyed to its identity, not its position
    # in the fleet.
    monkeypatch.setenv("FREQ_DROOP_ENABLED", "false")

    full = _tick_signature(_build_engine(monkeypatch, seed=42))

    dropped_engine = _build_engine(monkeypatch, seed=42)
    dropped_engine.meters = dropped_engine.meters[1:]
    dropped = _tick_signature(dropped_engine)

    full_by_meter = {(m, c, g, t, v) for (m, c, g, t, v) in full}
    dropped_by_meter = {(m, c, g, t, v) for (m, c, g, t, v) in dropped}
    # Every dropped-run reading must still appear verbatim in the full run.
    assert dropped_by_meter <= full_by_meter
    assert dropped_by_meter  # non-empty
