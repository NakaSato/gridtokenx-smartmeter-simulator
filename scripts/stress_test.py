import asyncio
import logging
import aiohttp
from datetime import datetime, timezone
import uuid

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("stress_test")

API_URL = "http://localhost:4000/api/meters/submit-reading"
API_KEY = "bf3a948c96147b7460f0a5073f1ec6774cc0761f19a74c94b97867de8a4564ab"  # From .env

async def send_reading(kwh: float, serial: str):
    payload = {
        "kwh_amount": kwh,
        "wallet_address": "8qH9z2...test_wallet", # Mock address
        "reading_timestamp": datetime.now(timezone.utc).isoformat(),
        "meter_serial": serial,
        "energy_generated": kwh if kwh > 0 else 0,
        "energy_consumed": abs(kwh) if kwh < 0 else 0,
        "voltage": 230.0,
        "current": abs(kwh) / 230.0
    }
    
    headers = {"Authorization": f"Bearer {API_KEY}"}
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(API_URL, json=payload, headers=headers) as response:
                status = response.status
                body = await response.text()
                if status == 200:
                    logger.info(f"SUCCESS: {kwh} kWh reading accepted.")
                elif status == 400:
                    logger.warning(f"REJECTED: {kwh} kWh reading (Limit check working). Body: {body}")
                else:
                    logger.error(f"ERROR: {kwh} kWh reading failed with status {status}. Body: {body}")
                return status, body
        except Exception as e:
            logger.error(f"FAILED to connect to API Gateway: {e}")
            return None, str(e)

async def run_stress_test():
    logger.info("Starting API Gateway kWh limit stress test...")
    
    # Test 1: Valid high reading (450 kWh)
    logger.info("Test 1: Sending 450 kWh (should be accepted)...")
    await send_reading(450.0, "STRESS_001")
    
    # Test 2: Over limit reading (550 kWh)
    logger.info("Test 2: Sending 550 kWh (should be rejected)...")
    await send_reading(550.0, "STRESS_002")
    
    # Test 3: Edge case (500 kWh)
    logger.info("Test 3: Sending 500 kWh (boundary test)...")
    await send_reading(500.0, "STRESS_003")

if __name__ == "__main__":
    asyncio.run(run_stress_test())
