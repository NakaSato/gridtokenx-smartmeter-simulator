"""Demand-response (load-shed) tests.

The controller resolves a per-meter consumption multiplier for the current sim
instant; an active event curtails participating load, relieving the feeder. At
the engine level a scheduled event must lower aggregate consumption and surface
the shed power in the tick summary.
"""

import asyncio
from datetime import datetime, timedelta, timezone
from pathlib import Path

from smart_meter_simulator.core.demand_response import DemandResponseController
from smart_meter_simulator.core.engine import SimulationEngine

REFERENCE_GLM_FILE = Path("src/smart_meter_simulator/data/grids/grid_bus_network.glm")

T0 = datetime(2026, 6, 10, 12, 0, 0, tzinfo=timezone.utc)


def _engine(meters: int = 40) -> SimulationEngine:
    engine = SimulationEngine(
        grid_topology=f"glm:{REFERENCE_GLM_FILE}", num_meters=meters
    )
    engine.grid.initialize_network(engine.meters)
    return engine


# --- controller unit tests --------------------------------------------------


def test_no_events_is_no_curtailment():
    ctrl = DemandResponseController()
    assert ctrl.load_factor(T0, "Residential") == 1.0
    assert not ctrl.has_active(T0)


def test_active_event_sheds_fraction():
    ctrl = DemandResponseController()
    ctrl.schedule(start=T0, end=T0 + timedelta(hours=1), reduction_fraction=0.3)
    assert ctrl.load_factor(T0, "Residential") == 0.7
    assert ctrl.has_active(T0)


def test_window_is_half_open():
    ctrl = DemandResponseController()
    end = T0 + timedelta(hours=1)
    ctrl.schedule(start=T0, end=end, reduction_fraction=0.5)
    # before start and at/after end -> no shed; inside -> shed.
    assert ctrl.load_factor(T0 - timedelta(seconds=1), "Residential") == 1.0
    assert ctrl.load_factor(T0, "Residential") == 0.5
    assert ctrl.load_factor(end, "Residential") == 1.0


def test_target_meter_types_filter():
    ctrl = DemandResponseController()
    ctrl.schedule(
        start=T0,
        end=T0 + timedelta(hours=1),
        reduction_fraction=0.4,
        target_meter_types=["Commercial"],
    )
    assert ctrl.load_factor(T0, "Commercial") == 0.6
    assert ctrl.load_factor(T0, "Residential") == 1.0


def test_overlapping_events_take_most_aggressive():
    ctrl = DemandResponseController()
    win = (T0, T0 + timedelta(hours=1))
    ctrl.schedule(start=win[0], end=win[1], reduction_fraction=0.3)
    ctrl.schedule(start=win[0], end=win[1], reduction_fraction=0.5)
    # 0.3 and 0.5 compose to a single 0.5 shed, not 0.65.
    assert ctrl.load_factor(T0, "Residential") == 0.5


def test_schedule_validation():
    ctrl = DemandResponseController()
    for bad in (0.0, -0.1, 1.5):
        try:
            ctrl.schedule(start=T0, end=T0 + timedelta(hours=1), reduction_fraction=bad)
            raise AssertionError(f"expected ValueError for fraction {bad}")
        except ValueError:
            pass
    try:
        ctrl.schedule(start=T0, end=T0, reduction_fraction=0.5)
        raise AssertionError("expected ValueError for end <= start")
    except ValueError:
        pass


def test_cancel_and_clear():
    ctrl = DemandResponseController()
    ev = ctrl.schedule(start=T0, end=T0 + timedelta(hours=1), reduction_fraction=0.2)
    assert ctrl.cancel(ev.event_id) is True
    assert ctrl.cancel(ev.event_id) is False
    ctrl.schedule(start=T0, end=T0 + timedelta(hours=1), reduction_fraction=0.2)
    ctrl.schedule(start=T0, end=T0 + timedelta(hours=1), reduction_fraction=0.3)
    assert ctrl.clear() == 2
    assert ctrl.load_factor(T0, "Residential") == 1.0


def test_event_ids_are_monotonic():
    ctrl = DemandResponseController()
    a = ctrl.schedule(start=T0, end=T0 + timedelta(hours=1), reduction_fraction=0.1)
    b = ctrl.schedule(start=T0, end=T0 + timedelta(hours=1), reduction_fraction=0.1)
    assert (a.event_id, b.event_id) == ("dr-1", "dr-2")


# --- engine integration -----------------------------------------------------


def test_active_event_lowers_consumption_and_reports_shed():
    baseline = _engine()
    asyncio.run(baseline.tick(timestamp=T0))
    base_cons = baseline.last_tick_summary["total_consumption_kwh"]
    assert baseline.last_tick_summary["total_dr_shed_kw"] == 0.0
    assert baseline.last_tick_summary["active_dr_events"] == 0

    shed = _engine()  # same seed + fleet -> directly comparable
    shed.dr_controller.schedule(
        start=T0, end=T0 + timedelta(hours=1), reduction_fraction=0.5
    )
    asyncio.run(shed.tick(timestamp=T0))

    assert shed.last_tick_summary["active_dr_events"] == 1
    assert shed.last_tick_summary["total_dr_shed_kw"] > 0.0
    assert shed.last_tick_summary["total_consumption_kwh"] < base_cons


def test_reset_deterministic_clears_dr_events():
    engine = _engine()
    engine.dr_controller.schedule(
        start=T0, end=T0 + timedelta(hours=1), reduction_fraction=0.5
    )
    asyncio.run(engine.reset_deterministic(autostart=False))
    assert engine.dr_controller.clear() == 0  # already empty after reset
