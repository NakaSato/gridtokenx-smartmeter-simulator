import asyncio
from unittest.mock import MagicMock, AsyncMock
from smart_meter_simulator.core.weather import WeatherSystem
from smart_meter_simulator.core.meter import SmartMeter
from smart_meter_simulator.config import MeterType


async def test_weather_integration():
    print("Testing Weather Integration...")

    # 1. Test WeatherSystem with mocked Service
    weather_system = WeatherSystem()
    weather_system.service.get_weather = AsyncMock(return_value=("Rainy", 28.5))

    condition, irradiance, temp_offset = await weather_system.get_real_weather(
        13.7563, 100.5018
    )

    print(f"Weather System Result: {condition}, {irradiance}, {temp_offset}")

    assert condition == "Rainy"
    assert irradiance == 0.1  # Rainy irradiance
    assert temp_offset == 8.5  # 28.5 - 20.0

    print("WeatherSystem test passed.")

    # 2. Test SmartMeter with GPS
    config = {
        "meter_id": "gps-meter-1",
        "meter_type": MeterType.SOLAR_PROSUMER,
        "location": "Bangkok",
        "user_type": "Residential",
        "has_solar": True,
        "has_battery": True,
        "battery_capacity": 10.0,
        "current_battery_level": 5.0,
        "latitude": 13.7563,
        "longitude": 100.5018,
    }
    meter = SmartMeter(config)

    # Verify GPS stored
    assert meter.latitude == 13.7563
    assert meter.longitude == 100.5018

    # Generate reading
    from datetime import datetime

    reading = meter.generate_reading(datetime.now())

    # Verify reading has GPS
    assert reading.latitude == 13.7563
    assert reading.longitude == 100.5018

    print("SmartMeter GPS test passed.")


if __name__ == "__main__":
    asyncio.run(test_weather_integration())
