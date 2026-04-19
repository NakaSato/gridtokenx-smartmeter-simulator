"""
Map Service

Centralizes all GIS and map rendering logic (GeoJSON, MVT) for the Grid Infrastructure.
Extracts complex geometry conversion logic out of the API router.
"""

import logging
import math
import numpy as np
from typing import List, Optional, Dict, Any
from fastapi import HTTPException

logger = logging.getLogger(__name__)

def get_app_state():
    """Get the global app state (lazy import to avoid circular dependency)."""
    from smart_meter_simulator.core import app_state
    return app_state

class MapService:
    """
    Handles GeoJSON and MVT rendering for the power grid network.
    """

    @staticmethod
    async def render_grid_geojson(
        layers: List[str],
        region: Optional[str] = None,
        bbox: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Build GeoJSON FeatureCollection for map rendering.
        """
        features = []
        requested_layers = set(layers)

        # Parse bounding box filter
        bounds = MapService._parse_bbox(bbox)

        # 1. EGAT Transmission Layer
        if "egat" in requested_layers or "all" in requested_layers:
            features.extend(MapService._render_egat_layer(region, bounds))

        # 2. Active Pandapower Distribution Layer
        if "grid" in requested_layers or "all" in requested_layers:
            state = get_app_state()
            if state.engine and state.engine.net is not None:
                features.extend(MapService.pandapower_to_geojson(state.engine.net, bounds))

        # 3. Simulator Meters Layer
        if "meters" in requested_layers or "all" in requested_layers:
            features.extend(MapService._render_meters_layer(bounds))

        # 4. Substations Layer
        if "substations" in requested_layers or "all" in requested_layers:
            subs_list = await MapService.get_substations_geojson()
            for sub in subs_list:
                coords = sub["geometry"]["coordinates"]
                if bounds and not (bounds["min_lon"] <= coords[0] <= bounds["max_lon"] and
                                   bounds["min_lat"] <= coords[1] <= bounds["max_lat"]):
                    continue
                features.append(sub)

        return {
            "type": "FeatureCollection",
            "features": features,
            "metadata": {
                "total_features": len(features),
                "layers_requested": layers,
                "region_filter": region,
                "bbox_filter": bbox,
                "generated_at": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
            },
        }

    @staticmethod
    async def render_grid_mvt(
        z: int, x: int, y: int,
        layers: List[str],
        region: Optional[str] = None,
        bbox: Optional[str] = None,
    ):
        """
        Generate Mapbox Vector Tile (MVT).
        """
        try:
            import mapbox_vector_tile
            import mercantile
        except ImportError:
            raise HTTPException(status_code=503, detail="MVT libraries not installed")

        bounds = mercantile.bounds(x, y, z)
        w, s, e, n = bounds.west, bounds.south, bounds.east, bounds.north

        # Get GeoJSON data and filter by tile bounds
        geojson_data = await MapService.render_grid_geojson(layers, region, f"{w},{s},{e},{n}")

        mvt_layers = {}
        for feature in geojson_data.get("features", []):
            layer_name = feature["properties"].get("layer", "unknown")
            if layer_name not in mvt_layers:
                mvt_layers[layer_name] = []
            mvt_layers[layer_name].append(feature)

        if not mvt_layers:
            return None # Router should handle empty response

        # Build MVT layer structure
        layer_list = [{"name": name, "features": feats} for name, feats in mvt_layers.items()]
        return mapbox_vector_tile.encode(layer_list)

    @staticmethod
    def pandapower_to_geojson(net, bounds: Optional[Dict[str, float]] = None) -> List[Dict[str, Any]]:
        """Convert pandapower network to GeoJSON features."""
        features = []
        
        # 1. Buses
        if hasattr(net, "bus") and len(net.bus) > 0:
            geodata = getattr(net, "res_bus_geodata", getattr(net, "bus_geodata", None))
            for idx, row in net.bus.iterrows():
                if geodata is not None and idx in geodata.index:
                    gd_row = geodata.loc[idx]
                    lon, lat = float(gd_row[0]), float(gd_row[1])
                    if bounds and not (bounds["min_lon"] <= lon <= bounds["max_lon"] and
                                       bounds["min_lat"] <= lat <= bounds["max_lat"]):
                        continue
                    features.append({
                        "type": "Feature",
                        "geometry": {"type": "Point", "coordinates": [lon, lat]},
                        "properties": {
                            "layer": "grid_bus",
                            "bus_index": int(idx),
                            "name": str(row.get("name", f"Bus_{idx}")),
                            "voltage_kv": float(row.get("vn_kv", 0)),
                        },
                    })

        # 2. Lines
        if hasattr(net, "line") and len(net.line) > 0 and 'geodata' in locals() and geodata is not None:
             for idx, row in net.line.iterrows():
                from_bus, to_bus = int(row.from_bus), int(row.to_bus)
                if from_bus in geodata.index and to_bus in geodata.index:
                    gd1, gd2 = geodata.loc[from_bus], geodata.loc[to_bus]
                    lon1, lat1 = float(gd1[0]), float(gd1[1])
                    lon2, lat2 = float(gd2[0]), float(gd2[1])
                    
                    if bounds:
                        mid_lon, mid_lat = (lon1 + lon2) / 2, (lat1 + lat2) / 2
                        if not (bounds["min_lon"] <= mid_lon <= bounds["max_lon"] and
                                bounds["min_lat"] <= mid_lat <= bounds["max_lat"]):
                            continue
                            
                    features.append({
                        "type": "Feature",
                        "geometry": {"type": "LineString", "coordinates": [[lon1, lat1], [lon2, lat2]]},
                        "properties": {
                            "layer": "grid_line",
                            "line_index": int(idx),
                            "name": str(row.get("name", f"Line_{idx}")),
                            "length_km": float(row.get("length_km", 0)),
                        },
                    })
        return features

    @staticmethod
    def _render_egat_layer(region: Optional[str], bounds: Optional[Dict[str, float]]) -> List[Dict[str, Any]]:
        features = []
        try:
            from smart_meter_simulator.adapters.egat_transmission import EGATTransmissionBuilder
            builder = EGATTransmissionBuilder()
            subs = builder.get_substations(region=region)
            lines = builder.get_lines(region=region)
            plants = builder.get_power_plants(region=region)

            for sub in subs:
                if bounds and not (bounds["min_lon"] <= sub.longitude <= bounds["max_lon"] and
                                   bounds["min_lat"] <= sub.latitude <= bounds["max_lat"]):
                    continue
                features.append({
                    "type": "Feature",
                    "geometry": {"type": "Point", "coordinates": [sub.longitude, sub.latitude]},
                    "properties": {
                        "layer": "egat_substation",
                        "id": sub.sub_id,
                        "name": sub.name_en,
                        "voltage_kv": sub.voltage_kv,
                        "marker_color": MapService._voltage_color(sub.voltage_kv),
                    },
                })

            for line in lines:
                from_sub, to_sub = builder.substations.get(line.from_substation), builder.substations.get(line.to_substation)
                if not from_sub or not to_sub: continue
                if bounds:
                    mid_lon, mid_lat = (from_sub.longitude + to_sub.longitude) / 2, (from_sub.latitude + to_sub.latitude) / 2
                    if not (bounds["min_lon"] <= mid_lon <= bounds["max_lon"] and bounds["min_lat"] <= mid_lat <= bounds["max_lat"]):
                        continue
                features.append({
                    "type": "Feature",
                    "geometry": {"type": "LineString", "coordinates": [[from_sub.longitude, from_sub.latitude], [to_sub.longitude, to_sub.latitude]]},
                    "properties": {
                        "layer": "egat_line",
                        "id": line.line_id,
                        "voltage_kv": line.voltage_kv,
                        "line_color": MapService._voltage_color(line.voltage_kv),
                    },
                })
        except ImportError: pass
        return features

    @staticmethod
    def _render_meters_layer(bounds: Optional[Dict[str, float]]) -> List[Dict[str, Any]]:
        features = []
        state = get_app_state()
        if state.engine and state.engine.meters:
            for idx, meter in enumerate(state.engine.meters):
                lat = meter.config.get("latitude", 13.70 + (idx * 0.003) % 0.3)
                lon = meter.config.get("longitude", 100.45 + (idx * 0.005) % 0.4)
                if bounds and not (bounds["min_lon"] <= lon <= bounds["max_lon"] and bounds["min_lat"] <= lat <= bounds["max_lat"]):
                    continue
                features.append({
                    "type": "Feature",
                    "geometry": {"type": "Point", "coordinates": [lon, lat]},
                    "properties": {
                        "layer": "meter",
                        "meter_id": meter.meter_id,
                        "marker_color": "#3b82f6",
                    },
                })
        return features

    @staticmethod
    async def get_substations_geojson() -> List[Dict[str, Any]]:
        """Get substations as GeoJSON from existing sources."""
        features = []
        try:
            from smart_meter_simulator.adapters.egat_transmission import EGAT_SUBSTATIONS
            for sub_id, sub in EGAT_SUBSTATIONS.items():
                features.append({
                    "type": "Feature",
                    "geometry": {"type": "Point", "coordinates": [sub["longitude"], sub["latitude"]]},
                    "properties": {
                        "layer": "substation",
                        "id": sub_id,
                        "name": sub["name_en"],
                        "voltage_kv": sub["voltage_kv"],
                        "province": sub["province"],
                    },
                })
        except ImportError: pass
        
        if not features:
            # Fallback static data
            subs = [
                {"id": "TH-SUB-01", "name": "Bang Khen", "lat": 13.87, "lon": 100.60},
                {"id": "TH-SUB-02", "name": "Pathum Wan", "lat": 13.74, "lon": 100.53},
            ]
            for s in subs:
                features.append({
                    "type": "Feature",
                    "geometry": {"type": "Point", "coordinates": [s["lon"], s["lat"]]},
                    "properties": {"layer": "substation", "id": s["id"], "name": s["name"]},
                })
        return features

    @staticmethod
    def _parse_bbox(bbox: Optional[str]) -> Optional[Dict[str, float]]:
        if not bbox: return None
        try:
            parts = [float(p.strip()) for p in bbox.split(",")]
            if len(parts) == 4:
                return {"min_lon": parts[0], "min_lat": parts[1], "max_lon": parts[2], "max_lat": parts[3]}
        except (ValueError, IndexError): pass
        return None

    @staticmethod
    def _voltage_color(voltage_kv: float) -> str:
        if voltage_kv >= 500: return "#dc2626"
        if voltage_kv >= 230: return "#f59e0b"
        if voltage_kv >= 115: return "#3b82f6"
        return "#22c55e"
