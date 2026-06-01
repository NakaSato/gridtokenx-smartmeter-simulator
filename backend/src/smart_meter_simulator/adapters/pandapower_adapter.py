import logging
import os
import pandapower as pp
import pandapower.topology as top
import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional, Tuple

logger = logging.getLogger(__name__)

class PandapowerAdapter:
    """
    Adapter to bridge AMI Smart Meters with Pandapower grid simulation.
    Supports building HV/MV/LV topologies and mapping meters to buses.
    """

    def __init__(self):
        self.net = None
        self.meter_to_bus = {}
        self.bus_geodata = {}

    def create_empty_network(self, name: str = "GridTokenX"):
        """Initialize a new empty pandapower network."""
        self.net = pp.create_empty_network(name=name)
        # Ensure geodata tables exist
        self.net.bus_geodata = pd.DataFrame(columns=['x', 'y'])
        self.net.line_geodata = pd.DataFrame(columns=['coords'])
        return self.net

    def build_island_hub(self):
        """
        Builds the Khanom–Samui–Phangan–Tao island network (Gulf of Thailand).
        As described in docs/architecture/grid-integration.md
        """
        net = self.create_empty_network("IslandHub")

        # 1. External Grid (Mainland)
        # Pandapower geodata is (x, y) -> (lon, lat)
        b_khanom = pp.create_bus(net, vn_kv=115, name="Khanom 115kV")
        net.bus_geodata.loc[b_khanom] = [99.86, 9.84]
        pp.create_ext_grid(net, bus=b_khanom, vm_pu=1.02, name="EGAT Mainland")

        # 2. Samui System
        b_samui_main = pp.create_bus(net, vn_kv=115, name="Samui Main 115kV")
        net.bus_geodata.loc[b_samui_main] = [99.93, 9.53]
        
        # Bottleneck line: 115 kV KMB Circuit 3 (20 km)
        pp.create_line(net, from_bus=b_khanom, to_bus=b_samui_main, length_km=20, 
                       std_type="N2XS(FL)2Y 1x240 RM/35 64/110 kV", 
                       name="115kV KMB (Circuit 3) Bottleneck")

        # Samui Distribution
        b_samui_dist = pp.create_bus(net, vn_kv=22, name="Samui Dist 22kV")
        net.bus_geodata.loc[b_samui_dist] = [99.93, 9.53]
        pp.create_transformer(net, hv_bus=b_samui_main, lv_bus=b_samui_dist, 
                              std_type="25 MVA 110/20 kV", name="Samui Main Trafo")

        # Samui Assets
        pp.create_sgen(net, bus=b_samui_dist, p_mw=25, name="Samui_EGAT_Gen")
        pp.create_storage(net, bus=b_samui_dist, p_mw=0, max_e_mwh=50, name="Samui_BESS")

        # 3. Phangan System
        b_phangan_dist = pp.create_bus(net, vn_kv=22, name="Phangan Dist 22kV")
        net.bus_geodata.loc[b_phangan_dist] = [100.00, 9.72]
        
        # 22 kV Submarine XLPE (15 km)
        pp.create_line(net, from_bus=b_samui_dist, to_bus=b_phangan_dist, length_km=15,
                       std_type="NA2XS2Y 1x185 RM/25 12/20 kV", 
                       name="Samui-Phangan Submarine")

        # 4. Tao System
        b_tao_dist = pp.create_bus(net, vn_kv=22, name="Tao Dist 22kV")
        net.bus_geodata.loc[b_tao_dist] = [99.83, 10.10]
        
        # 22 kV Submarine XLPE (40 km)
        pp.create_line(net, from_bus=b_phangan_dist, to_bus=b_tao_dist, length_km=40,
                       std_type="NA2XS2Y 1x185 RM/25 12/20 kV", 
                       name="Phangan-Tao Submarine")

        # Tao Assets
        pp.create_sgen(net, bus=b_tao_dist, p_mw=10, name="Tao_Diesel_Gen")

        self.net = net
        self._map_bus_geodata()
        return net

    def build_from_db(self, substations: List[Dict], lines: List[Dict], transformers: List[Dict] = None):
        """
        Builds the network topology from database records.
        """
        import json
        from scipy.spatial import cKDTree

        net = self.create_empty_network("DB_Dynamic_Grid")
        sub_map = {} # db_id -> bus_idx

        # 1. Create Buses from Substations
        sub_coords = []
        for sub in substations:
            geom = sub.get('geometry')
            if isinstance(geom, str):
                geom = json.loads(geom)
            
            if geom and geom.get('type') == 'Point':
                coords = geom.get('coordinates') # [lon, lat]
                bus_idx = pp.create_bus(net, vn_kv=float(sub.get('voltage_level_kv', 115)), 
                                        name=str(sub.get('name', 'Substation')))
                net.bus_geodata.loc[bus_idx] = [coords[0], coords[1]]
                sub_map[sub['id']] = bus_idx
                sub_coords.append([coords[0], coords[1], bus_idx])

        # 2. Add Slack
        if len(net.bus) > 0:
            pp.create_ext_grid(net, bus=net.bus.index[0], vm_pu=1.0, name="DB_Slack")

        # 3. Create Lines
        for line in lines:
            fb_id = line.get('from_substation_id')
            tb_id = line.get('to_substation_id')
            
            fb = sub_map.get(fb_id)
            tb = sub_map.get(tb_id)
            
            if fb is not None and tb is not None:
                pp.create_line(net, from_bus=fb, to_bus=tb, 
                               length_km=float(line.get('length_km', 1.0)),
                               std_type="N2XS(FL)2Y 1x240 RM/35 64/110 kV",
                               name=str(line.get('name', 'Line')))

        # 4. Create Transformers (MV/LV)
        if transformers:
            for trafo in transformers:
                sub_id = trafo.get('substation_id')
                hv_bus = sub_map.get(sub_id)
                if hv_bus is not None:
                    # Create a new LV bus at the same location
                    hv_row = net.bus.loc[hv_bus]
                    lv_bus = pp.create_bus(net, vn_kv=float(trafo.get('voltage_secondary_kv', 0.4)),
                                           name=f"{trafo.get('name', 'Trafo')}_LV",
                                           geodata=(self.bus_geodata[hv_bus]))
                    
                    pp.create_transformer(net, hv_bus=hv_bus, lv_bus=lv_bus,
                                          std_type="0.4 MVA 20/0.4 kV", # Default fallback
                                          name=str(trafo.get('name', 'Transformer')))

        self.net = net
        self._map_bus_geodata()
        logger.info(f"Loaded dynamic grid from DB: {len(self.net.bus)} buses, {len(self.net.line)} lines")
        return net

    def load_egat_grid(self, data_dir: Optional[str] = None):
        """
        Builds the Thailand transmission network from EGAT GeoJSON data.
        """
        import geopandas as gpd
        from shapely.geometry import Point, LineString
        from scipy.spatial import cKDTree

        net = self.create_empty_network("EGAT_Transmission")
        
        # Search for data directory
        search_paths = [data_dir, "data/geojson", "backend/data/geojson"]
        found_dir = None
        for path in search_paths:
            if path and os.path.exists(os.path.join(path, "egat_substations.geojson")):
                found_dir = path
                break
        
        if not found_dir:
            logger.warning(f"EGAT GeoJSON files not found. Falling back to Island Hub.")
            return self.build_island_hub()

        try:
            subs_path = f"{found_dir}/egat_substations.geojson"
            lines_path = f"{found_dir}/egat_combined_lines.geojson"
            
            subs_gdf = gpd.read_file(subs_path)
            lines_gdf = gpd.read_file(lines_path)
            
            # 1. Create Buses from Substations
            sub_coords = []
            for _, row in subs_gdf.iterrows():
                geom = row.geometry
                if isinstance(geom, Point):
                    voltages = []
                    for v in ['500', '230', '115', '69']:
                        v_val = row.get(f'voltage{v}')
                        if v_val and str(v_val).strip():
                            voltages.append(float(v))
                    
                    vn_kv = max(voltages) if voltages else 115.0
                    
                    bus_idx = pp.create_bus(net, vn_kv=vn_kv, 
                                            name=str(row.get('subname_t', 'Substation')))
                    net.bus_geodata.loc[bus_idx] = [geom.x, geom.y]
                    sub_coords.append([geom.x, geom.y, bus_idx])

            logger.info(f"Created {len(net.bus)} buses. GeoData size: {len(net.bus_geodata) if hasattr(net, 'bus_geodata') else 'N/A'}")
            
            # 1.5 Add External Grid to first bus as slack
            if len(net.bus) > 0:
                pp.create_ext_grid(net, bus=net.bus.index[0], vm_pu=1.0, name="Slack")

            # 2. Create Lines and Snap Endpoints
            # Use KDTree for fast snapping
            sub_points = np.array([[c[0], c[1]] for c in sub_coords])
            if len(sub_points) > 0:
                tree = cKDTree(sub_points)
                
                for _, row in lines_gdf.iterrows():
                    geom = row.geometry
                    if isinstance(geom, LineString):
                        coords = list(geom.coords)
                        start_pt = np.array([coords[0][0], coords[0][1]])
                        end_pt = np.array([coords[-1][0], coords[-1][1]])
                        
                        # Find nearest buses (within ~1km)
                        dist_s, idx_s = tree.query(start_pt)
                        dist_e, idx_e = tree.query(end_pt)
                        
                        # Snap threshold: 0.01 deg ~= 1.1km
                        if dist_s < 0.01 and dist_e < 0.01:
                            fb = int(sub_coords[idx_s][2])
                            tb = int(sub_coords[idx_e][2])
                            
                            if fb != tb:
                                # Estimate voltage from properties or length
                                vn_kv = 115.0 # Default
                                pp.create_line(net, from_bus=fb, to_bus=tb, length_km=geom.length * 111.0, 
                                               std_type="N2XS(FL)2Y 1x240 RM/35 64/110 kV",
                                               name=str(row.get('name', 'Line')))

            self.net = net
            self._map_bus_geodata()
            logger.info(f"Loaded EGAT grid: {len(self.net.bus)} buses, {len(self.net.line)} lines")
            return net
        except Exception as e:
            logger.error(f"Failed to load EGAT grid: {e}")
            return self.build_island_hub()

    def build_ieee_123_node(self, data_dir: Optional[str] = None):
        """
        Builds the IEEE 123-node test feeder for standard VPP logic benchmarks.
        Loads from the TESP repository GLM models.
        """
        # Search for the GLM file
        search_paths = [data_dir, "tesp_repo/data/feeders", "backend/tesp_repo/data/feeders"]
        glm_path = None
        for path in search_paths:
            if path and os.path.exists(os.path.join(path, "IEEE-123.glm")):
                glm_path = os.path.join(path, "IEEE-123.glm")
                break

        if glm_path:
            logger.info(f"Loading IEEE 123-node model from {glm_path}")
            return self.build_from_glm(glm_path)
        
        logger.warning("IEEE-123.glm not found. Falling back to a synthetic European LV network.")
        import pandapower.networks as pn
        self.net = pn.ieee_european_lv_asymmetric("off_peak_1440")
        self.net.name = "IEEE_European_LV_Fallback"
        self._map_bus_geodata()
        return self.net

    def build_ieee_8500_node(self, data_dir: Optional[str] = None):
        """
        Builds the IEEE 8500-node test feeder for large-scale network congestion benchmarks.
        Loads from the TESP repository GLM models.
        """
        # Search for the GLM file
        search_paths = [data_dir, "tesp_repo/examples/capabilities/ieee8500", "backend/tesp_repo/examples/capabilities/ieee8500"]
        glm_path = None
        for path in search_paths:
            if path and os.path.exists(os.path.join(path, "IEEE_8500.glm")):
                glm_path = os.path.join(path, "IEEE_8500.glm")
                break

        if glm_path:
            logger.info(f"Loading IEEE 8500-node model from {glm_path}")
            return self.build_from_glm(glm_path)
        
        logger.error("IEEE_8500.glm not found. Falling back to simple Island Hub.")
        return self.build_island_hub()

    def build_from_glm(self, glm_path: str):
        """
        Load a GridLAB-D .glm model file and convert it to a pandapower network.

        Uses GLMPandapowerConverter to parse GLM topology objects (node, load,
        line, transformer, regulator, switch) into pandapower elements.

        Args:
            glm_path: Path to the .glm file.

        Returns:
            The pandapower network built from the GLM file.
        """
        from .glm_converter import GLMPandapowerConverter

        converter = GLMPandapowerConverter()
        self.net = converter.convert(glm_path, name="GLM_Feeder")
        self._map_bus_geodata()
        logger.info(
            f"Loaded GLM network from {glm_path}: "
            f"{len(self.net.bus)} buses, {len(self.net.line)} lines, "
            f"{len(self.net.trafo)} trafos, {len(self.net.load)} loads"
        )
        return self.net

    def load_from_geojson(self, substations_path: str, lines_path: str):
        pass

    def _map_bus_geodata(self):
        """Cache bus coordinates for faster lookup."""
        self.bus_geodata = {}
        
        # Check if net has bus_geodata and it's not empty
        has_geo = hasattr(self.net, 'bus_geodata') and not self.net.bus_geodata.empty
        
        for idx in self.net.bus.index:
            if has_geo and idx in self.net.bus_geodata.index:
                self.bus_geodata[idx] = (float(self.net.bus_geodata.at[idx, 'x']), 
                                        float(self.net.bus_geodata.at[idx, 'y']))
            else:
                # Default/Fallback if no geodata for this bus
                self.bus_geodata[idx] = (0.0, 0.0)

    def map_meters_to_buses_spatial(self, meters: List[Any]):
        """
        Maps smart meters to the nearest bus in the network based on spatial distance.
        """
        from scipy.spatial import cKDTree
        
        self.meter_to_bus = {}
        
        # Build KDTree of all buses
        bus_coords = []
        bus_indices = []
        for idx, (x, y) in self.bus_geodata.items():
            bus_coords.append([x, y])
            bus_indices.append(idx)
            
        if not bus_coords:
            logger.warning("No buses in network to map meters to")
            return {}
            
        tree = cKDTree(np.array(bus_coords))
        
        for meter in meters:
            meter_lat = getattr(meter, 'latitude', None)
            meter_lon = getattr(meter, 'longitude', None)
            
            if meter_lat is None or meter_lon is None:
                config = getattr(meter, 'config', {})
                meter_lat = config.get('latitude')
                meter_lon = config.get('longitude')
                
            if meter_lat is not None and meter_lon is not None:
                # Query with [lon, lat]
                dist, idx = tree.query([meter_lon, meter_lat])
                self.meter_to_bus[meter.meter_id] = bus_indices[idx]
            else:
                # Fallback to first bus
                self.meter_to_bus[meter.meter_id] = bus_indices[0]
                
        return self.meter_to_bus

    def map_meters_to_buses_direct(self, meters: List[Any]):
        """
        Maps smart meters directly to bus indices using the 'bus_idx' config property.
        Used for generated IEEE node meters.
        """
        self.meter_to_bus = {}
        
        bus_indices = list(self.net.bus.index)
        if not bus_indices:
            logger.warning("No buses in network to map meters to")
            return {}

        for meter in meters:
            meter_id = meter.meter_id
            config = getattr(meter, 'config', {})
            bus_idx = config.get("bus_idx")
            
            if bus_idx is not None and bus_idx in bus_indices:
                self.meter_to_bus[meter_id] = bus_idx
            else:
                # Fallback to a random bus or first bus if invalid
                self.meter_to_bus[meter_id] = bus_indices[0]

        return self.meter_to_bus

    def map_meters_to_buses(self, meters: List[Any]):
        """
        Maps smart meters to the nearest bus in the network based on coordinates.
        In this simplified island model, we map by 'zone' property if available, 
        else by distance.
        """
        self.meter_to_bus = {}
        
        # Zone-based mapping for Island Hub
        zone_map = {
            "Mainland": "Khanom 115kV",
            "Samui": "Samui Dist 22kV",
            "Phangan": "Phangan Dist 22kV",
            "Tao": "Tao Dist 22kV"
        }

        for meter in meters:
            meter_id = meter.meter_id
            config = getattr(meter, 'config', {})
            zone = config.get("zone", "Samui")
            
            target_bus_name = zone_map.get(zone, "Samui Dist 22kV")
            bus_idx = self.net.bus[self.net.bus.name == target_bus_name].index
            
            if not bus_idx.empty:
                self.meter_to_bus[meter_id] = bus_idx[0]
            else:
                self.meter_to_bus[meter_id] = self.net.bus.index[0] # Fallback to first bus

        return self.meter_to_bus

    def update_measurements(self, readings: List[Any]):
        """
        Inject meter readings into the pandapower network as loads and sgens.
        """
        # Clear existing dynamic elements to avoid accumulation
        # Actually, in a simulation loop, we might want to just update values
        # but for simplicity we'll reset loads/sgens mapped to meters.
        
        # Reset P/Q for all loads and sgens that represent meters
        self.net.load.p_mw = 0
        self.net.load.q_mvar = 0
        self.net.sgen.p_mw = 0
        self.net.sgen.q_mvar = 0

        for r in readings:
            bus_idx = self.meter_to_bus.get(r.meter_id)
            if bus_idx is None:
                continue

            # Consumption (Load)
            # Energy (kWh) in interval -> Power (kW) -> MW
            # We'll assume the interval is known or provided in readings
            # For now, we'll use active_power_kw if available, else derived from energy
            p_mw = getattr(r, 'active_power_kw', 0) / 1000.0
            if p_mw == 0 and hasattr(r, 'energy_consumed'):
                # Simple conversion if interval is 5s (default in engine)
                p_mw = (r.energy_consumed * 720) / 1000.0 

            if p_mw > 0:
                # Find or create load at this bus for this meter
                load_idx = self.net.load[self.net.load.name == f"load_{r.meter_id}"].index
                if load_idx.empty:
                    pp.create_load(self.net, bus=bus_idx, p_mw=p_mw, q_mvar=p_mw*0.1, name=f"load_{r.meter_id}")
                else:
                    self.net.load.at[load_idx[0], 'p_mw'] = p_mw
                    self.net.load.at[load_idx[0], 'q_mvar'] = p_mw * 0.1

            # Generation (SGen)
            gen_mw = getattr(r, 'energy_generated', 0) * 720 / 1000.0
            if gen_mw > 0:
                sgen_idx = self.net.sgen[self.net.sgen.name == f"sgen_{r.meter_id}"].index
                if sgen_idx.empty:
                    pp.create_sgen(self.net, bus=bus_idx, p_mw=gen_mw, q_mvar=0, name=f"sgen_{r.meter_id}")
                else:
                    self.net.sgen.at[sgen_idx[0], 'p_mw'] = gen_mw

    def run_power_flow(self):
        """Execute the power flow solver."""
        try:
            pp.runpp(self.net, algorithm="iwamoto_nr", max_iteration=50, numba=True)
            return True
        except Exception as e:
            logger.error(f"Power flow failed: {e}")
            return False

    def get_grid_geojson(self) -> Dict[str, Any]:
        """
        Convert the current grid state to a GeoJSON FeatureCollection.
        """
        features = []

        # Buses
        for idx, row in self.net.bus.iterrows():
            pos = self.bus_geodata.get(idx, (0, 0))
            vm_pu = 1.0
            if hasattr(self.net, 'res_bus') and idx in self.net.res_bus.index:
                vm_pu = self.net.res_bus.at[idx, 'vm_pu']
            
            features.append({
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [pos[0], pos[1]]}, # Lon, Lat
                "properties": {
                    "type": "bus",
                    "id": int(idx),
                    "name": str(row['name']),
                    "vn_kv": float(row['vn_kv']),
                    "vm_pu": float(vm_pu),
                    "v_kv": float(vm_pu * row['vn_kv'])
                }
            })

        # Lines
        for idx, row in self.net.line.iterrows():
            fb = int(row['from_bus'])
            tb = int(row['to_bus'])
            f_pos = self.bus_geodata.get(fb, (0, 0))
            t_pos = self.bus_geodata.get(tb, (0, 0))
            
            loading = 0.0
            if hasattr(self.net, 'res_line') and idx in self.net.res_line.index:
                loading = self.net.res_line.at[idx, 'loading_percent']
            
            features.append({
                "type": "Feature",
                "geometry": {
                    "type": "LineString", 
                    "coordinates": [[f_pos[1], f_pos[0]], [t_pos[1], t_pos[0]]]
                },
                "properties": {
                    "type": "line",
                    "id": int(idx),
                    "name": str(row['name']),
                    "loading_percent": float(loading),
                    "max_i_ka": float(row['max_i_ka'])
                }
            })

        return {
            "type": "FeatureCollection",
            "features": features
        }
