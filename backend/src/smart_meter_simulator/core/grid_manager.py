import logging
from typing import Any, Dict, List, Optional
import numpy as np
import pandapower as pp
from ..config import MeterType, get_config
from ..services.telemetry_service import GridTelemetryService
from ..adapters.state_estimator import StateEstimator, EstimationAlgorithm

logger = logging.getLogger(__name__)

class GridManager:
    """
    Handles the power grid topology, state estimation, and nodal pricing.
    """
    def __init__(self, adapter: Optional[Any] = None):
        self.adapter = adapter
        self.net = None
        self.meter_to_bus = {}
        self.nodal_prices = {}
        self.avg_nodal_price = 0.28
        self.carbon_intensity = 250.0
        self.last_estimation_results = None

    def initialize_network(self, meters: List[Any]):
        """Build the network topology from the given meters."""
        if not self.adapter:
            return

        try:
            # Check for Island Hub Scenario
            is_island_hub = False
            config = get_config()
            
            # Simplified scenario detection
            if "Island Hub" in str(config.initial_locations_file):
                 is_island_hub = True

            if is_island_hub:
                from ..adapters.island_hub_topology import IslandHubTopology
                island_builder = IslandHubTopology()
                self.net, self.meter_to_bus = island_builder.build_island_hub(meters)
                logger.info("🏝️  Detected Island Hub scenario. Using specialized topology.")
            else:
                self.net, self.meter_to_bus = self.adapter.build_network_from_meters(meters)

            # Initialize static elements
            for meter in meters:
                bus_idx = self.meter_to_bus.get(meter.meter_id)
                if bus_idx is not None and not is_island_hub:
                    pp.create_load(self.net, bus=bus_idx, p_mw=0, q_mvar=0, name=f"L_{meter.meter_id}")
                    if meter.config.get('has_solar'):
                        pp.create_sgen(self.net, bus=bus_idx, p_mw=0, q_mvar=0, name=f"G_{meter.meter_id}")
            
            logger.info(f"Initialized grid topology: {len(self.net.bus)} buses, {len(self.net.line)} lines")
        except Exception as e:
            logger.error(f"Failed to initialize grid topology: {e}")

    def run_state_estimation(self, meters: List[Any], readings: List[Any]):
        """Run state estimation and update grid state."""
        if not self.adapter or not self.net:
            return None

        try:
            self.adapter.builder.clear()
            self._update_network_measurements(meters, readings)
            
            GridTelemetryService.inject_pseudo_measurements(self.net)
            self.net.measurement = self.adapter.get_measurement_table()

            # Run power flow for initialization
            pf_converged = self._run_power_flow()
            est_init = "results" if pf_converged else "flat"

            # Run state estimation
            estimator = StateEstimator(algorithm=EstimationAlgorithm.WLS)
            results = estimator.run_sanitized_estimation(self.net, init=est_init, max_removals=10)
            self.last_estimation_results = results
            
            # Update metrics
            self._calculate_carbon_intensity()
            self.calculate_nodal_prices()
            
            return results
        except Exception as e:
            logger.error(f"Error in grid estimation: {e}", exc_info=True)
            return None

    def _update_network_measurements(self, meters: List[Any], readings: List[Any]):
        """Update network loads and generator outputs based on readings."""
        load_updates_p = {}
        load_updates_q = {}
        sgen_updates_p = {}

        for meter, reading in zip(meters, readings):
            bus_idx = self.meter_to_bus.get(meter.meter_id)
            if bus_idx is None: continue

            hours = reading.interval_seconds / 3600.0
            p_mw = (reading.energy_consumed / hours / 1000.0) if hours > 0 else 0.0
            p_gen_mw = (reading.energy_generated / hours / 1000.0) if hours > 0 else 0.0
            q_mvar = p_mw * 0.3

            load_indices = self.net.load[self.net.load.bus == bus_idx].index
            if len(load_indices) > 0:
                l_idx = int(load_indices[0])
                load_updates_p[l_idx] = p_mw
                load_updates_q[l_idx] = q_mvar
                self.adapter.builder.add_active_power_measurement(meter.meter_id, bus_idx, p_mw, meter.config.get("meter_type", MeterType.GRID_CONSUMER))
            
            sgen_indices = self.net.sgen[self.net.sgen.bus == bus_idx].index
            if len(sgen_indices) > 0:
                s_idx = int(sgen_indices[0])
                sgen_updates_p[s_idx] = p_gen_mw
                self.adapter.builder.add_active_power_measurement(meter.meter_id + "_GEN", bus_idx, -p_gen_mw, meter.config.get("meter_type", MeterType.SOLAR_PROSUMER), is_generation=True)

            voltage_pu = (reading.voltage * np.sqrt(3)) / (self.net.bus.vn_kv.at[bus_idx] * 1000)
            self.adapter.builder.add_voltage_measurement(meter.meter_id, bus_idx, voltage_pu, meter.config.get("meter_type", MeterType.GRID_CONSUMER))

        if load_updates_p:
            self.net.load.loc[list(load_updates_p.keys()), ["p_mw", "q_mvar"]] = list(zip(load_updates_p.values(), load_updates_q.values()))
        if sgen_updates_p:
            self.net.sgen.loc[list(sgen_updates_p.keys()), "p_mw"] = list(sgen_updates_p.values())

    def _run_power_flow(self) -> bool:
        """Run power flow with fallbacks."""
        try:
            pp.runpp(self.net, algorithm="nr", calculate_voltage_angles=True)
            return True
        except pp.LoadflowNotConverged:
            try:
                pp.runpp(self.net, algorithm="bfsw", calculate_voltage_angles=True)
                return True
            except pp.LoadflowNotConverged:
                return False

    def _calculate_carbon_intensity(self):
        """Estimate system carbon intensity based on grid import."""
        grid_p_mw = self.net.res_ext_grid.p_mw.sum() if hasattr(self.net, "res_ext_grid") else 0.0
        total_load_mw = self.net.res_load.p_mw.sum() if hasattr(self.net, "res_load") else 1.0
        self.carbon_intensity = max(0.0, (grid_p_mw / total_load_mw) * 500.0) if total_load_mw > 0 else 500.0

    def calculate_nodal_prices(self) -> Dict[int, float]:
        """Locational Marginal Pricing (LMP) based on congestion."""
        config = get_config()
        base_price = config.grid_purchase_rate
        nodal_prices = {idx: base_price for idx in self.net.bus.index}

        if not hasattr(self.net, 'res_line'):
            self.nodal_prices = nodal_prices
            return nodal_prices

        line_loadings = self.net.res_line.loading_percent
        threshold = 85.0
        
        for idx, loading in line_loadings.items():
            if loading > threshold:
                penalty = ((loading - threshold) / (100.0 - threshold)) * (base_price * 0.5)
                target_bus = int(self.net.line.at[idx, 'to_bus'])
                
                # Simplified propagation
                affected = [target_bus]
                queue = [target_bus]
                while queue:
                    curr = queue.pop(0)
                    downstream = self.net.line[self.net.line.from_bus == curr]
                    for _, row in downstream.iterrows():
                        if int(row.to_bus) not in affected:
                            affected.append(int(row.to_bus))
                            queue.append(int(row.to_bus))
                
                for b_idx in affected:
                    if b_idx in nodal_prices:
                        nodal_prices[b_idx] += penalty

        self.nodal_prices = nodal_prices
        self.avg_nodal_price = sum(nodal_prices.values()) / len(nodal_prices) if nodal_prices else base_price
        return nodal_prices
