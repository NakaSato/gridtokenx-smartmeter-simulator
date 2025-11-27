import asyncio
from datetime import datetime
from smart_meter_simulator.core.meter import SmartMeter
from smart_meter_simulator.config import MeterType


async def test_static_data_generation():
    # Setup
    config = {
        "meter_id": "test-meter-1",
        "meter_type": MeterType.SOLAR_PROSUMER,
        "location": "Test Location",
        "user_type": "Residential",
        "has_solar": True,
        "has_battery": True,
        "battery_capacity": 10.0,
        "current_battery_level": 5.0,
    }
    meter = SmartMeter(config)

    # Test default dynamic generation
    reading1 = meter.generate_reading(datetime.now())
    assert reading1.meter_id == "test-meter-1"

    # Test static data override
    static_data = {
        "energy_generated": 12.3456,
        "energy_consumed": 5.6789,
        "battery_level": 80.5,
        "voltage": 230.5,
        "current": 10.5,
        "frequency": 50.1,
        "temperature": 30.0,
        "power_factor": 0.95,
        "max_sell_price": 0.15,
        "max_buy_price": 0.30,
    }

    # Inject static data (simulating what app.py does)
    meter.static_data = static_data

    # Generate reading with static data
    reading2 = meter.generate_reading(datetime.now())

    # Verify all fields match static data
    assert reading2.energy_generated == 12.3456
    assert reading2.energy_consumed == 5.6789
    assert reading2.battery_level == 80.5
    assert reading2.voltage == 230.5
    assert reading2.current == 10.5
    assert reading2.frequency == 50.1
    assert reading2.temperature == 30.0
    assert reading2.power_factor == 0.95
    assert reading2.max_sell_price == 0.15
    assert reading2.max_buy_price == 0.30

    # Verify derived values
    assert reading2.surplus_energy == max(0, 12.3456 - 5.6789)
    assert reading2.deficit_energy == max(0, -(12.3456 - 5.6789))

    # Test clearing static data
    delattr(meter, "static_data")
    reading3 = meter.generate_reading(datetime.now())

    # Should be back to dynamic (likely different from static values)
    # Note: It's theoretically possible but unlikely to match exactly 12.3456 randomly
    assert reading3.energy_generated != 12.3456 or reading3.voltage != 230.5


if __name__ == "__main__":
    asyncio.run(test_static_data_generation())
