"""Influx write-side point builders: readings + grid_state + carbon + bill.

No live broker — the builders are pure and asserted via line protocol.
"""

from __future__ import annotations

from datetime import datetime, timezone

from smart_meter_simulator.models.reading import EnergyReading
from smart_meter_simulator.persistence.influx_store import InfluxReadingStore

TS = datetime(2026, 6, 10, 8, 0, 0, tzinfo=timezone.utc)


def _store() -> InfluxReadingStore:
    return InfluxReadingStore(
        "http://localhost:8086",
        "tok",
        "org",
        "bucket",
        carbon_factors=(0.5, 0.04, 20.0),
        tariff_params=(0.3672, 0.07, 2.20),
    )


def _reading() -> EnergyReading:
    return EnergyReading(
        meter_id="m1",
        timestamp=TS,
        energy_generated=1.0,
        energy_consumed=2.0,
        surplus_energy=0.0,
        deficit_energy=1.0,
        interval_seconds=15,
        voltage=230.0,
        temperature=31.5,
        location="loc",
        meter_type="Solar_Prosumer",
        user_type="residential",
    )


def test_reading_point_includes_temperature_and_interval():
    lp = _store()._point(_reading(), "run-1").to_line_protocol()
    assert lp.startswith("meter_reading,")
    assert "temperature=31.5" in lp
    assert "interval_seconds=15i" in lp
    assert "sequence_number=0i" in lp
    assert "voltage=230" in lp


def test_grid_point_lifts_numeric_fields_and_weather_tag():
    summary = {
        "weather": "Cloudy",
        "total_losses_kw": 3.2,
        "transformer_tap_pos": -1,
        "frequency_hz": 49.98,
        "timestamp": "ignored-non-numeric",
        "reading_count": 80,
    }
    point = _store()._grid_point(summary, "run-1", TS)
    lp = point.to_line_protocol()
    assert lp.startswith("grid_state,")
    assert "weather=Cloudy" in lp
    assert "total_losses_kw=3.2" in lp
    assert "frequency_hz=49.98" in lp
    assert "timestamp" not in lp  # non-numeric skipped


def test_grid_point_none_when_no_numeric_fields():
    assert _store()._grid_point({"weather": "Sunny"}, "run-1", TS) is None


def test_derived_points_emit_carbon_and_bill():
    states = [("m1", "Solar_Prosumer", 200.0, 50.0, 120.0, 80.0)]
    points = _store()._derived_points(states, "run-1", TS)
    measurements = {p.to_line_protocol().split(",")[0] for p in points}
    assert measurements == {"meter_carbon", "meter_bill"}
    carbon_lp = next(
        p.to_line_protocol() for p in points if p.to_line_protocol().startswith("meter_carbon")
    )
    assert "net_emissions_kg=" in carbon_lp
    assert "offset_kg=" in carbon_lp


def test_derived_points_skipped_when_factors_absent():
    store = InfluxReadingStore("http://localhost:8086", "t", "o", "b")
    states = [("m1", "x", 10.0, 0.0, 5.0, 5.0)]
    assert store._derived_points(states, "run-1", TS) == []
