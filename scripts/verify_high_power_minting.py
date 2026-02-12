import asyncio
import logging
from datetime import datetime, timezone
from smart_meter_simulator.core.meter import SmartMeter
from smart_meter_simulator.models.reading import EnergyReading
from smart_meter_simulator.transport.http import HttpTransport
from smart_meter_simulator.config import SimulatorConfig

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def verify_high_power_minting():
    # 1. Configuration for High Power
    # We want > 1kWh in 15s. 
    # Power = 240kW -> 1kWh/15s.
    # Let's use 500kW to be safe (> 2kWh/15s).
    meter_config = {
        "meter_id": "TEST-HIGH-POWER-001",
        "meter_type": "Solar_Prosumer",
        "location": "Test_Lab",
        "has_solar": True,
        "solar_capacity": 1000.0, # 1MW capacity
        "panel_efficiency": 1.0,  # Max efficiency
        "wallet_address": "8S2e2p4ghqMJuzTz5AkAKSka7jqsjgBH7eWDcCHzXPND", # Use a known dev wallet
        "channels": ["v", "p", "q"],
        "user_type": "Prosumer"
    }
    
    meter = SmartMeter(meter_config)
    interval = 15 # 15 seconds
    
    logger.info(f"--- Phase 20 Verification: High-Power Minting ---")
    logger.info(f"Target: > 1kWh in {interval}s")
    
    # 2. Generate Reading
    # Noon (Sun at zenith)
    test_time = datetime(2025, 6, 21, 12, 0, 0, tzinfo=timezone.utc)
    
    # Force noon sunny weather for max generation
    meter.current_weather = "Sunny"
    
    # Generate reading with 15s interval
    reading = meter.generate_reading(test_time, interval_seconds=interval)
    
    logger.info(f"Generated Reading:")
    logger.info(f"  Energy Generated: {reading.energy_generated} kWh")
    logger.info(f"  Surplus Energy: {reading.surplus_energy} kWh")
    logger.info(f"  Interval: {reading.interval_seconds}s")
    
    # Power calculation verification
    payload = reading.to_submission_payload()
    logger.info(f"Submission Payload:")
    logger.info(f"  Power Generated (calc): {payload['power_generated']} kW")
    logger.info(f"  kwh (minting): {payload['kwh']} kWh")
    
    assert reading.energy_generated > 1.0, f"Energy generated {reading.energy_generated} should be > 1.0 kWh"
    assert payload['power_generated'] > 240.0, f"Power {payload['power_generated']} should be > 240 kW"
    
    logger.info("✅ Core Logic Verified: High power correctly scaled to kWh in short interval.")
    
    # 3. Test Submission (Optional, depends on gateway status)
    transport = HttpTransport()
    try:
        logger.info("Testing submission to API Gateway...")
        success = await transport.send_reading(reading)
        if success:
            logger.info("✅ API Gateway accepted high-kWh reading!")
        else:
            logger.warning("❌ API Gateway rejected reading or is unreachable.")
    except Exception as e:
        logger.error(f"Error during submission: {e}")
    finally:
        await transport.disconnect()

if __name__ == "__main__":
    asyncio.run(verify_high_power_minting())
