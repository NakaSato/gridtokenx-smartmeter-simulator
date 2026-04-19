"""
EGAT Transmission System Data Module

Realistic transmission-level grid model for Thailand based on EGAT (Electricity
Generating Authority of Thailand) infrastructure data.

Voltage Levels:
- 500 kV: Main backbone (HVDC/HVAC inter-regional)
- 230 kV: Regional interconnection
- 115 kV: Sub-transmission (connects to MEA/PEA substations)
- 69 kV: Legacy system (being phased out)

Grid Structure:
- EGAT operates the national transmission network
- MEA serves Bangkok Metro (Bangkok, Nonthaburi, Samut Prakan)
- PEA serves 74 other provinces
- Transmission is mostly radial with ring backups in critical areas

References:
- EGAT System Control and Operation Division
- OECD Thailand Renewable Grid Integration Assessment (2018)
- JICA Power System Operation Survey
- PyPSA-TH configuration (voltages: 69, 115, 230, 500 kV)
- CIGRE National Power System Thailand Report (2020)
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import pandas as pd
import numpy as np
import json
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

try:
    import pandapower as pp
    PANDAPOWER_AVAILABLE = True
except ImportError:
    PANDAPOWER_AVAILABLE = False

from .topology_builder import (
    TopologyBuilder,
    BusConfig,
    LineConfig,
    TransformerConfig,
    VoltageLevel,
)


class EGATVoltage(Enum):
    """EGAT standard transmission voltages."""
    KV_500 = 500.0
    KV_230 = 230.0
    KV_115 = 115.0
    KV_69 = 69.0


class SubstationType(Enum):
    """EGAT substation classifications."""
    MAIN_500 = "500kV Main"        # Primary backbone substations
    MAIN_230 = "230kV Regional"     # Regional interconnection
    SUB_115 = "115kV Sub"           # Sub-transmission (MEA/PEA interface)
    SUB_69 = "69kV Legacy"          # Legacy substations
    SWITCHING = "Switching Station" # Intermediate switching stations
    GENERATOR = "Generator Step-up" # Power plant connection


# =============================================================================
# Real EGAT Substation Data
# Compiled from public EGAT reports, OECD assessment, and JICA surveys.
# Coordinates are approximate, derived from official EGAT system maps.
# =============================================================================

# Data is now loaded from JSON files in the ../data/ directory.


@dataclass
class EGATSubstation:
    """EGAT transmission substation data class."""
    sub_id: str
    name: str
    name_en: str
    voltage_kv: float
    sub_type: SubstationType
    latitude: float
    longitude: float
    province: str
    region: str
    capacity_mva: float
    connected_generators: List[str] = field(default_factory=list)
    notes: str = ""


@dataclass
class EGATLine:
    """EGAT transmission line data class."""
    line_id: str
    from_substation: str
    to_substation: str
    voltage_kv: float
    length_km: float
    circuit: int
    conductor: str
    line_type: str  # HVAC or HVDC
    status: str
    notes: str = ""


@dataclass
class EGATPowerPlant:
    """EGAT power plant data class."""
    plant_id: str
    name: str
    plant_type: str
    capacity_mw: float
    status: str
    latitude: float
    longitude: float
    source: str = ""


class EGATTransmissionBuilder(TopologyBuilder):
    """
    Builds EGAT transmission-level network topology for Thailand.

    Creates a pandapower network model of EGAT's transmission system including:
    - 500 kV backbone substations and lines
    - 230 kV regional interconnections
    - 115 kV sub-transmission (MEA/PEA interface points)
    - Generator step-up connections

    Example:
        builder = EGATTransmissionBuilder()
        net = builder.build_full_network()
    """

    # EGAT transformer parameters (typical values)
    TRANSFORMER_500_230_VK = 12.0   # 500/230 kV short-circuit voltage
    TRANSFORMER_230_115_VK = 10.0   # 230/115 kV short-circuit voltage
    TRANSFORMER_500_115_VK = 14.0   # 500/115 kV short-circuit voltage
    TRANSFORMER_VKR = 0.5           # Resistive component (%)
    TRANSFORMER_PFE_KW = 10.0       # No-load losses (kW)
    TRANSFORMER_I0 = 0.1            # No-load current (%)

    def calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two points in km."""
        return self._haversine_km(lon1, lat1, lon2, lat2)

    def inject_into_pandapower(self, net: "pp.pandapowerNet"):
        """
        Inject EGAT transmission assets into an existing pandapower network.
        
        Args:
            net: The pandapower network to inject assets into.
        """
        import pandapower as pp
        import pandas as pd
        
        # 1. Add Substations as Buses
        sub_to_bus = {}
        for sub_id, sub in self.substations.items():
            # Avoid duplicate buses if they already exist by name
            existing_bus = net.bus[net.bus.name == sub.name_en]
            if not existing_bus.empty:
                bus_idx = existing_bus.index[0]
            else:
                bus_idx = pp.create_bus(
                    net, 
                    vn_kv=sub.voltage_kv, 
                    name=sub.name_en, 
                    type="b",
                    zone=sub.region
                )
            sub_to_bus[sub_id] = bus_idx
            
            # Store geodata
            if 'bus_geocoord' not in net or net.bus_geocoord is None:
                net.bus_geocoord = pd.DataFrame(columns=['x', 'y'])
            net.bus_geocoord.loc[bus_idx] = [sub.longitude, sub.latitude]

        # 2. Add Transmission Lines
        for line_id, line in self.lines.items():
            from_bus = sub_to_bus.get(line.from_substation)
            to_bus = sub_to_bus.get(line.to_substation)
            
            if from_bus is not None and to_bus is not None:
                # Check if line already exists
                pp.create_line(
                    net, 
                    from_bus=from_bus, 
                    to_bus=to_bus, 
                    length_km=line.length_km,
                    std_type=self._get_conductor_std_type(line.conductor),
                    name=line.line_id,
                    parallel=line.circuit
                )

        # 3. Add Power Plants as Generators
        for plant_id, plant in self.power_plants.items():
            # Find nearest substation to connect the plant
            nearest_sub_id = self._find_nearest_substation(plant.latitude, plant.longitude)
            if nearest_sub_id:
                bus_idx = sub_to_bus.get(nearest_sub_id)
                if bus_idx is not None:
                    pp.create_sgen(
                        net, 
                        bus=bus_idx, 
                        p_mw=plant.capacity_mw, 
                        q_mvar=0, 
                        name=plant.name,
                        type=plant.plant_type
                    )

    def __init__(self, network_name: str = "EGAT Transmission Network"):
        """
        Initialize EGAT transmission builder.

        Args:
            network_name: Name for the pandapower network
        """
        super().__init__(network_name)
        self.substations: Dict[str, EGATSubstation] = {}
        self.lines: Dict[str, EGATLine] = {}
        self.power_plants: Dict[str, EGATPowerPlant] = {}
        self._load_egat_data()
        self._load_supplemental_data()

    def _load_supplemental_data(self):
        """Load supplemental grid data from GeoJSON files."""
        try:
            import json
            from pathlib import Path
            
            # Use same project root logic as settings.py
            PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
            spotlight_file = PROJECT_ROOT / "data" / "spotlight-Khanom-power-station-103km.geojson"
            
            if not spotlight_file.exists():
                return
                
            with open(spotlight_file) as f:
                data = json.load(f)
                
            for idx, feature in enumerate(data.get("features", [])):
                props = feature.get("properties", {})
                geom = feature.get("geometry", {})
                feat_type = props.get("type")
                
                if feat_type == "substation":
                    sub_id = f"KHANOM_SUB_{idx}"
                    coords = geom.get("coordinates")
                    # Map to EGATSubstation
                    self.substations[sub_id] = EGATSubstation(
                        sub_id=sub_id,
                        name=props.get("name", "Khanom Substation"),
                        name_en=props.get("name", "Khanom Substation"),
                        voltage_kv=float(props.get("voltage_kv", 115.0)) if props.get("voltage_kv") else 115.0,
                        sub_type=SubstationType.SUB_115, # Default
                        latitude=coords[1],
                        longitude=coords[0],
                        province="Nakhon Si Thammarat",
                        region="South",
                        capacity_mva=100.0,
                    )
                elif feat_type == "plant":
                    plant_id = f"KHANOM_PLANT_{idx}"
                    coords = geom.get("coordinates")
                    self.power_plants[plant_id] = EGATPowerPlant(
                        plant_id=plant_id,
                        name=props.get("name", "Khanom Power Plant"),
                        plant_type=props.get("technology", "Thermal"),
                        capacity_mw=float(props.get("capacity_mw", 0)),
                        status=props.get("status", "Operating"),
                        latitude=coords[1],
                        longitude=coords[0],
                        source=props.get("source", "Spotlight"),
                    )
                elif feat_type == "transmission":
                    coords = geom.get("coordinates")
                    if not coords or len(coords) < 2:
                        continue
                        
                    start_pt = coords[0]
                    end_pt = coords[-1]
                    
                    # Find nearest substations to endpoints
                    from_sub = self._find_nearest_substation(start_pt[1], start_pt[0])
                    to_sub = self._find_nearest_substation(end_pt[1], end_pt[0])
                    
                    if from_sub and to_sub and from_sub != to_sub:
                        line_id = f"KHANOM_LINE_{idx}"
                        # Calculate length from coordinates
                        length_km = self._calculate_line_length(coords)
                        
                        self.lines[line_id] = EGATLine(
                            line_id=line_id,
                            from_substation=from_sub,
                            to_substation=to_sub,
                            voltage_kv=115.0, # Default for these spotlight lines
                            length_km=length_km,
                            circuit=1,
                            conductor="Al/St 240/40 2-bundle 220.0",
                            line_type="HVAC",
                            status="Operational",
                            notes=props.get("name", "Khanom Interconnection"),
                        )
                    
        except Exception as e:
            # Silent fail for supplemental data
            pass

    def _find_nearest_substation(self, lat, lon, threshold_km=5.0):
        """Find the nearest substation within threshold distance."""
        nearest_id = None
        min_dist = threshold_km
        
        for sub_id, sub in self.substations.items():
            dist = self._haversine_km(lon, lat, sub.longitude, sub.latitude)
            if dist < min_dist:
                min_dist = dist
                nearest_id = sub_id
        return nearest_id

    def _calculate_line_length(self, coords):
        """Calculate total length of LineString in km."""
        total_dist = 0
        for i in range(len(coords) - 1):
            total_dist += self._haversine_km(
                coords[i][0], coords[i][1],
                coords[i+1][0], coords[i+1][1]
            )
        return round(total_dist, 2)

    @staticmethod
    def _haversine_km(lon1: float, lat1: float, lon2: float, lat2: float) -> float:
        """Haversine distance in km."""
        import math
        R = 6371
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = (math.sin(dlat / 2) ** 2 +
             math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
             math.sin(dlon / 2) ** 2)
        return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    def _load_egat_data(self):
        """Load EGAT substation and line data from JSON files."""
        # Data files are located in the same directory structure as the adapter
        DATA_DIR = Path(__file__).parent.parent / "data"
        subs_path = DATA_DIR / "egat_substations.json"
        lines_path = DATA_DIR / "egat_lines.json"
        
        try:
            if not subs_path.exists() or not lines_path.exists():
                logger.error(f"EGAT data files missing at {DATA_DIR}")
                return

            with open(subs_path, "r", encoding="utf-8") as f:
                subs_json = json.load(f)
            
            for sub_id, sub_data in subs_json.items():
                self.substations[sub_id] = EGATSubstation(
                    sub_id=sub_id,
                    name=sub_data["name"],
                    name_en=sub_data["name_en"],
                    voltage_kv=sub_data["voltage_kv"],
                    sub_type=SubstationType(sub_data["type"]),
                    latitude=sub_data["latitude"],
                    longitude=sub_data["longitude"],
                    province=sub_data["province"],
                    region=sub_data["region"],
                    capacity_mva=sub_data["capacity_mva"],
                    connected_generators=sub_data.get("connected_generators", []),
                    notes=sub_data.get("notes", ""),
                )

            with open(lines_path, "r", encoding="utf-8") as f:
                lines_json = json.load(f)
            
            for idx, line_data in enumerate(lines_json):
                line_id = f"Line_{idx:03d}"
                self.lines[line_id] = EGATLine(
                    line_id=line_id,
                    from_substation=line_data["from_substation"],
                    to_substation=line_data["to_substation"],
                    voltage_kv=line_data["voltage_kv"],
                    length_km=line_data["length_km"],
                    circuit=line_data["circuit"],
                    conductor=line_data["conductor"],
                    line_type=line_data["type"],
                    status=line_data["status"],
                    notes=line_data.get("notes", ""),
                )
            logger.info(f"Successfully loaded {len(self.substations)} substations and {len(self.lines)} lines from JSON.")
        except Exception as e:
            logger.error(f"Failed to load EGAT data from JSON: {e}")

    def get_substations(
        self,
        voltage_kv: Optional[float] = None,
        region: Optional[str] = None,
        province: Optional[str] = None,
    ) -> List[EGATSubstation]:
        """
        Filter substations by criteria.

        Args:
            voltage_kv: Filter by voltage level
            region: Filter by region (North, Central, Northeast, East, South)
            province: Filter by province name

        Returns:
            List of matching EGATSubstation objects
        """
        result = list(self.substations.values())
        if voltage_kv is not None:
            result = [s for s in result if s.voltage_kv == voltage_kv]
        if region is not None:
            result = [s for s in result if s.region == region]
        if province is not None:
            result = [s for s in result if s.province == province]
        return result

    def get_lines(
        self,
        voltage_kv: Optional[float] = None,
        region: Optional[str] = None,
    ) -> List[EGATLine]:
        """
        Filter transmission lines by criteria.

        Args:
            voltage_kv: Filter by voltage level
            region: Filter by region (lines where both endpoints are in region)

        Returns:
            List of matching EGATLine objects
        """
        result = list(self.lines.values())
        if voltage_kv is not None:
            result = [l for l in result if l.voltage_kv == voltage_kv]
        if region is not None:
            def _in_region(sub_id):
                sub = self.substations.get(sub_id)
                return sub and sub.region == region
            result = [l for l in result if _in_region(l.from_substation) and _in_region(l.to_substation)]
        return result

    def get_power_plants(self, region: Optional[str] = None) -> List[EGATPowerPlant]:
        """Filter power plants by region."""
        result = list(self.power_plants.values())
        if region:
            # For supplemental plants, we set region manually or check coords
            # For simplicity, we filter by name or known regions
            if region == "South":
                result = [p for p in result if "KHANOM" in p.plant_id]
        return result

    def _get_conductor_std_type(self, conductor_str: str) -> str:
        """
        Map EGAT conductor specification to pandapower standard type.

        Uses pandapower's built-in standard types that closely match
        EGAT conductor specifications.

        Args:
            conductor_str: EGAT conductor description

        Returns:
            pandapower standard type string
        """
        if "560/50" in conductor_str:
            # 500 kV: Use largest available (380 kV class)
            return "679-AL1/86-ST1A 380.0"
        elif "240/40" in conductor_str:
            if "3-bundle" in conductor_str or "4-bundle" in conductor_str:
                # 230 kV: Use 220 kV class (large conductor)
                return "490-AL1/64-ST1A 220.0"
            else:
                # 115 kV: Use 110 kV class
                return "243-AL1/39-ST1A 110.0"
        else:
            return "243-AL1/39-ST1A 110.0"  # Default fallback

    def _get_transformer_type(self, hv_kv: float, lv_kv: float) -> Tuple[float, float]:
        """
        Get transformer parameters for voltage conversion.

        Args:
            hv_kv: High voltage side
            lv_kv: Low voltage side

        Returns:
            (sn_mva, vk_percent) tuple
        """
        if hv_kv == 500 and lv_kv == 230:
            return (1200.0, self.TRANSFORMER_500_230_VK)
        elif hv_kv == 230 and lv_kv == 115:
            return (600.0, self.TRANSFORMER_230_115_VK)
        elif hv_kv == 500 and lv_kv == 115:
            return (900.0, self.TRANSFORMER_500_115_VK)
        elif hv_kv == 230 and lv_kv == 22:
            return (100.0, 10.0)  # 230/22 kV distribution step-down
        elif hv_kv == 115 and lv_kv == 22:
            return (50.0, 10.0)  # 115/22 kV distribution step-down
        else:
            return (500.0, 10.0)  # Default

    def build_full_network(
        self,
        include_500kv: bool = True,
        include_230kv: bool = True,
        include_115kv: bool = True,
        include_lines: bool = True,
        include_transformers: bool = True,
    ) -> "pp.pandapowerNet":
        """
        Build complete EGAT transmission network.

        Args:
            include_500kv: Include 500 kV substations
            include_230kv: Include 230 kV substations
            include_115kv: Include 115 kV substations
            include_lines: Include transmission lines
            include_transformers: Include inter-voltage transformers

        Returns:
            Configured pandapower network
        """
        self.create_network()

        # Determine which voltage levels to include
        allowed_voltages = set()
        if include_500kv:
            allowed_voltages.add(500.0)
        if include_230kv:
            allowed_voltages.add(230.0)
        if include_115kv:
            allowed_voltages.add(115.0)

        # Create buses for each substation
        for sub_id, sub in self.substations.items():
            if sub.voltage_kv not in allowed_voltages:
                continue

            bus_id = f"EGAT_{sub_id}"

            # Determine voltage level enum
            if sub.voltage_kv >= 230:
                vlevel = VoltageLevel.HV
            else:
                vlevel = VoltageLevel.MV

            bus_config = BusConfig(
                bus_id=bus_id,
                voltage_level=vlevel,
                vn_kv=sub.voltage_kv,
                name=f"{sub.name_en}",
                zone=f"{sub.region}_{int(sub.voltage_kv)}kV",
                geo_data={"latitude": sub.latitude, "longitude": sub.longitude},
            )
            self.add_bus(bus_config)

            # Add external grid connection to 500 kV substations (slack buses)
            if sub.voltage_kv == 500.0 and sub.sub_type == SubstationType.MAIN_500:
                self.add_external_grid(bus_id, vm_pu=1.0, va_degree=0.0)

        # Create transmission lines
        if include_lines:
            for line_id, line in self.lines.items():
                if line.voltage_kv not in allowed_voltages:
                    continue

                from_bus = f"EGAT_{line.from_substation}"
                to_bus = f"EGAT_{line.to_substation}"

                # Skip if either endpoint not included
                if from_bus not in self.bus_map or to_bus not in self.bus_map:
                    continue

                conductor_std = self._get_conductor_std_type(line.conductor)

                line_config = LineConfig(
                    from_bus_id=from_bus,
                    to_bus_id=to_bus,
                    length_km=line.length_km,
                    std_type=conductor_std,
                    name=f"{line.from_substation}-{line.to_substation} ({line.voltage_kv}kV)",
                    parallel=line.circuit,
                )
                self.add_line(line_config)

        # Create inter-voltage transformers
        if include_transformers:
            # Find substations with multiple voltage levels at same location
            # (i.e., locations where 500/230 or 230/115 transformation occurs)
            self._add_auto_transformers()

        return self.net

    def _add_auto_transformers(self):
        """
        Automatically detect and add transformers between voltage levels.

        Transformers are added at locations where substations of different
        voltage levels are geographically co-located (within 2 km).
        """
        # Group substations by proximity (within 2 km)
        subs_list = list(self.substations.values())
        processed_pairs = set()

        for i, sub_a in enumerate(subs_list):
            for sub_b in subs_list[i + 1:]:
                # Skip same voltage level
                if sub_a.voltage_kv == sub_b.voltage_kv:
                    continue

                # Calculate distance (rough approximation)
                d_lat = abs(sub_a.latitude - sub_b.latitude)
                d_lon = abs(sub_a.longitude - sub_b.longitude)
                dist_km = np.sqrt(d_lat**2 + d_lon**2) * 111.0

                if dist_km < 2.0:  # Within 2 km = likely same station
                    pair_key = tuple(sorted([sub_a.sub_id, sub_b.sub_id]))
                    if pair_key in processed_pairs:
                        continue
                    processed_pairs.add(pair_key)

                    # Determine HV and LV sides
                    if sub_a.voltage_kv > sub_b.voltage_kv:
                        hv_sub, lv_sub = sub_a, sub_b
                    else:
                        hv_sub, lv_sub = sub_b, sub_a

                    hv_bus = f"EGAT_{hv_sub.sub_id}"
                    lv_bus = f"EGAT_{lv_sub.sub_id}"

                    if hv_bus not in self.bus_map or lv_bus not in self.bus_map:
                        continue

                    sn_mva, vk_pct = self._get_transformer_type(
                        hv_sub.voltage_kv, lv_sub.voltage_kv
                    )

                    trafo_config = TransformerConfig(
                        hv_bus_id=hv_bus,
                        lv_bus_id=lv_bus,
                        sn_mva=sn_mva,
                        vn_hv_kv=hv_sub.voltage_kv,
                        vn_lv_kv=lv_sub.voltage_kv,
                        name=f"TX_{hv_sub.sub_id}_{lv_sub.sub_id} ({hv_sub.voltage_kv}/{lv_sub.voltage_kv} kV)",
                    )
                    self.add_transformer(trafo_config)

    def build_regional_network(
        self,
        region: str,
        include_lower_voltage: bool = True,
    ) -> "pp.pandapowerNet":
        """
        Build network for a specific Thai region.

        Args:
            region: Region name (North, Central, Northeast, East, South)
            include_lower_voltage: Include lower voltage connections

        Returns:
            Configured pandapower network
        """
        self.create_network()

        # Get substations in this region
        region_subs = self.get_substations(region=region)
        region_sub_ids = {s.sub_id for s in region_subs}

        # Create buses
        for sub in region_subs:
            bus_id = f"EGAT_{sub.sub_id}"
            vlevel = VoltageLevel.HV if sub.voltage_kv >= 230 else VoltageLevel.MV

            bus_config = BusConfig(
                bus_id=bus_id,
                voltage_level=vlevel,
                vn_kv=sub.voltage_kv,
                name=f"{sub.name_en}",
                zone=f"{sub.region}_{int(sub.voltage_kv)}kV",
                geo_data={"latitude": sub.latitude, "longitude": sub.longitude},
            )
            self.add_bus(bus_config)

            if sub.voltage_kv == 500.0:
                self.add_external_grid(bus_id, vm_pu=1.0)

        # Add lines where both endpoints are in region
        for line in self.get_lines(region=region):
            from_bus = f"EGAT_{line.from_substation}"
            to_bus = f"EGAT_{line.to_substation}"

            if from_bus in self.bus_map and to_bus in self.bus_map:
                line_config = LineConfig(
                    from_bus_id=from_bus,
                    to_bus_id=to_bus,
                    length_km=line.length_km,
                    std_type=self._get_conductor_std_type(line.conductor),
                    name=f"{line.from_substation}-{line.to_substation}",
                    parallel=line.circuit,
                )
                self.add_line(line_config)

        return self.net

    def get_network_statistics(self) -> Dict[str, Any]:
        """
        Get comprehensive statistics of the EGAT transmission network.

        Returns:
            Dictionary with network statistics
        """
        subs = list(self.substations.values())
        lines = list(self.lines.values())

        total_capacity_500 = sum(s.capacity_mva for s in subs if s.voltage_kv == 500)
        total_capacity_230 = sum(s.capacity_mva for s in subs if s.voltage_kv == 230)
        total_capacity_115 = sum(s.capacity_mva for s in subs if s.voltage_kv == 115)

        line_length_500 = sum(l.length_km for l in lines if l.voltage_kv == 500)
        line_length_230 = sum(l.length_km for l in lines if l.voltage_kv == 230)
        line_length_115 = sum(l.length_km for l in lines if l.voltage_kv == 115)

        regions = set(s.region for s in subs)
        provinces = set(s.province for s in subs)

        return {
            "total_substations": len(subs),
            "substations_500kv": len([s for s in subs if s.voltage_kv == 500]),
            "substations_230kv": len([s for s in subs if s.voltage_kv == 230]),
            "substations_115kv": len([s for s in subs if s.voltage_kv == 115]),
            "total_transmission_lines": len(lines),
            "lines_500kv": len([l for l in lines if l.voltage_kv == 500]),
            "lines_230kv": len([l for l in lines if l.voltage_kv == 230]),
            "lines_115kv": len([l for l in lines if l.voltage_kv == 115]),
            "total_line_length_km": sum(l.length_km for l in lines),
            "line_length_500kv_km": line_length_500,
            "line_length_230kv_km": line_length_230,
            "line_length_115kv_km": line_length_115,
            "total_capacity_500kv_mva": total_capacity_500,
            "total_capacity_230kv_mva": total_capacity_230,
            "total_capacity_115kv_mva": total_capacity_115,
            "regions_covered": sorted(regions),
            "provinces_covered": sorted(provinces),
            "regions_count": len(regions),
            "provinces_count": len(provinces),
        }

    def export_geojson(self) -> Dict[str, Any]:
        """
        Export EGAT transmission network as GeoJSON.

        Returns:
            GeoJSON FeatureCollection with substations and lines
        """
        features = []

        # Substation features
        for sub in self.substations.values():
            features.append({
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [sub.longitude, sub.latitude],
                },
                "properties": {
                    "id": sub.sub_id,
                    "name": sub.name,
                    "name_en": sub.name_en,
                    "voltage_kv": sub.voltage_kv,
                    "type": sub.sub_type.value,
                    "province": sub.province,
                    "region": sub.region,
                    "capacity_mva": sub.capacity_mva,
                    "connected_generators": sub.connected_generators,
                    "notes": sub.notes,
                    "feature_type": "substation",
                },
            })

        # Line features
        for line in self.lines.values():
            from_sub = self.substations.get(line.from_substation)
            to_sub = self.substations.get(line.to_substation)
            if from_sub and to_sub:
                features.append({
                    "type": "Feature",
                    "geometry": {
                        "type": "LineString",
                        "coordinates": [
                            [from_sub.longitude, from_sub.latitude],
                            [to_sub.longitude, to_sub.latitude],
                        ],
                    },
                    "properties": {
                        "id": line.line_id,
                        "from": line.from_substation,
                        "to": line.to_substation,
                        "voltage_kv": line.voltage_kv,
                        "length_km": line.length_km,
                        "circuit": line.circuit,
                        "conductor": line.conductor,
                        "type": line.line_type,
                        "status": line.status,
                        "notes": line.notes,
                        "feature_type": "line",
                    },
                })

        return {
            "type": "FeatureCollection",
            "features": features,
            "metadata": {
                "source": "EGAT Transmission System",
                "substations_count": len(self.substations),
                "lines_count": len(self.lines),
                "generated_by": "smart_meter_simulator.adapters.egat_transmission",
            },
        }


def create_egat_full_network() -> "pp.pandapowerNet":
    """
    Convenience function: Build full EGAT transmission network.

    Returns:
        Pandapower network with all EGAT substations and lines
    """
    builder = EGATTransmissionBuilder()
    return builder.build_full_network()


def create_egat_regional_network(region: str) -> "pp.pandapowerNet":
    """
    Convenience function: Build EGAT network for specific region.

    Args:
        region: Region name (North, Central, Northeast, East, South)

    Returns:
        Pandapower network for the specified region
    """
    builder = EGATTransmissionBuilder()
    return builder.build_regional_network(region=region)


def get_egat_statistics() -> Dict[str, Any]:
    """
    Convenience function: Get EGAT transmission network statistics.

    Returns:
        Dictionary with network statistics
    """
    builder = EGATTransmissionBuilder()
    return builder.get_network_statistics()


def get_egat_geojson() -> Dict[str, Any]:
    """
    Convenience function: Export EGAT network as GeoJSON.

    Returns:
        GeoJSON FeatureCollection
    """
    builder = EGATTransmissionBuilder()
    return builder.export_geojson()
