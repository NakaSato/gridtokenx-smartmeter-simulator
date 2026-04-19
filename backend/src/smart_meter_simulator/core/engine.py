"""
Simulation Engine for Smart Meter Simulator
Orchestrates the simulation of multiple smart meters with grid integration.
"""

import asyncio
import logging
import math
import json
import os
from datetime import datetime, timezone, timedelta, date
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from ..config import MeterType, SimulatorConfig, get_config
from ..models.reading import EnergyReading
from ..transport.base import TransportLayer
from .attacker import FDIAttacker
from .billing import BillingEngine
from .data_source import ProfileDataSource
from .db import DatabaseManager
from .frequency import FrequencyModel
from .island import IslandManager
from .meter import SmartMeter
from .optimizer import OptimizationEngine
from .vpp import VPPManager
from ..services.telemetry_service import GridTelemetryService
from ..services.analytics_service import GridAnalyticsService

logger = logging.getLogger(__name__)

class SimulationMode(Enum):
    """Simulation mode enumeration"""
    RANDOM = "random"
    PLAYBACK = "playback"

class SimulationEngine:
    """
    Orchestrates the simulation of multiple smart meters.
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
        self.adapter = adapter  # PandapowerAdapter
        self.db_manager = db_manager
        self.running = False
        self.paused = False
        self.mode = SimulationMode.RANDOM
        self.playback_profile: Optional[str] = None
        self.data_source = ProfileDataSource()
        self.optimizer = OptimizationEngine()
        self.vpp = VPPManager()
        self.frequency_model = FrequencyModel()
        self.island_manager = IslandManager()
        self.billing = BillingEngine()
        self.attacker = FDIAttacker()
        from .forecaster import EdgeForecastingEngine
        self.forecaster = EdgeForecastingEngine("SAMUI-HUB-01")
        from .ews import EarlyWarningSystem
        self.ews = EarlyWarningSystem()

        # Get config
        config = get_config()
        self.interval = config.simulation_interval

        self.real_time_interval = 5 # Real seconds between ticks
        self.external_clock = False # Set to True for co-simulation
        
        # Geo-SAM Integration
        self.solar_inventory = []
        self.bus_solar_capacity = {} # bus_idx -> total_kwp
        
        # Start 24 hours ago to ensure valid timestamps
        now = datetime.now(timezone.utc)
        self.current_sim_time = now - timedelta(hours=24)
        
        # Grid state
        self.last_estimation_results = None
        self.net = None
        self.meter_to_bus = {} # meter_id -> bus_index

        # Dynamic Simulation Controls
        self.weather_mode = "Sunny"
        self.grid_stress_multiplier = 1.0

        # Pre-initialize price attributes to avoid AttributeErrors before first tick
        self.net_nodal_prices = {} 
        self.net_avg_nodal_price = 0.28
        self.last_carbon_intensity = 250.0
        self.last_bottleneck_capacity = None # EWS: Track sudden capacity drops
        
    async def start(self):
        """Start the simulation."""
        self.running = True
        logger.info(f"Starting simulation with {len(self.meters)} meters")
        await self.transport.connect()
        
        # Persistence: create session and save meter configs
        if self.db_manager:
            import uuid
            self.session_id = str(uuid.uuid4())
            await self.db_manager.create_session(self.session_id, {
                "num_meters": len(self.meters),
                "mode": self.mode.value,
                "interval": self.interval
            })
            for meter in self.meters:
                await self.db_manager.save_meter_config(
                    meter.meter_id, 
                    meter.config.get('meter_type', 'unknown'),
                    meter.config.get('location', 'unknown'),
                    meter.config.get('accuracy_class', 'unknown'),
                    meter.config
                )
            logger.info(f"Simulation metadata persisted to DB. Session: {self.session_id}")
        
        # Initialize network if adapter is present
        if self.adapter:
            try:
                import pandapower as pp
                
                # Check for Island Hub Scenario
                is_island_hub = False
                
                # Check config locations file first
                config = get_config()
                loc_file = config.initial_locations_file
                if loc_file.endswith(".json") and os.path.exists(loc_file):
                    try:
                        with open(loc_file, 'r') as f:
                            data = json.load(f)
                            if data.get("scenario") == "Gulf of Thailand Island Hub":
                                is_island_hub = True
                    except Exception:
                        pass
                
                # Fallback to data source metadata
                if not is_island_hub and hasattr(self.data_source, 'last_loaded_metadata'):
                    meta = self.data_source.last_loaded_metadata
                    if meta.get("scenario") == "Gulf of Thailand Island Hub":
                        is_island_hub = True
                
                if is_island_hub:
                    from ..adapters.island_hub_topology import IslandHubTopology
                    island_builder = IslandHubTopology()
                    self.net, self.meter_to_bus = island_builder.build_island_hub(self.meters)
                    logger.info("🏝️  Detected Gulf of Thailand Island Hub scenario. Using specialized topology.")
                else:
                    # Build network using adapter's intelligence (topology builder)
                    self.net, self.meter_to_bus = self.adapter.build_network_from_meters(self.meters)
                
                # Initialize static elements (Loads/Sgens) for each meter
                for meter in self.meters:
                    # Register with VPP
                    self.vpp.register_meter(
                        meter.meter_id, 
                        meter.config, 
                        {"battery_level": meter.battery_level}
                    )

                    bus_idx = self.meter_to_bus.get(meter.meter_id)
                    if bus_idx is not None and not is_island_hub:
                        # Only create placeholder elements if not already created by specialized builder
                        pp.create_load(self.net, bus=bus_idx, p_mw=0, q_mvar=0, name=f"L_{meter.meter_id}")
                        if meter.config.get('has_solar'):
                            pp.create_sgen(self.net, bus=bus_idx, p_mw=0, q_mvar=0, name=f"G_{meter.meter_id}")
                
                logger.info(f"Initialized grid topology: {len(self.net.bus)} buses, {len(self.net.line)} lines, {len(self.meters)} meters mapped")
                
                # Geo-SAM Integration - Load and map solar inventory
                if self.db_manager:
                    self.solar_inventory = await self.db_manager.get_all_solar_inventory()
                    if self.net:
                        self.bus_solar_capacity = GridTelemetryService.map_solar_to_grid(self.net, self.solar_inventory)
            except Exception as e:
                logger.error(f"Failed to initialize grid topology: {e}")
        
        if self.external_clock:
            logger.info("SimulationEngine: External clock mode active. Internal loop bypassed.")
            return

        # Start internal loop if not driven by external clock (e.g. Mosaik)
        asyncio.create_task(self._simulation_loop())

    async def _simulation_loop(self):
        """Internal simulation loop (Real-time mode)."""
        while self.running:
            # Check if paused
            while self.paused and self.running:
                await asyncio.sleep(1)
            
            if not self.running:
                break

            start_time = datetime.now()
            try:
                await self.tick()
            except Exception as e:
                logger.error(f"Error in simulation tick: {e}", exc_info=True)
                
            # Wait for next tick
            elapsed = (datetime.now() - start_time).total_seconds()
            wait_time = max(0, self.real_time_interval - elapsed)
            await asyncio.sleep(wait_time)

    async def add_meter(self, meter: SmartMeter):
        """Dynamically add a new meter to the running simulation."""
        self.meters.append(meter)
        
        # Assign to a random bus for now (simple topology extension)
        import random
        if self.net is not None:
            load_buses = self.net.load.bus.values
            if len(load_buses) > 0:
                bus_idx = random.choice(load_buses)
                self.meter_to_bus[meter.meter_id] = bus_idx
                
                # Update net if possible
                import pandapower as pp
                pp.create_load(self.net, bus=bus_idx, p_mw=0, q_mvar=0, name=f"L_{meter.meter_id}")
                if meter.config.get('has_solar'):
                    pp.create_sgen(self.net, bus=bus_idx, p_mw=0, q_mvar=0, name=f"G_{meter.meter_id}")
        
        logger.info(f"Added new meter {meter.meter_id} to simulation")
        if self.db_manager and hasattr(self, 'session_id'):
            await self.db_manager.save_meter_config(
                meter.meter_id, 
                meter.config.get('meter_type', 'unknown'),
                meter.config.get('location', 'unknown'),
                meter.config.get('accuracy_class', 'unknown'),
                meter.config
            )
            
    async def stop(self):
        """Stop the simulation and clean up resources."""
        self.running = False
        
        # 1. Disconnect all transports
        await self.transport.disconnect()
        
        # 2. Close persistent HTTP session if it exists
        if hasattr(self, '_http_session'):
            await self._http_session.close()
            logger.info("SimulationEngine HTTP session closed")
        
        # 3. Close database session and dispose of engine
        if self.db_manager and hasattr(self, 'session_id'):
            await self.db_manager.close_session(self.session_id)
            await self.db_manager.close()
        
        logger.info("Simulation stopped gracefully")
        
    async def disconnect_grid(self):
        """Force disconnection from main grid (Islanding)."""
        if self.adapter and self.net:
            success = self.island_manager.disconnect(self.net, self.meters, self.meter_to_bus)
            if success:
                logger.warning("MICROGRID ISLANDED SUCCESSFULLY")
                # Notify Transport of critical event
                await self.transport.send_alert({
                    "type": "GRID_EVENT",
                    "subtype": "ISLANDING",
                    "timestamp": self.current_sim_time.isoformat(),
                    "message": "Main grid disconnected. Forming microgrid."
                })
            return success
        return False
        
    async def reconnect_grid(self):
        """Reconnect to main grid."""
        if self.adapter and self.net:
            success = self.island_manager.reconnect(self.net)
            if success:
                # Restore all shedded loads
                for cluster_id in self.vpp.clusters:
                    self.vpp.reset_shedding(cluster_id)
                    
                logger.info("MICROGRID RECONNECTED")
                await self.transport.send_alert({
                    "type": "GRID_EVENT",
                    "subtype": "RECONNECTION",
                    "timestamp": self.current_sim_time.isoformat(),
                    "message": "Resynchronized with main grid. All loads restored."
                })
            return success
        return False

    async def tick_once(self, timestamp: Optional[datetime] = None):
        """Execute exactly one simulation step (for Co-Simulation)."""
        if timestamp:
            self.current_sim_time = timestamp
        await self.tick()

    async def tick(self, timestamp: Optional[datetime] = None):
        """Execute one simulation step."""
        # Log Rust acceleration status on first tick
        if not hasattr(self, '_rust_logged'):
            try:
                from smart_meter_simulator.core.rust_engine import USE_RUST_ENGINE
                if USE_RUST_ENGINE:
                    logger.info("🦀 Rust acceleration enabled and active (3000-7000x faster)")
                    self._rust_logged = True
                else:
                    logger.info("⚠️  Rust acceleration enabled but extension not loaded (using Python fallback)")
                    self._rust_logged = True
            except ImportError:
                logger.info("⚠️  Rust engine not available (using Python fallback)")
                self._rust_logged = True

        if timestamp:
            self.current_sim_time = timestamp
        timestamp = self.current_sim_time

        # 1. Generate readings
        readings, playback_data = self._generate_readings(timestamp)

        # 2. Run Grid Estimation (Digital Twin)
        await self._run_grid_estimation(timestamp, readings)

        # 3. Accumulate readings into billing engine
        # Apply FDI attacks before billing (attacks affect billed amounts)
        if self.attacker.is_attacking():
            self.attacker.inject_readings(readings)

        for reading in readings:
            self.billing.consume_reading(
                meter_id=reading.meter_id,
                energy_consumed_kwh=reading.energy_consumed,
                energy_generated_kwh=reading.energy_generated,
                timestamp=reading.timestamp,
            )

        # 4. Send readings (Async)
        await self._send_readings_async(timestamp, readings)

        # Advance simulated time
        self.current_sim_time += timedelta(seconds=self.interval)

    def _generate_readings(self, timestamp: datetime) -> Tuple[List[EnergyReading], Dict[str, Any]]:
        """
        Generate smart meter readings for the current simulation timestamp.

        Handles playback data fetching, VPP dispatch, islanding stability,
        weather/frequency updates, and reading generation (Rust-accelerated
        or Python fallback).

        Args:
            timestamp: Current simulation timestamp.

        Returns:
            Tuple of (list of EnergyReading objects, playback data dict).
        """
        readings: List[EnergyReading] = []

        # Batch fetch playback data if in PLAYBACK mode
        playback_data: Dict[str, Any] = {}
        if self.mode == SimulationMode.PLAYBACK and self.playback_profile:
            playback_data = self.data_source.get_values_batch(self.playback_profile, timestamp)

            # Data Source Management
            # Inject standard load profile or historical CSV/Parquet data directly into meters
            for m in self.meters:
                if m.meter_id in playback_data:
                    # Value could represent net (negative=gen, positive=cons) or absolute
                    val = playback_data[m.meter_id]
                    if val < 0:
                        m.manual_override_gen = abs(val)
                        m.manual_override_cons = 0.0
                    else:
                        m.manual_override_cons = abs(val)
                        m.manual_override_gen = 0.0

        # Generate Forecasts and Optimization Signals
        meter_ids = [m.meter_id for m in self.meters]

        # VPP Dispatch & AFRR Response
        freq = self.frequency_model.state.frequency
        if abs(freq - 50.0) > 0.02:
            for cluster_id in self.vpp.clusters:
                target_kw = self.vpp.calculate_afrr_response(cluster_id, freq)
                if target_kw != 0:
                    dispatches = self.vpp.dispatch_cluster(cluster_id, target_kw)
                    for m_id, kw in dispatches.items():
                        m_obj = next((m for m in self.meters if m.meter_id == m_id), None)
                        if m_obj: m_obj.receive_dispatch(kw)
        else:
            # Frequency is healthy, reset all specific VPP dispatches
            for m in self.meters:
                if m.vpp_dispatch_kw != 0:
                    m.receive_dispatch(0.0)

        # Intelligent Grid Healing (Islanding Stability)
        if self.island_manager.state.is_islanded:
            freq = self.frequency_model.state.frequency
            # Trigger Black Start if frequency collapsed
            if freq < 47.0:
                 self.island_manager.black_start_sequence(self.vpp)

            # Orchestrate stability across all microgrid clusters
            for cluster_id in self.vpp.clusters:
                status = self.vpp.get_cluster_status(cluster_id)
                dispatches = self.vpp.orchestrate_microgrid_stability(
                    cluster_id, freq,
                    total_cons=status.get("total_cons_kw", 0),
                    total_gen=status.get("total_gen_kw", 0)
                )
                if dispatches:
                    for mid, kw in dispatches.items():
                        m_obj = next((m for m in self.meters if m.meter_id == mid), None)
                        if m_obj: m_obj.receive_dispatch(kw)

        for meter in self.meters:
            meter.update_weather(self.weather_mode)
            meter.receive_frequency(self.frequency_model.state.frequency)

        # Rust-Accelerated Reading Generation
        # Use Rust batch engine when no overrides are needed (fast path)
        from smart_meter_simulator.config import get_config
        config = get_config()

        use_rust_batch = (
            config.rust_acceleration_enabled
            and playback_data is None
            and not any(hasattr(m, 'manual_override_gen') for m in self.meters)
            and self.grid_stress_multiplier == 1.0
        )

        if use_rust_batch:
            # Fast path: Rust batch generation (3000-7000x faster)
            try:
                from smart_meter_simulator.core.rust_engine import RustAcceleratedMeter

                hour = timestamp.hour + timestamp.minute / 60.0
                weather_factor = 1.0 if self.weather_mode == "Sunny" else 0.7

                # Convert meter objects to config dicts for Rust
                meter_configs = [
                    {
                        'meter_id': m.meter_id,
                        'meter_type': m.config['meter_type'],
                        'has_solar': m.config.get('has_solar', False),
                        'has_battery': m.config.get('has_battery', False),
                        'solar_capacity': m.config.get('solar_capacity', 0.0),
                        'battery_capacity': m.config.get('battery_capacity', 0.0),
                        'base_consumption': m.config.get('base_consumption', 1.0),
                        'panel_efficiency': m.config.get('panel_efficiency', 0.18),
                        'current_battery_level': m.battery_level,
                        'price_elasticity': m.config.get('price_elasticity', 0.15),
                        'accuracy_class': m.accuracy_class.value if hasattr(m.accuracy_class, 'value') else 2.0,
                    }
                    for m in self.meters
                ]

                # Generate all readings in one Rust call
                rust_readings = RustAcceleratedMeter.generate_readings_batch(
                    meters=meter_configs,
                    timestamp=timestamp,
                    weather_factor=weather_factor,
                    interval_seconds=self.interval,
                )

                # Convert Rust readings back to EnergyReading objects
                for meter, rust_reading in zip(self.meters, rust_readings):
                    from smart_meter_simulator.models.reading import EnergyReading

                    reading = EnergyReading(
                        meter_id=rust_reading['meter_id'],
                        timestamp=timestamp,
                        energy_generated=rust_reading['energy_generated_kwh'],
                        energy_consumed=rust_reading['energy_consumed_kwh'],
                        surplus_energy=rust_reading['surplus_energy'],
                        deficit_energy=rust_reading['deficit_energy'],
                        interval_seconds=self.interval,
                        battery_level=rust_reading['battery_level'],
                        location=meter.config.get('location', 'Unknown'),
                        meter_type=meter.config.get('meter_type', 'Unknown'),
                        user_type=meter.config.get('user_type', 'Unknown'),
                        voltage=rust_reading['voltage'],
                        current=rust_reading['current'],
                        reactive_power_kvar=rust_reading['reactive_power'],
                        frequency=rust_reading['frequency'],
                        temperature=20.0,  # Default
                        power_factor=rust_reading['power_factor'],
                        nodal_price=0.50,  # Default
                        carbon_intensity=0.0,  # Default
                        max_sell_price=meter.config.get('max_sell_price', 0.50),
                        max_buy_price=meter.config.get('max_buy_price', 0.30),
                        rec_eligible=meter.config.get('has_solar', False),
                        carbon_offset=0.0,
                        weather_condition=self.weather_mode,
                    )

                    readings.append(reading)
                    meter.last_reading = reading

                    logger.debug(f"Rust reading generated for {meter.meter_id}")

            except Exception as e:
                logger.warning(f"Rust batch generation failed, falling back to Python: {e}")
                use_rust_batch = False

        # Slow path: Python per-meter generation (fallback or when overrides active)
        if not use_rust_batch:
            for meter in self.meters:
                # Fetch historical data if in PLAYBACK mode
                override_gen = None
                override_cons = None
                if playback_data:
                    override_gen = playback_data.get(f"{meter.meter_id}_GEN")
                    override_cons = playback_data.get(f"{meter.meter_id}_CONS")

                    # If neither GEN nor CONS found, try just the meter_id as CONS
                    if override_gen is None and override_cons is None:
                        override_cons = playback_data.get(meter.meter_id)

                # Check for manual overrides (from API/Verification)
                if hasattr(meter, 'manual_override_gen'):
                    override_gen = meter.manual_override_gen
                if hasattr(meter, 'manual_override_cons'):
                    override_cons = meter.manual_override_cons

                # Apply Grid Stress Multiplier
                if self.grid_stress_multiplier != 1.0 and override_cons is None:
                    # We'll apply it during calculation in generate_reading if we don't have an override
                    # But for immediate feedback, let's inject it into the base calculation
                    pass # Already handled by meter.generate_reading if we update it

                # AI-Driven Optimization
                forced_dispatch = None
                if meter.config.get('has_battery'):
                    # Individual forecast for this meter
                    load_f = np.zeros(24)  # Placeholder forecast
                    # Simple solar forecast for this meter if it has panels
                    gen_f = np.zeros(24)

                    # Determine optimal dispatch
                    forced_dispatch = self.optimizer.optimize_battery_dispatch(
                        meter.meter_id,
                        meter.battery_level,
                        gen_f - load_f,
                        price_forecast=None
                    )

                reading = meter.generate_reading(
                    timestamp,
                    override_gen=override_gen,
                    override_cons=override_cons,
                    forced_dispatch=forced_dispatch,
                    interval_seconds=self.interval,
                    grid_stress=self.grid_stress_multiplier
                )

                readings.append(reading)
                meter.last_reading = reading

                # VPP State Update
                hours = reading.interval_seconds / 3600.0
                p_cons = (reading.energy_consumed / hours) if hours > 0 else 0.0
                p_gen = (reading.energy_generated / hours) if hours > 0 else 0.0
                self.vpp.update_meter_state(meter.meter_id, meter.battery_level, p_cons=p_cons, p_gen=p_gen)

                # Sync Shedding State
                if meter.meter_id in self.vpp.meter_map:
                    cid = self.vpp.meter_map[meter.meter_id]
                    meter.is_shed = self.vpp.clusters[cid].resources[meter.meter_id].is_shed

        return readings, playback_data

    async def _run_grid_estimation(
        self, timestamp: datetime, readings: List[EnergyReading]
    ) -> None:
        """
        Run pandapower grid estimation (Digital Twin).
        """
        if not self.adapter or not self.net:
            return

        try:
            import pandapower as pp
            from ..config import MeterType

            # Clear previous measurements
            self.adapter.builder.clear()

            # Update network elements and add measurements
            load_updates_p = {}
            load_updates_q = {}
            sgen_updates_p = {}

            for meter, reading in zip(self.meters, readings):
                bus_idx = self.meter_to_bus.get(meter.meter_id)
                if bus_idx is None:
                    continue

                hours = reading.interval_seconds / 3600.0
                p_mw = (reading.energy_consumed / hours / 1000.0) if hours > 0 else 0.0
                p_gen_mw = (reading.energy_generated / hours / 1000.0) if hours > 0 else 0.0
                q_mvar = p_mw * 0.3

                load_indices = self.net.load[self.net.load.bus == bus_idx].index
                if len(load_indices) > 0:
                    load_idx = int(load_indices[0])
                    load_updates_p[load_idx] = p_mw
                    load_updates_q[load_idx] = q_mvar
                    self.adapter.builder.add_active_power_measurement(
                        meter.meter_id, bus_idx, p_mw,
                        meter.config.get("meter_type", MeterType.GRID_CONSUMER),
                        element_type="bus",
                    )
                    self.adapter.builder.add_reactive_power_measurement(
                        meter.meter_id, bus_idx, q_mvar,
                        meter.config.get("meter_type", MeterType.GRID_CONSUMER),
                        element_type="bus",
                    )

                sgen_indices = self.net.sgen[self.net.sgen.bus == bus_idx].index
                if len(sgen_indices) > 0:
                    sgen_idx = int(sgen_indices[0])
                    sgen_updates_p[sgen_idx] = p_gen_mw
                    self.adapter.builder.add_active_power_measurement(
                        meter.meter_id + "_GEN", bus_idx, -p_gen_mw,
                        meter.config.get("meter_type", MeterType.SOLAR_PROSUMER),
                        is_generation=True,
                        element_type="bus",
                    )

                voltage_pu = (reading.voltage * np.sqrt(3)) / (
                    self.net.bus.vn_kv.at[bus_idx] * 1000
                )
                self.adapter.builder.add_voltage_measurement(
                    meter.meter_id, bus_idx, voltage_pu,
                    meter.config.get("meter_type", MeterType.GRID_CONSUMER),
                )

            if load_updates_p:
                self.net.load.loc[list(load_updates_p.keys()), "p_mw"] = list(
                    load_updates_p.values()
                )
                self.net.load.loc[list(load_updates_q.keys()), "q_mvar"] = list(
                    load_updates_q.values()
                )
            if sgen_updates_p:
                self.net.sgen.loc[list(sgen_updates_p.keys()), "p_mw"] = list(
                    sgen_updates_p.values()
                )

            GridTelemetryService.inject_pseudo_measurements(self.net)

            if len(self.net.ext_grid) > 0:
                slack_bus = self.net.ext_grid.bus.values[0]
                self.adapter.builder.add_voltage_measurement(
                    "SB_01", slack_bus, 1.0, MeterType.BATTERY_STORAGE
                )

            self.net.measurement = self.adapter.get_measurement_table()

            # Run power flow
            pf_converged = False
            try:
                pp.runpp(
                    self.net,
                    algorithm="nr",
                    calculate_voltage_angles=True,
                    max_iteration=30,
                )
                pf_converged = True
            except pp.LoadflowNotConverged:
                logger.warning("Newton-Raphson failed to converge. Retrying with 'bfsw'...")
                try:
                    pp.runpp(
                        self.net,
                        algorithm="bfsw",
                        calculate_voltage_angles=True,
                        max_iteration=50,
                    )
                    pf_converged = True
                except pp.LoadflowNotConverged:
                    logger.warning("Power Flow failed both 'nr' and 'bfsw'.")
                    from ..adapters.state_estimator import StateEstimator
                    estimator_check = StateEstimator()
                    if not estimator_check.check_observability(self.net):
                        logger.error(
                            "SYSTEM IS NOT OBSERVABLE: Missing critical measurements."
                        )
                        GridTelemetryService.inject_pseudo_measurements(self.net, force_all=True)

            est_init = "results" if pf_converged else "flat"

            if not pf_converged:
                self.net.res_bus["vm_pu"] = 1.0
                self.net.res_bus["va_degree"] = 0.0

            # Run state estimation
            from ..adapters.state_estimator import StateEstimator, EstimationAlgorithm

            estimator = StateEstimator(algorithm=EstimationAlgorithm.WLS)
            results = estimator.run_sanitized_estimation(
                self.net, init=est_init, max_removals=10
            )
            self.last_estimation_results = results

            if results.bad_data_detected:
                logger.warning(
                    f"Sanitization: Removed {len(results.bad_data_detected)} bad measurements: {results.bad_data_detected}"
                )

            bad_data = estimator.detect_bad_data(self.net)
            if bad_data:
                logger.warning(
                    f"Residual Bad Data detected in cleaned results ({len(bad_data)} measurements): {bad_data}"
                )

            # Calculate nodal prices
            self.calculate_nodal_prices()

            # 🏝️  Island Hub: Bottleneck Monitoring & Resolution
            bottleneck_line = self.net.line[self.net.line.name == "115kV KMB (Circuit 3) Bottleneck"]
            if not bottleneck_line.empty:
                line_idx = bottleneck_line.index[0]
                loading_pct = self.net.res_line.loading_percent.at[line_idx]
                capacity_mw = (self.net.line.at[line_idx, 'max_i_ka'] * 
                               self.net.bus.vn_kv.at[self.net.line.at[line_idx, 'from_bus']] * 
                               np.sqrt(3))
                
                # 🚨 EARLY WARNING SYSTEM (EWS): Detect Anomaly
                ews_alert = self.ews.monitor_line_health("115kV KMB (Circuit 3)", capacity_mw, loading_pct)
                if ews_alert:
                    asyncio.create_task(self.transport.send_alert(ews_alert))
                    # Override logic for emergency response
                    if ews_alert["type"] == "EWS_CAPACITY_DROP" and loading_pct > 90.0:
                         loading_pct = 120.0 # Force emergency peak decision
                
                # 🔮 EDGE FORECASTING & COST OPTIMIZATION: 24-hour lookahead
                weather = {"temp_c": 32.0, "cloud_cover": 10.0} 
                forecast_load = self.forecaster.generate_24h_forecast(avg_cons_mw, weather, timestamp)
                # Assume PV forecast is 15% of demand for this presentation
                forecast_pv = forecast_load * 0.15 
                
                # 🧠 AI Load Forecasting (Constraint Prediction)
                from smart_meter_simulator.services.analytics_service import GridAnalyticsService
                agg_forecast = GridAnalyticsService.calculate_aggregate_forecast(self.meters, timestamp)
                ai_forecast = agg_forecast.get("ai_forecast", [])
                
                # Proactive AI-Driven BESS Dispatch
                ai_dispatches = self.vpp.proactive_bess_dispatch_from_forecast(ai_forecast)
                if ai_dispatches:
                    for m_id, kw in ai_dispatches.items():
                        m_obj = next((m for m in self.meters if m.meter_id == m_id), None)
                        if m_obj:
                            m_obj.receive_dispatch(kw)
                            asyncio.create_task(self.transport.send_alert({
                                "type": "PROACTIVE_BOTTLENECK_RESOLUTION",
                                "line": "115kV KMB (Circuit 3)",
                                "loading": f"{loading_pct:.1f}%",
                                "asset": m_id,
                                "dispatch_kw": kw,
                                "trigger": "AI_FORECAST"
                            }))
                
                # Generate 'Recommended Schedule' (Cost Minimization Objective)
                schedule = self.optimizer.calculate_cost_optimized_schedule(
                    forecast_load, forecast_pv, capacity_mw
                )
                
                # Run Operator Strategy Game (Financial Optimization)
                dispatches = self.vpp.resolve_bottleneck_game(loading_pct, capacity_mw)
                if dispatches:
                    for m_id, kw in dispatches.items():
                        m_obj = next((m for m in self.meters if m.meter_id == m_id), None)
                        if m_obj:
                            m_obj.receive_dispatch(kw)
                            # Alert the transport about the strategic dispatch
                            asyncio.create_task(self.transport.send_alert({
                                "type": "BOTTLENECK_RESOLUTION",
                                "line": "115kV KMB (Circuit 3)",
                                "loading": f"{loading_pct:.1f}%",
                                "asset": m_id,
                                "dispatch_kw": kw,
                                "mape_score": f"{self.forecaster.last_mape:.1f}%",
                                "potential_savings": f"{schedule[0]['savings_vs_diesel_thb']:.1f} THB/hr"
                            }))
                        # Save to Database (Event Tracking)
                        if self.db_manager:
                            asyncio.create_task(self.db_manager.save_grid_event(
                                event_type="bottleneck",
                                severity="critical" if loading_pct > 100 else "warning",
                                message=f"Transmission bottleneck resolved on 115kV KMB. Loading: {loading_pct:.1f}%",
                                metadata={
                                    "line": "115kV KMB (Circuit 3)",
                                    "loading_pct": float(loading_pct),
                                    "dispatches": dispatches,
                                    "optimized_schedule": schedule[:6] # Log next 6 hours
                                }
                            ))
                
                # 📊 ETL Pipeline: Transform and Load Node States (Continuous Metrics)
                if self.db_manager:
                    etl_results = GridAnalyticsService.process_island_hub_etl(self.vpp, self.net, timestamp, loading_pct)
                    for res in etl_results:
                        asyncio.create_task(self.db_manager.save_node_state(
                            node_id=res["node_id"],
                            timestamp=res["timestamp"],
                            metrics=res["metrics"]
                        ))

            # Calculate system-wide imbalance
            total_gen_kwh = sum(r.energy_generated for r in readings)
            total_cons_kwh = sum(r.energy_consumed for r in readings)
            avg_gen_mw = (total_gen_kwh / 0.25) / 1000.0
            avg_cons_mw = (total_cons_kwh / 0.25) / 1000.0
            imbalance_mw = avg_gen_mw - avg_cons_mw

            # Calculate carbon intensity
            grid_p_mw = (
                self.net.res_ext_grid.p_mw.sum()
                if self.net and hasattr(self.net, "res_ext_grid")
                else 0.0
            )
            total_load_mw = (
                self.net.res_load.p_mw.sum()
                if self.net and hasattr(self.net, "res_load")
                else 1.0
            )
            self.last_carbon_intensity = (
                max(0.0, (grid_p_mw / total_load_mw) * 500.0)
                if total_load_mw > 0
                else 500.0
            )

            # Step frequency model
            self.frequency_model.step(imbalance_mw, self.real_time_interval)

            # AFRR / VPP dispatch based on frequency deviation
            freq = self.frequency_model.state.frequency
            if abs(freq - 50.0) > 0.02:
                for cluster_id in self.vpp.clusters:
                    target_kw = self.vpp.calculate_afrr_response(cluster_id, freq)
                    if target_kw != 0:
                        meter_prices = {}
                        if self.net:
                            for m in self.meters:
                                b_idx = self.meter_to_bus.get(m.meter_id)
                                if b_idx is not None:
                                    meter_prices[m.meter_id] = self.net_nodal_prices.get(
                                        b_idx, 0.25
                                    )
                        dispatches = self.vpp.dispatch_cluster(
                            cluster_id,
                            target_kw,
                            nodal_prices=meter_prices,
                            carbon_intensity=self.last_carbon_intensity,
                        )
                        for mid, kw in dispatches.items():
                            for m in self.meters:
                                if m.meter_id == mid:
                                    m.receive_dispatch(kw)
            else:
                for m in self.meters:
                    if m.vpp_dispatch_kw != 0:
                        m.receive_dispatch(0.0)

            # Broadcast results
            if results and results.converged:
                broadcast_dict = {
                    "timestamp": timestamp.isoformat(),
                    "total_generation": float(avg_gen_mw),
                    "total_consumption": float(avg_cons_mw),
                    "net_balance": float(imbalance_mw),
                    "active_meters": int(len(self.meters)),
                    "avg_voltage_pu": float(
                        getattr(results, "avg_voltage_pu", 1.0)
                    ),
                    "carbon_intensity": float(
                        getattr(self, "last_carbon_intensity", 0.0)
                    ),
                    "weather_mode": self.weather_mode,
                    "grid_stress": self.grid_stress_multiplier,
                    "frequency": {
                        "value": float(self.frequency_model.state.frequency),
                        "rocof": float(self.frequency_model.state.rocof),
                        "angle": float(self.frequency_model.state.angle_deg),
                    },
                }
                await self.transport.send_grid_status(broadcast_dict)
                logger.info(
                    f"Grid estimation converged: chi2={results.chi2_statistic if results.chi2_statistic is not None else 0:.4f}"
                )

                # InfluxDB metrics
                try:
                    temp_c = 28.0 + (
                        2.0 if self.weather_mode == "Sunny" else -3.0
                    )
                    await self.transport.send_weather(
                        {
                            "timestamp": timestamp.isoformat(),
                            "condition": self.weather_mode,
                            "temperature_c": temp_c,
                            "solar_efficiency_pct": (
                                100.0 if self.weather_mode == "Sunny" else 65.0
                            ),
                            "location": "Central_Grid",
                        }
                    )
                    await self.transport.send_carbon_intensity(
                        {
                            "timestamp": timestamp.isoformat(),
                            "intensity_gco2_kwh": self.last_carbon_intensity,
                            "zone": "Central_Grid",
                            "total_generation_kwh": avg_gen_mw * 0.25 * 1000.0,
                            "total_consumption_kwh": avg_cons_mw * 0.25 * 1000.0,
                        }
                    )
                    await self.transport.send_frequency_event(
                        {
                            "timestamp": timestamp.isoformat(),
                            "frequency_hz": self.frequency_model.state.frequency,
                            "roc_hz_per_sec": self.frequency_model.state.rocof,
                            "imbalance_kw": imbalance_mw * 1000.0,
                            "total_generation_kw": avg_gen_mw * 1000.0,
                            "total_load_kw": avg_cons_mw * 1000.0,
                        }
                    )
                    await self.transport.send_islanding_event(
                        {
                            "timestamp": timestamp.isoformat(),
                            "mode": (
                                "islanded"
                                if self.island_manager.state.is_islanded
                                else "grid_connected"
                            ),
                            "trigger": (
                                "manual"
                                if not self.island_manager.state.is_islanded
                                else "none"
                            ),
                            "island_frequency_hz": self.frequency_model.state.frequency,
                            "power_balance_kw": imbalance_mw * 1000.0,
                        }
                    )
                    for cluster_id in self.vpp.clusters:
                        status = self.vpp.get_cluster_status(cluster_id)
                        await self.transport.send_vpp_dispatch(
                            {
                                "timestamp": timestamp.isoformat(),
                                "cluster_id": cluster_id,
                                "status": "active",
                                "total_capacity_kw": status.get(
                                    "total_capacity_kwh", 0.0
                                )
                                * 4.0,
                                "total_dispatch_kw": status.get(
                                    "total_gen_kw", 0.0
                                )
                                - status.get("total_cons_kw", 0.0),
                                "health_score": status.get("health_score", 100.0),
                                "carbon_saved_kg": status.get(
                                    "carbon_saved_g", 0.0
                                )
                                / 1000.0,
                                "num_meters": status.get("num_resources", 0),
                            }
                        )
                    await self.transport.send_simulation_step(
                        {
                            "timestamp": timestamp.isoformat(),
                            "status": "running",
                            "active_meters": len(self.meters),
                            "total_generation_kw": avg_gen_mw * 1000.0,
                            "total_consumption_kw": avg_cons_mw * 1000.0,
                            "net_balance_kw": imbalance_mw * 1000.0,
                            "readings_sent": len(readings),
                        }
                    )
                except Exception as metric_err:
                    logger.warning(
                        f"Failed to send advanced InfluxDB metrics: {metric_err}"
                    )
            else:
                logger.warning("Grid estimation failed to converge")

        except Exception as e:
            logger.error(f"Error in grid estimation loop: {e}", exc_info=True)




    async def _send_readings_async(self, timestamp: datetime, readings: list):
        # 3. Send readings in batch (IO bound) for better performance/UI consistency
        logger.info(f"Sending batch of {len(readings)} readings to transports...")

        # 4. Send telemetry batch only (ZK proof generation removed)
        try:
            await self.transport.send_batch(readings)
        except Exception as e:
            logger.error(f"Error sending telemetry batch: {e}")

        logger.info(f"Step complete at {timestamp}")


    def calculate_nodal_prices(self) -> Dict[int, float]:
        """
        Locational Marginal Pricing (LMP).
        Calculates prices at each bus based on TPA charges and grid congestion.
        """
        config = get_config()
        
        if self.net is None or not hasattr(self.net, 'res_line'):
            return {bus_idx: config.grid_purchase_rate for bus_idx in self.net.bus.index} if self.net else {}

        # 1. Start with regional base price
        base_price = config.grid_purchase_rate
        
        # 2. Add fixed TPA (Third Party Access) charges as baseline wheeling
        total_tpa = 0.0 # TPA charges removed
        # For simplicity, we assume the base_price already includes some margin, 
        # but LMP should reflect the granular cost of delivery.
        
        nodal_prices = {bus_idx: base_price + total_tpa for bus_idx in self.net.bus.index}
        
        # 3. Calculate congestion penalties based on line loading
        if hasattr(self, 'last_estimation_results') and self.last_estimation_results and self.last_estimation_results.converged and hasattr(self.net, 'res_line_est'):
             line_loadings = self.net.res_line_est.loading_percent
        else:
             line_loadings = self.net.res_line.loading_percent
        
        congestion_threshold = 85.0 # Start penalizing at 85%
        
        for idx, loading in line_loadings.items():
            if loading > congestion_threshold:
                # Penalty: increases linearly from 85% to 100%
                # At 100% loading, penalty equals 50% of base price
                penalty = ((loading - congestion_threshold) / (100.0 - congestion_threshold)) * (base_price * 0.5)
                
                # Apply penalty to the 'to_bus' and PROPAGATE DOWNSTREAM
                # In a distribution radial feeder, everything beyond the congested segment suffers.
                try:
                    target_bus = int(self.net.line.at[idx, 'to_bus'])
                    
                    # Propagation logic: find all buses connected downstream of target_bus
                    # This is simplified for radial networks
                    affected_buses = [target_bus]
                    
                    # Breadth-first search for downstream buses (assuming to_bus is further from slack)
                    queue = [target_bus]
                    visited = {target_bus}
                    while queue:
                        current = queue.pop(0)
                        # Find lines where from_bus is current
                        downstream_lines = self.net.line[self.net.line.from_bus == current]
                        for _, row in downstream_lines.iterrows():
                            next_bus = int(row.to_bus)
                            if next_bus not in visited:
                                affected_buses.append(next_bus)
                                visited.add(next_bus)
                                queue.append(next_bus)
                    
                    for bus_idx in affected_buses:
                        if bus_idx in nodal_prices:
                            nodal_prices[bus_idx] += penalty
                            
                    logger.info(f"  Line {idx} Congested ({loading:.1f}%) -> {len(affected_buses)} buses penalized by {penalty:.4f} THB/kWh")
                except Exception as e:
                    logger.error(f"Error propagating congestion penalty for line {idx}: {e}")
            
        self.net_nodal_prices = nodal_prices
        self.net_avg_nodal_price = sum(nodal_prices.values()) / len(nodal_prices) if nodal_prices else base_price
        return nodal_prices
    
    # ========================================================================
