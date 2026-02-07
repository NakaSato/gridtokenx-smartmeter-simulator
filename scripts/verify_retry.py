import asyncio
import logging
import aiohttp
from datetime import datetime, timezone
from meter.transport.http import HttpTransport
from meter.models.reading import EnergyReading
from meter.config import MeterType

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("verify_retry")

# Mock the simulator config for API URL
from meter.config import SimulatorConfig
SimulatorConfig.API_GATEWAY_URL = "http://localhost:4000"
SimulatorConfig.SUBMIT_READING_ENDPOINT = "/api/meters/submit-reading"

API_KEY = "bf3a948c96147b7460f0a5073f1ec6774cc0761f19a74c94b97867de8a4564ab"

async def run_retry_verification():
    logger.info("Verifying HTTP Transport Retry Logic...")
    
    transport = HttpTransport(base_url=SimulatorConfig.API_GATEWAY_URL, api_key=API_KEY)
    
    # Create a reading that will be rejected (550 kWh)
    reading = EnergyReading(
        meter_id="RETRY_TEST_001",
        timestamp=datetime.now(timezone.utc),
        energy_generated=550.0, # High value to trigger rejection
        energy_consumed=0.0,
        surplus_energy=550.0,
        deficit_energy=0.0,
        battery_level=0.0,
        location="Test",
        meter_type=MeterType.GRID_CONSUMER,
        user_type="residential",
        wallet_address="8qH9z2...test_wallet"
    )
    
    # Manually inject session to monitor calls (optional, but let's just use logging)
    # Ideally we'd mock aiohttp, but running against real gateway confirms full stack behavior.
    
    start_time = datetime.now()
    success = await transport.send_reading(reading)
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    if not success:
        logger.info(f"Reading correctly failed. Duration: {duration:.2f}s")
        if duration < 1.0:
            print("SUCCESS: Failed immediately without retrying (duration < 1s).")
        else:
            print(f"FAILURE: Duration {duration:.2f}s suggests retries occurred (Expected < 1s).")
    else:
        print("FAILURE: Reading was unexpectedly successful.")

    await transport.disconnect()

if __name__ == "__main__":
    asyncio.run(run_retry_verification())
