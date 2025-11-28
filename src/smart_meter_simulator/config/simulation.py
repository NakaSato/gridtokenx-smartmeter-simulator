"""
Simulation configuration settings.
"""

from typing import Dict, Any
from pydantic import Field, BaseModel


class SimulationConfig(BaseModel):
    """Simulation configuration settings."""
    
    # Timing
    interval: int = Field(default=15 * 60, description="Simulation interval in seconds (15 minutes)")
    real_time_interval: int = Field(default=5, description="Real time interval in seconds")
    
    # Weather
    default_weather: str = Field(default="Auto", description="Default weather condition")
    weather_modes: list[str] = Field(
        default=["Auto", "Sunny", "Partly_Cloudy", "Cloudy", "Rainy"],
        description="Available weather modes"
    )
    
    # Multipliers
    solar_multiplier: float = Field(default=1.0, ge=0.0, le=1.0, description="Solar generation multiplier")
    consumption_multiplier: float = Field(default=1.0, ge=0.0, le=2.0, description="Energy consumption multiplier")
    
    # Pricing
    grid_buy_price: float = Field(default=0.28, ge=0.10, le=0.50, description="Grid buy price per kWh")
    grid_sell_price: float = Field(default=0.12, ge=0.05, le=0.35, description="Grid sell price per kWh")
    
    # Emissions
    grid_emission_factor: float = Field(default=0.5, ge=0.0, description="Grid emission factor kgCO2/kWh")
    solar_emission_factor: float = Field(default=0.05, ge=0.0, description="Solar emission factor kgCO2/kWh")
    carbon_offset_rate: float = Field(default=0.1, ge=0.0, description="Carbon offset rate")
    
    def get_weather_factors(self, weather: str) -> tuple[float, float]:
        """Get irradiance and temperature offset for weather condition."""
        factors = {
            "Sunny": (1.0, 0.0),
            "Partly_Cloudy": (0.7, -2.0),
            "Cloudy": (0.3, -5.0),
            "Rainy": (0.1, -8.0),
        }
        return factors.get(weather, (1.0, 0.0))
    
    def get_preset(self, preset_name: str) -> Dict[str, Any]:
        """Get preset configuration."""
        presets = {
            "sunny_day": {
                "weather": "Sunny",
                "solar_multiplier": 1.0,
                "consumption_multiplier": 0.7,
                "grid_buy_price": 0.28,
                "grid_sell_price": 0.12,
            },
            "cloudy_day": {
                "weather": "Cloudy",
                "solar_multiplier": 0.3,
                "consumption_multiplier": 1.0,
                "grid_buy_price": 0.32,
                "grid_sell_price": 0.10,
            },
            "night_time": {
                "weather": "Auto",
                "solar_multiplier": 0.0,
                "consumption_multiplier": 1.2,
                "grid_buy_price": 0.35,
                "grid_sell_price": 0.08,
            },
            "peak_demand": {
                "weather": "Auto",
                "solar_multiplier": 0.6,
                "consumption_multiplier": 1.8,
                "grid_buy_price": 0.45,
                "grid_sell_price": 0.15,
            },
            "battery_test": {
                "weather": "Partly_Cloudy",
                "solar_multiplier": 0.7,
                "consumption_multiplier": 0.5,
                "grid_buy_price": 0.28,
                "grid_sell_price": 0.12,
            },
            "auto": {
                "weather": "Auto",
                "solar_multiplier": 1.0,
                "consumption_multiplier": 1.0,
                "grid_buy_price": 0.28,
                "grid_sell_price": 0.12,
            },
        }
        return presets.get(preset_name, presets["auto"])
