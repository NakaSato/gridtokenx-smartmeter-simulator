"""BESS battery device + SmartMeter integration tests.

Dispatch energy accounting (charge/discharge limits, round-trip efficiency, SoC
bounds) is checked on the pure :class:`Battery`; integration confirms a metered
site with a battery emits SoC/power on its reading and one without does not.
"""

from datetime import datetime, timezone
from math import sqrt

from smart_meter_simulator.config import get_config
from smart_meter_simulator.devices.ami import SmartMeter
from smart_meter_simulator.devices.battery import Battery

# Per-meter overrides pin capacity/C-rate; efficiency, min- and initial-SoC come
# from global config defaults (round-trip 0.90, min 0.10, initial 0.50).
_OVERRIDES = {
    "battery_capacity_kwh": 100.0,
    "battery_max_charge_kw": 5.0,
    "battery_max_discharge_kw": 5.0,
}


def _battery() -> Battery:
    return Battery(dict(_OVERRIDES))


def _leg_eff() -> float:
    return sqrt(get_config().battery_round_trip_efficiency)


def test_initial_soc_from_config():
    b = _battery()
    cfg = get_config()
    assert b.soc_kwh == 100.0 * cfg.battery_initial_soc_frac
    assert b.min_soc_kwh == 100.0 * cfg.battery_min_soc_frac


def test_charge_limited_by_c_rate_and_efficiency():
    b = _battery()
    start = b.soc_kwh
    charge_kw, discharge_kw = b.dispatch(net_kw=50.0, time_factor=1.0)
    assert discharge_kw == 0.0
    assert charge_kw == 5.0  # capped by max_charge_kw, surplus/room ample
    # cells receive eff_charge of the drawn energy
    assert b.soc_kwh == start + 5.0 * 1.0 * _leg_eff()


def test_discharge_limited_by_c_rate_and_efficiency():
    b = _battery()
    start = b.soc_kwh
    charge_kw, discharge_kw = b.dispatch(net_kw=-50.0, time_factor=1.0)
    assert charge_kw == 0.0
    assert discharge_kw == 5.0  # capped by max_discharge_kw, energy ample
    # delivering 5 kW draws 5/eff from the cells
    assert b.soc_kwh == start - 5.0 * 1.0 / _leg_eff()


def test_no_overcharge_past_capacity():
    b = _battery()
    b.soc_kwh = b.capacity_kwh - 0.5  # nearly full
    charge_kw, _ = b.dispatch(net_kw=50.0, time_factor=1.0)
    # room is only 0.5 kWh of cell storage -> accept << C-rate
    assert 0.0 < charge_kw < 5.0
    assert b.soc_kwh <= b.capacity_kwh + 1e-9


def test_discharge_floored_at_min_soc():
    b = _battery()
    b.soc_kwh = b.min_soc_kwh + 0.5  # nearly empty
    _, discharge_kw = b.dispatch(net_kw=-50.0, time_factor=1.0)
    assert 0.0 < discharge_kw < 5.0
    assert b.soc_kwh >= b.min_soc_kwh - 1e-9


def test_idle_when_balanced():
    b = _battery()
    start = b.soc_kwh
    assert b.dispatch(net_kw=0.0, time_factor=1.0) == (0.0, 0.0)
    assert b.soc_kwh == start


def test_zero_time_factor_is_noop():
    b = _battery()
    start = b.soc_kwh
    assert b.dispatch(net_kw=50.0, time_factor=0.0) == (0.0, 0.0)
    assert b.soc_kwh == start


# --- SmartMeter integration ---------------------------------------------------


def _meter_config(has_battery: bool) -> dict:
    return {
        "meter_id": "BAT-1",
        "meter_type": "Hybrid_Prosumer",
        "user_type": "residential",
        "location": "bus-1",
        "has_solar": False,
        "has_battery": has_battery,
        "base_consumption": 1.0,
        **_OVERRIDES,
    }


def test_meter_with_battery_emits_soc():
    meter = SmartMeter(_meter_config(has_battery=True))
    assert meter.battery is not None
    reading = meter.generate_reading(
        datetime(2026, 6, 7, 12, 0, tzinfo=timezone.utc), interval_seconds=900
    )
    assert reading.battery_soc_kwh is not None
    assert reading.battery_power_kw is not None


def test_meter_without_battery_has_no_battery_fields():
    meter = SmartMeter(_meter_config(has_battery=False))
    assert meter.battery is None
    reading = meter.generate_reading(
        datetime(2026, 6, 7, 12, 0, tzinfo=timezone.utc), interval_seconds=900
    )
    assert reading.battery_soc_kwh is None
    assert reading.battery_power_kw is None
