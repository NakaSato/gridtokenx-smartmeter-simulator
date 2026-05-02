"""
EGAT Transmission System Data Module - Refactored
"""

from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
import numpy as np
import json
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

from .osm_grid_mapper import OSMGridMapper
 
# Global cache for direct router access
EGAT_SUBSTATIONS: Dict[str, Any] = {}

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

from .egat_configs.egat_standards import EGATVoltage, SubstationType, TRANSFORMER_DEFAULTS
from ..models.egat import EGATSubstation, EGATLine, EGATPowerPlant

class EGATTransmissionBuilder(TopologyBuilder):
    """
    Builds EGAT transmission-level network topology for Thailand.
    """

    def __init__(self, network_name: str = "EGAT Transmission Network"):
        super().__init__(network_name)
        self.substations: Dict[str, EGATSubstation] = {}
        self.lines: Dict[str, EGATLine] = {}
        self.power_plants: Dict[str, EGATPowerPlant] = {}
        self._load_egat_data()

    def _load_egat_data(self):
        DATA_DIR = Path(__file__).parent.parent / "data"
        subs_path = DATA_DIR / "egat_substations.json"
        lines_path = DATA_DIR / "egat_lines.json"
        try:
            if not subs_path.exists() or not lines_path.exists(): return
            with open(subs_path, "r", encoding="utf-8") as f:
                subs_json = json.load(f)
            for sub_id, d in subs_json.items():
                sub = EGATSubstation(
                    sub_id=sub_id, name=d["name"], name_en=d["name_en"], voltage_kv=d["voltage_kv"],
                    sub_type=SubstationType(d["type"]), latitude=d["latitude"], longitude=d["longitude"],
                    province=d["province"], region=d["region"], capacity_mva=d["capacity_mva"],
                    connected_generators=d.get("connected_generators", [])
                )
                self.substations[sub_id] = sub
                EGAT_SUBSTATIONS[sub_id] = d # Fill global cache
            with open(lines_path, "r", encoding="utf-8") as f:
                lines_json = json.load(f)
            for idx, d in enumerate(lines_json):
                lid = f"Line_{idx:03d}"
                self.lines[lid] = EGATLine(
                    line_id=lid, from_substation=d["from_substation"], to_substation=d["to_substation"],
                    voltage_kv=d["voltage_kv"], length_km=d["length_km"], circuit=d.get("circuit", 1),
                    conductor=d.get("conductor", "Unknown"), line_type=d.get("type", "AC"),
                    status=d.get("status", "operational")
                )
            
            # Auto-load spotlight data if available
            BACKEND_DATA_DIR = Path(__file__).parent.parent.parent.parent / "data"
            spotlight_path = BACKEND_DATA_DIR / "geojson" / "spotlight_samui.geojson"
            if spotlight_path.exists():
                self.load_from_geojson(str(spotlight_path))
            elif (DATA_DIR / "spotlight_samui.geojson").exists():
                # Fallback to local data dir if not in central geojson dir
                self.load_from_geojson(str(DATA_DIR / "spotlight_samui.geojson"))
        except Exception as e: logger.error(f"Failed to load EGAT data: {e}")

    def build_full_network(self, include_voltages=[500.0, 230.0, 115.0]) -> "pp.pandapowerNet":
        self.create_network()
        self.inject_into_pandapower(self.net, include_voltages)
        return self.net

    def inject_into_pandapower(self, net: "pp.pandapowerNet", include_voltages=[500.0, 230.0, 115.0]):
        """Inject EGAT assets into an existing pandapower network."""
        # Use our internal net for bus mapping if we are building a full network,
        # otherwise we need to manage bus mapping carefully for the target net.
        # For simplicity, we'll assume we can use our add_bus/add_line methods
        # by temporarily setting self.net to the target net.
        old_net = self.net
        self.net = net
        try:
            for sid, sub in self.substations.items():
                if sub.voltage_kv in include_voltages:
                    vlevel = VoltageLevel.HV if sub.voltage_kv >= 230 else VoltageLevel.MV
                    self.add_bus(BusConfig(
                        bus_id=f"EGAT_{sid}", voltage_level=vlevel, vn_kv=sub.voltage_kv,
                        name=sub.name_en, zone=f"{sub.region}_{int(sub.voltage_kv)}kV",
                        geo_data={"latitude": sub.latitude, "longitude": sub.longitude}
                    ))
            for lid, line in self.lines.items():
                if line.voltage_kv in include_voltages:
                    f, t = f"EGAT_{line.from_substation}", f"EGAT_{line.to_substation}"
                    if f in self.bus_map and t in self.bus_map:
                        self.add_line(LineConfig(from_bus_id=f, to_bus_id=t, length_km=line.length_km, 
                                               std_type=self._get_conductor_std_type(line.conductor), name=lid, parallel=line.circuit))
        finally:
            self.net = old_net

    def _get_conductor_std_type(self, conductor_str: str) -> str:
        if "560/50" in conductor_str: return "679-AL1/86-ST1A 380.0"
        elif "240/40" in conductor_str: return "490-AL1/64-ST1A 220.0" if "bundle" in conductor_str else "243-AL1/39-ST1A 110.0"
        return "243-AL1/39-ST1A 110.0"

    def calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate Euclidean distance between two points (simplified)."""
        return np.sqrt((lat1 - lat2)**2 + (lon1 - lon2)**2) * 111.0 # approx km

    def get_substations(self, voltage_kv: Optional[float] = None, region: Optional[str] = None) -> List[EGATSubstation]:
        subs = list(self.substations.values())
        if voltage_kv:
            subs = [s for s in subs if s.voltage_kv == voltage_kv]
        if region:
            subs = [s for s in subs if s.region == region]
        return subs

    def get_lines(self, voltage_kv: Optional[float] = None, region: Optional[str] = None) -> List[EGATLine]:
        lines = list(self.lines.values())
        if voltage_kv:
            lines = [l for l in lines if l.voltage_kv == voltage_kv]
        if region:
            # A line is in a region if either its 'from' or 'to' substation is in that region
            lines = [l for l in lines if (
                self.substations.get(l.from_substation) and self.substations[l.from_substation].region == region or
                self.substations.get(l.to_substation) and self.substations[l.to_substation].region == region
            )]
        return lines

    def get_power_plants(self, region: Optional[str] = None) -> List[EGATPowerPlant]:
        """Return list of power plants, optionally filtered by region."""
        plants = list(self.power_plants.values())
        
        # Add legacy plants from substations if not already present
        for sid, sub in self.substations.items():
            if region and sub.region != region: continue
            for gen_id in sub.connected_generators:
                if gen_id not in self.power_plants:
                    plants.append(EGATPowerPlant(
                        plant_id=gen_id, name=gen_id.replace("_", " "), plant_type="Thermal",
                        capacity_mw=500.0, status="operational", latitude=sub.latitude, longitude=sub.longitude,
                        source="EGAT"
                    ))
        
        if region:
            plants = [p for p in plants if p.region == region or not p.region]
        return plants

    def get_network_statistics(self) -> Dict[str, Any]:
        lines_df = pd.DataFrame([l.__dict__ for l in self.lines.values()])
        subs_df = pd.DataFrame([s.__dict__ for s in self.substations.values()])
        
        stats = {
            "total_substations": len(self.substations),
            "total_transmission_lines": len(self.lines),
            "total_line_length_km": float(lines_df["length_km"].sum()) if not lines_df.empty else 0.0,
            "regions_covered": subs_df["region"].unique().tolist() if not subs_df.empty else [],
            "provinces_covered": subs_df["province"].unique().tolist() if not subs_df.empty else [],
        }
        
        for kv in [500.0, 230.0, 115.0]:
            k = f"{int(kv)}kv"
            stats[f"substations_{k}"] = len(subs_df[subs_df["voltage_kv"] == kv]) if not subs_df.empty else 0
            stats[f"line_length_{k}_km"] = float(lines_df[lines_df["voltage_kv"] == kv]["length_km"].sum()) if not lines_df.empty else 0.0
            stats[f"total_capacity_{k}_mva"] = float(subs_df[subs_df["voltage_kv"] == kv]["capacity_mva"].sum()) if not subs_df.empty else 0.0
            
        return stats

    def build_regional_network(self, region: str) -> "pp.pandapowerNet":
        self.create_network()
        # Find all voltages active in this region
        subs = self.get_substations(region=region)
        voltages = sorted(list(set(s.voltage_kv for s in subs)))
        self.inject_into_pandapower(self.net, include_voltages=voltages)
        return self.net

    def export_geojson(self) -> Dict[str, Any]:
        features = []
        for sid, sub in self.substations.items():
            features.append({
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [sub.longitude, sub.latitude]},
                "properties": {
                    "layer": "egat_substation", "id": sid, "name": sub.name, "name_en": sub.name_en,
                    "voltage_kv": sub.voltage_kv, "type": sub.sub_type.value, "province": sub.province,
                    "region": sub.region, "capacity_mva": sub.capacity_mva, "marker_color": "#dc2626" if sub.voltage_kv >= 500 else "#3b82f6"
                }
            })
        for lid, line in self.lines.items():
            f, t = self.substations.get(line.from_substation), self.substations.get(line.to_substation)
            if f and t:
                features.append({
                    "type": "Feature",
                    "geometry": {"type": "LineString", "coordinates": [[f.longitude, f.latitude], [t.longitude, t.latitude]]},
                    "properties": {
                        "layer": "egat_line", "id": lid, "voltage_kv": line.voltage_kv, "length_km": line.length_km,
                        "from": line.from_substation, "to": line.to_substation, 
                        "line_type": line.line_type,
                        "line_color": "#dc2626" if line.voltage_kv >= 500 else "#3b82f6"
                    }
                })
        for pid, plant in self.power_plants.items():
            features.append({
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [plant.longitude, plant.latitude]},
                "properties": {
                    "layer": "egat_plant", "id": pid, "name": plant.name, "type": plant.plant_type,
                    "capacity_mw": plant.capacity_mw, "status": plant.status, "marker_color": "#10b981"
                }
            })
        return {"type": "FeatureCollection", "features": features}

    def load_from_geojson(self, path: str):
        """Load OSM or EGAT data from GeoJSON."""
        logger.info(f"Loading grid data from GeoJSON: {path}")
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            for feature in data.get("features", []):
                props = feature["properties"]
                geom = feature["geometry"]
                ptype = props.get("type")
                
                # Handle Substations
                if ptype == "substation" or props.get("power") == "substation" or props.get("layer") == "egat_substation":
                    # Generate a unique ID if name is generic or missing
                    name = props.get("name", "Substation")
                    sid = props.get("id") or props.get("sub_id")
                    if not sid:
                        sid = f"SUB_{len(self.substations)}" if name == "Substation" else name
                    
                    if geom["type"] == "Point":
                        lon, lat = geom["coordinates"]
                    else:
                        coords = geom["coordinates"][0]
                        lon = sum(c[0] for c in coords) / len(coords)
                        lat = sum(c[1] for c in coords) / len(coords)

                    # Safe SubstationType lookup
                    stype_raw = props.get("substation_type")
                    try:
                        stype = SubstationType(stype_raw)
                    except ValueError:
                        # Fallback to SUB_115 if unknown
                        stype = SubstationType.SUB_115
                        if stype_raw:
                            logger.debug(f"Unknown substation_type '{stype_raw}', defaulting to SUB_115")

                    self.substations[sid] = EGATSubstation(
                        sub_id=sid,
                        name=props.get("name", sid),
                        name_en=props.get("name_en", props.get("name", sid)),
                        voltage_kv=float(props.get("voltage_kv") or 115.0),
                        sub_type=stype,
                        latitude=lat,
                        longitude=lon,
                        province=props.get("province", "Unknown"),
                        region=props.get("region", "Unknown"),
                        capacity_mva=float(props.get("capacity_mva", 100.0))
                    )
                
                # Handle Transmission Lines
                elif ptype == "transmission" or props.get("power") == "line" or props.get("layer") == "egat_line":
                    lid = props.get("id") or props.get("line_id") or f"LINE_{len(self.lines)}"
                    # Use voltage_class if voltage_kv is missing (OSM spotlight schema)
                    v_kv_raw = str(props.get("voltage_kv") or props.get("voltage_class") or "115000")
                    # Handle multiple voltages like "115000;230000"
                    v_kv_str = v_kv_raw.split(';')[0]
                    try:
                        v_kv = float(v_kv_str)
                        if v_kv > 1000:
                            v_kv = v_kv / 1000
                    except ValueError:
                        v_kv = 115.0
                    
                    self.lines[lid] = EGATLine(
                        line_id=lid,
                        from_substation=props.get("from_substation", "Unknown"),
                        to_substation=props.get("to_substation", "Unknown"),
                        voltage_kv=float(v_kv or 115.0),
                        length_km=float(props.get("length_km", props.get("distance_km", 1.0))),
                        circuit=int(props.get("circuit", 1)),
                        conductor=props.get("conductor", "Unknown"),
                        line_type=props.get("type", "overhead"),
                        status=props.get("status", "operational")
                    )

                # Handle Power Plants (Spotlight Schema)
                elif ptype == "plant":
                    pid = props.get("name") or f"PLANT_{len(self.power_plants)}"
                    if geom["type"] == "Point":
                        lon, lat = geom["coordinates"]
                        self.power_plants[pid] = EGATPowerPlant(
                            plant_id=pid,
                            name=props.get("name", pid),
                            plant_type=props.get("technology", "Thermal"),
                            capacity_mw=float(props.get("capacity_mw", 0.0)),
                            status=props.get("status", "operational"),
                            latitude=lat,
                            longitude=lon,
                            source=props.get("source", "Unknown")
                        )
            
            logger.info(f"Loaded {len(self.substations)} substations, {len(self.lines)} lines, and {len(self.power_plants)} plants from GeoJSON")
        except Exception as e:
            logger.error(f"Failed to load GeoJSON: {e}")

    def fetch_from_osm(self, location: str = "Thailand"):
        """Fetch grid data from OSM and merge into current network."""
        try:
            mapper = OSMGridMapper()
            data = mapper.fetch_transmission_data(location=location)
            subs, lines = mapper.map_to_egat_models(data)
            
            for sub in subs:
                self.substations[sub.sub_id] = sub
            for line in lines:
                self.lines[line.line_id] = line
                
            logger.info(f"Merged {len(subs)} substations and {len(lines)} lines from OSM")
        except Exception as e:
            logger.error(f"Error during OSM fetch: {e}")

    def build_topology(self):
        """Build topology (already handled in build_full_network)."""
        pass
