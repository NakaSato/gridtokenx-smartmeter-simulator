"""Reading-field population regression tests."""

from datetime import datetime, timezone

from smart_meter_simulator.devices.ami import SmartMeter


def _meter() -> SmartMeter:
    return SmartMeter(
        {
            "meter_id": "VPU-1",
            "meter_type": "Grid_Consumer",
            "user_type": "residential",
            "location": "bus-1",
            "has_solar": False,
            "base_consumption": 1.0,
        }
    )


def test_reading_carries_bus_voltage_pu():
    meter = _meter()
    reading = meter.generate_reading(
        datetime(2026, 6, 7, 12, 0, tzinfo=timezone.utc),
        interval_seconds=900,
        grid_voltage_pu=0.973,
    )
    # voltage_pu must be populated (was silently None before), so a persisted
    # run carries per-meter voltage for replay.
    assert reading.voltage_pu == 0.973
