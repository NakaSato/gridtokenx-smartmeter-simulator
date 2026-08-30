"""The daily export cap spends WHOLE WATT-HOURS, the unit readings are recorded in.

Exporters write ``round(kwh * 1000)`` per reading and round generation and
consumption INDEPENDENTLY, so a reading's recorded surplus is
``round(g*1000) - round(c*1000)`` — up to a whole watt-hour away from
``round((g-c)*1000)``. A budget accounted in floats therefore lets a day whose
float arithmetic lands exactly on the cap emit a file a few watt-hours over it.

Measured before the fix, on the 30-day 80-meter reference export: 124 of 360
meter-days between 1 and 4 Wh above a 10 kWh cap, while the float total was
3,599.973 kWh against 3,600.000. Right in energy, wrong in the unit anyone reads.
"""

from datetime import datetime, timezone
from types import SimpleNamespace

from smart_meter_simulator.core.engine import SimulationEngine


def _reading(meter_id: str, generated: float, consumed: float) -> SimpleNamespace:
    return SimpleNamespace(
        meter_id=meter_id,
        energy_generated=generated,
        energy_consumed=consumed,
        surplus_energy=max(0.0, generated - consumed),
        deficit_energy=max(0.0, consumed - generated),
    )


def _engine(cap_kwh: float) -> SimpleNamespace:
    return SimpleNamespace(
        export_cap_kwh=cap_kwh,
        _export_cap_day=None,
        _export_cap_used={},
        export_cap_curtailed_kwh=0.0,
        current_sim_time=datetime(2025, 1, 6, 12, 0, tzinfo=timezone.utc),
    )


def _recorded_surplus(r) -> int:
    """What the exporter will actually write for this reading."""
    return round(r.energy_generated * 1000.0) - round(r.energy_consumed * 1000.0)


def _float_surplus_wh(r) -> float:
    """What the exporter's float daily aggregate will accumulate."""
    return (r.energy_generated - r.energy_consumed) * 1000.0


def test_recorded_surplus_never_exceeds_the_cap():
    """The property the whole change exists for.

    Values chosen so each tick's independently-rounded surplus is a half-watt-hour
    off the float one — the accumulation that used to walk past the cap.
    """
    eng = _engine(0.01)  # 10 Wh budget, reached in a few ticks
    total = 0
    for _ in range(40):
        r = _reading("m1", generated=0.0015005, consumed=0.0010005)
        SimulationEngine._apply_export_cap(eng, [r])
        total += _recorded_surplus(r)
    assert total <= 10, f"recorded {total} Wh against a 10 Wh cap"


def test_the_budget_is_spent_up_to_the_cap_and_never_past_it():
    """Exactly on clean values; at or under it in general.

    The budget can finish a few watt-hours UNDER when a reading's float and
    integer surpluses disagree, because the larger of the two is charged. Under
    is not a violation; over is.
    """
    eng = _engine(0.01)
    total = 0
    for _ in range(40):
        r = _reading("m1", generated=0.004, consumed=0.0)
        SimulationEngine._apply_export_cap(eng, [r])
        total += _recorded_surplus(r)
    assert total == 10  # clean values: exactly the budget


def test_the_float_aggregate_also_honours_the_cap():
    """The half this fix's first attempt broke.

    Charging only the integer let the float daily total drift over — 10.004495
    kWh against a 10.0 cap on the reference export, caught by the exporter's own
    self-check, not by these tests. Both representations are published, so both
    are asserted.
    """
    eng = _engine(0.01)
    total_float = 0.0
    for _ in range(40):
        r = _reading("m1", generated=0.0015005, consumed=0.0010005)
        SimulationEngine._apply_export_cap(eng, [r])
        total_float += _float_surplus_wh(r)
    assert total_float <= 10.0 + 1e-6, f"float total {total_float} Wh over a 10 Wh cap"


def test_a_reading_inside_the_budget_is_untouched():
    eng = _engine(10.0)
    r = _reading("m1", generated=2.0, consumed=0.5)
    SimulationEngine._apply_export_cap(eng, [r])
    assert r.energy_generated == 2.0
    assert _recorded_surplus(r) == 1500


def test_curtailment_lands_the_recorded_surplus_on_the_remaining_budget():
    eng = _engine(0.002)  # 2 Wh
    r = _reading("m1", generated=0.005, consumed=0.0)  # offers 5 Wh
    SimulationEngine._apply_export_cap(eng, [r])
    assert _recorded_surplus(r) == 2
    # And the curtailment is reported, in kWh as the other instruments do.
    assert eng.export_cap_curtailed_kwh > 0.0


def test_budget_is_per_meter():
    eng = _engine(0.002)
    readings = [_reading("m1", 0.005, 0.0), _reading("m2", 0.005, 0.0)]
    SimulationEngine._apply_export_cap(eng, readings)
    assert [_recorded_surplus(r) for r in readings] == [2, 2]


def test_importing_and_self_consuming_readings_are_ignored():
    eng = _engine(10.0)
    importing = _reading("m1", generated=0.5, consumed=2.0)
    balanced = _reading("m2", generated=1.0, consumed=1.0)
    SimulationEngine._apply_export_cap(eng, [importing, balanced])
    assert importing.energy_generated == 0.5
    assert balanced.energy_generated == 1.0
    assert eng._export_cap_used == {}  # neither spent budget


def test_budget_resets_on_a_new_simulated_day():
    eng = _engine(0.002)
    r1 = _reading("m1", 0.005, 0.0)
    SimulationEngine._apply_export_cap(eng, [r1])
    assert _recorded_surplus(r1) == 2

    eng.current_sim_time = datetime(2025, 1, 7, 12, 0, tzinfo=timezone.utc)
    r2 = _reading("m1", 0.005, 0.0)
    SimulationEngine._apply_export_cap(eng, [r2])
    assert _recorded_surplus(r2) == 2  # a fresh day, a fresh budget


def test_disabled_cap_is_a_no_op():
    eng = _engine(0.0)
    r = _reading("m1", generated=99.0, consumed=0.0)
    SimulationEngine._apply_export_cap(eng, [r])
    assert r.energy_generated == 99.0
