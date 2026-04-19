"""
Test script for Island Hub Bottleneck Scenario
"""
import asyncio
import logging
from datetime import datetime
from smart_meter_simulator.core.engine import SimulationEngine
from smart_meter_simulator.core.meter import SmartMeter
from smart_meter_simulator.meter_generator import MeterGenerator
from smart_meter_simulator.adapters.pandapower_adapter import PandapowerAdapter
from smart_meter_simulator.transport.http import HttpTransport
from smart_meter_simulator.config import get_config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    config = get_config()
    # Force use the islands locations
    config.locations_file = "initial_locations_islands.json"
    
    logger.info(f"Initializing engine with {config.initial_locations_file}...")
    
    generator = MeterGenerator(config.num_meters)
    meters = [SmartMeter(c) for c in generator.generate_meters()]
    
    adapter = PandapowerAdapter()
    engine = SimulationEngine(meters, HttpTransport(), adapter=adapter)
    engine.playback_profile = "island_hub_peak_scenario"
    
    # Start engine (initializes topology)
    await engine.start()
    
    # Simulate a few ticks to reach a peak
    # The profile starts at 00:00. Peak is around noon.
    # We can jump to tick 48 (12:00)
    logger.info("Jumping to noon peak...")
    engine.current_sim_time = datetime(2024, 4, 22, 12, 0)
    
    await engine.tick()
    
    # Check if BESS received dispatch
    bess = next((m for m in engine.meters if m.meter_id == "SAMUI-BESS-01"), None)
    if bess:
        logger.info(f"BESS Dispatch after Tick 1: {bess.vpp_dispatch_kw:.2f} kW")
        
    logger.info("Running Tick 2 to see effect...")
    await engine.tick()
    
    if engine.net is not None:
        logger.info("Line Loadings:")
        for idx, line in engine.net.line.iterrows():
            loading = engine.net.res_line.loading_percent.at[idx]
            logger.info(f"- {line['name']}: {loading:.2f}%")
    
    logger.info("Test complete.")

if __name__ == "__main__":
    asyncio.run(main())
