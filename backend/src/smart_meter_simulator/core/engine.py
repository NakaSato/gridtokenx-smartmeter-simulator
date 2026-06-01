"""
Simulation Engine for Smart Meter Simulator
Orchestrates the simulation of multiple smart meters with grid integration.
"""

import typing

if typing.TYPE_CHECKING:
    from smart_meter_simulator.devices.ami import SmartMeter

import asyncio
import logging
import uuid
from datetime import datetime, timezone, timedelta
from typing import Any, List, Optional


from ..config import SimulationMode, get_config
from ..transport.base import TransportLayer
from .billing import BillingEngine
from .data_source import ProfileDataSource
from .db import DatabaseManager
from .frequency import FrequencyModel
from .island import IslandManager

from .vpp import VPPManager
from ..services.cost_calculator_service import CostCalculatorService
from ..services.loadshed_scenario_service import LoadShedScenarioService

# New Managers
import time
import json
from .grid_manager import GridManager
from .vpp_handler import VPPHandler
from .reading_manager import ReadingManager
from .event_manager import EventManager
from .metrics import SIMULATION_TICK_TIME, ACTIVE_METERS, TRANSPORT_LATENCY, TRANSPORT_PAYLOAD_SIZE

logger = logging.getLogger(__name__)


class SimulationEngine:
    """
    Orchestrates the simulation of multiple smart meters by coordinating
    specialized managers for grid, VPP, reading generation, and events.
    """

    def __init__(
        self,
        meters: List["SmartMeter"],
        transport: TransportLayer,
        adapter: Optional[Any] = None,
        db_manager: Optional[DatabaseManager] = None,
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
        # Modular Managers
        # Select grid adapter: GridLAB-D (if enabled) or PandapowerAdapter (default)
        grid_adapter = adapter
        if get_config().gridlabd_enabled:
            from ..adapters.gridlabd_adapter import GridlabdAdapter
            grid_adapter = GridlabdAdapter(
                mode=get_config().gridlabd_mode,
                glm_path=get_config().gridlabd_glm_file,
                gridlabd_executable=get_config().gridlabd_executable,
            )
            logger.info(f"Using GridlabdAdapter in {get_config().gridlabd_mode} mode")
        self.grid = GridManager(grid_adapter)
        self.vpp_handler = VPPHandler(
            self.vpp_manager, self.frequency_model, self.island_manager
        )
        self.reading_manager = ReadingManager(self.data_source)
        self.event_manager = EventManager(transport, None)
        self.cost_calculator = CostCalculatorService()
        self.loadshed_scenario = LoadShedScenarioService()

        # Transactive Market Handler (optional)
        self.market_handler = None
        if get_config().market_enabled:
            from ..market import ThaiRetailMarket, TOUEngine, MarketHandler
            config = get_config()
            tou = TOUEngine(
                on_peak_rate=config.tou_on_peak_rate,
                off_peak_rate=config.tou_off_peak_rate,
                on_peak_start=config.tou_on_peak_start,
                on_peak_end=config.tou_on_peak_end,
                ft_adjustment=config.ft_adjustment,
            )
            market = ThaiRetailMarket(
                price_cap=config.market_price_cap,
                price_floor=config.market_price_floor,
            )
            self.market_handler = MarketHandler(
                market=market,
                tou_engine=tou,
                clearing_interval=config.market_clearing_interval,
            )

        # Simulation State
        self.running = False
        self.paused = False
        self.mode = SimulationMode.RANDOM
        self.playback_profile: Optional[str] = None
        self.interval = get_config().simulation_interval
        self.real_time_interval = 5
        self.current_sim_time = datetime.now(timezone.utc).replace(hour=8, minute=0, second=0, microsecond=0)
        self.start_sim_time = self.current_sim_time
        self.helics_time_seconds = 0.0
        self.helics_adapter = None
        if get_config().helics_enabled:
            from ..adapters.helics_adapter import HelicsAdapter
            self.helics_adapter = HelicsAdapter(
                fed_name=get_config().helics_federate_name,
                core_type=get_config().helics_core_type,
                broker_address=get_config().helics_broker_address,
                broker_port=get_config().helics_broker_port,
                time_period=float(get_config().helics_time_period),
                data_flow=get_config().helics_data_flow,
            )

        self.weather_mode = "Sunny"
        self.grid_stress_multiplier = 1.0

    async def start(self):
        """Start the simulation."""
        self.running = True
        logger.info(f"Starting simulation with {len(self.meters)} meters")
        await self.transport.connect()

        # Initialize HELICS if enabled
        if self.helics_adapter:
            success = self.helics_adapter.initialize(
                self.meters,
                subscription_mappings=get_config().helics_subscription_mappings
            )
            if success:
                await self.helics_adapter.enter_execution_mode()
                self.start_sim_time = self.current_sim_time
                self.helics_time_seconds = 0.0
            else:
                logger.error("Failed to initialize HELICS. Co-simulation will fall back to normal mode.")
                self.helics_adapter = None

        if self.db_manager:
            self.session_id = str(uuid.uuid4())
            await self.db_manager.create_session(
                self.session_id,
                {
                    "num_meters": len(self.meters),
                    "mode": self.mode.value,
                    "interval": self.interval,
                },
            )
            for meter in self.meters:
                await self.db_manager.save_meter_config(
                    meter.meter_id,
                    meter.config.get("meter_type", "unknown"),
                    meter.config.get("location", "unknown"),
                    meter.config.get("accuracy_class", "unknown"),
                    meter.config,
                )

        # Initialize Grid
        self.grid.initialize_network(self.meters)
        self.vpp_handler.register_meters(self.meters)

        # Register meters with market handler
        if self.market_handler:
            self.market_handler.register_meters(self.meters)

        # Start load-shedding scenario execution matching current sim time
        self.loadshed_scenario.start(self.current_sim_time)
        
        ACTIVE_METERS.set(len(self.meters))

        # Start loop
        asyncio.create_task(self._simulation_loop())

    async def _simulation_loop(self):
        """Internal simulation loop."""
        while self.running:
            while self.paused and self.running:
                await asyncio.sleep(1)

            if not self.running:
                break

            if self.helics_adapter:
                try:
                    target_time = self.helics_time_seconds + self.interval
                    granted_time = await self.helics_adapter.request_time(target_time)
                    self.helics_time_seconds = granted_time

                    # Determine corresponding sim time
                    sim_timestamp = self.start_sim_time + timedelta(seconds=granted_time)
                    await self.tick(timestamp=sim_timestamp)
                except Exception as e:
                    logger.error(f"Error in HELICS simulation loop: {e}", exc_info=True)
                    await asyncio.sleep(1)
            else:
                start_time = datetime.now()
                try:
                    await self.tick()
                except Exception as e:
                    logger.error(f"Error in simulation tick: {e}", exc_info=True)

                elapsed = (datetime.now() - start_time).total_seconds()
                await asyncio.sleep(max(0, self.real_time_interval - elapsed))

    async def tick(self, timestamp: Optional[datetime] = None):
        """Execute one simulation step."""
        tick_start = time.time()
        if timestamp:
            self.current_sim_time = timestamp
        ts = self.current_sim_time

        # Update HELICS subscriptions if active
        if self.helics_adapter:
            self.helics_adapter.update_subscriptions()
            price = self.helics_adapter.get_subscription_value(
                "retail_price", get_config().grid_purchase_rate
            )
            self.grid.avg_nodal_price = price
            for meter in self.meters:
                dispatch_price = self.helics_adapter.get_subscription_value(
                    f"{meter.meter_id}/dispatch_price", price
                )
                self.grid.nodal_prices[meter.meter_id] = dispatch_price

                # Fetch dynamic load shed status from HELICS
                is_shed = self.helics_adapter.get_subscription_value(
                    f"{meter.meter_id}/is_shed", False
                )
                meter.is_shed = is_shed

        # Run time-series scenario step update
        self.loadshed_scenario.update_step(ts, self.meters)

        # 1. Frequency and VPP Pre-processing
        self.vpp_handler.handle_frequency_response(
            self.meters,
            self.grid.nodal_prices,
            self.grid.meter_to_bus,
            self.grid.carbon_intensity,
        )
        self.vpp_handler.handle_island_stability(self.meters)

        # 1b. Market Clearing (transactive energy)
        if self.market_handler:
            market_result = self.market_handler.run_market_clearing(self.meters, ts)
            # Override nodal prices with market-cleared prices
            market_prices = self.market_handler.get_nodal_prices()
            for meter_id, price in market_prices.items():
                self.grid.nodal_prices[meter_id] = price
            # Set average nodal price for non-market meters
            if market_prices:
                self.grid.avg_nodal_price = self.market_handler.get_clearing_price()

        # 2. Generate Readings
        readings, _ = self.reading_manager.generate_all(
            self.meters,
            ts,
            self.interval,
            self.mode,
            self.playback_profile,
            self.weather_mode,
            self.grid_stress_multiplier,
        )

        # 3. Grid Update
        self.grid.update_grid_state(self.meters, readings)

        # 4. Billing
        for r in readings:
            self.billing.consume_reading(
                r.meter_id, r.energy_consumed, r.energy_generated, r.timestamp
            )

        # 5. Data Persistence & Broadcasting
        self.vpp_handler.update_vpp_states(self.meters, readings)
        await self._broadcast_status(ts, readings)
        
        transport_type = type(self.transport).__name__
        transport_start = time.time()
        await self.transport.send_batch(readings)
        TRANSPORT_LATENCY.labels(transport_type=transport_type).observe(time.time() - transport_start)
        
        # Estimate payload size (approximate bytes)
        # Using string length of dict representation as a proxy
        approx_size = sum(len(str(r.__dict__)) for r in readings)
        TRANSPORT_PAYLOAD_SIZE.labels(transport_type=transport_type).observe(approx_size)

        # 6. Operational Cost Ingestion
        strategy_mode = "NORMAL"
        if self.island_manager.state.is_islanded:
            strategy_mode = "ISLAND"
        elif abs(self.frequency_model.state.frequency - 50.0) > 0.02:
            strategy_mode = "aFRR"
        elif any(m.vpp_dispatch_kw != 0 for m in self.meters):
            strategy_mode = "VPP_DISPATCH"

        step_costs = self.cost_calculator.calculate_step_costs(
            readings, strategy_mode=strategy_mode
        )
        if hasattr(self.transport, "send_operational_costs"):
            await self.transport.send_operational_costs(step_costs)

        # Publish results to HELICS
        if self.helics_adapter:
            self.helics_adapter.publish_meter_data(readings)
            self.helics_adapter.publish_frequency(self.frequency_model.state.frequency)

        # Advance time if not managed by HELICS
        if not self.helics_adapter:
            self.current_sim_time += timedelta(seconds=self.interval)
            
        SIMULATION_TICK_TIME.observe(time.time() - tick_start)

    async def _broadcast_status(self, ts: datetime, readings: List[Any]):
        """Broadcast grid and VPP status to all transports."""

        # System imbalance for frequency model
        total_gen_mw = (
            sum(r.energy_generated for r in readings)
            / (self.interval / 3600.0)
            / 1000.0
        )
        total_cons_mw = (
            sum(r.energy_consumed for r in readings) / (self.interval / 3600.0) / 1000.0
        )
        self.frequency_model.step(total_gen_mw - total_cons_mw, self.real_time_interval)

        status = {
            "timestamp": ts.isoformat(),
            "total_generation": float(total_gen_mw),
            "total_consumption": float(total_cons_mw),
            "net_balance": float(total_gen_mw - total_cons_mw),
            "frequency": {"value": float(self.frequency_model.state.frequency)},
            "carbon_intensity": float(self.grid.carbon_intensity),
            "weather_mode": self.weather_mode,
        }
        await self.transport.send_grid_status(status)

    async def stop(self):
        """Stop simulation and clean up."""
        self.running = False
        self.loadshed_scenario.stop()
        if self.helics_adapter:
            await self.helics_adapter.finalize()
        await self.transport.disconnect()
        if self.db_manager and hasattr(self, "session_id"):
            await self.db_manager.close_session(self.session_id)
            await self.db_manager.close()
        logger.info("Simulation stopped gracefully")

    async def add_meter(self, meter: "SmartMeter"):
        """Add a new meter to the simulation."""
        self.meters.append(meter)
        self.vpp_handler.register_meters([meter])
        if self.market_handler:
            self.market_handler.register_meters([meter])
        
        ACTIVE_METERS.set(len(self.meters))
        
        if self.db_manager:
            await self.db_manager.save_meter_config(
                meter.meter_id,
                meter.config.get("meter_type", "unknown"),
                meter.config.get("location", "unknown"),
                meter.config.get("accuracy_class", "unknown"),
                meter.config,
            )
        return True

    async def remove_meter(self, meter_id: str):
        """Remove a meter from the simulation."""
        original_count = len(self.meters)
        self.meters = [m for m in self.meters if m.meter_id != meter_id]
        
        if len(self.meters) < original_count:
            ACTIVE_METERS.set(len(self.meters))
            return True
        return False

    async def clear_meters(self):
        """Remove all meters from the simulation."""
        self.meters = []
        ACTIVE_METERS.set(0)
        return True

    async def pause_simulation(self):
        """Pause the simulation loop."""
        self.paused = True
        return True

    async def resume_simulation(self):
        """Resume the simulation loop."""
        self.paused = False
        return True

    async def step_simulation(self):
        """Manually execute one tick."""
        await self.tick()
        return True

    async def disconnect_grid(self):
        if self.grid.net:
            success = self.island_manager.disconnect(
                self.grid.net, self.meters, self.grid.meter_to_bus
            )
            if success:
                await self.event_manager.broadcast_islanding_event(
                    "ISLANDING",
                    "Microgrid islanded.",
                    self.current_sim_time.isoformat(),
                )
            return success
        return False

    async def reconnect_grid(self):
        if self.grid.net:
            success = self.island_manager.reconnect(self.grid.net)
            if success:
                for cid in self.vpp_manager.clusters:
                    self.vpp_manager.reset_shedding(cid)
                await self.event_manager.broadcast_islanding_event(
                    "RECONNECTION",
                    "Grid resynchronized.",
                    self.current_sim_time.isoformat(),
                )
            return success
        return False
