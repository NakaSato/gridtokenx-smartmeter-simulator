import httpx
import logging
import time
from typing import Dict, Tuple, Optional

logger = logging.getLogger(__name__)


class WeatherService:
    """
    Service to fetch real-time weather data from Open-Meteo API.
    Includes caching to respect API limits and connection pooling for performance.
    """

    BASE_URL = "https://api.open-meteo.com/v1/forecast"
    CACHE_DURATION = 900  # 15 minutes in seconds

    def __init__(self):
        self._cache: Dict[str, Dict] = {}  # key: "lat,lon", value: {timestamp, data}
        self._client: Optional[httpx.AsyncClient] = None
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create persistent HTTP client with connection pooling."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=10.0,
                limits=httpx.Limits(max_connections=10, max_keepalive_connections=5),
            )
        return self._client
    
    async def close(self):
        """Close the HTTP client (call on shutdown)."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    async def get_weather(self, lat: float, lon: float) -> Tuple[str, float]:
        """
        Get current weather condition and temperature for a location.
        Returns: (condition_string, temperature_celsius)
        """
        cache_key = f"{lat:.4f},{lon:.4f}"
        now = time.time()

        # Check cache
        if cache_key in self._cache:
            entry = self._cache[cache_key]
            if now - entry["timestamp"] < self.CACHE_DURATION:
                return entry["data"]

        try:
            client = await self._get_client()
            response = await client.get(
                self.BASE_URL,
                params={
                    "latitude": lat,
                    "longitude": lon,
                    "current": "temperature_2m,weather_code",
                },
            )
            response.raise_for_status()
            data = response.json()

            current = data.get("current", {})
            code = current.get("weather_code", 0)
            temp = current.get("temperature_2m", 25.0)

            condition = self._map_wmo_code(code)

            result = (condition, temp)

            # Update cache
            self._cache[cache_key] = {"timestamp": now, "data": result}

            return result

        except Exception as e:
            logger.error(f"Error fetching weather for {lat},{lon}: {e}")
            # Fallback to default if API fails
            return ("Sunny", 25.0)

    def _map_wmo_code(self, code: int) -> str:
        """Map WMO weather code to our internal weather states."""
        # 0: Clear sky
        if code == 0:
            return "Sunny"

        # 1, 2, 3: Mainly clear, partly cloudy, and overcast
        if code == 1:
            return "Sunny"
        if code == 2:
            return "Partly Cloudy"
        if code == 3:
            return "Cloudy"

        # 45, 48: Fog
        if code in [45, 48]:
            return "Cloudy"

        # 51-55: Drizzle
        # 61-65: Rain
        # 80-82: Rain showers
        if 50 <= code <= 69 or 80 <= code <= 82:
            return "Rainy"

        # 71-77: Snow
        # 85-86: Snow showers
        if 70 <= code <= 79 or 85 <= code <= 86:
            return "Rainy"  # Map snow to rainy for now as we don't have Snow state

        # 95, 96, 99: Thunderstorm
        if code in [95, 96, 99]:
            return "Stormy"

        return "Sunny"  # Default
