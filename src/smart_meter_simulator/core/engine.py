import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import List

from .meter import SmartMeter
from .weather import WeatherSystem
from .market import MarketSystem
from ..transport.base import TransportLayer
from ..models.reading import EnergyReading

from .database import DatabaseManager

logger = logging.getLogger(__name__)


class SimulationEngine:
    """
    Orchestrates the simulation of multiple smart meters.
    """

    def __init__(
        self,
        meters: List[SmartMeter],
        transport: TransportLayer,
        db_manager: DatabaseManager = None,
    ):
        self.meters = meters
        self.transport = transport
        self.db_manager = db_manager
        self.running = False
        self.paused = False
        # Simulation settings
        self.interval = 16 * 60  # 16 minutes (to avoid duplicate check window of 15m)
        self.real_time_interval = 15 # 15 seconds real time between ticks
        # Start at current time to avoid future timestamp issues
        now = datetime.now(timezone.utc)
        self.current_sim_time = now
        print(
            f"DEBUG: SimulationEngine initialized with start time: {self.current_sim_time}"
        )

        # Initialize Systems
        self.weather_system = WeatherSystem()
        self.market_system = MarketSystem()

        # Track totals for market logic
        self.last_total_gen = 100.0  # Initial dummy values
        self.last_total_cons = 100.0

        # Save initial meter configs if DB is present
        if self.db_manager:
            for meter in self.meters:
                self.db_manager.save_meter(meter.config)

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
        # Use real time to satisfy API Gateway tolerance
        timestamp = datetime.now(timezone.utc)

        # 1. Update Global Weather
        current_weather = self.weather_system.update()
        irradiance, temp_offset = self.weather_system.get_factors()

        # 2. Update Market Prices (based on previous tick's totals)
        sell_price, buy_price = self.market_system.update(
            self.last_total_gen, self.last_total_cons
        )

        # 3. Generate readings
        readings: List[EnergyReading] = []
        current_tick_gen = 0.0
        current_tick_cons = 0.0

        for meter in self.meters:
            # Update meter environment
            # Check for GPS and Real Weather mode
            # For now, we default to Real Weather if meter has GPS, as per user request
            if (
                hasattr(meter, "latitude")
                and meter.latitude is not None
                and hasattr(meter, "longitude")
                and meter.longitude is not None
            ):
                try:
                    # Fetch specific weather for this meter
                    # Note: This is async, but we are in async tick()
                    # However, we need to be careful about performance if we have many meters.
                    # WeatherService caches, so it should be fine.
                    (
                        condition,
                        irradiance,
                        temp_offset,
                    ) = await self.weather_system.get_real_weather(
                        meter.latitude, meter.longitude
                    )
                    meter.update_weather(condition, irradiance, temp_offset)
                except Exception as e:
                    logger.error(
                        f"Failed to fetch real weather for {meter.meter_id}: {e}"
                    )
                    # Fallback to global weather
                    meter.update_weather(current_weather, irradiance, temp_offset)
            else:
                # Use global simulated weather
                meter.update_weather(current_weather, irradiance, temp_offset)

            meter.update_prices(sell_price, buy_price)

            reading = meter.generate_reading(timestamp)
            readings.append(reading)

            # Save to DB if available
            if self.db_manager:
                self.db_manager.save_reading(reading)

            # Accumulate totals
            current_tick_gen += reading.energy_generated
            current_tick_cons += reading.energy_consumed

        # Update totals for next tick's market calculation
        self.last_total_gen = current_tick_gen
        self.last_total_cons = current_tick_cons

        # 4. Send readings
        tasks = [self.transport.send_reading(reading) for reading in readings]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        success_count = 0
        for i, result in enumerate(results):
            meter = self.meters[i]
            if result is True:
                success_count += 1
                meter.is_connected = True
            else:
                meter.is_connected = False
                logger.warning(f"Failed to send reading for {meter.meter_id}: {result}")

        logger.info(
            f"Generated {len(readings)} readings. Weather: {current_weather}. Prices: ${sell_price:.2f}/${buy_price:.2f}. Sent {success_count}"
        )
