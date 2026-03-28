"""
Grid Topology Builder - Phase 2 Implementation

Creates realistic electrical distribution network topologies in pandapower.
Supports multiple voltage levels, transformer connections, and various network structures.

References:
- meter_spec.md Section 4.1 (Network Architecture)
- meter_spec.md Section 4.2 (Grid Topology Modeling)
"""

from typing import List, Dict, Any, Optional, Tuple
from enum import Enum
from dataclasses import dataclass
import pandas as pd
import numpy as np
from scipy.spatial import Delaunay
import networkx as nx

try:
    import pandapower as pp
    import pandapower.networks as pn
    PANDAPOWER_AVAILABLE = True
except ImportError:
    PANDAPOWER_AVAILABLE = False


class VoltageLevel(Enum):
    """Voltage levels for distribution networks."""
    HV = "High Voltage"        # 110+ kV (transmission/subtransmission)
    MV = "Medium Voltage"      # 1-35 kV (primary distribution)
    LV = "Low Voltage"         # 0.23-0.4 kV (secondary distribution)


class NetworkTopology(Enum):
    """Network topology types."""
    RADIAL = "radial"          # Tree structure, single path to each bus
    RING = "ring"              # Looped structure with redundancy
    MESH = "mesh"              # Fully connected grid
    FEEDER = "feeder"          # Multiple radial feeders from substation


@dataclass
class BusConfig:
    """Configuration for a single bus."""
    bus_id: str
    voltage_level: VoltageLevel
    vn_kv: float  # Nominal voltage in kV
    name: Optional[str] = None
    zone: Optional[str] = None
    geo_data: Optional[Dict[str, float]] = None  # latitude, longitude


@dataclass
class LineConfig:
    """Configuration for a line connection."""
    from_bus_id: str
    to_bus_id: str
    length_km: float
    std_type: str = "NAYY 4x50 SE"  # Default LV cable
    name: Optional[str] = None
    parallel: int = 1


@dataclass
class TransformerConfig:
    """Configuration for a transformer."""
    hv_bus_id: str  # High voltage side
    lv_bus_id: str  # Low voltage side
    sn_mva: float   # Rated power in MVA
    vn_hv_kv: float # HV nominal voltage
    vn_lv_kv: float # LV nominal voltage
    std_type: Optional[str] = None
    name: Optional[str] = None


class TopologyBuilder:
    """
    Builds electrical distribution network topologies in pandapower.
    
    Supports:
    - Multiple voltage levels (HV, MV, LV)
    - Various network structures (radial, ring, mesh, feeder)
    - Transformer connections between voltage levels
    - Geographic metadata for spatial analysis
    """
    
    def __init__(self, network_name: str = "Distribution Network"):
        """
        Initialize topology builder.
        
        Args:
            network_name: Name for the pandapower network
        """
        if not PANDAPOWER_AVAILABLE:
            raise ImportError(
                "pandapower is required for TopologyBuilder. "
                "Install with: pip install pandapower>=2.14.0"
            )
        
        self.network_name = network_name
        self.net: Optional[pp.pandapowerNet] = None
        self.bus_map: Dict[str, int] = {}  # bus_id -> pandapower bus index
        
    def create_network(self) -> pp.pandapowerNet:
        """
        Create an empty pandapower network.
        
        Returns:
            Empty pandapower network object
        """
        self.net = pp.create_empty_network(name=self.network_name)
        self.bus_map = {}
        return self.net
    
    def add_bus(self, config: BusConfig) -> int:
        """
        Add a bus to the network.
        
        Args:
            config: Bus configuration
            
        Returns:
            Pandapower bus index
        """
        if self.net is None:
            raise ValueError("Network not created. Call create_network() first.")
        
        # Check if bus already exists
        if config.bus_id in self.bus_map:
            return self.bus_map[config.bus_id]
        
        # Create bus
        bus_idx = pp.create_bus(
            self.net,
            vn_kv=config.vn_kv,
            name=config.name or config.bus_id,
            zone=config.zone,
            geodata=None if not config.geo_data else (
                config.geo_data.get('latitude'),
                config.geo_data.get('longitude')
            )
        )
        
        self.bus_map[config.bus_id] = bus_idx
        return bus_idx
    
    def add_line(self, config: LineConfig) -> int:
        """
        Add a line connection between two buses.
        
        Args:
            config: Line configuration
            
        Returns:
            Pandapower line index
        """
        if self.net is None:
            raise ValueError("Network not created. Call create_network() first.")
        
        # Get or create buses
        from_bus = self.bus_map.get(config.from_bus_id)
        to_bus = self.bus_map.get(config.to_bus_id)
        
        if from_bus is None or to_bus is None:
            raise ValueError(
                f"Buses must exist before creating line: "
                f"{config.from_bus_id} -> {config.to_bus_id}"
            )
        
        # Create line
        line_idx = pp.create_line(
            self.net,
            from_bus=from_bus,
            to_bus=to_bus,
            length_km=config.length_km,
            std_type=config.std_type,
            name=config.name or f"{config.from_bus_id}_{config.to_bus_id}",
            parallel=config.parallel
        )
        
        return line_idx
    
    def add_transformer(self, config: TransformerConfig) -> int:
        """
        Add a transformer between two voltage levels.
        
        Args:
            config: Transformer configuration
            
        Returns:
            Pandapower transformer index
        """
        if self.net is None:
            raise ValueError("Network not created. Call create_network() first.")
        
        hv_bus = self.bus_map.get(config.hv_bus_id)
        lv_bus = self.bus_map.get(config.lv_bus_id)
        
        if hv_bus is None or lv_bus is None:
            raise ValueError(
                f"Buses must exist before creating transformer: "
                f"{config.hv_bus_id} -> {config.lv_bus_id}"
            )
        
        # Create transformer
        if config.std_type:
            trafo_idx = pp.create_transformer(
                self.net,
                hv_bus=hv_bus,
                lv_bus=lv_bus,
                std_type=config.std_type,
                name=config.name or f"Trafo_{config.hv_bus_id}_{config.lv_bus_id}"
            )
        else:
            trafo_idx = pp.create_transformer_from_parameters(
                self.net,
                hv_bus=hv_bus,
                lv_bus=lv_bus,
                sn_mva=config.sn_mva,
                vn_hv_kv=config.vn_hv_kv,
                vn_lv_kv=config.vn_lv_kv,
                vk_percent=6.0,  # Typical short-circuit voltage
                vkr_percent=1.0,  # Typical resistive component
                pfe_kw=0,  # No-load losses (can be configured)
                i0_percent=0,  # No-load current
                name=config.name or f"Trafo_{config.hv_bus_id}_{config.lv_bus_id}"
            )
        
        return trafo_idx
    
    def add_external_grid(self, bus_id: str, vm_pu: float = 1.0, va_degree: float = 0.0) -> int:
        """
        Add external grid connection (slack bus).
        
        Args:
            bus_id: Bus to connect grid to
            vm_pu: Voltage magnitude in per-unit
            va_degree: Voltage angle in degrees
            
        Returns:
            Pandapower external grid index
        """
        if self.net is None:
            raise ValueError("Network not created. Call create_network() first.")
        
        bus_idx = self.bus_map.get(bus_id)
        if bus_idx is None:
            raise ValueError(f"Bus {bus_id} does not exist")
        
        ext_grid_idx = pp.create_ext_grid(
            self.net,
            bus=bus_idx,
            vm_pu=vm_pu,
            va_degree=va_degree,
            name=f"Grid_{bus_id}"
        )
        
        return ext_grid_idx
    
    def build_radial_network(
        self,
        num_buses: int,
        voltage_kv: float = 0.4,
        line_length_km: float = 0.1,
        add_grid: bool = True
    ) -> pp.pandapowerNet:
        """
        Build a simple radial (tree) network.
        
        Args:
            num_buses: Number of buses to create
            voltage_kv: Nominal voltage in kV
            line_length_km: Length of each line segment
            add_grid: Whether to add external grid at bus 0
            
        Returns:
            Configured pandapower network
        """
        self.create_network()
        
        # Determine voltage level
        if voltage_kv < 1.0:
            voltage_level = VoltageLevel.LV
            std_type = "NAYY 4x50 SE"  # LV cable
        elif voltage_kv < 35.0:
            voltage_level = VoltageLevel.MV
            std_type = "NA2XS2Y 1x185 RM/25 12/20 kV"  # MV cable
        else:
            voltage_level = VoltageLevel.HV
            std_type = "N2XS(FL)2Y 1x120 RM/35 64/110 kV"  # HV cable
        
        # Create buses
        for i in range(num_buses):
            bus_config = BusConfig(
                bus_id=f"Bus_{i}",
                voltage_level=voltage_level,
                vn_kv=voltage_kv,
                name=f"Bus {i}",
                zone=f"Zone_{i // 10}"  # Group into zones of 10
            )
            self.add_bus(bus_config)
        
        # Connect buses sequentially (radial topology)
        for i in range(num_buses - 1):
            line_config = LineConfig(
                from_bus_id=f"Bus_{i}",
                to_bus_id=f"Bus_{i+1}",
                length_km=line_length_km,
                std_type=std_type,
                name=f"Line_{i}_{i+1}"
            )
            self.add_line(line_config)
        
        # Add external grid
        if add_grid:
            self.add_external_grid("Bus_0", vm_pu=1.0)
        
        return self.net
    
    def build_feeder_network(
        self,
        num_feeders: int,
        buses_per_feeder: int,
        voltage_kv: float = 0.4,
        line_length_km: float = 0.1,
        substation_bus_id: str = "Substation"
    ) -> pp.pandapowerNet:
        """
        Build a multi-feeder network with radial feeders from a substation.
        
        Args:
            num_feeders: Number of radial feeders
            buses_per_feeder: Number of buses on each feeder
            voltage_kv: Nominal voltage in kV
            line_length_km: Length of each line segment
            substation_bus_id: ID for substation bus
            
        Returns:
            Configured pandapower network
        """
        self.create_network()
        
        voltage_level = VoltageLevel.LV if voltage_kv < 1.0 else VoltageLevel.MV
        std_type = "NAYY 4x50 SE" if voltage_kv < 1.0 else "NA2XS2Y 1x185 RM/25 12/20 kV"
        
        # Create substation bus
        substation_config = BusConfig(
            bus_id=substation_bus_id,
            voltage_level=voltage_level,
            vn_kv=voltage_kv,
            name="TX-01 (800 kVA)" if substation_bus_id == "TX-01" else "Substation",
            zone="Substation"
        )
        self.add_bus(substation_config)
        self.add_external_grid(substation_bus_id, vm_pu=1.0)
        
        # Create feeders
        for feeder_idx in range(num_feeders):
            # Create buses for this feeder
            for bus_idx in range(buses_per_feeder):
                bus_id = f"Feeder{feeder_idx}_Bus{bus_idx}"
                bus_config = BusConfig(
                    bus_id=bus_id,
                    voltage_level=voltage_level,
                    vn_kv=voltage_kv,
                    name=f"F{feeder_idx} B{bus_idx}",
                    zone=f"Feeder_{feeder_idx}"
                )
                self.add_bus(bus_config)
            
            # Connect first bus to substation
            first_bus_id = f"Feeder{feeder_idx}_Bus0"
            line_config = LineConfig(
                from_bus_id=substation_bus_id,
                to_bus_id=first_bus_id,
                length_km=line_length_km,
                std_type=std_type,
                name=f"Feeder_{feeder_idx}_Main"
            )
            self.add_line(line_config)
            
            # Connect buses within feeder (radial)
            for bus_idx in range(buses_per_feeder - 1):
                from_bus_id = f"Feeder{feeder_idx}_Bus{bus_idx}"
                to_bus_id = f"Feeder{feeder_idx}_Bus{bus_idx+1}"
                line_config = LineConfig(
                    from_bus_id=from_bus_id,
                    to_bus_id=to_bus_id,
                    length_km=line_length_km,
                    std_type=std_type,
                    name=f"F{feeder_idx}_L{bus_idx}"
                )
                self.add_line(line_config)
        
        return self.net
    
    def build_multi_voltage_network(
        self,
        hv_buses: int = 1,
        mv_buses: int = 3,
        lv_buses_per_mv: int = 5,
        hv_voltage_kv: float = 110.0,
        mv_voltage_kv: float = 10.0,
        lv_voltage_kv: float = 0.4
    ) -> pp.pandapowerNet:
        """
        Build a multi-voltage level network with transformers.
        
        Topology:
        - HV buses (transmission/subtransmission)
        - HV/MV transformers
        - MV buses (primary distribution)
        - MV/LV transformers
        - LV buses (secondary distribution)
        
        Args:
            hv_buses: Number of HV buses
            mv_buses: Number of MV buses per HV bus
            lv_buses_per_mv: Number of LV buses per MV bus
            hv_voltage_kv: HV voltage level
            mv_voltage_kv: MV voltage level
            lv_voltage_kv: LV voltage level
            
        Returns:
            Configured pandapower network
        """
        self.create_network()
        
        # Create HV level
        for hv_idx in range(hv_buses):
            hv_bus_id = f"HV_Bus_{hv_idx}"
            hv_config = BusConfig(
                bus_id=hv_bus_id,
                voltage_level=VoltageLevel.HV,
                vn_kv=hv_voltage_kv,
                name=f"HV {hv_idx}",
                zone="HV"
            )
            self.add_bus(hv_config)
            
            # Add grid connection to first HV bus
            if hv_idx == 0:
                self.add_external_grid(hv_bus_id, vm_pu=1.0)
            
            # Create MV buses connected to this HV bus
            for mv_idx in range(mv_buses):
                mv_bus_id = f"HV{hv_idx}_MV_Bus_{mv_idx}"
                mv_config = BusConfig(
                    bus_id=mv_bus_id,
                    voltage_level=VoltageLevel.MV,
                    vn_kv=mv_voltage_kv,
                    name=f"MV {hv_idx}-{mv_idx}",
                    zone=f"MV_{hv_idx}"
                )
                self.add_bus(mv_config)
                
                # Add HV/MV transformer
                trafo_hv_mv = TransformerConfig(
                    hv_bus_id=hv_bus_id,
                    lv_bus_id=mv_bus_id,
                    sn_mva=10.0,  # 10 MVA transformer
                    vn_hv_kv=hv_voltage_kv,
                    vn_lv_kv=mv_voltage_kv,
                    name=f"Trafo_HV{hv_idx}_MV{mv_idx}"
                )
                self.add_transformer(trafo_hv_mv)
                
                # Create LV buses connected to this MV bus
                for lv_idx in range(lv_buses_per_mv):
                    lv_bus_id = f"HV{hv_idx}_MV{mv_idx}_LV_Bus_{lv_idx}"
                    lv_config = BusConfig(
                        bus_id=lv_bus_id,
                        voltage_level=VoltageLevel.LV,
                        vn_kv=lv_voltage_kv,
                        name=f"LV {hv_idx}-{mv_idx}-{lv_idx}",
                        zone=f"LV_{hv_idx}_{mv_idx}"
                    )
                    self.add_bus(lv_config)
                    
                    # Add MV/LV transformer
                    trafo_mv_lv = TransformerConfig(
                        hv_bus_id=mv_bus_id,
                        lv_bus_id=lv_bus_id,
                        sn_mva=0.4,  # 400 kVA transformer
                        vn_hv_kv=mv_voltage_kv,
                        vn_lv_kv=lv_voltage_kv,
                        name=f"Trafo_MV{mv_idx}_LV{lv_idx}"
                    )
                    self.add_transformer(trafo_mv_lv)
                    
                    # Connect LV buses within same MV zone (optional)
                    if lv_idx > 0:
                        prev_lv_bus_id = f"HV{hv_idx}_MV{mv_idx}_LV_Bus_{lv_idx-1}"
                        line_config = LineConfig(
                            from_bus_id=prev_lv_bus_id,
                            to_bus_id=lv_bus_id,
                            length_km=0.05,  # 50m
                            std_type="NAYY 4x50 SE",
                            name=f"LV_Line_{hv_idx}_{mv_idx}_{lv_idx}"
                        )
                        self.add_line(line_config)
        
        return self.net
    
    def add_feeder(
        self,
        parent_bus_id: str,
        feeder_name: str,
        num_buses: int,
        voltage_kv: float = 0.4,
        line_length_km: float = 0.05,
        zone_id: Optional[str] = None
    ) -> List[int]:
        """
        Add a radial feeder branching from an existing bus.
        
        Args:
            parent_bus_id: Bus ID to attach feeder to
            feeder_name: Name prefix for the feeder
            num_buses: Number of buses in the feeder
            voltage_kv: Voltage level of the feeder
            line_length_km: Length of line segments
            zone_id: Optional zone identifier for SLP assignment
            
        Returns:
            List of created bus indices
        """
        if self.net is None:
            raise ValueError("Network not created. Call create_network() first.")
            
        parent_bus_idx = self.bus_map.get(parent_bus_id)
        if parent_bus_idx is None:
             raise ValueError(f"Parent bus {parent_bus_id} does not exist")

        voltage_level = VoltageLevel.LV if voltage_kv < 1.0 else VoltageLevel.MV
        std_type = "NAYY 4x50 SE" if voltage_kv < 1.0 else "NA2XS2Y 1x185 RM/25 12/20 kV"
        
        created_bus_indices = []
        previous_bus_id = parent_bus_id
        
        for i in range(num_buses):
            bus_id = f"{feeder_name}_Bus_{i}"
            # Check if bus already exists to avoid duplication
            if bus_id in self.bus_map:
                created_bus_indices.append(self.bus_map[bus_id])
                previous_bus_id = bus_id
                continue

            bus_config = BusConfig(
                bus_id=bus_id,
                voltage_level=voltage_level,
                vn_kv=voltage_kv,
                name=f"{feeder_name} Node {i}",
                zone=zone_id or feeder_name
            )
            bus_idx = self.add_bus(bus_config)
            created_bus_indices.append(bus_idx)
            
            # Connect to previous bus
            line_config = LineConfig(
                from_bus_id=previous_bus_id,
                to_bus_id=bus_id,
                length_km=line_length_km,
                std_type=std_type,
                name=f"{feeder_name}_Line_{i}"
            )
            self.add_line(line_config)
            
            previous_bus_id = bus_id
            
        return created_bus_indices
    
    def get_bus_index(self, bus_id: str) -> Optional[int]:
        """
        Get pandapower bus index from bus_id.
        
        Args:
            bus_id: Bus identifier
            
        Returns:
            Pandapower bus index or None if not found
        """
        return self.bus_map.get(bus_id)
    
    def get_network_summary(self) -> Dict[str, Any]:
        """
        Get summary statistics of the network.
        
        Returns:
            Dictionary with network statistics
        """
        if self.net is None:
            return {"error": "Network not created"}
        
        return {
            "name": self.network_name,
            "buses": len(self.net.bus),
            "lines": len(self.net.line),
            "transformers": len(self.net.trafo),
            "external_grids": len(self.net.ext_grid),
            "loads": len(self.net.load),
            "generators": len(self.net.gen),
            "static_generators": len(self.net.sgen),
            "voltage_levels": self._get_voltage_levels(),
        }
    
    def _get_voltage_levels(self) -> List[float]:
        """Get unique voltage levels in the network."""
        if self.net is None:
            return []
        return sorted(self.net.bus['vn_kv'].unique().tolist())

        return self.net

    def build_street_aligned_network(
        self,
        bus_configs: List[BusConfig],
        voltage_kv: float = 0.4,
        add_grid: bool = True
    ) -> pp.pandapowerNet:
        """
        Build a realistic LV network with a "Main Street" backbone and service drops.
        
        Logic:
        1. Identify the "Main Street" backbone by finding a line that minimizes
           lateral distance to most nodes (or just use the longest axis for now).
        2. Create a series of "Feeder" nodes along this backbone.
        3. Connect each house to its nearest perpendicular point on the backbone.
        
        Args:
            bus_configs: List of bus configurations with coordinates.
            voltage_kv: Nominal voltage in kV.
            add_grid: Whether to add external grid.
            
        Returns:
            Pandapower network with backbone and service drops.
        """
        self.create_network()
        
        if not bus_configs:
            return self.net

        points = np.array([[c.geo_data['longitude'], c.geo_data['latitude']] for c in bus_configs if c.geo_data])
        if len(points) < 2:
            return self.net

        # 1. Determine a simple backbone (e.g., the line connecting the extremes of the cluster)
        # In a real system, we'd use road geometry, but for now, we'll project nodes to a "best fit line".
        # We'll use the Principal Component as the "Street" direction.
        mean = np.mean(points, axis=0)
        u, s, vh = np.linalg.svd(points - mean)
        backbone_dir = vh[0] # Direction of the street
        
        # 2. Project all points onto the backbone line
        projections = []
        for i, p in enumerate(points):
            # p_proj = mean + <p - mean, backbone_dir> * backbone_dir
            offset = np.dot(p - mean, backbone_dir)
            p_proj = mean + offset * backbone_dir
            projections.append((offset, p_proj, i))
            
        # Sort projections along the backbone
        projections.sort(key=lambda x: x[0])
        
        # 3. Create Backbone Nodes (Feeders)
        std_type_feeder = "NAYY 4x150 SE" # Thick cable for main feeder
        std_type_service = "NAYY 4x50 SE"  # Thinner cable for service drop
        
        previous_backbone_bus_id = None
        
        # We'll create one backbone node for each unique projection point or a sampled set
        # To keep it simple, one backbone node per house.
        for i, (offset, p_proj, house_idx) in enumerate(projections):
            house_config = bus_configs[house_idx]
            backbone_node_id = f"Backbone_{house_config.bus_id}"
            
            # Add backbone node
            self.add_bus(BusConfig(
                bus_id=backbone_node_id,
                voltage_level=VoltageLevel.LV,
                vn_kv=voltage_kv,
                name=f"Feeder Node {i}",
                geo_data={'longitude': p_proj[0], 'latitude': p_proj[1]},
                zone=house_config.zone
            ))
            
            # Connect to previous backbone node (Feeder line)
            if previous_backbone_bus_id:
                # Distance in degrees to km
                dist = np.linalg.norm(p_proj - prev_p_proj) * 111.0
                self.add_line(LineConfig(
                    from_bus_id=previous_backbone_bus_id,
                    to_bus_id=backbone_node_id,
                    length_km=max(dist, 0.005),
                    std_type=std_type_feeder,
                    name=f"Main_Feeder_{i}"
                ))
            
            # Add the house bus
            self.add_bus(house_config)
            
            # Connect house to backbone node (Service Drop)
            # Distance in degrees to km
            dist_drop = np.linalg.norm(points[house_idx] - p_proj) * 111.0
            self.add_line(LineConfig(
                from_bus_id=backbone_node_id,
                to_bus_id=house_config.bus_id,
                length_km=max(dist_drop, 0.005),
                std_type=std_type_service,
                name=f"Service_Drop_{house_config.bus_id}"
            ))
            
            previous_backbone_bus_id = backbone_node_id
            prev_p_proj = p_proj

        # 4. Add Substation and Transformer at the start of the backbone
        if add_grid and projections:
            first_house_idx = projections[0][2]
            base_p = points[first_house_idx]
            
            # Substation slightly offset from the first house
            substation_bus_id = "MV_Substation"
            self.add_bus(BusConfig(
                bus_id=substation_bus_id,
                voltage_level=VoltageLevel.MV,
                vn_kv=22.0,  # 22kV MV
                name="Primary Substation",
                geo_data={'longitude': base_p[0], 'latitude': base_p[1] + 0.0005},
                zone=bus_configs[first_house_idx].zone
            ))
            
            first_backbone_id = f"Backbone_{bus_configs[first_house_idx].bus_id}"
            
            # Add Transformer 22/0.4 kV
            self.add_transformer(TransformerConfig(
                hv_bus_id=substation_bus_id,
                lv_bus_id=first_backbone_id,
                sn_mva=0.63,     # 630 kVA
                vn_hv_kv=22.0,   # High-voltage side
                vn_lv_kv=0.4,    # Low-voltage side
                name="Distribution_Transformer"
            ))
            
            self.add_external_grid(substation_bus_id, vm_pu=1.0)
            
        return self.net
