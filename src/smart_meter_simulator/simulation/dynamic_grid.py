
import pandapower as pp
import pandapower.networks as pn
import numpy as np
import logging
from typing import List, Dict, Optional
from ..core.meter import SmartMeter

logger = logging.getLogger(__name__)

class DynamicCommunityGrid:
    """
    A dynamic grid model built directly from the list of SmartMeters.
    It represents a simple community microgrid (Transformer -> Line -> House).
    """

    def __init__(self, meters: List[SmartMeter], voltage_level_kv: float = 0.4):
        self.net = pp.create_empty_network()
        self.meters = meters
        self.voltage_level_kv = voltage_level_kv
        self.meter_bus_map: Dict[str, int] = {} # meter_id -> bus_index
        
        self.build_network()

    def build_network(self):
        """Builds the network topology based on current meters."""
        logger.info(f"Building Dynamic Community Grid for {len(self.meters)} meters...")
        
        # 1. Create Main Grid Connection (MV Side)
        # 22kV Medium Voltage Grid
        # Use a fixed reference point (e.g., slightly offset from the first meter or center)
        ref_lat = 13.780157
        ref_lon = 100.560237
        if self.meters and self.meters[0].latitude is not None and self.meters[0].longitude is not None:
            ref_lat = self.meters[0].latitude
            ref_lon = self.meters[0].longitude

        self.mv_bus = pp.create_bus(self.net, vn_kv=22.0, name="MV Grid Connection", 
                                    geodata=(ref_lon, ref_lat + 0.001)) # Offset slightly north
        pp.create_ext_grid(self.net, bus=self.mv_bus, vm_pu=1.02, name="Main Grid Supply")
        
        # 2. Create Community Main Transformer (22kV -> 0.4kV)
        self.lv_main_bus = pp.create_bus(self.net, vn_kv=self.voltage_level_kv, name="Community Main Bus",
                                         geodata=(ref_lon, ref_lat))
        
        pp.create_transformer(self.net, hv_bus=self.mv_bus, lv_bus=self.lv_main_bus, 
                              std_type="0.63 MVA 20/0.4 kV", name="Community Transformer")
        
        # 3. Create Zone Feeders (0.4kV Bus per Zone)
        # This simulates the main distribution lines going to different neighborhoods
        self.zone_bus_map: Dict[int, int] = {}
        
        # Identify unique zones from meters
        zone_ids = set()
        for m in self.meters:
            if m.grid_zone_id is not None:
                zone_ids.add(m.grid_zone_id)
        if not zone_ids:
            zone_ids.add(0) # Default zone if none assigned
            
        for z_id in zone_ids:
            # Create Feeder Bus for this Zone
            zone_bus = pp.create_bus(self.net, vn_kv=self.voltage_level_kv, name=f"Feeder_Zone_{z_id}")
            self.zone_bus_map[z_id] = zone_bus
            
            # Create Feeder Line from Main Transformer to Zone Feeder
            # In "Real Data Only" mode, we might want this even closer or at 0 distance
            # if the meters are already at their real positions.
            dist_km = 0.1 # Fixed minimal distance for the main feeder
            pp.create_line(self.net, from_bus=self.lv_main_bus, to_bus=zone_bus,
                           length_km=dist_km,
                           std_type="NAYY 4x150 SE", # Thicker cable for feeder
                           name=f"Feeder_Line_Zone_{z_id}")
        
        # 4. Create Lines and Buses for each Meter
        for meter in self.meters:
            self._add_meter_node(meter)
            
        logger.info("Grid Model Built.")

    def _add_meter_node(self, meter: SmartMeter):
        """Adds a single meter node to the grid."""
        # Create House Bus
        geodata = (meter.longitude, meter.latitude) if meter.longitude is not None and meter.latitude is not None else None
        house_bus = pp.create_bus(self.net, vn_kv=self.voltage_level_kv, name=f"Bus_{meter.meter_id}",
                                  geodata=geodata)
        self.meter_bus_map[meter.meter_id] = house_bus
        
        # Determine Parent Bus (Zone Feeder or Main)
        zone_id = meter.grid_zone_id if meter.grid_zone_id is not None else 0
        parent_bus = self.zone_bus_map.get(zone_id, self.lv_main_bus)
        
        # Create Service Line (Zone Bus -> House Bus)
        # Use static distance from config if available, otherwise fallback to tiny fixed 20m
        dist_m = meter.config.get("dist_m", 20.0)
        distance_km = max(0.005, dist_m / 1000.0)
        
        # Check if we have R/X to create a custom line, otherwise use standard type
        line_r = meter.config.get("line_R")
        line_x = meter.config.get("line_X")
        
        if line_r is not None and line_x is not None:
             # Create custom line with precise R, X from the dataset
             pp.create_line_from_parameters(
                 self.net, from_bus=parent_bus, to_bus=house_bus,
                 length_km=1.0, # Parameters are already for the full line
                 r_ohm_per_km=line_r,
                 x_ohm_per_km=line_x,
                 c_nf_per_km=0,
                 max_i_ka=0.2, # Standard 200A
                 name=f"Line_{meter.meter_id}"
             )
        else:
            pp.create_line(self.net, from_bus=parent_bus, to_bus=house_bus, 
                           length_km=distance_km, 
                           std_type="NAYY 4x50 SE", # Standard Aluminum LV cable
                           name=f"Line_{meter.meter_id}")
        
        # Create Load Element (Consumer)
        # Initial value 0, will be updated in simulation step
        pp.create_load(self.net, bus=house_bus, p_mw=0.0, name=f"Load_{meter.meter_id}")
        
        # Create Generation Element (Prosumer)
        if meter.config.get("has_solar", False):
            # Initial value 0
            pp.create_sgen(self.net, bus=house_bus, p_mw=0.0, name=f"Solar_{meter.meter_id}")

    def update_grid_state(self, meter_states: Dict[str, Dict[str, float]]):
        """
        Updates the grid loads and generation based on current meter readings.
        
        Args:
            meter_states: Dict of meter_id -> {'p_load_mw': float, 'p_gen_mw': float}
        """
        for meter_id, state in meter_states.items():
            bus_idx = self.meter_bus_map.get(meter_id)
            if bus_idx is None:
                continue
                
            # Find Load element connected to this bus
            # Optimized: We could map meter_id -> load_idx directly, but this is robust
            load_indices = self.net.load[self.net.load.bus == bus_idx].index
            if len(load_indices) > 0:
                self.net.load.at[load_indices[0], 'p_mw'] = state.get('p_load_mw', 0.0)
                
            # Find Sgen element
            sgen_indices = self.net.sgen[self.net.sgen.bus == bus_idx].index
            if len(sgen_indices) > 0:
                self.net.sgen.at[sgen_indices[0], 'p_mw'] = state.get('p_gen_mw', 0.0)

    def run_power_flow(self) -> bool:
        """Runs the power flow calculation."""
        try:
            pp.runpp(self.net)
            return True
        except pp.LoadflowNotConverged:
            logger.error("Power Flow Diverged!")
            return False
        except Exception as e:
            logger.error(f"Power Flow Error: {e}")
            return False

    def get_node_voltage(self, meter_id: str) -> float:
        """Returns the voltage (p.u.) for a specific meter."""
        bus_idx = self.meter_bus_map.get(meter_id)
        if bus_idx is not None and bus_idx in self.net.res_bus.index:
            return self.net.res_bus.at[bus_idx, 'vm_pu']
        return 1.0 # Default fallback

    def check_grid_violations(self) -> Dict[str, bool]:
        """
        Checks for violations after power flow.
        Returns: {'voltage_violation': bool, 'line_overload': bool, 'trafo_overload': bool}
        """
        violations = {
             'voltage_violation': False,
             'line_overload': False,
             'trafo_overload': False
        }
        
        # 1. Voltage Violation (< 0.9 or > 1.1 pu)
        # We ignore MV bus for this check, focus on LV customer buses
        if not self.net.res_bus.empty:
            min_vm = self.net.res_bus['vm_pu'].min()
            max_vm = self.net.res_bus['vm_pu'].max()
            if min_vm < 0.9 or max_vm > 1.1:
                violations['voltage_violation'] = True
                logger.warning(f"Voltage Violation Detected: Min {min_vm:.3f}, Max {max_vm:.3f}")

        # 2. Line Overload (> 100%)
        if not self.net.res_line.empty:
            max_loading = self.net.res_line['loading_percent'].max()
            if max_loading > 100.0:
                violations['line_overload'] = True
                logger.warning(f"Line Overload Detected: {max_loading:.1f}%")

        # 3. Transformer Overload
        if not self.net.res_trafo.empty:
            max_trafo = self.net.res_trafo['loading_percent'].max()
            if max_trafo > 100.0:
                violations['trafo_overload'] = True
                logger.warning(f"Transformer Overload Detected: {max_trafo:.1f}%")

        return violations

    def validate_transaction(self, buyer_id: str, seller_id: str, energy_kwh: float) -> bool:
        """
        Validates if a P2P transaction is physically feasible WITHOUT running a full new simulation
        for every single trade (optimization).
        
        Ideally, we should:
        1. Snapshot current state.
        2. Apply trade logic (Does trade change physical flow? NO, usually not).
        
        BUT, if the user assumes "Trade = Dispatch", then yes.
        Assumption: The grid is already running. We just check if the grid is HEALTHY.
        If the grid is currently in violation, we block trades to "stabilize".
        """
        # Run power flow if not fresh? (Assumed called after run_power_flow)
        
        violations = self.check_grid_violations()
        if any(violations.values()):
            logger.info(f"Transaction Rejected due to Grid Violations: {violations}")
            return False
            
        return True
