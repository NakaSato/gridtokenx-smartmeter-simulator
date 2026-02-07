import asyncio
import logging
from datetime import datetime, timezone
import numpy as np

# Mocking parts of the system if not running in the full environment
from meter.core.engine import SimulationEngine, SimulationMode
from meter.core.meter import SmartMeter
from meter.transport.base import TransportLayer
from meter.adapters.pandapower_adapter import PandapowerAdapter
from meter.config import MeterType

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("verify_pseudo")

class MockTransport(TransportLayer):
    async def connect(self): return True
    async def disconnect(self): return True
    async def send_reading(self, reading): 
        logger.info(f"Reading sent: {reading.meter_id} - {reading.energy_consumed} kWh")
        return True
    async def send_grid_status(self, status):
        logger.info(f"Grid status: {status}")
        return True
    async def send_auction_bid(self, bid, batch_id): return True
    
    async def send_batch(self, readings):
        for r in readings:
            await self.send_reading(r)
        return True
    
    def is_connected(self) -> bool:
        return True

async def run_verification():
    # 1. Setup meters - Create only a few to leave unobserved buses
    # We'll rely on the PandapowerAdapter to build a network that has more buses than meters
    meter_configs = [
        {
            "meter_id": "METER_001",
            "meter_type": MeterType.GRID_CONSUMER,
            "location": "Bus_1",
            "user_type": "residential",
            "has_solar": False
        },
        {
            "meter_id": "METER_002",
            "meter_type": MeterType.SOLAR_PROSUMER,
            "location": "Bus_2",
            "user_type": "residential",
            "has_solar": True,
            "solar_capacity": 5.0
        }
    ]
    
    meters = [SmartMeter(cfg) for cfg in meter_configs]
    transport = MockTransport()
    adapter = PandapowerAdapter()
    
    engine = SimulationEngine(meters, transport, adapter)
    engine.real_time_interval = 1 # Speed up for test
    
    logger.info("Starting verification simulation...")
    
    # Manually trigger start logic enough to init network
    await transport.connect()
    
    # The engine normally builds the network from meters. 
    # Let's verify how build_network_from_meters behaves.
    # We want to ensure it creates a net with unobserved buses.
    
    # For this verification, we might need to manually inject a net or 
    # mock the adapter to return a net with more buses.
    
    # Actually, let's just run a tick and check logs.
    # The engine._inject_pseudo_measurements() logic should trigger.
    
    try:
        # Initialize network
        engine.net, engine.meter_to_bus = adapter.build_network_from_meters(meters)
        
        # Add a manual bus to ensure unobserved buses exist
        import pandapower as pp
        new_bus = pp.create_bus(engine.net, vn_kv=0.4, name="Unobserved_Bus")
        # Connect it with a line so it's part of the topology
        pp.create_line(engine.net, from_bus=0, to_bus=new_bus, length_km=0.1, std_type="NAYY 4x50 SE")
        
        logger.info(f"Network initialized with {len(engine.net.bus)} buses. Meters mapped to {len(engine.meter_to_bus)} buses.")
        
        # Run one tick
        await engine.tick()
        
        # Check results
        if engine.last_estimation_results:
            logger.info(f"Estimation Converged: {engine.last_estimation_results.converged}")
            logger.info(f"Mean Absolute Error: {engine.last_estimation_results.mean_absolute_error}")
            
            if engine.last_estimation_results.converged:
                print("SUCCESS: Pseudo-measurement injection verified and estimation converged.")
            else:
                print("FAILURE: Estimation failed to converge even with pseudo-measurements.")
        else:
            print("FAILURE: No estimation results found.")
            
    except Exception as e:
        logger.error(f"Verification failed with error: {e}", exc_info=True)
    finally:
        await transport.disconnect()

if __name__ == "__main__":
    asyncio.run(run_verification())
