"""
Map Service (Simplified)
"""

import logging
from typing import List, Optional, Dict, Any
from fastapi import HTTPException

logger = logging.getLogger(__name__)

def get_app_state():
    """Get the global app state (lazy import to avoid circular dependency)."""
    from smart_meter_simulator.core import app_state
    return app_state

class MapService:
    """
    Handles GeoJSON rendering for the power grid network.
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

        # 1. Simulator Meters Layer
        if "meters" in requested_layers or "all" in requested_layers:
            features.extend(MapService._render_meters_layer(bounds))

        # 2. Substations Layer (Static Fallback)
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
    def _render_meters_layer(bounds: Optional[Dict[str, float]]) -> List[Dict[str, Any]]:
        features = []
        state = get_app_state()
        if state.engine and state.engine.meters:
            for idx, meter in enumerate(state.engine.meters):
                lat = float(meter.config.get("latitude", 13.70))
                lon = float(meter.config.get("longitude", 100.45))
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
        """Get substations as GeoJSON (Static Fallback)."""
        features = []
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
