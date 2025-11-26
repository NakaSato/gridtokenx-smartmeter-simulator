import asyncio
import logging
from datetime import datetime, timezone
from typing import List, Optional

from .meter import SmartMeter
from ..transport.base import TransportLayer
from ..models.reading import EnergyReading

logger = logging.getLogger(__name__)

class SimulationEngine:
    """
    Orchestrates the simulation of multiple smart meters.
    """
    
    def __init__(self, meters: List[SmartMeter], transport: TransportLayer):
        self.meters = meters
        self.transport = transport
        self.running = False
        self.paused = False
        self.interval = 15 * 60 # 15 minutes in seconds (simulated)
        self.real_time_interval = 5 # Real seconds between ticks
        # Start simulation at noon to ensure solar generation
        self.current_sim_time = datetime.now(timezone.utc).replace(hour=12, minute=0, second=0, microsecond=0)
        
    async def start(self):
        """Start the simulation loop."""
        self.running = True
        logger.info(f"Starting simulation with {len(self.meters)} meters")
        await self.transport.connect()
        
        while self.running:
            # Check if paused
            while self.paused and self.running:
                await asyncio.sleep(1)
            
            if not self.running:
                break
                
            start_time = datetime.now()
            try:
                await self.tick()
                # Advance simulated time
                from datetime import timedelta
                self.current_sim_time += timedelta(seconds=self.interval)
            except Exception as e:
                logger.error(f"Error in simulation tick: {e}")
                
            # Wait for next tick
            elapsed = (datetime.now() - start_time).total_seconds()
            wait_time = max(0, self.real_time_interval - elapsed)
            await asyncio.sleep(wait_time)
            
    async def stop(self):
        """Stop the simulation."""
        self.running = False
        await self.transport.disconnect()
        logger.info("Simulation stopped")
        
    async def tick(self):
        """Execute one simulation step."""
        timestamp = self.current_sim_time
        
        # 1. Generate readings (CPU bound, could be offloaded if heavy)
        readings: List[EnergyReading] = []
        for meter in self.meters:
            # Update weather (simplified global weather for now)
            meter.update_weather("Sunny") 
            readings.append(meter.generate_reading(timestamp))
            
        # 2. Send readings (IO bound)
        # Send concurrently
        tasks = [self.transport.send_reading(reading) for reading in readings]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        success_count = sum(1 for r in results if r is True)
        logger.info(f"Generated {len(readings)} readings. Sent {success_count} successfully at {timestamp}")
