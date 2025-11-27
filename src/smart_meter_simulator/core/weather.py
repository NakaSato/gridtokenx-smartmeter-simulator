import random
from typing import Dict, Tuple


class WeatherSystem:
    """
    Simulates a dynamic weather system with realistic transitions.
    """

    STATES = ["Sunny", "Partly Cloudy", "Cloudy", "Rainy", "Stormy"]

    # Transition probabilities [Current][Next]
    TRANSITIONS = {
        "Sunny": {
            "Sunny": 0.7,
            "Partly Cloudy": 0.2,
            "Cloudy": 0.1,
            "Rainy": 0.0,
            "Stormy": 0.0,
        },
        "Partly Cloudy": {
            "Sunny": 0.3,
            "Partly Cloudy": 0.4,
            "Cloudy": 0.2,
            "Rainy": 0.1,
            "Stormy": 0.0,
        },
        "Cloudy": {
            "Sunny": 0.1,
            "Partly Cloudy": 0.3,
            "Cloudy": 0.4,
            "Rainy": 0.2,
            "Stormy": 0.0,
        },
        "Rainy": {
            "Sunny": 0.0,
            "Partly Cloudy": 0.1,
            "Cloudy": 0.3,
            "Rainy": 0.5,
            "Stormy": 0.1,
        },
        "Stormy": {
            "Sunny": 0.0,
            "Partly Cloudy": 0.0,
            "Cloudy": 0.2,
            "Rainy": 0.4,
            "Stormy": 0.4,
        },
    }

    # Solar irradiance factor (0.0 to 1.0)
    IRRADIANCE = {
        "Sunny": 1.0,
        "Partly Cloudy": 0.7,
        "Cloudy": 0.4,
        "Rainy": 0.1,
        "Stormy": 0.05,
    }

    # Temperature offset (degrees Celsius relative to base)
    TEMP_OFFSET = {
        "Sunny": 2.0,
        "Partly Cloudy": 0.0,
        "Cloudy": -2.0,
        "Rainy": -4.0,
        "Stormy": -5.0,
    }

    def __init__(self, initial_state="Sunny"):
        self.current_state = initial_state
        # Lazy import to avoid circular dependencies if any
        from .weather_service import WeatherService

        self.service = WeatherService()

    def update(self) -> str:
        """Update global simulated weather state."""
        probs = self.TRANSITIONS[self.current_state]
        states = list(probs.keys())
        weights = list(probs.values())

        self.current_state = random.choices(states, weights=weights, k=1)[0]
        return self.current_state

    def get_factors(self, state: str = None) -> Tuple[float, float]:
        """Return (irradiance_factor, temp_offset) for a given state."""
        target_state = state or self.current_state
        return (
            self.IRRADIANCE.get(target_state, 1.0),
            self.TEMP_OFFSET.get(target_state, 0.0),
        )

    async def get_real_weather(
        self, lat: float, lon: float
    ) -> Tuple[str, float, float]:
        """
        Get real weather for coordinates.
        Returns: (condition, irradiance_factor, temperature_celsius)
        """
        condition, temp = await self.service.get_weather(lat, lon)

        # Get factors based on condition
        irradiance, _ = self.get_factors(condition)

        # For real weather, we return the actual temperature, not an offset
        # But SmartMeter expects an offset from 20C base.
        # SmartMeter logic: temperature = 20.0 + temp_offset + random
        # So temp_offset = temp - 20.0
        temp_offset = temp - 20.0

        return condition, irradiance, temp_offset
