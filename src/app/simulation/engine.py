"""
Physics-based Simulation Engine for Microgrid Optimization.

This engine focuses on:
1. Realistic grid physics simulation using pandapower
2. Power flow analysis and voltage/loss calculations
3. Microgrid zone management and optimization
4. Smart meter data generation based on physical grid state

Note: P2P matching and trading are handled by the API Gateway and Blockchain.
This simulator provides the physical layer simulation only.
"""

import logging
import random
from typing import List, Dict, Optional
from datetime import datetime, time, timezone
import pandapower as pp

from ..core.engine import SimulationEngine
from ..core.meter import SmartMeter
from ..transport.base import TransportLayer
from ..core.database import DatabaseManager
from .thai_grid import ThaiGridModel
from .utcc_campus import UTCCSmartCampus
from .dynamic_grid import DynamicCommunityGrid
from ..services.gis_service import GISService
from ..services.zoning_service import MicrogridZoningService
from ..services.ledger_service import LedgerService
from ..services.token_service import TokenService
from ..models.grid_state import GridState, ZoneState, GridAnalysisResult

logger = logging.getLogger(__name__)


class PhysicsSimulationEngine(SimulationEngine):
    """
    Enhanced Simulation Engine that uses Pandapower physics models
    to drive smart meter readings with realistic grid behavior.
    
    Focuses on:
    - Power flow calculations
    - Voltage profile analysis
    - Technical loss computation
    - Power quality (THD) estimation
    - Microgrid zone optimization support
    """
    
    def __init__(
        self,
        meters: List[SmartMeter],
        transport: TransportLayer,
        db_manager: DatabaseManager = None,
        model_type: str = "DYNAMIC",
        num_zones: int = 5,
    ):
        super().__init__(meters, transport, db_manager)
        
        self.gis = GISService()
        self.model_type = model_type
        self.province = "Bangkok"
        
        # Zoning service for microgrid management
        self.zoning = MicrogridZoningService(num_zones=num_zones)
        self.zoning_service = self.zoning
        
        # Simulation time management
        self.time_offset_hours = -6
        self.current_sim_time = datetime.combine(
            datetime.now(timezone.utc).date(), 
            time(12, 0),  # Start at noon for better solar simulation
            tzinfo=timezone.utc
        )
        
        # Initialize Ledger for grid event logging
        if db_manager:
            self.ledger = LedgerService(db_manager)
        else:
            self.ledger = LedgerService(DatabaseManager())
        
        # Grid analysis results cache
        self.last_grid_analysis: Optional[GridAnalysisResult] = None
        self.zone_states: Dict[int, ZoneState] = {}
        
        # Initial mapping/zoning
        self._assign_meter_zones()
        self._last_zone_count = len(self.meters)
        
        # Token Service (for REC/generation tracking)
        self.token_service = TokenService()

        # Initialize grid model
        logger.info(f"Initializing Physics Model: {model_type}")
        if model_type == "UTCC":
            self.grid_model = UTCCSmartCampus()
            self.province = "Bangkok"
        elif model_type == "THAI_GRID":
            self.grid_model = ThaiGridModel()
            self.province = "Bangkok"
        else:
            # Dynamic Grid (Default) - builds from meter locations
            self.grid_model = DynamicCommunityGrid(self.meters)
            self.province = "Bangkok"
            
        self.net = self.grid_model.net
        
        # Map meters to grid for static models
        if model_type in ("UTCC", "THAI_GRID"):
            self._map_meters_to_grid()
    
    def _is_on_peak_hour(self) -> bool:
        """Check if current simulation time is during peak hours (9:00-22:00)."""
        if not hasattr(self, 'current_sim_time') or self.current_sim_time is None:
            return False
        hour = self.current_sim_time.hour
        return 9 <= hour < 22
        
    def _map_meters_to_grid(self):
        """Map meters to grid elements for static grid models (ThaiGrid/UTCC)."""
        self.meter_map: Dict[str, Dict[str, int]] = {}
        load_indices = self.net.load.index.tolist()
        sgen_indices = self.net.sgen.index.tolist()
        
        for meter in self.meters:
            is_producer = meter.config.get("has_solar", False)
            mapping = {}
            if is_producer and sgen_indices:
                idx = random.choice(sgen_indices)
                mapping["sgen_idx"] = idx
                mapping["bus_idx"] = self.net.sgen.at[idx, "bus"]
                mapping["name"] = self.net.sgen.at[idx, "name"]
            elif load_indices:
                idx = random.choice(load_indices)
                mapping["load_idx"] = idx
                mapping["bus_idx"] = self.net.load.at[idx, "bus"]
                mapping["name"] = self.net.load.at[idx, "name"]
            else:
                mapping["bus_idx"] = random.choice(self.net.bus.index.tolist())
                
            self.meter_map[meter.meter_id] = mapping
    
    def _map_single_meter(self, meter: SmartMeter):
        """Add a single meter to the grid dynamically."""
        if isinstance(self.grid_model, DynamicCommunityGrid):
            self.grid_model._add_meter_node(meter)
            logger.info(f"Dynamically added meter {meter.meter_id} to Dynamic Grid")
    
    def _assign_meter_zones(self):
        """Assign meters to microgrid zones using K-Means clustering."""
        coordinates = []
        needs_zoning = False
        
        for meter in self.meters:
            if meter.grid_zone_id is None:
                needs_zoning = True
            
            if meter.latitude and meter.longitude:
                coordinates.append((meter.latitude, meter.longitude))
        
        if needs_zoning:
            if coordinates and len(coordinates) >= self.zoning.num_zones:
                logger.info("Running KMeans clustering for zone assignment...")
                zone_ids = self.zoning.fit(coordinates)
                idx_coord = 0
                for meter in self.meters:
                    if meter.latitude and meter.longitude:
                        meter.grid_zone_id = zone_ids[idx_coord]
                        idx_coord += 1
                    elif meter.grid_zone_id is None:
                        meter.grid_zone_id = random.randint(1, self.zoning.num_zones)
            else:
                logger.info("Not enough coordinates for clustering. Assigning random zones.")
                for meter in self.meters:
                    if meter.grid_zone_id is None:
                        meter.grid_zone_id = random.randint(1, self.zoning.num_zones)
        else:
            logger.info("All meters have pre-assigned zones. Skipping clustering.")

    def validate_grid_state(self) -> bool:
        """
        Validate current grid state for voltage violations and overloads.
        
        Returns:
            True if grid is healthy, False if violations detected
        """
        if isinstance(self.grid_model, DynamicCommunityGrid):
            success = self.grid_model.run_power_flow()
            if not success:
                return False
            violations = self.grid_model.check_grid_violations()
            if any(violations.values()):
                logger.warning(f"Grid Validation Failed: {violations}")
                return False
            return True
        return True

    def get_grid_state(self, meter_id: str) -> GridState:
        """
        Get the current grid state for a specific meter.
        
        Args:
            meter_id: The meter identifier
            
        Returns:
            GridState object with current physical parameters
        """
        meter = next((m for m in self.meters if m.meter_id == meter_id), None)
        if not meter or not meter.static_data:
            return GridState()
        
        return GridState(
            voltage_pu=meter.static_data.get("voltage_pu", 1.0),
            frequency_hz=meter.static_data.get("frequency", 50.0),
            thd_voltage=meter.static_data.get("thd_voltage", 0.0),
            thd_current=meter.static_data.get("thd_current", 0.0),
            is_on_peak=self._is_on_peak_hour(),
            power_factor=meter.static_data.get("power_factor", 1.0),
            temperature_c=meter.static_data.get("temperature", 25.0)
        )

    def get_zone_state(self, zone_id: int) -> ZoneState:
        """
        Get aggregated state for a microgrid zone.
        
        Args:
            zone_id: The zone identifier
            
        Returns:
            ZoneState object with aggregated zone metrics
        """
        zone_meters = [m for m in self.meters if m.grid_zone_id == zone_id]
        
        if not zone_meters:
            return ZoneState(zone_id=zone_id)
        
        voltages = []
        total_load = 0.0
        total_gen = 0.0
        
        for meter in zone_meters:
            if meter.static_data:
                v = meter.static_data.get("voltage_pu", 1.0)
                voltages.append(v)
                total_load += meter.static_data.get("energy_consumed", 0.0)
                total_gen += meter.static_data.get("energy_generated", 0.0)
        
        avg_v = sum(voltages) / len(voltages) if voltages else 1.0
        min_v = min(voltages) if voltages else 1.0
        max_v = max(voltages) if voltages else 1.0
        
        return ZoneState(
            zone_id=zone_id,
            avg_voltage_pu=avg_v,
            min_voltage_pu=min_v,
            max_voltage_pu=max_v,
            total_load_kw=total_load,
            total_generation_kw=total_gen,
            net_power_kw=total_load - total_gen,
            meter_count=len(zone_meters),
            has_voltage_violation=(min_v < 0.95 or max_v > 1.05)
        )

    def analyze_grid(self) -> GridAnalysisResult:
        """
        Perform comprehensive grid analysis.
        
        Returns:
            GridAnalysisResult with all grid metrics and optimization recommendations
        """
        result = GridAnalysisResult(timestamp=self.current_sim_time)
        
        # Run power flow if not already done
        if isinstance(self.grid_model, DynamicCommunityGrid):
            result.power_flow_converged = self.grid_model.run_power_flow()
        
        # Calculate totals
        for meter in self.meters:
            if meter.static_data:
                result.total_load_mw += meter.static_data.get("energy_consumed", 0.0) / 1000.0
                result.total_generation_mw += meter.static_data.get("energy_generated", 0.0) / 1000.0
        
        # Get zone states
        zone_ids = set(m.grid_zone_id for m in self.meters if m.grid_zone_id is not None)
        for zone_id in zone_ids:
            zone_state = self.get_zone_state(zone_id)
            result.zone_states[zone_id] = zone_state
            
            if zone_state.has_voltage_violation:
                result.voltage_violations.append(f"Zone {zone_id}")
        
        # Calculate losses (simplified)
        if result.total_generation_mw > 0:
            delivered = result.total_generation_mw - result.total_load_mw
            if delivered > 0:
                result.total_loss_mw = delivered * 0.02  # Estimate 2% loss
                result.loss_percentage = (result.total_loss_mw / result.total_generation_mw) * 100
        
        # Generate recommendations
        if result.voltage_violations:
            result.recommendations.append(
                f"Voltage violations detected in {len(result.voltage_violations)} zones. "
                "Consider battery dispatch or load shedding."
            )
        
        net_power = result.total_load_mw - result.total_generation_mw
        if net_power > 0 and self._is_on_peak_hour():
            result.recommendations.append(
                f"Grid importing {net_power:.2f} MW during peak hours. "
                "Recommend battery discharge to reduce peak demand."
            )
        
        self.last_grid_analysis = result
        return result

    async def tick(self):
        """
        Execute one simulation tick.
        
        This method:
        1. Handles dynamic meter additions
        2. Updates weather conditions
        3. Runs physics calculations (power flow)
        4. Updates meter readings with physical data
        5. Sends readings to API Gateway
        """
        # Handle dynamic meter additions
        if isinstance(self.grid_model, DynamicCommunityGrid):
            for meter in self.meters:
                if meter.meter_id not in self.grid_model.meter_bus_map:
                    self._map_single_meter(meter)
        
        # Re-zone if meter count changed
        if len(self.meters) != getattr(self, "_last_zone_count", 0):
            self._assign_meter_zones()
            self._last_zone_count = len(self.meters)

        # Update weather
        current_weather = self.weather_system.update()
        global_irradiance, global_temp_offset = self.weather_system.get_factors()
        zone_weather = await self._fetch_zone_weather()
        
        for meter in self.meters:
            if meter.grid_zone_id is not None and meter.grid_zone_id in zone_weather:
                condition, irradiance, temp_offset = zone_weather[meter.grid_zone_id]
                meter.update_weather(condition, irradiance, temp_offset)
            else:
                meter.update_weather(current_weather, global_irradiance, global_temp_offset)

        # Calculate load/generation for each meter
        updates = {}
        timestamp = self.current_sim_time
        
        for meter in self.meters:
            cons_kw = meter._calculate_consumption(timestamp)
            gen_kw = 0.0
            if meter.config.get("has_solar"):
                gen_kw = meter._calculate_solar_generation(timestamp)
            
            updates[meter.meter_id] = {
                'p_load_mw': cons_kw / 1000.0,
                'p_gen_mw': gen_kw / 1000.0
            }
            
            # Store energy values for reading generation
            if meter.static_data is None:
                meter.static_data = {}
            meter.static_data["energy_consumed"] = cons_kw
            meter.static_data["energy_generated"] = gen_kw
            
            # Mint NRG tokens for solar generation (REC tracking)
            gen_kwh = gen_kw * (15.0 / 60.0)  # 15 min interval
            if gen_kwh > 0:
                self.token_service.mint_nrg(meter, gen_kwh)

        # Run physics calculations
        if isinstance(self.grid_model, DynamicCommunityGrid):
            self.grid_model.update_grid_state(updates)
            grid_success = self.grid_model.run_power_flow()
            
            if grid_success:
                self._update_physics_data(updates)
        else:
            # Legacy models - use nominal values
            self._apply_nominal_physics()

        # Generate and send readings
        await super().tick()
        
        # Update zone states cache
        zone_ids = set(m.grid_zone_id for m in self.meters if m.grid_zone_id is not None)
        for zone_id in zone_ids:
            self.zone_states[zone_id] = self.get_zone_state(zone_id)

    def _update_physics_data(self, updates: Dict):
        """Update meter static_data with physics-based calculations."""
        from .power_quality import estimate_thd_for_bus
        
        for meter in self.meters:
            vm_pu = self.grid_model.get_node_voltage(meter.meter_id)
            voltage = vm_pu * 230.0
            
            if meter.static_data is None:
                meter.static_data = {}
            
            meter.static_data["voltage"] = voltage
            meter.static_data["voltage_pu"] = vm_pu
            
            # Physics-based frequency calculation
            state = updates.get(meter.meter_id, {})
            p_load = state.get('p_load_mw', 0)
            p_gen = state.get('p_gen_mw', 0)
            freq_deviation = -0.001 * (p_load - p_gen) * 1000
            freq_deviation = max(-0.05, min(0.05, freq_deviation))
            meter.static_data["frequency"] = 50.0 + freq_deviation
            
            # Power factor based on load type
            has_solar = meter.config.get("has_solar", False)
            base_pf = 0.98 if has_solar else 0.92
            load_factor = min(1.0, p_load * 1000 / max(1, meter.config.get("base_consumption", 1.0)))
            pf = base_pf - 0.02 * load_factor
            meter.static_data["power_factor"] = max(0.85, min(1.0, pf))
            meter.static_data["temperature"] = 25.0 + meter.temp_offset
            
            # THD estimation
            thd_v, thd_i = estimate_thd_for_bus(
                has_ev_charger=False,
                has_solar_inverter=has_solar,
                ev_power_kw=0,
                solar_power_kw=p_gen * 1000
            )
            meter.static_data["thd_voltage"] = thd_v
            meter.static_data["thd_current"] = thd_i

    def _apply_nominal_physics(self):
        """Apply nominal physics values for legacy grid models."""
        for meter in self.meters:
            if meter.static_data is None:
                meter.static_data = {}
            
            meter.static_data["voltage"] = 230.0
            meter.static_data["voltage_pu"] = 1.0
            meter.static_data["frequency"] = 50.0
            meter.static_data["power_factor"] = 0.95
            meter.static_data["temperature"] = 25.0 + meter.temp_offset
            meter.static_data["thd_voltage"] = 2.0
            meter.static_data["thd_current"] = 5.0

    async def _fetch_zone_weather(self) -> Dict:
        """Fetch weather data for each zone (placeholder for real API integration)."""
        # In production, this would call a weather API
        # For now, return empty to use global weather
        return {}

    # =========================================================================
    # Microgrid Optimization API
    # =========================================================================
    
    def get_optimization_data(self) -> Dict:
        """
        Get data package for external optimization algorithms.
        
        Returns a dict containing all necessary information for
        battery dispatch, load scheduling, or DER optimization.
        """
        return {
            "timestamp": self.current_sim_time.isoformat(),
            "is_on_peak": self._is_on_peak_hour(),
            "grid_analysis": self.last_grid_analysis,
            "zone_states": self.zone_states,
            "meters": [
                {
                    "meter_id": m.meter_id,
                    "zone_id": m.grid_zone_id,
                    "has_solar": m.config.get("has_solar", False),
                    "has_battery": m.config.get("has_battery", False),
                    "battery_level": m.battery_level,
                    "battery_capacity": m.config.get("battery_capacity", 0),
                    "current_load_kw": m.static_data.get("energy_consumed", 0) if m.static_data else 0,
                    "current_gen_kw": m.static_data.get("energy_generated", 0) if m.static_data else 0,
                    "voltage_pu": m.static_data.get("voltage_pu", 1.0) if m.static_data else 1.0,
                }
                for m in self.meters
            ]
        }

    def apply_battery_dispatch(self, meter_id: str, power_kw: float) -> bool:
        """
        Apply battery dispatch command to a meter.
        
        Args:
            meter_id: Target meter
            power_kw: Positive = discharge, Negative = charge
            
        Returns:
            True if command applied successfully
        """
        meter = next((m for m in self.meters if m.meter_id == meter_id), None)
        if not meter or not meter.config.get("has_battery"):
            return False
        
        # Update battery state (simplified)
        capacity = meter.config.get("battery_capacity", 10.0)
        current_level = meter.battery_level
        
        # Calculate new level (15 min interval)
        energy_change_kwh = power_kw * (15.0 / 60.0)
        new_level = current_level - (energy_change_kwh / capacity * 100)
        new_level = max(0, min(100, new_level))
        
        meter.battery_level = new_level
        logger.info(f"Battery dispatch: {meter_id} {power_kw}kW, level: {current_level:.1f}% -> {new_level:.1f}%")
        return True

    def get_loss_analysis(self) -> Dict:
        """
        Get technical loss analysis for the grid.
        
        Returns breakdown of losses by zone and recommendations.
        """
        analysis = self.analyze_grid()
        
        return {
            "total_loss_mw": analysis.total_loss_mw,
            "loss_percentage": analysis.loss_percentage,
            "by_zone": {
                zone_id: {
                    "load_kw": state.total_load_kw,
                    "generation_kw": state.total_generation_kw,
                    "net_kw": state.net_power_kw,
                    "estimated_loss_kw": abs(state.net_power_kw) * 0.02  # 2% estimate
                }
                for zone_id, state in analysis.zone_states.items()
            },
            "recommendations": analysis.recommendations
        }
