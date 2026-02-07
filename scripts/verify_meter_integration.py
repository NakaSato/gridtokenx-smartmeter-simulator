import logging
import sys
import os
from datetime import datetime

# Ensure src is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from smart_meter_simulator.core.meter import SmartMeter, MeterType
from smart_meter_simulator.models.reading import EnergyReading

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("verify_meter_integration")

def run_test():
    logger.info("Testing SmartMeter integration with real ZK proofs...")
    
    config = {
        "meter_id": "TEST_METER_ZK",
        "meter_type": MeterType.SOLAR_PROSUMER,
        "location": "Test_Loc",
        "user_type": "residential",
        "has_solar": True,
        "solar_capacity": 10.0
    }
    
    meter = SmartMeter(config)
    
    # Create a reading with surplus to trigger a bid
    timestamp = datetime.now()
    reading = meter.generate_reading(timestamp, override_gen=50.0, override_cons=10.0)
    # Surplus = 40.0
    
    logger.info(f"Generated reading: Surplus={reading.surplus_energy}")
    
    bid = meter.generate_confidential_bid(reading)
    
    if bid:
        logger.info("Bid generated successfully.")
        logger.info(f"Encrypted Amount: {bid['encrypted_amount']}")
        logger.info(f"Encrypted Price: {bid['encrypted_price']}")
        logger.info(f"Range Proof: {bid.get('range_proof', 'MISSING')[:20]}...")
        
        # Check if it looks like a real proof (Base64 of 64 bytes)
        import base64
        try:
            amt_bytes = base64.b64decode(bid['encrypted_amount'])
            price_bytes = base64.b64decode(bid['encrypted_price'])
            proof_bytes = base64.b64decode(bid['range_proof'])
            
            if len(amt_bytes) == 64 and len(price_bytes) == 64 and len(proof_bytes) > 0:
                logger.info("SUCCESS: Bid contains valid 64-byte ciphertexts and range proof.")
                logger.info(f"Range Proof Size: {len(proof_bytes)} bytes")
            else:
                logger.warning(f"Ciphertext/Proof lengths: Amount={len(amt_bytes)}, Price={len(price_bytes)}, Proof={len(proof_bytes)}")
                
        except Exception as e:
            logger.error(f"Failed to decode base64: {e}")
            
    else:
        logger.error("Failed to generate bid.")

if __name__ == "__main__":
    run_test()
