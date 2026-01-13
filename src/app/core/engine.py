import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import List

from .meter import SmartMeter
from .weather import WeatherSystem
from .market import MarketSystem
from ..transport.base import TransportLayer
from ..models.reading import EnergyReading
from ..services.zoning_service import MicrogridZoningService

from .database import DatabaseManager

logger = logging.getLogger(__name__)


class SimulationEngine:
    """
    Orchestrates the simulation of multiple smart meters.
    """
    
    # Batch transfer settings for efficient API Gateway communication
    BATCH_SIZE = 50  # Readings per batch (266 meters = ~6 batches)
    MAX_CONCURRENT = 5  # Max parallel batch/individual requests
    USE_BATCH_MODE = True  # True=batch, False=rate-limited individual

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
        self.interval = 60  # 1 minute (Accelerated for real-time visualization)
        self.real_time_interval = 15  # 15 seconds real time between ticks
        # Start at current time to avoid future timestamp issues
        now = datetime.now(timezone.utc)
        self.current_sim_time = now
        
        # Time offset for testing (e.g., +6 hours to simulate daytime at night)
        self.time_offset_hours = 0
        
        print(
            f"DEBUG: SimulationEngine initialized with start time: {self.current_sim_time}"
        )

        # Initialize Systems
        self.weather_system = WeatherSystem()
        self.market_system = MarketSystem()

        # Track totals for market logic
        self.last_total_gen = 100.0  # Initial dummy values
        self.last_total_cons = 100.0

        # Initialize Microgrid Zoning Service
        # UTCC now has 3 main transformers (Custom 21-Meter Grid)
        self.zoning_service = MicrogridZoningService(num_zones=3, random_state=42)
        self._assign_zones()

        # Save initial meter configs if DB is present
        if self.db_manager:
            for meter in self.meters:
                self.db_manager.save_meter(meter.config)
    
    def _assign_zones(self):
        """
        Cluster meters into microgrid zones based on GPS coordinates.
        Uses K-Means clustering to simulate transformer service areas.
        """
        # Filter meters with valid GPS coordinates
        valid_meters = [
            m for m in self.meters 
            if m.latitude is not None and m.longitude is not None
        ]
        
        if not valid_meters:
            logger.warning("No meters with GPS coordinates for zone assignment")
            return
        
        coordinates = [(m.latitude, m.longitude) for m in valid_meters]
        zone_ids = self.zoning_service.fit(coordinates)
        
        # Assign zone IDs to meters
        for meter, zone_id in zip(valid_meters, zone_ids):
            meter.grid_zone_id = zone_id
        
        # Log zone summary
        zone_summary = self.zoning_service.get_zone_summary()
        logger.info(f"Assigned {len(valid_meters)} meters to {len(zone_summary)} zones")
        for zone_id, info in zone_summary.items():
            logger.info(f"  Zone {zone_id} ({info.transformer_name}): {info.meter_count} meters")

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
        """Execute one simulation step with performance optimizations."""
        import time
        tick_start = time.perf_counter()
        
        # Use the managed current_sim_time instead of calculating from now()
        timestamp = self.current_sim_time

        # 1. Update Global Weather (fallback)
        current_weather = self.weather_system.update()
        global_irradiance, global_temp_offset = self.weather_system.get_factors()

        # 2. Fetch zone weather concurrently (5 zones = 5 API calls instead of 266)
        weather_start = time.perf_counter()
        zone_weather = await self._fetch_zone_weather()
        weather_elapsed = time.perf_counter() - weather_start

        # 3. Update Market Prices (based on previous tick's totals)
        sell_price, buy_price = self.market_system.update(
            self.last_total_gen, self.last_total_cons
        )

        # 4. Generate readings with zone-based weather
        readings: List[EnergyReading] = []
        current_tick_gen = 0.0
        current_tick_cons = 0.0

        for meter in self.meters:
            # Use zone weather if available, otherwise global
            if meter.grid_zone_id is not None and meter.grid_zone_id in zone_weather:
                condition, irradiance, temp_offset = zone_weather[meter.grid_zone_id]
                meter.update_weather(condition, irradiance, temp_offset)
            else:
                meter.update_weather(current_weather, global_irradiance, global_temp_offset)

            meter.update_prices(sell_price, buy_price)
            reading = meter.generate_reading(timestamp)
            readings.append(reading)

            current_tick_gen += reading.energy_generated
            current_tick_cons += reading.energy_consumed

        # 5. Batch save to DB (single transaction)
        if self.db_manager:
            db_start = time.perf_counter()
            self.db_manager.save_readings_batch(readings)
            db_elapsed = time.perf_counter() - db_start
        else:
            db_elapsed = 0

        # Update totals for next tick's market calculation
        self.last_total_gen = current_tick_gen
        self.last_total_cons = current_tick_cons

        # 6. Send readings (optimized for 266+ meters)
        send_start = time.perf_counter()
        if self.USE_BATCH_MODE:
            success_count, failed_meters = await self._send_readings_batched(readings)
        else:
            success_count, failed_meters = await self._send_readings_concurrent(readings)
        send_elapsed = time.perf_counter() - send_start

        # Update meter connection status
        for meter in self.meters:
            meter.is_connected = meter.meter_id not in failed_meters

        tick_elapsed = time.perf_counter() - tick_start
        logger.info(
            f"Tick: {len(readings)} readings in {tick_elapsed:.2f}s | "
            f"Weather: {weather_elapsed:.2f}s, DB: {db_elapsed:.2f}s, Send: {send_elapsed:.2f}s | "
            f"{current_weather} THB {sell_price:.2f}/THB {buy_price:.2f}"
        )

    async def _fetch_zone_weather(self) -> dict:
        """
        Fetch weather for each zone's centroid concurrently.
        Returns dict: {zone_id: (condition, irradiance, temp_offset)}
        """
        zone_summary = self.zoning_service.get_zone_summary()
        if not zone_summary:
            return {}
        
        async def fetch_zone(zone_id, info):
            try:
                condition, irradiance, temp_offset = await self.weather_system.get_real_weather(
                    info.centroid_lat, info.centroid_lon
                )
                return zone_id, (condition, irradiance, temp_offset)
            except Exception as e:
                logger.warning(f"Zone {zone_id} weather fetch failed: {e}")
                return zone_id, None
        
        results = await asyncio.gather(
            *[fetch_zone(zid, info) for zid, info in zone_summary.items()],
            return_exceptions=True
        )
        
        zone_weather = {}
        for result in results:
            if isinstance(result, Exception):
                continue
            zone_id, weather_data = result
            if weather_data:
                zone_weather[zone_id] = weather_data
        
        return zone_weather

    async def _send_readings_batched(self, readings: List[EnergyReading]) -> tuple:
        """
        Send readings in batches with concurrency control.
        Optimal for large meter counts (266+).
        
        Returns:
            tuple: (success_count, set of failed meter IDs)
        """
        from typing import Set
        
        # Split into batches
        batches = [readings[i:i + self.BATCH_SIZE] 
                   for i in range(0, len(readings), self.BATCH_SIZE)]
        
        semaphore = asyncio.Semaphore(self.MAX_CONCURRENT)
        failed_meters: Set[str] = set()
        success_count = 0
        
        async def send_batch_with_limit(batch: List[EnergyReading], batch_idx: int):
            nonlocal success_count
            async with semaphore:
                try:
                    result = await self.transport.send_batch(batch)
                    if result:
                        logger.debug(f"Batch {batch_idx+1}/{len(batches)} sent ({len(batch)} readings)")
                        return batch, True
                    else:
                        return batch, False
                except Exception as e:
                    logger.error(f"Batch {batch_idx+1} failed: {e}")
                    return batch, False
        
        # Send all batches concurrently (limited by semaphore)
        results = await asyncio.gather(
            *[send_batch_with_limit(batch, i) for i, batch in enumerate(batches)],
            return_exceptions=True
        )
        
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Batch exception: {result}")
                continue
            batch, success = result
            if success:
                success_count += len(batch)
            else:
                for reading in batch:
                    failed_meters.add(reading.meter_id)
        
        logger.info(f"Batch transfer complete: {len(batches)} batches, {success_count} readings sent")
        return success_count, failed_meters

    async def _send_readings_concurrent(self, readings: List[EnergyReading]) -> tuple:
        """
        Send readings individually with rate limiting.
        Fallback when batch endpoint is unavailable.
        
        Returns:
            tuple: (success_count, set of failed meter IDs)
        """
        from typing import Set
        
        # Allow more concurrent requests for individual mode
        max_concurrent = self.MAX_CONCURRENT * 10  # 50 concurrent
        semaphore = asyncio.Semaphore(max_concurrent)
        failed_meters: Set[str] = set()
        success_count = 0
        
        async def send_with_limit(reading: EnergyReading):
            nonlocal success_count
            async with semaphore:
                try:
                    result = await self.transport.send_reading(reading)
                    if result:
                        return reading.meter_id, True
                    return reading.meter_id, False
                except Exception as e:
                    logger.error(f"Send failed for {reading.meter_id}: {e}")
                    return reading.meter_id, False
        
        results = await asyncio.gather(
            *[send_with_limit(r) for r in readings],
            return_exceptions=True
        )
        
        for result in results:
            if isinstance(result, Exception):
                continue
            meter_id, success = result
            if success:
                success_count += 1
            else:
                failed_meters.add(meter_id)
        
        return success_count, failed_meters

