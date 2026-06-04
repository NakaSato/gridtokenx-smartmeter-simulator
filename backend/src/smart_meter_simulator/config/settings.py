"""Configuration for the GLM grid model simulator."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from smart_meter_simulator.config.enums import WeatherCondition


PROJECT_ROOT = Path(__file__).parent.parent.parent.parent


class SimulatorConfig(BaseSettings):
    """Environment-backed simulator settings."""

    model_config = SettingsConfigDict(
        env_file=(str(PROJECT_ROOT / ".env"), str(PROJECT_ROOT / ".env.local")),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    simulation_interval: int = Field(default=15, alias="SIMULATION_INTERVAL", gt=0)
    num_meters: int = Field(default=80, alias="NUM_METERS", gt=0)
    output_file: str = Field(default="./data/meter_readings.jsonl", alias="OUTPUT_FILE")
    autostart_simulation: bool = Field(default=True, alias="AUTOSTART_SIMULATION")

    grid_topology: str = Field(
        default="glm:src/smart_meter_simulator/data/grids/grid_bus_network.glm",
        alias="GRID_TOPOLOGY",
        description="Topology source spec. Only glm:path/to/file.glm is supported.",
    )

    telemetry_source: str = Field(
        default="synthetic",
        alias="TELEMETRY_SOURCE",
        description=(
            "Telemetry source spec. 'synthetic' (device models) or "
            "'replay:path/to/readings.csv' to drive meters from real data."
        ),
    )
    meter_registry: str = Field(
        default="",
        alias="METER_REGISTRY",
        description=(
            "Optional path to a meter registry (.csv/.json) pinning real meters to "
            "topology buses. When set, the fleet is built from it instead of randomly."
        ),
    )

    solar_efficiency_min: float = Field(
        default=0.85, alias="SOLAR_PANEL_EFFICIENCY_MIN", ge=0, le=1
    )
    solar_efficiency_max: float = Field(
        default=0.95, alias="SOLAR_PANEL_EFFICIENCY_MAX", ge=0, le=1
    )
    base_generation_min: float = Field(default=2.0, alias="BASE_GENERATION_MIN", ge=0)
    base_generation_max: float = Field(default=7.0, alias="BASE_GENERATION_MAX", ge=0)
    pv_model_enabled: bool = Field(default=True, alias="PV_MODEL_ENABLED")
    pv_surface_tilt_deg: float = Field(default=15.0, alias="PV_SURFACE_TILT_DEG")
    pv_surface_azimuth_deg: float = Field(default=180.0, alias="PV_SURFACE_AZIMUTH_DEG")
    pv_temperature_coefficient: float = Field(
        default=-0.003, alias="PV_TEMPERATURE_COEFFICIENT"
    )
    pv_dc_ac_ratio: float = Field(default=1.10, alias="PV_DC_AC_RATIO", gt=0)
    pv_on_every_bus: bool = Field(default=True, alias="PV_ON_EVERY_BUS")
    bus_pv_capacity_min_kw: float = Field(
        default=10.0, alias="BUS_PV_CAPACITY_MIN_KW", ge=0
    )
    bus_pv_capacity_max_kw: float = Field(
        default=10.0, alias="BUS_PV_CAPACITY_MAX_KW", ge=0
    )

    base_consumption_min: float = Field(default=0.5, alias="BASE_CONSUMPTION_MIN", ge=0)
    base_consumption_max: float = Field(default=3.0, alias="BASE_CONSUMPTION_MAX", ge=0)
    noise_factor_min: float = Field(default=0.05, alias="NOISE_FACTOR_MIN", ge=0, le=1)
    noise_factor_max: float = Field(default=0.15, alias="NOISE_FACTOR_MAX", ge=0, le=1)
    zip_impedance_fraction: float = Field(
        default=0.20, alias="ZIP_IMPEDANCE_FRACTION", ge=0
    )
    zip_current_fraction: float = Field(
        default=0.30, alias="ZIP_CURRENT_FRACTION", ge=0
    )
    zip_power_fraction: float = Field(default=0.50, alias="ZIP_POWER_FRACTION", ge=0)

    line_length_unit: str = Field(default="ft", alias="LINE_LENGTH_UNIT")
    line_resistance_ohm_per_km: float = Field(
        default=0.642, alias="LINE_RESISTANCE_OHM_PER_KM", gt=0
    )
    line_reactance_ohm_per_km: float = Field(
        default=0.083, alias="LINE_REACTANCE_OHM_PER_KM", ge=0
    )
    line_capacity_kw: float = Field(default=500.0, alias="LINE_CAPACITY_KW", gt=0)

    solar_prosumer_ratio: float = Field(
        default=0.25, alias="SOLAR_PROSUMER_RATIO", ge=0, le=1
    )
    grid_consumer_ratio: float = Field(
        default=0.50, alias="GRID_CONSUMER_RATIO", ge=0, le=1
    )
    hybrid_prosumer_ratio: float = Field(
        default=0.15, alias="HYBRID_PROSUMER_RATIO", ge=0, le=1
    )

    weather_sunny_weight: float = Field(
        default=0.4, alias="WEATHER_SUNNY_WEIGHT", ge=0, le=1
    )
    weather_partly_cloudy_weight: float = Field(
        default=0.3, alias="WEATHER_PARTLY_CLOUDY_WEIGHT", ge=0, le=1
    )
    weather_cloudy_weight: float = Field(
        default=0.15, alias="WEATHER_CLOUDY_WEIGHT", ge=0, le=1
    )
    weather_overcast_weight: float = Field(
        default=0.1, alias="WEATHER_OVERCAST_WEIGHT", ge=0, le=1
    )
    weather_rainy_weight: float = Field(
        default=0.05, alias="WEATHER_RAINY_WEIGHT", ge=0, le=1
    )

    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    metrics_port: int = Field(default=9091, alias="METRICS_PORT", gt=0)
    simulation_speed_multiplier: float = Field(
        default=1.0, alias="SIMULATION_SPEED_MULTIPLIER", gt=0
    )
    random_seed: int = Field(default=42, alias="RANDOM_SEED")
    weather_change_frequency: int = Field(
        default=5, alias="WEATHER_CHANGE_FREQUENCY", gt=0
    )
    base_latitude: float = Field(default=13.758252, alias="BASE_LATITUDE")
    base_longitude: float = Field(default=100.687455, alias="BASE_LONGITUDE")
    min_load_kw: float = Field(default=0.1, alias="MIN_LOAD_KW", ge=0)
    max_load_kw: float = Field(default=500.0, alias="MAX_LOAD_KW", gt=0)

    @property
    def weather_weights(self) -> Dict[WeatherCondition, float]:
        return {
            WeatherCondition.SUNNY: self.weather_sunny_weight,
            WeatherCondition.PARTLY_CLOUDY: self.weather_partly_cloudy_weight,
            WeatherCondition.CLOUDY: self.weather_cloudy_weight,
            WeatherCondition.OVERCAST: self.weather_overcast_weight,
            WeatherCondition.RAINY: self.weather_rainy_weight,
        }

    @field_validator("*", mode="before")
    @classmethod
    def expand_env_vars(cls, value: Any) -> Any:
        if isinstance(value, str) and "${" in value:
            import re

            def replace_var(match: re.Match[str]) -> str:
                var_name = match.group(1)
                return os.getenv(var_name, match.group(0))

            return re.sub(r"\${([^}]+)}", replace_var, value)
        return value


_config_instance: SimulatorConfig | None = None


def get_config() -> SimulatorConfig:
    """Return the singleton config instance."""
    global _config_instance
    if _config_instance is None:
        _config_instance = SimulatorConfig()
    return _config_instance


def __getattr__(name: str) -> Any:
    if name.isupper():
        field_name = name.lower()
        config = get_config()
        if hasattr(config, field_name):
            return getattr(config, field_name)
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
