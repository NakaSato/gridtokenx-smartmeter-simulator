"""Inverter AC cap (`--max-gen-kw` / `engine.generation_limit_kw`).

The instrument exists because neither export instrument can do its job. Both
`_apply_export_limit` (kW of export) and `_apply_export_cap` (kWh/day of export)
bound `generated - consumed`, so a premises that self-consumes its output is
invisible to both no matter how much it generates. A consumer that screens the
RAW generation reading therefore sees a number they cannot influence — which is
exactly what GridTokenX's oracle does, bounding `energy_produced` and
`energy_consumed` independently at the connection limit.

The self-consuming case below is the one that matters: it passes an export limit
of zero and is still clipped.
"""

from types import SimpleNamespace

import pytest

from smart_meter_simulator.core.engine import SimulationEngine


INTERVAL = 900  # seconds; the 15-minute tick the bench datasets use


def _reading(generated: float, consumed: float) -> SimpleNamespace:
    return SimpleNamespace(
        energy_generated=generated,
        energy_consumed=consumed,
        surplus_energy=max(0.0, generated - consumed),
        deficit_energy=max(0.0, consumed - generated),
    )


def _engine(limit_kw: float) -> SimpleNamespace:
    """Minimal stand-in: the method touches only these two attributes."""
    return SimpleNamespace(
        generation_limit_kw=limit_kw,
        generation_limit_curtailed_kwh=0.0,
    )


def _apply(limit_kw: float, readings):
    eng = _engine(limit_kw)
    clipped = SimulationEngine._apply_generation_limit(eng, readings, INTERVAL)
    return eng, clipped


def test_disabled_by_default_is_a_no_op():
    r = _reading(generated=99.0, consumed=0.0)
    eng, clipped = _apply(0.0, [r])
    assert clipped == 0.0
    assert r.energy_generated == 99.0
    assert eng.generation_limit_curtailed_kwh == 0.0


def test_generation_under_the_cap_is_untouched():
    # 10 kW over a 900 s tick == 2.5 kWh.
    r = _reading(generated=2.0, consumed=0.5)
    _, clipped = _apply(10.0, [r])
    assert clipped == 0.0
    assert r.energy_generated == 2.0
    assert r.surplus_energy == 1.5


def test_generation_above_the_cap_is_clipped_to_it():
    # A 13.8 kW array on a 10 kW inverter: 3.45 kWh offered, 2.5 kWh allowed.
    r = _reading(generated=3.45, consumed=1.25)
    eng, clipped = _apply(10.0, [r])
    assert r.energy_generated == 2.5
    # approx, not equality: 3.45 - 2.5 is 0.9500000000000002 in binary floating
    # point. The clipped VALUE is what matters and it is exact; the difference is
    # not.
    assert clipped == pytest.approx(0.95)
    assert eng.generation_limit_curtailed_kwh == pytest.approx(0.95)


def test_a_self_consuming_meter_is_still_clipped():
    """The case no export instrument can reach.

    Generation exactly equals consumption, so export is zero and an export limit
    — even one of 0 kW — has nothing to act on. The generation READING is still
    4 kWh (16 kW), which a raw-reading screen rejects. This is the whole reason
    the instrument is separate.
    """
    r = _reading(generated=4.0, consumed=4.0)
    assert r.surplus_energy == 0.0  # nothing to export, before or after
    _, clipped = _apply(10.0, [r])
    assert r.energy_generated == 2.5
    assert clipped == 1.5
    assert r.surplus_energy == 0.0
    assert r.deficit_energy == 1.5  # now importing, which is physically right


def test_derived_fields_stay_consistent():
    r = _reading(generated=5.0, consumed=1.0)
    _apply(10.0, [r])
    assert r.surplus_energy == max(0.0, r.energy_generated - r.energy_consumed)
    assert r.deficit_energy == max(0.0, r.energy_consumed - r.energy_generated)


def test_clipping_tallies_across_meters_and_ticks():
    eng = _engine(10.0)
    for _ in range(2):
        readings = [_reading(3.5, 0.0), _reading(2.0, 0.0), _reading(4.5, 0.0)]
        SimulationEngine._apply_generation_limit(eng, readings, INTERVAL)
    # per tick: (3.5-2.5) + 0 + (4.5-2.5) = 3.0
    assert eng.generation_limit_curtailed_kwh == 6.0


def test_cap_scales_with_the_interval():
    """A kW limit is only a kWh limit once an interval is fixed."""
    r_short = _reading(generated=1.0, consumed=0.0)
    SimulationEngine._apply_generation_limit(_engine(10.0), [r_short], 60)
    assert r_short.energy_generated == pytest.approx(1.0 / 6.0)  # 10 kW * 60 s

    r_long = _reading(generated=1.0, consumed=0.0)
    SimulationEngine._apply_generation_limit(_engine(10.0), [r_long], 3600)
    assert r_long.energy_generated == 1.0  # 10 kW * 1 h == 10 kWh, no clipping
