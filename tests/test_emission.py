import asyncio
from smart_meter_simulator.core.meter import SmartMeter
from smart_meter_simulator.models.reading import EnergyReading
from datetime import datetime


async def test_emission_calculation():
    print("Testing Emission Calculation...")

    # 1. Setup Meter
    config = {
        "meter_id": "test-meter-emission",
        "meter_type": "Solar_Prosumer",
        "location": "Test Location",
        "has_solar": True,
        "solar_capacity": 5.0,
        "user_type": "Prosumer",
    }
    meter = SmartMeter(config)

    # 2. Generate Reading
    # We need to mock internal methods or just check if net_emission is present and calculated
    # Let's use a static data override to control inputs for precise calculation check
    meter.static_data = {
        "energy_generated": 10.0,
        "energy_consumed": 5.0,
        "voltage": 240.0,
        "current": 10.0,
        "frequency": 50.0,
        "temperature": 25.0,
        "power_factor": 1.0,
    }

    reading = meter.generate_reading(datetime.now())

    # 3. Verify Calculation
    # Formula: (consumed * 0.5) - (generated * (0.5 - 0.05))
    # Expected: (5.0 * 0.5) - (10.0 * 0.45)
    # Expected: 2.5 - 4.5 = -2.0

    expected_emission = (5.0 * 0.5) - (10.0 * (0.5 - 0.05))
    print(f"Generated: {reading.energy_generated}, Consumed: {reading.energy_consumed}")
    print(f"Net Emission: {reading.net_emission}, Expected: {expected_emission}")

    assert abs(reading.net_emission - expected_emission) < 0.001
    print("Emission calculation correct.")

    # 4. Verify Connection Status Field
    # This is set in Engine, but we can check if the attribute exists on meter
    assert (
        hasattr(meter, "is_connected") is False
    )  # Default should be False or unset until engine runs

    print("Emission and Status test passed.")


if __name__ == "__main__":
    asyncio.run(test_emission_calculation())
