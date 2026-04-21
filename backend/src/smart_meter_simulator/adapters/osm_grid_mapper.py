import osmnx as ox
import geopandas as gpd
import pandas as pd
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from shapely.geometry import Point
from ..models.egat import EGATSubstation, EGATLine
from .egat_configs.egat_standards import SubstationType

logger = logging.getLogger(__name__)

class OSMGridMapper:
    """
    Utility to fetch and map power grid data from OpenStreetMap using OSMnx.
    """

    def __init__(self, cache_dir: Optional[str] = None):
        if cache_dir:
            ox.settings.cache_folder = cache_dir
        ox.settings.use_cache = True
        ox.settings.log_console = False

    def fetch_grid_data(
        self, 
        location: Optional[str] = None, 
        point: Optional[Tuple[float, float]] = None, 
        dist: int = 50000,
        voltages: Optional[List[str]] = None,
        include_distribution: bool = False
    ) -> Dict[str, gpd.GeoDataFrame]:
        """
        Fetch transmission and distribution grid data (lines, substations, transformers).
        """
        power_types = ["line", "substation"]
        if include_distribution:
            power_types.extend(["transformer", "minor_line", "pole"])

        tags = {"power": power_types}
        if voltages:
            tags["voltage"] = voltages

        try:
            if location:
                logger.info(f"Fetching OSM data for location: {location}")
                gdf = ox.features_from_place(location, tags=tags)
            elif point:
                logger.info(f"Fetching OSM data around point: {point} (dist={dist}m)")
                gdf = ox.features_from_point(point, tags=tags, dist=dist)
            else:
                raise ValueError("Either location or point must be provided")

            # Split into categories
            lines_gdf = gdf[gdf["power"].isin(["line", "minor_line"])].copy()
            subs_gdf = gdf[gdf["power"] == "substation"].copy()
            trans_gdf = gdf[gdf["power"] == "transformer"].copy()

            logger.info(f"Found {len(lines_gdf)} lines, {len(subs_gdf)} substations, and {len(trans_gdf)} transformers")
            return {"lines": lines_gdf, "substations": subs_gdf, "transformers": trans_gdf}

        except Exception as e:
            logger.error(f"Failed to fetch OSM data: {e}")
            return {"lines": gpd.GeoDataFrame(), "substations": gpd.GeoDataFrame()}

    def map_to_egat_models(
        self, 
        osm_data: Dict[str, gpd.GeoDataFrame]
    ) -> Tuple[List[EGATSubstation], List[EGATLine]]:
        """
        Map OSM GeoDataFrames to EGAT models with spatial connectivity matching.
        """
        substations = []
        lines = []
        
        subs_gdf = osm_data["substations"].copy()
        if subs_gdf.empty:
            return [], []

        # 1. Map Substations first
        for idx, row in subs_gdf.iterrows():
            try:
                voltage_str = str(row.get("voltage", "115000")).split(";")[0]
                voltage_kv = float(voltage_str) / 1000 if voltage_str.isdigit() else 115.0
                
                sub_type = SubstationType.SUB_115
                if voltage_kv >= 500: sub_type = SubstationType.MAIN_500
                elif voltage_kv >= 230: sub_type = SubstationType.MAIN_230

                geom = row.geometry
                lat, lon = (geom.centroid.y, geom.centroid.x) if geom else (0.0, 0.0)
                
                sid = f"OSM_{idx[1]}" if isinstance(idx, tuple) else f"OSM_{idx}"
                sub = EGATSubstation(
                    sub_id=sid,
                    name=row.get("name", f"Substation {idx}"),
                    name_en=row.get("name:en", row.get("name", "Unknown")),
                    voltage_kv=voltage_kv,
                    sub_type=sub_type,
                    latitude=lat,
                    longitude=lon,
                    province=row.get("addr:province", "Unknown"),
                    region="Unknown",
                    capacity_mva=100.0,
                    connected_generators=[]
                )
                substations.append(sub)
                # Store model ID back in GDF for spatial matching
                subs_gdf.at[idx, "model_id"] = sid
            except Exception as e:
                logger.warning(f"Failed to map OSM substation {idx}: {e}")

        # 2. Map Lines and match endpoints to substations
        lines_gdf = osm_data["lines"]
        for idx, row in lines_gdf.iterrows():
            try:
                if not row.geometry or row.geometry.geom_type != "LineString":
                    continue
                    
                voltage_str = str(row.get("voltage", "115000")).split(";")[0]
                voltage_kv = float(voltage_str) / 1000 if voltage_str.isdigit() else 115.0

                # Find from/to substations using start/end points
                coords = list(row.geometry.coords)
                start_pt = Point(coords[0])
                end_pt = Point(coords[-1])
                
                from_sub = self._find_nearest_substation(start_pt, subs_gdf)
                to_sub = self._find_nearest_substation(end_pt, subs_gdf)

                line = EGATLine(
                    line_id=f"OSM_Line_{idx[1]}" if isinstance(idx, tuple) else f"OSM_Line_{idx}",
                    from_substation=from_sub or "Unknown",
                    to_substation=to_sub or "Unknown",
                    voltage_kv=voltage_kv,
                    length_km=row.geometry.length * 111.32, # Approx degrees to km at equator
                    circuit=int(row.get("circuits", 1)) if str(row.get("circuits")).isdigit() else 1,
                    conductor=row.get("conductor", "ACSR"),
                    line_type="overhead",
                    status="operational"
                )
                lines.append(line)
            except Exception as e:
                logger.warning(f"Failed to map OSM line {idx}: {e}")

        return substations, lines

    def _find_nearest_substation(self, point: Any, subs_gdf: gpd.GeoDataFrame, threshold_deg: float = 0.005) -> Optional[str]:
        """Find nearest substation within threshold (approx 500m)."""
        if subs_gdf.empty: return None
        
        # Calculate distances to all substations
        distances = subs_gdf.geometry.distance(point)
        min_dist = distances.min()
        
        if min_dist <= threshold_deg:
            nearest_idx = distances.idxmin()
            return subs_gdf.loc[nearest_idx, "model_id"]
        
        return None

    def export_to_geojson(self, osm_data: Dict[str, gpd.GeoDataFrame], output_path: str):
        """Export raw OSM data to GeoJSON."""
        combined = pd.concat([osm_data["lines"], osm_data["substations"]])
        combined.to_file(output_path, driver="GeoJSON")
        logger.info(f"Exported OSM data to {output_path}")

if __name__ == "__main__":
    # Test execution
    logging.basicConfig(level=logging.INFO)
    mapper = OSMGridMapper()
    # Bangkok area
    data = mapper.fetch_grid_data(point=(13.7563, 100.5018), dist=20000, voltages=["500000", "230000", "115000"])
    subs, lines = mapper.map_to_egat_models(data)
    print(f"Mapped {len(subs)} substations and {len(lines)} lines from OSM")
