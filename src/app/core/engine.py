import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import List, Optional

from .meter import SmartMeter
from ..transport.base import TransportLayer
from ..models.reading import EnergyReading

logger = logging.getLogger(__name__)

from enum import Enum
from .data_source import ProfileDataSource
from .analytics import GridAnalytics
from .attacker import FDI_Attacker
from .db import DatabaseManager

class SimulationMode(Enum):
    RANDOM = "random"
    PLAYBACK = "playback"

class SimulationEngine:
    """
    Orchestrates the simulation of multiple smart meters.
    """
    
    def __init__(self, meters: List[SmartMeter], transport: TransportLayer, adapter: Optional[any] = None, db_manager: Optional[DatabaseManager] = None):
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
        
        self.interval = 15 * 60 # 15 minutes in seconds (simulated)
        self.real_time_interval = 5 # Real seconds between ticks
        # Start 24 hours ago to ensure valid timestamps
        now = datetime.now(timezone.utc)
        self.current_sim_time = now - timedelta(hours=24)
        
        # Grid state
        self.last_estimation_results = None
        self.net = None
        self.meter_to_bus = {} # meter_id -> bus_index
        
    async def start(self):
        """Start the simulation loop."""
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
                import pandapower as pp
                # Build network using adapter's intelligence (topology builder)
                self.net, self.meter_to_bus = self.adapter.build_network_from_meters(self.meters)
                
                # Initialize static elements (Loads/Sgens) for each meter
                # The network builder gives us the map, but we still need to create the Load/Sgen elements
                # if they weren't created by the builder (which they aren't, it only does topology)
                for meter in self.meters:
                    bus_idx = self.meter_to_bus.get(meter.meter_id)
                    if bus_idx is not None:
                        # Create initial load/sgen with zero power
                        # They will be updated in tick()
                        pp.create_load(self.net, bus=bus_idx, p_mw=0, q_mvar=0, name=f"L_{meter.meter_id}")
                        if meter.config.get('has_solar'):
                            pp.create_sgen(self.net, bus=bus_idx, p_mw=0, q_mvar=0, name=f"G_{meter.meter_id}")
                
                logger.info(f"Initialized grid topology: {len(self.net.bus)} buses, {len(self.net.line)} lines, {len(self.meters)} meters mapped")
            except Exception as e:
                logger.error(f"Failed to initialize grid topology: {e}")
        
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
        if self.db_manager and hasattr(self, 'session_id'):
            await self.db_manager.close_session(self.session_id)
        logger.info("Simulation stopped")
        
    async def tick(self):
        """Execute one simulation step."""
        timestamp = self.current_sim_time
        
        # 1. Generate readings
        readings: List[EnergyReading] = []
        for meter in self.meters:
            meter.update_weather("Sunny") 
            
            # Fetch historical data if in PLAYBACK mode
            override_gen = None
            override_cons = None
            if self.mode == SimulationMode.PLAYBACK and self.playback_profile:
                # Expect columns: meter_id_GEN and meter_id_CONS or just meter_id (defaults to CONS)
                override_gen = self.data_source.get_value(self.playback_profile, f"{meter.meter_id}_GEN", timestamp)
                override_cons = self.data_source.get_value(self.playback_profile, f"{meter.meter_id}_CONS", timestamp)
                
                # If neither GEN nor CONS found, try just the meter_id as CONS
                if override_gen is None and override_cons is None:
                    override_cons = self.data_source.get_value(self.playback_profile, meter.meter_id, timestamp)
            
            reading = meter.generate_reading(timestamp, override_gen=override_gen, override_cons=override_cons)
            readings.append(reading)
            meter.last_reading = reading
            
        # 1.5 Intercept with FDI Attacker (Cyber-security Simulation)
        readings = self.attacker.intercept(readings)

        # 2. Run Grid Estimation (Digital Twin)
        if self.adapter and self.net:
            try:
                import pandapower as pp
                import numpy as np
                from ..config import MeterType
                
                # Clear previous measurements
                self.adapter.builder.clear()
                
                # Update network elements and add measurements
                for meter, reading in zip(self.meters, readings):
                    bus_idx = self.meter_to_bus.get(meter.meter_id)
                    if bus_idx is None: continue
                    
                    # Convert values (kWh -> MW)
                    p_mw = reading.energy_consumed * 4.0 / 1000.0
                    p_gen_mw = reading.energy_generated * 4.0 / 1000.0
                    q_mvar = p_mw * 0.3 # Assumed
                    
                    # Update load elements
                    load_indices = self.net.load[self.net.load.bus == bus_idx].index
                    if len(load_indices) > 0:
                        load_idx = int(load_indices[0])
                        self.net.load.at[load_idx, 'p_mw'] = p_mw
                        self.net.load.at[load_idx, 'q_mvar'] = q_mvar
                        
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
                    
                    # Update sgen elements
                    sgen_indices = self.net.sgen[self.net.sgen.bus == bus_idx].index
                    if len(sgen_indices) > 0:
                        sgen_idx = int(sgen_indices[0])
                        self.net.sgen.at[sgen_idx, 'p_mw'] = p_gen_mw
                        # Add generation measurement as nodal injection (Generation is NEGATIVE load)
                        # Actually, better to keep it as load measurement but at bus.
                        # Nodal P injection = Gen - Load. 
                        # But SE usually supports multiple measurements at the same bus.
                        self.adapter.builder.add_active_power_measurement(
                            meter.meter_id + "_GEN", bus_idx, -p_gen_mw, # Injection is Gen - Load? 
                            # No, pandapower SE Nodal 'p' is bus injection (Gen - Load).
                            meter.config.get('meter_type', MeterType.SOLAR_PROSUMER),
                            is_generation=True,
                            element_type='bus'
                        )
                        
                    # Add remaining measurements (using the adapter's logic for consistency)
                    # We can use the helper we already have, but it re-creates elements.
                    # Instead, we just manually call the builder for the rest.
                    voltage_pu = (reading.voltage * np.sqrt(3)) / (self.net.bus.vn_kv.at[bus_idx] * 1000)
                    self.adapter.builder.add_voltage_measurement(
                        meter.meter_id, bus_idx, voltage_pu,
                        meter.config.get('meter_type', MeterType.GRID_CONSUMER)
                    )
                
                # Add Slack Bus voltage measurement for stability
                if len(self.net.ext_grid) > 0:
                    slack_bus = self.net.ext_grid.bus.values[0]
                    self.adapter.builder.add_voltage_measurement(
                        "SB_01", slack_bus, 1.0, MeterType.BATTERY_STORAGE
                    )
                
                # Assign measurements to net
                self.net.measurement = self.adapter.get_measurement_table()
                
                # Run power flow first to provide initial guess (NR algorithm)
                # Use recycling for performance (Phase 6)
                pp.runpp(self.net, algorithm='nr', calculate_voltage_angles=True,
                         recycle={'Ybus': True, 'trafo': True})
                
                # Run estimation
                from ..adapters.state_estimator import StateEstimator, EstimationAlgorithm
                estimator = StateEstimator(algorithm=EstimationAlgorithm.WLS)
                results = estimator.run_estimation(self.net)
                self.last_estimation_results = results
                
                # Analyze Grid Health (Analytics Layer)
                self.analytics.analyze_step(self.net, results)
                
                # Broadcast results via transport
                if results and results.converged:
                    broadcast_dict = {
                        "converged": True,
                        "num_measurements": results.num_measurements,
                        "mae": float(results.mean_absolute_error) if results.mean_absolute_error is not None else 0.0,
                        "max_residual": float(results.max_residual) if results.max_residual is not None else 0.0,
                        "v_deviation_avg": float(results.v_deviation_avg) if results.v_deviation_avg is not None else 0.0,
                        "total_losses_mw": float(results.total_losses_mw) if results.total_losses_mw is not None else 0.0,
                        "health": self.analytics.get_summary()["latest"],
                        "timestamp": timestamp.isoformat()
                    }
                    await self.transport.send_grid_status(broadcast_dict)
                    logger.info(f"Grid estimation converged: chi2={res.chi2_statistic if res.chi2_statistic is not None else 0:.4f}")
                else:
                    logger.warning("Grid estimation failed to converge")
                    
            except Exception as e:
                logger.error(f"Error in grid estimation loop: {e}", exc_info=True)
                
        # 3. Send readings (IO bound)
        tasks = [self.transport.send_reading(reading) for reading in readings]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        success_count = sum(1 for r in results if r is True)
        logger.info(f"Generated {len(readings)} readings. Sent {success_count} successfully at {timestamp}")
