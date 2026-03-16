import aiohttp
import json
import os
import logging
from typing import List, Optional, Tuple
from geopy.distance import geodesic

logger = logging.getLogger(__name__)

CACHE_FILE = ".matched_routes_cache.json"

class MapboxMatcher:
    """
    Utility to snap coordinates to road networks using Mapbox Map Matching API.
    Includes persistent caching and high-fidelity distance calculation.
    """
    def __init__(self, access_token: Optional[str] = None):
        self.access_token = access_token or os.getenv("VITE_MAPBOX_ACCESS_TOKEN")
        self.cache = self._load_cache()

    def calculate_distance(self, coordinates: List[List[float]]) -> float:
        """Calculates total distance in meters with architectural sag factor (3%)."""
        total_dist = 0.0
        for i in range(len(coordinates) - 1):
            p1 = (coordinates[i][1], coordinates[i][0]) # (lat, lon)
            p2 = (coordinates[i+1][1], coordinates[i+1][0])
            total_dist += geodesic(p1, p2).meters
        return total_dist * 1.03 # 3% sag factor for electrical lines

    def _load_cache(self):
        if os.path.exists(CACHE_FILE):
            try:
                with open(CACHE_FILE, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load Mapbox cache: {e}")
        return {}

    def _save_cache(self):
        try:
            with open(CACHE_FILE, 'w') as f:
                json.dump(self.cache, f)
        except Exception as e:
            logger.warning(f"Failed to save Mapbox cache: {e}")

    async def match_route(self, coordinates: List[List[float]]) -> Tuple[List[List[float]], float]:
        """
        Snap a series of coordinates to the road network.
        coordinates: List of [lng, lat]
        Returns: Tuple of (matched_coords, distance_m)
        """
        # Default distance if no matching occurs
        default_dist = self.calculate_distance(coordinates)

        if not self.access_token:
            return coordinates, default_dist

        # If it's a single point, can't match a route
        if len(coordinates) < 2:
            return coordinates, default_dist

        # Simple cache key based on coordinates
        cache_key = json.dumps(coordinates)
        if cache_key in self.cache:
            entry = self.cache[cache_key]
            # Handle legacy cache without distance
            if isinstance(entry, list):
                dist = self.calculate_distance(entry)
                return entry, dist
            return entry["coords"], entry["distance"]

        # Mapbox Map Matching API expects lon,lat semicolon separated
        # Limited to 100 points per request
        coord_slice = coordinates[:100]
        coord_str = ";".join([f"{c[0]},{c[1]}" for c in coord_slice])
        
        url = f"https://api.mapbox.com/matching/v5/mapbox/driving/{coord_str}"
        params = {
            "access_token": self.access_token,
            "geometries": "geojson",
            "overview": "full",
            "tidy": "true"
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if data.get("code") == "Ok" and data.get("matchings"):
                            matched_coords = data["matchings"][0]["geometry"]["coordinates"]
                            dist = self.calculate_distance(matched_coords)
                            self.cache[cache_key] = {"coords": matched_coords, "distance": dist}
                            self._save_cache()
                            return matched_coords, dist
                        else:
                            logger.warning(f"Mapbox Match NOT OK: {data.get('code')}")
                    else:
                        text = await resp.text()
                        logger.error(f"Mapbox API error: {resp.status} - {text}")
        except Exception as e:
            logger.error(f"Mapbox matching failed: {e}")

        return coordinates, default_dist
