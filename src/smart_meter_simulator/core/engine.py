"""
Simulation Engine for Smart Meter Simulator
Orchestrates the simulation of multiple smart meters with grid integration.
"""

import asyncio
import logging
import math
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

import numpy as np

from ..config import MeterType, SimulatorConfig, get_config
from ..models.reading import EnergyReading
from ..transport.base import TransportLayer
from ..utils.zk_worker import zk_pool
from .adr import ADRManager
from .analytics import GridAnalytics
from .attacker import FDI_Attacker
from .data_source import ProfileDataSource
from .db import DatabaseManager
from .frequency import FrequencyModel
from .island import IslandManager
from .market import MarketManager, MarketOrder
from .meter import SmartMeter
from .optimizer import OptimizationEngine
from .settlement import SettlementEngine
from .vpp import VPPManager
from .billing import ThaiBillingEngine
from ..config.thai_market import TariffCategory

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
        self.analytics = GridAnalytics()
        self.attacker = FDI_Attacker()
        self.optimizer = OptimizationEngine()
        self.market = MarketManager()
        self.vpp = VPPManager()
        self.settlement = SettlementEngine()
        self.adr = ADRManager()
        self.frequency_model = FrequencyModel()
        self.island_manager = IslandManager()
        
        config = get_config()
        self.interval = config.simulation_interval
        self.real_time_interval = 5 # Real seconds between ticks
        self.external_clock = False # Set to True for co-simulation (Phase 17)
        
        # Phase 1: Thai Billing Integration
        self.billing_engines: Dict[str, ThaiBillingEngine] = {}
        for meter in self.meters:
            # Map meter types to appropriate Thai Tariff Categories
            category = TariffCategory.TYPE_1_1_2
            if meter.config.get('meter_type') == MeterType.EV_CHARGER.value:
                category = TariffCategory.TYPE_1_3
            elif meter.config.get('meter_type') == MeterType.RESIDENTIAL.value and meter.config.get('base_consumption', 0) < 1.0:
                 category = TariffCategory.TYPE_1_1_1
            
            self.billing_engines[meter.meter_id] = ThaiBillingEngine(
                account_id=meter.meter_id,
                tariff_category=category
            )
        
        # Phase 3: Geo-SAM Integration
        self.solar_inventory = []
        self.bus_solar_capacity = {} # bus_idx -> total_kwp
        
        # Start 24 hours ago to ensure valid timestamps
        now = datetime.now(timezone.utc)
        self.current_sim_time = now - timedelta(hours=24)
        
        # Grid state
        self.last_estimation_results = None
        self.net = None
        self.meter_to_bus = {} # meter_id -> bus_index

        # Phase 31: Dynamic Simulation Controls
        self.weather_mode = "Sunny"
        self.grid_stress_multiplier = 1.0

        # Pre-initialize price attributes to avoid AttributeErrors before first tick
        self.net_nodal_prices = {} 
        self.net_avg_nodal_price = 0.28
        self.last_carbon_intensity = 250.0 # Phase 22
        
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
                # Build network using adapter's intelligence (topology builder)
                self.net, self.meter_to_bus = self.adapter.build_network_from_meters(self.meters)
                self.net_nodal_prices = {}
                
                # Initialize static elements (Loads/Sgens) for each meter
                for meter in self.meters:
                    # Register with VPP (Phase 10)
                    self.vpp.register_meter(
                        meter.meter_id, 
                        meter.config, 
                        {"battery_level": meter.battery_level}
                    )

                    bus_idx = self.meter_to_bus.get(meter.meter_id)
                    if bus_idx is not None:
                        pp.create_load(self.net, bus=bus_idx, p_mw=0, q_mvar=0, name=f"L_{meter.meter_id}")
                        if meter.config.get('has_solar'):
                            pp.create_sgen(self.net, bus=bus_idx, p_mw=0, q_mvar=0, name=f"G_{meter.meter_id}")
                
                logger.info(f"Initialized grid topology: {len(self.net.bus)} buses, {len(self.net.line)} lines, {len(self.meters)} meters mapped")
                
                # Phase 3: Geo-SAM Integration - Load and map solar inventory
                if self.db_manager:
                    self.solar_inventory = await self.db_manager.get_all_solar_inventory()
                    if self.solar_inventory:
                        self._map_solar_to_grid()
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
        """Stop the simulation."""
        self.running = False
        await self.transport.disconnect()
        if self.db_manager and hasattr(self, 'session_id'):
            await self.db_manager.close_session(self.session_id)
        
        # Shutdown multiprocessing workers
        zk_pool.shutdown()
        
        logger.info("Simulation stopped")
        
    async def disconnect_grid(self):
        """Force disconnection from main grid (Islanding)."""
        if self.adapter and self.net:
            success = self.island_manager.disconnect(self.net, self.meters, self.meter_to_bus)
            if success:
                logger.warning("MICROGRID ISLANDED SUCCESSFULLY")
                # Phase 12: Notify Transport of critical event
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
                # Phase 19: Restore all shedded loads
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
        if timestamp:
            self.current_sim_time = timestamp
        timestamp = self.current_sim_time
        
        # 1. Generate readings
        readings: List[EnergyReading] = []
        
        # Batch fetch playback data if in PLAYBACK mode
        playback_data = {}
        if self.mode == SimulationMode.PLAYBACK and self.playback_profile:
            playback_data = self.data_source.get_values_batch(self.playback_profile, timestamp)
            
            # Phase 4: Data Source Management 
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
                    
        # 0.5 Generate Forecasts and Optimization Signals (Phase 9)
        meter_ids = [m.meter_id for m in self.meters]
        
        # Dynamic Tariff & Price Forecast & ADR
        current_tariff = self.market.tariff_manager.get_current_tariff(timestamp)
        price_forecast = np.array(self.market.tariff_manager.get_forecast(timestamp, horizon_steps=24))
        
        # Apply ADR Modifiers
        adr_modifier = self.adr.get_tariff_modifier(timestamp)
        
        # Handle ADR Frequency Deviation Events
        adr_frequency = self.adr.get_frequency_deviation(timestamp)
        if adr_frequency is not None:
            self.frequency_model.set_frequency(adr_frequency)
            logger.info(f"ADR Frequency Event: Setting frequency to {adr_frequency} Hz")
        
        if adr_modifier != 1.0:
            current_tariff.import_rate *= adr_modifier
            current_tariff.is_peak = True # Force peak status during event
            price_forecast = price_forecast * adr_modifier # Broadcast effect on forecast too
            
            # Phase 15 & 16: Execute VPP Balancing if ADR is active
            # SECURITY GATE: Suspend VPP if under active attack (Phase 16)
            is_under_attack = self.last_estimation_results.bad_data_detected if self.last_estimation_results else False
            
            if is_under_attack:
                logger.error("VPP OPERATIONS SUSPENDED: Grid under active attack. Suspending coordination for safety.")
                # Reset dispatch for all
                for m in self.meters: m.receive_dispatch(0.0)
            else:
                # Phase 21: Map nodal prices to meters for VPP (LMP)
                meter_prices = {}
                if self.net: # Check engine's stored prices, not net attributes
                    for m in self.meters:
                        b_idx = self.meter_to_bus.get(m.meter_id)
                        if b_idx is not None:
                            meter_prices[m.meter_id] = self.net_nodal_prices.get(b_idx, 0.25)

                if adr_modifier != 1.0:
                    # If ADR modifier > 1.0 (Peak), we want to DISCHARGE (target > 0)
                    for cluster_id in self.vpp.clusters:
                        status = self.vpp.get_cluster_status(cluster_id)
                        if status.get("flex_up_kw", 0) > 0:
                            target_kw = status["flex_up_kw"] * 0.2
                            dispatches = self.vpp.dispatch_cluster(cluster_id, target_kw, nodal_prices=meter_prices)
                            for m_id, kw in dispatches.items():
                                m_obj = next((m for m in self.meters if m.meter_id == m_id), None)
                                if m_obj: m_obj.receive_dispatch(kw)
                        else:
                            # Reset dispatch if no flexibility
                            for m_id in self.vpp.clusters[cluster_id].resources:
                                m_obj = next((m for m in self.meters if m.meter_id == m_id), None)
                                if m_obj: m_obj.receive_dispatch(0.0)
                else:
                    # AFRR Response (No active ADR)
                    freq = self.frequency_model.state.frequency
                    if abs(freq - 50.0) > 0.02:
                        for cluster_id in self.vpp.clusters:
                            target_kw = self.vpp.calculate_afrr_response(cluster_id, freq)
                            if target_kw != 0:
                                dispatches = self.vpp.dispatch_cluster(cluster_id, target_kw, nodal_prices=meter_prices)
                                for m_id, kw in dispatches.items():
                                    m_obj = next((m for m in self.meters if m.meter_id == m_id), None)
                                    if m_obj: m_obj.receive_dispatch(kw)
                    else:
                        # Frequency is healthy, reset all specific VPP dispatches
                        for m in self.meters:
                            if m.vpp_dispatch_kw != 0:
                                m.receive_dispatch(0.0)
        
        # Phase 19: Intelligent Grid Healing (Islanding Stability)
        if self.island_manager.state.is_islanded:
            freq = self.frequency_model.state.frequency
            # Trigger Black Start if frequency collapsed
            if freq < 47.0:
                 self.island_manager.black_start_sequence(self.vpp)
            
            # Orchestrate stability across all microgrid clusters
            for cluster_id in self.vpp.clusters:
                # Approx current imbalance based on last reported values 
                # (Reading generation starts after this block)
                recent_gen = sum(m.last_cons_noise for m in self.meters) # Mock lookup
                # Actually, VPP knows current status from update_meter_state
                # For Phase 19, we use VPP's internal cluster status
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
            meter.receive_price_signal(current_tariff)
            meter.receive_frequency(self.frequency_model.state.frequency)
            
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
            
            # Phase 31: Apply Grid Stress Multiplier
            if self.grid_stress_multiplier != 1.0 and override_cons is None:
                # We'll apply it during calculation in generate_reading if we don't have an override
                # But for immediate feedback, let's inject it into the base calculation
                pass # Already handled by meter.generate_reading if we update it
            
            # AI-Driven Optimization (Phase 9)
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
                    price_forecast=price_forecast
                )
            
            reading = meter.generate_reading(
                timestamp, 
                override_gen=override_gen, 
                override_cons=override_cons,
                forced_dispatch=forced_dispatch,
                interval_seconds=self.interval,
                grid_stress=self.grid_stress_multiplier
            )
            
            # Phase 25: Sync with real blockchain via API Gateway
            if meter.config.get('wallet_address'):
                # We could fetch this in every tick, but performance-wise we might want to throttle
                # For now, let's try direct sync
                try:
                    import aiohttp
                    # All services now reachable via Kong on PORT 4000
                    gateway_url = self.config.get('api_gateway_url', 'http://localhost:4000')
                    url = f"{gateway_url}/api/v1/wallets/{meter.config['wallet_address']}/balance"
                    
                    # Store session on self if not exists for connection pooling
                    if not hasattr(self, '_http_session'):
                        self._http_session = aiohttp.ClientSession()
                    
                    async with self._http_session.get(url, timeout=1.0) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            reading.is_synced_with_solana = True
                            reading.solana_sol_balance = data.get('sol_balance', 0.0)
                            reading.solana_gtnx_balance = data.get('grx_balance', 0.0)
                except Exception as e:
                    logger.debug(f"Failed to sync blockchain balance for {meter.meter_id}: {e}")

            readings.append(reading)
            meter.last_reading = reading
            
            # VPP State Update
            hours = reading.interval_seconds / 3600.0
            p_cons = (reading.energy_consumed / hours) if hours > 0 else 0.0
            p_gen = (reading.energy_generated / hours) if hours > 0 else 0.0
            self.vpp.update_meter_state(meter.meter_id, meter.battery_level, p_cons=p_cons, p_gen=p_gen)
            
            # Sync Shedding State (Phase 19)
            if meter.meter_id in self.vpp.meter_map:
                cid = self.vpp.meter_map[meter.meter_id]
                meter.is_shed = self.vpp.clusters[cid].resources[meter.meter_id].is_shed
            
            # Market Dynamics (Collect Orders)
            params = meter.get_bid_params(reading)
            if params:
                self.market.submit_order(MarketOrder(
                    meter_id=meter.meter_id,
                    is_buy=params["is_bid"],
                    amount=params["amount"],
                    price=meter.config.get('max_buy_price' if params["is_bid"] else 'max_sell_price', 0.25),
                    timestamp=timestamp,
                    latitude=meter.config.get('latitude'),
                    longitude=meter.config.get('longitude'),
                    bus_id=self.meter_to_bus.get(meter.meter_id)
                ))
            
        # 1.5 Intercept with FDI Attacker (Cyber-security Simulation)
        readings = self.attacker.intercept(readings)

        # 2. Run Grid Estimation (Digital Twin)
        if self.adapter and self.net:
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
                    if bus_idx is None: continue
                    
                    # Convert values (kWh -> MW) using actual interval
                    hours = reading.interval_seconds / 3600.0
                    p_mw = (reading.energy_consumed / hours / 1000.0) if hours > 0 else 0.0
                    p_gen_mw = (reading.energy_generated / hours / 1000.0) if hours > 0 else 0.0
                    q_mvar = p_mw * 0.3 # Assumed
                    
                    # Store updates for batch application
                    load_indices = self.net.load[self.net.load.bus == bus_idx].index
                    if len(load_indices) > 0:
                        load_idx = int(load_indices[0])
                        load_updates_p[load_idx] = p_mw
                        load_updates_q[load_idx] = q_mvar
                        
                        # Add measurements (Nodal instead of element-based for better observability)
                        self.adapter.builder.add_active_power_measurement(
                            meter.meter_id, bus_idx, p_mw, 
                            meter.config.get('meter_type', MeterType.GRID_CONSUMER),
                            element_type='bus'
                        )
                        self.adapter.builder.add_reactive_power_measurement(
                            meter.meter_id, bus_idx, q_mvar, 
                            meter.config.get('meter_type', MeterType.GRID_CONSUMER),
                            element_type='bus'
                        )
                    
                    # Store sgen updates
                    sgen_indices = self.net.sgen[self.net.sgen.bus == bus_idx].index
                    if len(sgen_indices) > 0:
                        sgen_idx = int(sgen_indices[0])
                        sgen_updates_p[sgen_idx] = p_gen_mw
                        
                        self.adapter.builder.add_active_power_measurement(
                            meter.meter_id + "_GEN", bus_idx, -p_gen_mw, 
                            meter.config.get('meter_type', MeterType.SOLAR_PROSUMER),
                            is_generation=True,
                            element_type='bus'
                        )
                        
                    # Add voltage measurements
                    voltage_pu = (reading.voltage * np.sqrt(3)) / (self.net.bus.vn_kv.at[bus_idx] * 1000)
                    self.adapter.builder.add_voltage_measurement(
                        meter.meter_id, bus_idx, voltage_pu,
                        meter.config.get('meter_type', MeterType.GRID_CONSUMER)
                    )
                
                # Apply updates in batch for better performance
                if load_updates_p:
                    self.net.load.loc[list(load_updates_p.keys()), 'p_mw'] = list(load_updates_p.values())
                    self.net.load.loc[list(load_updates_q.keys()), 'q_mvar'] = list(load_updates_q.values())
                if sgen_updates_p:
                    self.net.sgen.loc[list(sgen_updates_p.keys()), 'p_mw'] = list(sgen_updates_p.values())
                
                # 2.2 Inject Pseudo-measurements for unobserved buses (Phase 3 foundation)
                self._inject_pseudo_measurements()
                
                # Add Slack Bus voltage measurement for stability
                if len(self.net.ext_grid) > 0:
                    slack_bus = self.net.ext_grid.bus.values[0]
                    self.adapter.builder.add_voltage_measurement(
                        "SB_01", slack_bus, 1.0, MeterType.BATTERY_STORAGE
                    )
                
                # Assign measurements to net
                self.net.measurement = self.adapter.get_measurement_table()
                
                # Run power flow first to provide initial guess
                # Use robust settings to handle realistic/high-load scenarios
                pf_converged = False
                try:
                    pp.runpp(self.net, algorithm='nr', calculate_voltage_angles=True,
                             max_iteration=30)
                    pf_converged = True
                except pp.LoadflowNotConverged:
                    logger.warning("Newton-Raphson failed to converge. Retrying with 'bfsw' algorithm...")
                    try:
                        # Fallback to Backward-Forward Sweep (usually more robust for radial/distribution)
                        pp.runpp(self.net, algorithm='bfsw', calculate_voltage_angles=True,
                                 max_iteration=50)
                        pf_converged = True
                    except pp.LoadflowNotConverged:
                        logger.warning("Power Flow failed both 'nr' and 'bfsw'. Checking observability...")
                        # Diagnostic: Check observability before failing
                        if not estimator.check_observability(self.net):
                            logger.error("SYSTEM IS NOT OBSERVABLE: Missing critical measurements or disconnected topology.")
                            # Emergency: Inject more pseudo-measurements if dead-end
                            self._inject_pseudo_measurements(force_all=True)
                        else:
                            logger.info("System is observable but PF failed to converge. Attempting estimation with flat start.")

                # Choose init strategy based on power flow result
                # When PF fails, res_bus has NaN/zero voltages which poison 'results' init
                est_init = 'results' if pf_converged else 'flat'
                
                # If power flow failed, reset bus voltages to flat start so estimation
                # doesn't encounter singular matrices from zero-voltage rows
                if not pf_converged:
                    self.net.res_bus['vm_pu'] = 1.0
                    self.net.res_bus['va_degree'] = 0.0
                
                # Run estimation with sanitization
                from ..adapters.state_estimator import StateEstimator, EstimationAlgorithm
                estimator = StateEstimator(algorithm=EstimationAlgorithm.WLS)
                results = estimator.run_sanitized_estimation(self.net, init=est_init, max_removals=10)
                self.last_estimation_results = results
                
                # Check for bad data detected and removed during sanitization
                if results.bad_data_detected:
                    logger.warning(f"Sanitization: Removed {len(results.bad_data_detected)} bad measurements: {results.bad_data_detected}")
                
                # Bad Data Detection on the FINAL results (Phase 3 enhancement)
                bad_data = estimator.detect_bad_data(self.net)
                if bad_data:
                    logger.warning(f"Residual Bad Data detected in cleaned results ({len(bad_data)} measurements): {bad_data}")
                
                # Calculate Nodal Prices based on congestion (Phase 21)
                self.calculate_nodal_prices()
                
                # Analyze Grid Health (Analytics Layer)
                report = self.analytics.analyze_step(self.net, results)
                
                # 2.3 Propagate results to individual meter readings for UI visibility
                if results and results.converged:
                    res_bus = self.net.res_bus
                    res_df = results.residuals
                    
                    for reading in readings:
                        bus_idx = self.meter_to_bus.get(reading.meter_id)
                        if bus_idx is not None:
                            # Estimated voltage from Digital Twin
                            reading.voltage_pu = float(res_bus.at[bus_idx, 'vm_pu'])
                            
                            # Phase 24: Enterprise Metrics
                            reading.nodal_price = self.net_nodal_prices.get(bus_idx, 0.50)
                            reading.carbon_intensity = getattr(self, 'last_carbon_intensity', 0.0)

                            # Residual Monitoring
                            meter_res = res_df[res_df.measurement == reading.meter_id]
                            if not meter_res.empty:
                                val = float(meter_res.iloc[0]['norm_residual'])
                                reading.norm_residual = val
                                reading.ewma_residual = self.analytics.residual_ewma.get(reading.meter_id, val)
                                reading.is_compromised = val > 4.0 or reading.ewma_residual > 2.0
                                
                # Phase 12: Update Frequency Model
                # Calculate system-wide imbalance (MW)
                # Convert kWh (over 15 mins) to avg Power (kW) -> MW
                total_gen_kwh = sum(r.energy_generated for r in readings)
                total_cons_kwh = sum(r.energy_consumed for r in readings)
                
                # Avg Power = Energy / Time
                # Time = 0.25 hours
                avg_gen_mw = (total_gen_kwh / 0.25) / 1000.0
                avg_cons_mw = (total_cons_kwh / 0.25) / 1000.0
                
                imbalance_mw = avg_gen_mw - avg_cons_mw
                
                # Phase 22: Calculate Carbon Intensity (every tick)
                # Intensity = (Grid_Power / Total_Load) * Grid_Intensity_Factor
                # Grid_Intensity_Factor for Thailand is approx. 450-500 g CO2/kWh
                grid_p_mw = self.net.res_ext_grid.p_mw.sum() if self.net and hasattr(self.net, 'res_ext_grid') else 0.0
                total_load_mw = self.net.res_load.p_mw.sum() if self.net and hasattr(self.net, 'res_load') else 1.0
                # If all power is from grid, intensity is 500. If all from local solar, intensity is 0.
                self.last_carbon_intensity = max(0.0, (grid_p_mw / total_load_mw) * 500.0) if total_load_mw > 0 else 500.0

                # Step the frequency model using real-time interval (e.g., 5 seconds) to show dynamics
                self.frequency_model.step(imbalance_mw, self.real_time_interval)
                
                # Phase 13: AFRR / VPP Logic
                # Dispatch VPP based on frequency deviation
                freq = self.frequency_model.state.frequency
                if abs(freq - 50.0) > 0.02:
                    # Calculate AFRR
                    for cluster_id in self.vpp.clusters:
                        target_kw = self.vpp.calculate_afrr_response(cluster_id, freq)
                        if target_kw != 0:
                            # Phase 21: Pass Nodal Prices to VPP logic
                            # Map bus prices to meter prices
                            meter_prices = {}
                            if self.net: 
                                for m in self.meters:
                                    b_idx = self.meter_to_bus.get(m.meter_id)
                                    if b_idx is not None:
                                        meter_prices[m.meter_id] = self.net_nodal_prices.get(b_idx, 0.25)
                            
                            # Phase 22: Pass Carbon Intensity (already calculated above)
                            
                            dispatches = self.vpp.dispatch_cluster(
                                cluster_id, target_kw, 
                                nodal_prices=meter_prices, 
                                carbon_intensity=self.last_carbon_intensity
                            )
                            # Apply dispatches
                            for mid, kw in dispatches.items():
                                for m in self.meters:
                                    if m.meter_id == mid:
                                        m.receive_dispatch(kw)
                else:
                    # Frequency is healthy, reset all specific VPP dispatches
                    for m in self.meters:
                        if m.vpp_dispatch_kw != 0:
                            m.receive_dispatch(0.0)


                # Broadcast results via transport
                if results and results.converged:
                    # Map to GridHealth interface expected by UI
                    # Phase 9 & 10: Market & Settlement
                    market_results = self.market.clear_market(timestamp, self.net_nodal_prices)
                    self.settlement.process_interval(timestamp, readings, market_results)

                    # Phase 1: Thai Billing Integration
                    # Record transactions for each meter in its billing engine
                    trades = market_results.get("trades", [])
                    p2p_buy_volumes = {} # meter_id -> kwh
                    p2p_sell_volumes = {} # meter_id -> kwh
                    
                    for trade in trades:
                        b_id, s_id = trade["buyer"], trade["seller"]
                        amt, prc = trade["amount"], trade["price"]
                        surcharge = trade.get("locational_surcharge", 0.0)
                        
                        p2p_buy_volumes[b_id] = p2p_buy_volumes.get(b_id, 0.0) + amt
                        p2p_sell_volumes[s_id] = p2p_sell_volumes.get(s_id, 0.0) + amt
                        
                        if b_id in self.billing_engines:
                            self.billing_engines[b_id].add_p2p_purchase(amt, prc, s_id, timestamp, locational_surcharge_baht_kwh=surcharge)
                        if s_id in self.billing_engines:
                            self.billing_engines[s_id].add_p2p_sale(amt, prc, b_id, timestamp)

                    for reading in readings:
                        m_id = reading.meter_id
                        if m_id not in self.billing_engines: continue
                        engine = self.billing_engines[m_id]
                        
                        # Physical Net at Grid Connection Point
                        physical_net = reading.deficit_energy - reading.surplus_energy
                        p2p_net = p2p_buy_volumes.get(m_id, 0.0) - p2p_sell_volumes.get(m_id, 0.0)
                        financial_grid_flow = physical_net - p2p_net
                        
                        if financial_grid_flow > 0:
                            engine.add_grid_consumption(financial_grid_flow, timestamp)
                        elif financial_grid_flow < 0:
                            engine.add_grid_export(abs(financial_grid_flow), timestamp)
                            
                        # Record solar generation if any
                        if reading.energy_generated > 0:
                            # Split into self-consumption and export is handled by financial_grid_flow logic above
                            # for billing, but we record the total for stats
                            # self_consumption_ratio is approximated here or can be calculated
                            # For now, record the reading's generated energy
                            engine.add_solar_generation(reading.energy_generated, timestamp, self_consumption_ratio=0.5)

                    # report is a dict from analytics.analyze_step()
                    broadcast_dict = {
                        "timestamp": timestamp.isoformat(),
                        "total_generation": float(avg_gen_mw),
                        "total_consumption": float(avg_cons_mw),
                        "total_loss_mw": float(report.get("total_loss_mw", 0.0)),
                        "net_balance": float(imbalance_mw),
                        "active_meters": int(len(self.meters)),
                        "co2_saved_kg": float(total_gen_kwh * 0.431),
                        "avg_voltage_pu": float(report.get("avg_voltage_pu", 1.0)),
                        "max_voltage_pu": float(report.get("max_voltage_pu", 1.0)),
                        "min_voltage_pu": float(report.get("min_voltage_pu", 1.0)),
                        "num_violations": int(report.get("num_violations", 0)),
                        "loss_percentage": float(report.get("loss_percentage", 0.0)),
                        "health_score": float(report.get("health_score", 100.0)),
                        "is_under_attack": bool(report.get("is_under_attack", False)),
                        "anomaly_score": float(report.get("anomaly_score", 0.0)),
                        "attack_alerts": report.get("attack_alerts", []),
                        # Phase 21 & 22: Advanced Metrics
                        "avg_nodal_price": float(report.get("avg_nodal_price", 0.0)),
                        "carbon_intensity": float(getattr(self, 'last_carbon_intensity', 0.0)),
                        
                        # Phase 31: Dynamic Context
                        "weather_mode": self.weather_mode,
                        "grid_stress": self.grid_stress_multiplier,
                        
                        # Phase 9: Market Clearing
                        "market": market_results,
                        # Phase 10: VPP Status
                        "vpp": self.vpp.get_cluster_status("Default_VPP"),
                        # Phase 10: Settlement
                        "settlement": {
                            "total_grid_revenue": sum(a.grid_export_kwh * get_config().grid_feed_in_rate for a in self.settlement.accounts.values()),
                            "total_grid_cost": sum(a.grid_import_kwh * get_config().grid_purchase_rate for a in self.settlement.accounts.values()),
                            "total_p2p_volume": sum(a.p2p_buy_kwh for a in self.settlement.accounts.values())
                        },
                        # Phase 1: Thai Billing Summary (Aggregate)
                        "thai_billing": {
                            "total_net_amount": sum(
                                engine.generate_monthly_bill(timestamp.month, timestamp.year).net_amount_baht 
                                for engine in self.billing_engines.values()
                            ),
                            "total_p2p_savings": sum(
                                engine.get_billing_summary(timestamp.month, timestamp.year).total_p2p_savings_baht
                                for engine in self.billing_engines.values()
                            ),
                            "avg_cost_kwh": (
                                sum(engine.get_billing_summary(timestamp.month, timestamp.year).average_cost_per_kwh_baht 
                                    for engine in self.billing_engines.values()) / len(self.billing_engines)
                            ) if self.billing_engines else 0
                        },
                        # Phase 11: Tariff & ADR
                        "tariff": {
                            "type": current_tariff.tariff_type,
                            "import_rate": current_tariff.import_rate,
                            "export_rate": current_tariff.export_rate,
                            "is_peak": current_tariff.is_peak,
                            "forecast": price_forecast.tolist()
                        },
                        "adr_event": {
                            "active": bool(self.adr.get_active_event(timestamp)),
                            "type": self.adr.get_active_event(timestamp).event_type.value if self.adr.get_active_event(timestamp) else None,
                            "modifier": float(adr_modifier)
                        },
                        # Phase 12: Frequency
                        "frequency": {
                            "value": float(self.frequency_model.state.frequency),
                            "rocof": float(self.frequency_model.state.rocof),
                            "angle": float(self.frequency_model.state.angle_deg)
                        },
                        "island_status": {
                             "is_islanded": self.island_manager.state.is_islanded,
                             "forming_meter": self.island_manager.state.grid_forming_meter_id
                        },
                        # Phase 13: Load Forecasting
                        "load_forecast": self._calculate_aggregate_forecast(timestamp),
                        # Phase 14: EV Fleet
                        "ev_fleet": {
                            "total_evs": int(len([m for m in self.meters if MeterType(m.config['meter_type']) == MeterType.EV_CHARGER])),
                            "avg_soc": float(sum(m.battery_level for m in self.meters if MeterType(m.config['meter_type']) == MeterType.EV_CHARGER) / len([m for m in self.meters if MeterType(m.config['meter_type']) == MeterType.EV_CHARGER])) if any(MeterType(m.config['meter_type']) == MeterType.EV_CHARGER for m in self.meters) else 0.0,
                            "v2g_active": int(sum(1 for m in self.meters if MeterType(m.config['meter_type']) == MeterType.EV_CHARGER and 18 <= timestamp.hour <= 21 and m.battery_level > (get_config().ev_v2g_threshold_soc * 100))),
                            "available_capacity_kwh": float(sum(m.config.get('ev_battery_capacity', get_config().ev_battery_capacity_max) for m in self.meters if MeterType(m.config['meter_type']) == MeterType.EV_CHARGER))
                        },
                        # Phase 15: VPP Clusters
                        "vpp_clusters": self.vpp.get_all_cluster_statuses(),
                        # Compatibility fields
                        "chi2": float(results.chi2_statistic or 0),
                        "num_measurements": int(results.num_measurements)
                    }
                    
                    # Phase 13 Debugging
                    if "load_forecast" in broadcast_dict:
                        fc = broadcast_dict["load_forecast"]
                        logger.info(f"📊 Sending Grid Forecast: Gen[0]={fc['generation'][0]:.2f}, Cons[0]={fc['consumption'][0]:.2f} MW")
                        
                    await self.transport.send_grid_status(broadcast_dict)
                    logger.info(f"Grid estimation converged: chi2={results.chi2_statistic if results.chi2_statistic is not None else 0:.4f}")

                    # Persistence (Phase 5)
                    if self.db_manager:
                        asyncio.create_task(self.db_manager.save_grid_metrics({
                            "timestamp": timestamp,
                            "imbalance_mw": float(imbalance_mw),
                            "avg_voltage_pu": float(report.get("avg_voltage_pu", 1.0)),
                            "health_score": float(report.get("health_score", 100.0)),
                            "avg_nodal_price": float(report.get("avg_nodal_price", 0.0)),
                            "carbon_intensity": float(report.get("carbon_intensity", 0.0)),
                            "total_loss_mw": float(report.get("total_loss_mw", 0.0)),
                            "frequency_hz": float(self.frequency_model.state.frequency)
                        }))
                else:
                    logger.warning("Grid estimation failed to converge")
                    
            except Exception as e:
                logger.error(f"Error in grid estimation loop: {e}", exc_info=True)

        # 3. Send readings (Async)
        await self._send_readings_async(timestamp, readings)
        
        # Advance simulated time
        self.current_sim_time += timedelta(seconds=self.interval)

    def _calculate_aggregate_forecast(self, start_time: datetime, horizon_steps: int = 24) -> Dict[str, List[float]]:
        """
        Calculate aggregate generation and consumption forecast for the next N steps.
        """
        gen_forecast = []
        cons_forecast = []
        
        for i in range(horizon_steps):
            future_time = start_time + timedelta(minutes=15 * i)
            step_gen = 0.0
            step_cons = 0.0
            
            for meter in self.meters:
                # Use internal calculation methods without updating state
                # Note: These methods are deterministic based on time/weather except for noise
                # For forecast, we ignore noise.
                
                # Solar forecast
                if meter.config.get('has_solar'):
                    hour = future_time.hour + future_time.minute / 60.0
                    if 6 <= hour <= 18:
                        time_factor = math.sin(math.pi * (hour - 6) / 12) ** 2
                        capacity = meter.config.get('solar_capacity', 5.0)
                        efficiency = meter.config.get('panel_efficiency', 0.18)
                        # Assume Sunny for forecast
                        step_gen += (capacity * time_factor * efficiency * 2)
                
                # Consumption forecast (Simplified version of _calculate_consumption)
                meter_type = MeterType(meter.config['meter_type'])
                base = meter.config.get('base_consumption', 1.0)
                meter_offset = (hash(meter.meter_id) % 100) / 100.0
                hour = future_time.hour + future_time.minute / 60.0
                weekday = future_time.weekday() < 5
                
                factor = 1.0
                if meter_type in [MeterType.RESIDENTIAL, MeterType.SOLAR_PROSUMER, MeterType.HYBRID_PROSUMER]:
                    m_peak_time = 7.5 + (meter_offset * 1.5)
                    e_peak_time = 18.5 + (meter_offset * 2.0)
                    m_peak = 0.8 * math.exp(-((hour - m_peak_time) ** 2) / (2 * 1.2 ** 2))
                    e_peak = 1.5 * math.exp(-((hour - e_peak_time) ** 2) / (2 * 2.5 ** 2))
                    factor = (1.2 + m_peak * 0.5 + e_peak * 1.2 + 0.3 * math.sin(math.pi * hour / 24)) if not weekday else (0.6 + m_peak + e_peak)
                elif meter_type == MeterType.COMMERCIAL:
                    business_hours = 1.8 if (9 <= hour <= 17) else 0.4
                    if 7 <= hour < 9: business_hours = 0.4 + (1.4 * (hour - 7) / 2.0)
                    elif 17 < hour <= 19: business_hours = 1.8 - (1.4 * (hour - 17) / 2.0)
                    factor = business_hours + meter_offset * 0.2 if weekday else (0.3 + meter_offset * 0.1)
                else:
                    factor = 1.0 + 0.2 * math.sin(2 * math.pi * hour / 24) + meter_offset
                
                step_cons += (base * factor)
                
            # Convert units (kWh -> MW) same way as current measurements
            gen_forecast.append(round((step_gen / 1000.0) * 4.0, 4))
            cons_forecast.append(round((step_cons / 1000.0) * 4.0, 4))
            
        return {
            "generation": gen_forecast,
            "consumption": cons_forecast,
            "carbon_intensity": [round(max(50.0, 500.0 - (g * 50.0)), 1) for g in gen_forecast]
        }


    def _map_solar_to_grid(self):
        """
        Phase 3: Spatial matching of detected solar panels to the nearest grid bus.
        Uses bus_geocoord in the pandapower net.
        """
        if not self.net or not self.solar_inventory:
            return

        if 'bus_geocoord' not in self.net or self.net.bus_geocoord is None:
            logger.warning("Geo-SAM: Cannot perform spatial matching - net.bus_geocoord is missing")
            return

        from scipy.spatial import KDTree
        
        # Prepare bus coordinates
        bus_coords = self.net.bus_geocoord[['x', 'y']].values # [lng, lat]
        bus_indices = self.net.bus_geocoord.index.tolist()
        tree = KDTree(bus_coords)
        
        matched_count = 0
        total_kwp = 0.0
        self.bus_solar_capacity = {}
        
        for panel in self.solar_inventory:
            geom = panel.get('geometry', {})
            if geom.get('type') == 'Point':
                coords = geom.get('coordinates', [])
                if len(coords) == 2:
                    # coords is [lng, lat]
                    dist, idx_in_bus_coords = tree.query(coords)
                    
                    # Heuristic threshold: 100 meters (~0.0009 degrees at equator)
                    if dist < 0.001:
                        bus_idx = bus_indices[idx_in_bus_coords]
                        
                        # Calculate capacity: Area * 0.15 kW/m2 (or use pre-calculated potential)
                        kwp = panel.get('kwp_potential')
                        if kwp is None:
                            area = panel.get('area_sqm', 0)
                            kwp = area * 0.15
                        
                        self.bus_solar_capacity[bus_idx] = self.bus_solar_capacity.get(bus_idx, 0.0) + kwp
                        matched_count += 1
                        total_kwp += kwp
        
        if matched_count > 0:
            logger.info(f"[Geo-SAM] Matched {matched_count} solar features to {len(self.bus_solar_capacity)} buses. Total Capacity: {total_kwp:.2f} kWp")

    async def _send_readings_async(self, timestamp: datetime, readings: list):
        # 3. Send readings in batch (IO bound) for better performance/UI consistency
        logger.info(f"Sending batch of {len(readings)} readings to transports...")

        # 4. Check for and send confidential bids (Parallelized)
        from ..utils.zk_worker import zk_pool

        config = get_config()
        batch_id = config.default_auction_batch
        bid_tasks = []
        bid_metadata = []

        for meter, reading in zip(self.meters, readings):
            params = meter.get_bid_params(reading)
            if params:
                # Dispatch heavy ZK work to process pool (Order already submitted to market)
                task = zk_pool.generate_bid_data_async(params["amount_u64"], params["price_u64"])
                bid_tasks.append(task)
                bid_metadata.append((meter, params))
        
        # Primary tasks list
        tasks = []
        tasks.append(self.transport.send_batch(readings))

        if bid_tasks:
            try:
                logger.info(f"Generating {len(bid_tasks)} ZK proofs in parallel using ZKWorkerPool...")
                results = await asyncio.gather(*bid_tasks)
                
                for (meter, params), result in zip(bid_metadata, results):
                    if result and result[0] is not None:
                        bid_payload = meter.from_worker_result(params, result)
                        tasks.append(self.transport.send_auction_bid(bid_payload, batch_id))
            except Exception as e:
                logger.error(f"Error generating ZK proofs: {e}")
        
        # Ensure all transport tasks are awaited
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        
        logger.info(f"Step complete at {timestamp}. Total tasks: {len(tasks)}")

    def _inject_pseudo_measurements(self, force_all: bool = False):
        """
        Inject pseudo-measurements for buses that don't have real meter readings.
        Transit nodes (zero-load, zero-gen) get rigid 'Virtual' measurements (P=0, Q=0).
        """
        if not self.net: return
        
        # Element-based measurements (v, p, q on buses/lines)
        # Handle case where measurement table might be empty
        try:
            observed_elements = set(self.net.measurement.element[self.net.measurement.element_type == 'bus'])
        except (AttributeError, KeyError):
            observed_elements = set()

        all_buses = set(self.net.bus.index)
        unobserved_buses = all_buses - observed_elements
        
        if not unobserved_buses and not force_all: return
        
        # If force_all is True, we ensure EVERY bus has a voltage measurement at least
        target_buses = all_buses if force_all else unobserved_buses
        
        from ..config import MeterType
        
        count = 0
        for bus_idx in target_buses:
            # Check if it's a zero-injection transit node (no load, no sgen, no ext_grid)
            has_load = not self.net.load[self.net.load.bus == bus_idx].empty
            has_sgen = not self.net.sgen[self.net.sgen.bus == bus_idx].empty
            is_slack = not self.net.ext_grid[self.net.ext_grid.bus == bus_idx].empty
            
            if not has_load and not has_sgen and not is_slack:
                # Transit node: known P=0, Q=0 with tight variance (near-zero injection constraint)
                # Use 0.001 instead of 0.00001 to allow for numerical tolerance in power flow
                self.adapter.builder.add_active_power_measurement(
                    f"Virtual_Bus{bus_idx}_P", bus_idx, 0.0, 
                    MeterType.SUBSTATION, 
                    std_dev=0.001, element_type='bus'
                )
                self.adapter.builder.add_reactive_power_measurement(
                    f"Virtual_Bus{bus_idx}_Q", bus_idx, 0.0, 
                    MeterType.SUBSTATION,
                    std_dev=0.001, element_type='bus'
                )
                # Add pseudo-voltage for transit nodes to aid convergence
                self.adapter.builder.add_voltage_measurement(
                    f"Virtual_Bus{bus_idx}_V", bus_idx, 1.0,
                    MeterType.SUBSTATION, std_dev=0.02
                )
                count += 3
            elif not is_slack:
                # Non-zero injection but no meter: inject pseudo P, Q, V from nominal model values
                nominal_p = 0.0
                nominal_q = 0.0
                load_at_bus = self.net.load[self.net.load.bus == bus_idx]
                sgen_at_bus = self.net.sgen[self.net.sgen.bus == bus_idx]
                if not load_at_bus.empty:
                    nominal_p = float(load_at_bus.p_mw.sum())
                    nominal_q = float(load_at_bus.q_mvar.sum())
                
                # Phase 3: Geo-SAM Enhanced Injection
                # If we have detected solar capacity at this unobserved bus, inject it
                if bus_idx in self.bus_solar_capacity:
                    kwp = self.bus_solar_capacity[bus_idx]
                    # Calculate current generation based on time of day (similar to meter.py)
                    hour = self.current_sim_time.hour + self.current_sim_time.minute / 60.0
                    time_factor = 0.0
                    if 6 <= hour <= 18:
                        time_factor = math.sin(math.pi * (hour - 6) / 12) ** 2
                    
                    # Assume panel efficiency 0.15 (standard) and "Sunny" for pseudo-gen
                    # Or use a more refined weather factor if available in engine
                    gen_mw = (kwp * time_factor * 0.8) / 1000.0 # 0.8 is approx weather factor
                    nominal_p -= gen_mw
                    logger.debug(f"  Geo-SAM: Adding {gen_mw*1000:.2f} kW pseudo-gen to Bus {bus_idx}")

                if not sgen_at_bus.empty:
                    nominal_p -= float(sgen_at_bus.p_mw.sum())
                
                self.adapter.builder.add_active_power_measurement(
                    f"Pseudo_Bus{bus_idx}_P", bus_idx, nominal_p,
                    MeterType.GRID_CONSUMER, std_dev=max(abs(nominal_p) * 0.3, 0.01),
                    element_type='bus'
                )
                self.adapter.builder.add_reactive_power_measurement(
                    f"Pseudo_Bus{bus_idx}_Q", bus_idx, nominal_q,
                    MeterType.GRID_CONSUMER, std_dev=max(abs(nominal_q) * 0.3, 0.01),
                    element_type='bus'
                )
                self.adapter.builder.add_voltage_measurement(
                    f"Pseudo_Bus{bus_idx}_V", bus_idx, 1.0, 
                    MeterType.GRID_CONSUMER, std_dev=0.05
                )
                count += 3
                
        if count > 0:
            logger.debug(f"Injected {count} pseudo/virtual measurements for {len(unobserved_buses)} unobserved buses")
    def calculate_nodal_prices(self) -> Dict[int, float]:
        """
        Phase 21: Locational Marginal Pricing (LMP).
        Calculates prices at each bus based on TPA charges and grid congestion.
        """
        config = get_config()
        from ..config import thai_market
        
        if self.net is None or not hasattr(self.net, 'res_line'):
            return {bus_idx: config.grid_purchase_rate for bus_idx in self.net.bus.index} if self.net else {}

        # 1. Start with regional base price
        base_price = config.grid_purchase_rate
        
        # 2. Add fixed TPA (Third Party Access) charges as baseline wheeling
        total_tpa = sum(c.rate_baht_per_kwh for c in thai_market.TPA_CHARGES)
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
