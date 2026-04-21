"""
Simulation Engine for Smart Meter Simulator
Orchestrates the simulation of multiple smart meters with grid integration.
"""

import asyncio
import logging
import json
import os
import uuid
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from ..config import SimulationMode, get_config
from ..transport.base import TransportLayer
from .attacker import FDIAttacker
from .billing import BillingEngine
from .data_source import ProfileDataSource
from .db import DatabaseManager
from .frequency import FrequencyModel
from .island import IslandManager
from .meter import SmartMeter
from .vpp import VPPManager
from .ews import EarlyWarningSystem
from .forecaster import EdgeForecastingEngine
from .optimizer import OptimizationEngine

# New Managers
from .grid_manager import GridManager
from .vpp_handler import VPPHandler
from .reading_manager import ReadingManager
from .event_manager import EventManager
from ..services.telemetry_service import GridTelemetryService
from ..services.analytics_service import GridAnalyticsService

logger = logging.getLogger(__name__)

class SimulationEngine:
    """
    Orchestrates the simulation of multiple smart meters by coordinating
    specialized managers for grid, VPP, reading generation, and events.
    """

    def __init__(
        self,
        meters: List[SmartMeter],
        transport: TransportLayer,
        adapter: Optional[Any] = None,
        db_manager: Optional[DatabaseManager] = None
    ):
        self.meters = meters
        self.transport = transport
        self.db_manager = db_manager
        
        # Core Models
        self.data_source = ProfileDataSource()
        self.vpp_manager = VPPManager()
        self.frequency_model = FrequencyModel()
        self.island_manager = IslandManager()
        self.billing = BillingEngine()
        self.attacker = FDIAttacker()
        self.forecaster = EdgeForecastingEngine("SAMUI-HUB-01")
        self.optimizer = OptimizationEngine()
        self.ews = EarlyWarningSystem()

        # Modular Managers
        self.grid = GridManager(adapter)
        self.vpp_handler = VPPHandler(self.vpp_manager, self.frequency_model, self.island_manager)
        self.reading_manager = ReadingManager(self.data_source)
        self.event_manager = EventManager(transport, self.ews)

        # Simulation State
        self.running = False
        self.paused = False
        self.mode = SimulationMode.RANDOM
        self.playback_profile: Optional[str] = None
        self.interval = get_config().simulation_interval
        self.real_time_interval = 5
        self.current_sim_time = datetime.now(timezone.utc) - timedelta(hours=24)
        
        self.weather_mode = "Sunny"
        self.grid_stress_multiplier = 1.0

    async def start(self):
        """Start the simulation."""
        self.running = True
        logger.info(f"Starting simulation with {len(self.meters)} meters")
        await self.transport.connect()
        
        if self.db_manager:
            self.session_id = str(uuid.uuid4())
            await self.db_manager.create_session(self.session_id, {
                "num_meters": len(self.meters), "mode": self.mode.value, "interval": self.interval
            })
            for meter in self.meters:
                await self.db_manager.save_meter_config(meter.meter_id, meter.config.get('meter_type', 'unknown'), meter.config.get('location', 'unknown'), meter.config.get('accuracy_class', 'unknown'), meter.config)

        # Initialize Grid
        self.grid.initialize_network(self.meters)
        self.vpp_handler.register_meters(self.meters)
        
        # Start loop
        asyncio.create_task(self._simulation_loop())

    async def _simulation_loop(self):
        """Internal simulation loop."""
        while self.running:
            while self.paused and self.running:
                await asyncio.sleep(1)
            
            if not self.running: break

            start_time = datetime.now()
            try:
                await self.tick()
            except Exception as e:
                logger.error(f"Error in simulation tick: {e}", exc_info=True)
                
            elapsed = (datetime.now() - start_time).total_seconds()
            await asyncio.sleep(max(0, self.real_time_interval - elapsed))

    async def tick(self, timestamp: Optional[datetime] = None):
        """Execute one simulation step."""
        if timestamp: self.current_sim_time = timestamp
        ts = self.current_sim_time

        # 1. Frequency and VPP Pre-processing
        self.vpp_handler.handle_frequency_response(self.meters, self.grid.nodal_prices, self.grid.meter_to_bus, self.grid.carbon_intensity)
        self.vpp_handler.handle_island_stability(self.meters)

        # 2. Generate Readings
        readings, _ = self.reading_manager.generate_all(
            self.meters, ts, self.interval, self.mode, self.playback_profile, 
            self.weather_mode, self.grid_stress_multiplier
        )

        # 3. Grid Estimation & Advanced Analytics
        est_results = self.grid.run_state_estimation(self.meters, readings)
        if est_results and est_results.converged:
            await self.event_manager.monitor_grid_health(self.grid.net, ts.isoformat())
            await self._handle_proactive_dispatches(ts)

        # 4. Billing & Attacks
        if self.attacker.is_attacking():
            self.attacker.inject_readings(readings)
        for r in readings:
            self.billing.consume_reading(r.meter_id, r.energy_consumed, r.energy_generated, r.timestamp)

        # 5. Data Persistence & Broadcasting
        self.vpp_handler.update_vpp_states(self.meters, readings)
        await self._broadcast_status(ts, readings, est_results)
        await self.transport.send_batch(readings)

        # Advance time
        self.current_sim_time += timedelta(seconds=self.interval)

    async def _handle_proactive_dispatches(self, timestamp: datetime):
        """Handle AI-driven proactive dispatches for grid constraints."""
        agg_forecast = GridAnalyticsService.calculate_aggregate_forecast(self.meters, timestamp)
        ai_forecast = agg_forecast.get("ai_forecast", [])
        
        dispatches = self.vpp_manager.proactive_bess_dispatch_from_forecast(ai_forecast)
        if dispatches:
            for mid, kw in dispatches.items():
                m = next((m for m in self.meters if m.meter_id == mid), None)
                if m: m.receive_dispatch(kw)
            await self.event_manager.send_vpp_dispatch_alerts(dispatches, "115kV KMB (Circuit 3)", 0.0, "PROACTIVE_BOTTLENECK")

    async def _broadcast_status(self, ts: datetime, readings: List[Any], results: Any):
        """Broadcast grid and VPP status to all transports."""
        if not results or not results.converged: return

        # System imbalance for frequency model
        total_gen_mw = sum(r.energy_generated for r in readings) / (self.interval / 3600.0) / 1000.0
        total_cons_mw = sum(r.energy_consumed for r in readings) / (self.interval / 3600.0) / 1000.0
        self.frequency_model.step(total_gen_mw - total_cons_mw, self.real_time_interval)

        status = {
            "timestamp": ts.isoformat(),
            "total_generation": float(total_gen_mw),
            "total_consumption": float(total_cons_mw),
            "net_balance": float(total_gen_mw - total_cons_mw),
            "frequency": {"value": float(self.frequency_model.state.frequency)},
            "carbon_intensity": float(self.grid.carbon_intensity),
            "weather_mode": self.weather_mode
        }
        await self.transport.send_grid_status(status)

    async def stop(self):
        """Stop simulation and clean up."""
        self.running = False
        await self.transport.disconnect()
        if self.db_manager and hasattr(self, 'session_id'):
            await self.db_manager.close_session(self.session_id)
            await self.db_manager.close()
        logger.info("Simulation stopped gracefully")

    async def disconnect_grid(self):
        if self.grid.net:
            success = self.island_manager.disconnect(self.grid.net, self.meters, self.grid.meter_to_bus)
            if success: await self.event_manager.broadcast_islanding_event("ISLANDING", "Microgrid islanded.", self.current_sim_time.isoformat())
            return success
        return False

    async def reconnect_grid(self):
        if self.grid.net:
            success = self.island_manager.reconnect(self.grid.net)
            if success:
                for cid in self.vpp_manager.clusters: self.vpp_manager.reset_shedding(cid)
                await self.event_manager.broadcast_islanding_event("RECONNECTION", "Grid resynchronized.", self.current_sim_time.isoformat())
            return success
        return False
