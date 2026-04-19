"""
Island Hub Topology Builder

Specialized topology for the Gulf of Thailand Island Hub:
Khanom Mainland -> Koh Samui -> Koh Phangan -> Koh Tao.

Implements specific transmission constraints and large-scale assets:
- 115 kV Bottleneck (Khanom to Samui)
- 50 MWh BESS (Samui)
- 10 MW Diesel Generator (Tao)
- 33 kV Submarine Cables (Samui -> Phangan -> Tao)
"""

import logging
from typing import List, Dict, Any, Tuple, Optional
import pandas as pd
import numpy as np

try:
    import pandapower as pp
    import pandapower.topology as top
    PANDAPOWER_AVAILABLE = True
except ImportError:
    PANDAPOWER_AVAILABLE = False

from .topology_builder import TopologyBuilder, BusConfig, VoltageLevel

logger = logging.getLogger(__name__)

class IslandHubTopology(TopologyBuilder):
    """
    Builds the Khanom-Samui-Phangan-Tao transmission and distribution network.
    """

    def build_island_hub(self, meters: List[Any]) -> Tuple["pp.pandapowerNet", Dict[str, int]]:
        """
        Build the network based on the island hub description.
        """
        if not PANDAPOWER_AVAILABLE:
            raise ImportError("pandapower is required for IslandHubTopology")

        net = pp.create_empty_network(name="Gulf of Thailand Island Hub")
        meter_to_bus = {}

        # 1. Define Backbone Buses
        # Mainland (Khanom)
        bus_khanom_115 = pp.create_bus(net, vn_kv=115.0, name="EGAT Khanom 115kV", zone="Mainland", type="b")
        pp.create_ext_grid(net, bus=bus_khanom_115, vm_pu=1.02, name="EGAT_Grid_Supply")

        # Koh Samui (Primary Hub)
        bus_samui_115 = pp.create_bus(net, vn_kv=115.0, name="Samui Main 115kV", zone="Samui", type="b")
        bus_samui_33 = pp.create_bus(net, vn_kv=33.0, name="Samui Dist 33kV", zone="Samui", type="b")
        pp.create_transformer(net, hv_bus=bus_samui_115, lv_bus=bus_samui_33, std_type="25 MVA 110/20 kV", name="Samui_Main_Trafo")

        # Koh Phangan
        bus_phangan_33 = pp.create_bus(net, vn_kv=33.0, name="Phangan Dist 33kV", zone="Phangan", type="b")

        # Koh Tao
        bus_tao_33 = pp.create_bus(net, vn_kv=33.0, name="Tao Dist 33kV", zone="Tao", type="b")

        # 2. Add Transmission Lines & Constraints
        # 115 kV KMB (Circuit 3) - The Bottleneck
        # Modeling as 20km 115kV line with limited capacity (e.g., 40 MVA)
        pp.create_line(net, from_bus=bus_khanom_115, to_bus=bus_samui_115, length_km=20.0, 
                       std_type="149-AL1/24-ST1A 110.0", name="115kV KMB (Circuit 3) Bottleneck")
        
        # Set bottleneck constraint: limit the current to ~80% of standard to simulate thermal constraint
        net.line.at[net.line[net.line.name == "115kV KMB (Circuit 3) Bottleneck"].index[0], 'max_i_ka'] = 0.25 # Reduced capacity

        # 33 kV Submarine Cable Samui -> Phangan
        pp.create_line(net, from_bus=bus_samui_33, to_bus=bus_phangan_33, length_km=15.0, 
                       std_type="NA2XS2Y 1x240 RM/25 12/20 kV", name="33kV Samui-Phangan XLPE")

        # 33 kV Submarine Cable Phangan -> Tao
        pp.create_line(net, from_bus=bus_phangan_33, to_bus=bus_tao_33, length_km=40.0, 
                       std_type="NA2XS2Y 1x240 RM/25 12/20 kV", name="33kV Phangan-Tao XLPE")

        # 3. Inject Large-Scale Assets
        # Samui 50 MWh BESS
        # We model this as a storage element or a generator at the 33kV bus
        pp.create_storage(net, bus=bus_samui_33, p_mw=0, max_e_mwh=50.0, name="Samui_50MWh_BESS", 
                          max_p_mw=20.0, min_p_mw=-20.0)

        # Samui EGAT Generator (25 MW)
        pp.create_gen(net, bus=bus_samui_33, p_mw=0, max_p_mw=25.0, name="Samui_EGAT_Gen", vm_pu=1.0)

        # Tao 10 MW Diesel Generator
        pp.create_gen(net, bus=bus_tao_33, p_mw=0, max_p_mw=10.0, name="Tao_Diesel_Gen", vm_pu=1.0)

        # 4. Map Meters to Buses based on Zone
        for m in meters:
            zone = m.config.get('zone', 'unknown')
            bus_idx = None
            
            if zone == "Samui":
                bus_idx = bus_samui_33
            elif zone == "Phangan":
                bus_idx = bus_phangan_33
            elif zone == "Tao":
                bus_idx = bus_tao_33
            elif zone == "Mainland":
                bus_idx = bus_khanom_115
            
            if bus_idx is not None:
                meter_to_bus[m.meter_id] = bus_idx
                # Coordinates for visualization
                lat = m.config.get('latitude')
                lng = m.config.get('longitude')
                if lat is not None and lng is not None:
                    if 'bus_geocoord' not in net or net.bus_geocoord is None:
                        net.bus_geocoord = pd.DataFrame(columns=['x', 'y'])
                    net.bus_geocoord.loc[bus_idx] = [lng, lat]

        logger.info(f"Island Hub Topology Built: {len(net.bus)} buses, {len(net.line)} lines, {len(meter_to_bus)} meters mapped")
        return net, meter_to_bus
