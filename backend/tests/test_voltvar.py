"""IEEE 1547 volt-VAR (Q(V)) reactive-support tests.

The Q(V) curve is unit-tested directly; integration confirms that enabling
volt-VAR engages reactive support on the reference feeder and that it stays
within the inverter's apparent-power headroom.
"""

import asyncio
from pathlib import Path

from smart_meter_simulator.core.engine import SimulationEngine
from smart_meter_simulator.core.grid_manager import GridManager

REFERENCE_GLM_FILE = Path("src/smart_meter_simulator/data/grids/grid_bus_network.glm")


def _engine(meters: int = 40) -> SimulationEngine:
    engine = SimulationEngine(
        grid_topology=f"glm:{REFERENCE_GLM_FILE}", num_meters=meters
    )
    engine.grid.initialize_network(engine.meters)
    return engine


# --- Q(V) curve (load convention: + absorbs at high V, - injects at low V) ---


def test_voltvar_curve_breakpoints():
    q = GridManager._voltvar_q_factor
    v1, v2, v3, v4 = 0.92, 0.98, 1.02, 1.08
    assert q(0.90, v1, v2, v3, v4) == -1.0  # below v1: full injection
    assert q(0.95, v1, v2, v3, v4) < 0.0  # ramp injection
    assert q(1.00, v1, v2, v3, v4) == 0.0  # deadband
    assert q(0.98, v1, v2, v3, v4) == 0.0  # deadband edge
    assert q(1.02, v1, v2, v3, v4) == 0.0  # deadband edge
    assert q(1.05, v1, v2, v3, v4) > 0.0  # ramp absorption
    assert q(1.10, v1, v2, v3, v4) == 1.0  # above v4: full absorption


def test_voltvar_curve_monotonic_and_bounded():
    q = GridManager._voltvar_q_factor
    v1, v2, v3, v4 = 0.92, 0.98, 1.02, 1.08
    prev = -2.0
    for i in range(0, 130):
        vm = 0.85 + i * 0.002
        f = q(vm, v1, v2, v3, v4)
        assert -1.0 <= f <= 1.0
        assert f >= prev - 1e-9  # non-decreasing in voltage
        prev = f


# --- integration on the reference feeder --------------------------------------


def test_voltvar_engages_reactive_support():
    engine = _engine()
    asyncio.run(engine.tick())
    grid = engine.grid
    # Reference feeder under PV export drives buses outside the deadband, so the
    # inverters should be providing nonzero net reactive support.
    assert grid.total_reactive_support_kvar > 0.0
    assert engine.last_tick_summary["total_reactive_support_kvar"] == (
        grid.total_reactive_support_kvar
    )


def test_voltvar_disabled_provides_no_support():
    engine = _engine()
    engine.config.pv_voltvar_enabled = False
    asyncio.run(engine.tick())
    assert engine.grid.total_reactive_support_kvar == 0.0


def test_voltvar_respects_inverter_headroom():
    engine = _engine()
    cfg = engine.config
    asyncio.run(engine.tick())
    grid = engine.grid
    # Total support cannot exceed the sum of per-inverter caps
    # (q_max_frac x sn), the loosest possible bound.
    cap = sum(
        kw * cfg.pv_voltvar_inverter_oversize * cfg.pv_voltvar_q_max_frac
        for kw in grid.pv_capacity_by_bus.values()
    )
    assert grid.total_reactive_support_kvar <= cap + 1e-6
