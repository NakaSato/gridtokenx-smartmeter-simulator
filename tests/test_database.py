import asyncio
import os
import sqlite3
import json
from smart_meter_simulator.core.database import DatabaseManager
from smart_meter_simulator.core.meter import SmartMeter
from smart_meter_simulator.models.reading import EnergyReading
from datetime import datetime

DB_PATH = "test_smart_meter.db"


async def test_database_persistence():
    print("Testing Database Persistence...")

    # Cleanup previous test
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    # 1. Initialize Database
    db = DatabaseManager(DB_PATH)

    # 2. Test Save Meter
    meter_config = {
        "meter_id": "test-meter-db",
        "meter_type": "Solar_Prosumer",
        "location": "Test DB Location",
        "latitude": 13.7563,
        "longitude": 100.5018,
    }
    db.save_meter(meter_config)

    # Verify meter saved
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM meters WHERE meter_id=?", ("test-meter-db",))
        row = cursor.fetchone()
        assert row is not None
        assert row[0] == "test-meter-db"
        assert row[3] == 13.7563  # latitude
        print("Meter saved successfully.")

    # 3. Test Save Reading
    reading = EnergyReading(
        meter_id="test-meter-db",
        timestamp=datetime.now(),
        energy_generated=10.5,
        energy_consumed=5.2,
        battery_level=85.0,
        temperature=30.0,
        voltage=240.0,
        current=5.0,
        frequency=50.0,
        surplus_energy=5.3,
        deficit_energy=0.0,
        meter_type="Solar_Prosumer",
        user_type="Prosumer",
        location="Test DB Location",
    )
    # Manually add weather_condition as it might be dynamic
    reading.weather_condition = "Sunny"

    db.save_reading(reading)

    # Verify reading saved
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM readings WHERE meter_id=?", ("test-meter-db",))
        row = cursor.fetchone()
        assert row is not None
        assert row[1] == "test-meter-db"
        assert row[3] == 10.5  # energy_generated
        print("Reading saved successfully.")

    # 4. Test Delete Meter
    db.delete_meter("test-meter-db")

    # Verify deletion
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM meters WHERE meter_id=?", ("test-meter-db",))
        assert cursor.fetchone() is None

        cursor.execute("SELECT * FROM readings WHERE meter_id=?", ("test-meter-db",))
        assert cursor.fetchone() is None
        print("Meter and readings deleted successfully.")

    # Cleanup
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    print("Database Persistence test passed.")


if __name__ == "__main__":
    asyncio.run(test_database_persistence())
