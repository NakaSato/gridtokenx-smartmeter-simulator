import requests
import logging
import time
from typing import Dict, Optional, Tuple
from functools import lru_cache

logger = logging.getLogger(__name__)

class WeatherService:
    """
    Public API Weather Service using Open-Meteo.
    Provides real-time temperature data based on geographic coordinates.
    Includes caching to prevent rate limiting and improve performance.
    """
    
    BASE_URL = "https://api.open-meteo.com/v1/forecast"
    CACHE_EXPIRY = 600  # 10 minutes
    
    def __init__(self):
        self._cache: Dict[Tuple[float, float], Dict] = {}
        self._last_request_time = 0
        self._min_request_interval = 1.0  # 1 second between API calls if not cached

    def get_temperature(self, lat: float, lon: float) -> float:
        """
        Get current temperature for given coordinates.
        Coordinates are rounded to 2 decimal places (~1.1km precision) for better caching.
        """
        # Round coordinates to group nearby meters
        r_lat = round(lat, 2)
        r_lon = round(lon, 2)
        cache_key = (r_lat, r_lon)
        
        now = time.time()
        
        # Check cache
        if cache_key in self._cache:
            entry = self._cache[cache_key]
            if now - entry["timestamp"] < self.CACHE_EXPIRY:
                return entry["temp"]

        # Throttle requests
        if now - self._last_request_time < self._min_request_interval:
            # If throttled and we have a stale cache, return it
            if cache_key in self._cache:
                return self._cache[cache_key]["temp"]
            # Otherwise return a reasonable default
            return 25.0

        try:
            params = {
                "latitude": r_lat,
                "longitude": r_lon,
                "current_weather": "true",
                "timezone": "auto"
            }
            
            response = requests.get(self.BASE_URL, params=params, timeout=5)
            self._last_request_time = time.time()
            
            if response.status_code == 200:
                data = response.json()
                temp = data.get("current_weather", {}).get("temperature")
                if temp is not None:
                    self._cache[cache_key] = {
                        "temp": temp,
                        "timestamp": now
                    }
                    logger.debug(f"Fetched weather for {r_lat}, {r_lon}: {temp}°C")
                    return temp
            
            logger.warning(f"Weather API error: {response.status_code}")
        except Exception as e:
            logger.error(f"Failed to fetch weather: {e}")
            
        # Fallback to last known or default
        if cache_key in self._cache:
            return self._cache[cache_key]["temp"]
        return 25.0

# Singleton instance
_instance: Optional[WeatherService] = None

def get_weather_service() -> WeatherService:
    global _instance
    if _instance is None:
        _instance = WeatherService()
    return _instance
