"""
Simulator configuration settings using Pydantic BaseSettings
Provides type-safe configuration with validation

Usage:
    from smart_meter_simulator.config import config  # Recommended
    config.kafka_topic
    
    Or for backward compatibility:
    from smart_meter_simulator.config import SimulatorConfig
    SimulatorConfig.KAFKA_TOPIC  # Works via module-level __getattr__
"""

import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from .enums import WeatherCondition

# Get the project root directory (parent of smart_meter_simulator package)
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
ENV_FILE_PATH = PROJECT_ROOT / ".env"


class SimulatorConfig(BaseSettings):
    """
    Simulator configuration from environment variables.
    Uses Pydantic BaseSettings for type-safe configuration.
    """

    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE_PATH),
        env_file_encoding='utf-8',
        case_sensitive=False,
        extra='ignore'
    )

    # Kafka Configuration
    kafka_servers: str = Field(default="", alias="KAFKA_BOOTSTRAP_SERVERS")
    kafka_topic: str = Field(default="meter-readings", alias="KAFKA_TOPIC")

    # InfluxDB Configuration (Time-Series Database)
    influxdb_url: str = Field(default="http://localhost:7020", alias="INFLUXDB_URL")
    influxdb_token: str = Field(default="admin_token", alias="INFLUXDB_TOKEN")
    influxdb_org: str = Field(default="gridtokenx", alias="INFLUXDB_ORG")
    influxdb_bucket: str = Field(default="meter_readings", alias="INFLUXDB_BUCKET")

    # Database Configuration
    database_url: str = Field(
        default="postgresql://gridtokenx:gridtokenx_password@localhost:5432/gridtokenx",
        alias="DATABASE_URL"
    )
    
    # GIS Database Configuration (PostGIS for spatial data)
    gis_database_url: str = Field(
        default="postgresql+asyncpg://gridtokenx:gridtokenx_password@localhost:5433/gridtokenx_gis",
        alias="GIS_DATABASE_URL"
    )


    # Simulation Configuration
    simulation_interval: int = Field(default=900, alias="SIMULATION_INTERVAL", gt=0)
    num_meters: int = Field(default=20, alias="NUM_METERS", gt=0)
    output_file: str = Field(default="./data/meter_readings.jsonl", alias="OUTPUT_FILE")
    autostart_simulation: bool = Field(default=True, alias="AUTOSTART_SIMULATION")

    # Solar Configuration
    solar_efficiency_min: float = Field(default=0.85, alias="SOLAR_PANEL_EFFICIENCY_MIN", ge=0, le=1)
    solar_efficiency_max: float = Field(default=0.95, alias="SOLAR_PANEL_EFFICIENCY_MAX", ge=0, le=1)
    base_generation_min: float = Field(default=3.0, alias="BASE_GENERATION_MIN", ge=0)
    base_generation_max: float = Field(default=12.0, alias="BASE_GENERATION_MAX", ge=0)

    # Consumption Configuration
    base_consumption_min: float = Field(default=1.5, alias="BASE_CONSUMPTION_MIN", ge=0)
    base_consumption_max: float = Field(default=8.0, alias="BASE_CONSUMPTION_MAX", ge=0)
    noise_factor_min: float = Field(default=0.05, alias="NOISE_FACTOR_MIN", ge=0, le=1)
    noise_factor_max: float = Field(default=0.15, alias="NOISE_FACTOR_MAX", ge=0, le=1)

    # Grid Configuration
    grid_purchase_rate: float = Field(default=0.28, alias="GRID_PURCHASE_RATE", ge=0)

    # Weather Configuration
    weather_sunny_weight: float = Field(default=0.4, alias="WEATHER_SUNNY_WEIGHT", ge=0, le=1)
    weather_partly_cloudy_weight: float = Field(default=0.3, alias="WEATHER_PARTLY_CLOUDY_WEIGHT", ge=0, le=1)
    weather_cloudy_weight: float = Field(default=0.15, alias="WEATHER_CLOUDY_WEIGHT", ge=0, le=1)
    weather_overcast_weight: float = Field(default=0.1, alias="WEATHER_OVERCAST_WEIGHT", ge=0, le=1)
    weather_rainy_weight: float = Field(default=0.05, alias="WEATHER_RAINY_WEIGHT", ge=0, le=1)

    @property
    def weather_weights(self) -> Dict[WeatherCondition, float]:
        """Get weather condition weights as a dictionary"""
        return {
            WeatherCondition.SUNNY: self.weather_sunny_weight,
            WeatherCondition.PARTLY_CLOUDY: self.weather_partly_cloudy_weight,
            WeatherCondition.CLOUDY: self.weather_cloudy_weight,
            WeatherCondition.OVERCAST: self.weather_overcast_weight,
            WeatherCondition.RAINY: self.weather_rainy_weight,
        }

    # Battery Configuration
    battery_capacity_min: float = Field(default=10.0, alias="BATTERY_CAPACITY_MIN", ge=0)
    battery_capacity_max: float = Field(default=30.0, alias="BATTERY_CAPACITY_MAX", ge=0)
    battery_efficiency_min: float = Field(default=0.90, alias="BATTERY_EFFICIENCY_MIN", ge=0, le=1)
    battery_efficiency_max: float = Field(default=0.95, alias="BATTERY_EFFICIENCY_MAX", ge=0, le=1)

    # EV Configuration
    ev_battery_capacity_min: float = Field(default=40.0, alias="EV_BATTERY_CAPACITY_MIN", ge=0)
    ev_battery_capacity_max: float = Field(default=80.0, alias="EV_BATTERY_CAPACITY_MAX", ge=0)
    ev_charge_rate_kw: float = Field(default=7.4, alias="EV_CHARGE_RATE_KW", ge=0)
    ev_v2g_discharge_rate_kw: float = Field(default=5.0, alias="EV_V2G_DISCHARGE_RATE_KW", ge=0)
    ev_v2g_threshold_soc: float = Field(default=0.4, alias="EV_V2G_THRESHOLD_SOC", ge=0, le=1)

    # DC Fast Charger Configuration
    dc_charge_rate_kw: float = Field(default=150.0, alias="DC_CHARGE_RATE_KW", ge=0)
    dc_charge_rate_tiers: List[int] = Field(default=[50, 150, 350], alias="DC_CHARGE_RATE_TIERS")
    dc_connector_count_min: int = Field(default=2, alias="DC_CONNECTOR_COUNT_MIN", ge=1)
    dc_connector_count_max: int = Field(default=8, alias="DC_CONNECTOR_COUNT_MAX", ge=1)
    dc_max_station_capacity_kw: float = Field(default=600.0, alias="DC_MAX_STATION_CAPACITY_KW", ge=0)
    dc_charger_ratio: float = Field(default=0.02, alias="DC_CHARGER_RATIO", ge=0, le=1)

    # Rust Acceleration
    rust_acceleration_enabled: bool = Field(default=True, alias="RUST_ACCELERATION_ENABLED")

    # Meter Type Distribution
    solar_prosumer_ratio: float = Field(default=0.35, alias="SOLAR_PROSUMER_RATIO", ge=0, le=1)
    grid_consumer_ratio: float = Field(default=0.30, alias="GRID_CONSUMER_RATIO", ge=0, le=1)
    hybrid_prosumer_ratio: float = Field(default=0.20, alias="HYBRID_PROSUMER_RATIO", ge=0, le=1)
    battery_storage_ratio: float = Field(default=0.05, alias="BATTERY_STORAGE_RATIO", ge=0, le=1)
    ev_charger_ratio: float = Field(default=0.10, alias="EV_CHARGER_RATIO", ge=0, le=1)


    # WebSocket Configuration
    ws_enabled: bool = Field(default=True, alias="WS_ENABLED")
    ws_host: str = Field(default="localhost", alias="WS_HOST")
    ws_port: int = Field(default=8765, alias="WS_PORT", gt=0)

    # Logging Configuration
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    metrics_port: int = Field(default=9091, alias="METRICS_PORT", gt=0)
    health_check_interval: int = Field(default=60, alias="HEALTH_CHECK_INTERVAL", gt=0)

    # API Gateway Configuration (Oracle Bridge)
    api_gateway_url: str = Field(default="http://localhost:4030", alias="API_GATEWAY_URL")
    submit_reading_endpoint: str = Field(default="/v1/ingest/telemetry")
    submit_batch_endpoint: str = Field(default="/v1/ingest/telemetry/batch")
    register_meter_endpoint: str = Field(default="/v1/query/meters/register")
    api_key: str = Field(default="gridtokenx_secret_key_2025", alias="API_KEY")
    c2c_api_key: str = Field(default="gridtokenx_c2c_live_feed", alias="C2C_API_KEY")

    # Transport Configuration
    transport_type: str = Field(default="grpc", alias="TRANSPORT_TYPE") # "grpc", "http", "kafka", "mqtt"
    grpc_gateway_host: str = Field(default="localhost", alias="GRPC_GATEWAY_HOST")
    grpc_gateway_port: int = Field(default=5030, alias="GRPC_GATEWAY_PORT")

    # MQTT Configuration (Industrial AMI)
    mqtt_broker_url: str = Field(default="localhost", alias="MQTT_BROKER_URL")
    mqtt_port: int = Field(default=1883, alias="MQTT_PORT")
    mqtt_username: Optional[str] = Field(default=None, alias="MQTT_USERNAME")
    mqtt_password: Optional[str] = Field(default=None, alias="MQTT_PASSWORD")
    mqtt_topic: str = Field(default="gridtokenx/ami/telemetry", alias="MQTT_TOPIC")

    # DLMS Configuration
    enable_dlms_binary: bool = Field(default=True, alias="ENABLE_DLMS_BINARY")

    # Development Configuration
    simulation_speed_multiplier: float = Field(default=1.0, alias="SIMULATION_SPEED_MULTIPLIER", gt=0)
    random_seed: int = Field(default=42, alias="RANDOM_SEED")
    weather_change_frequency: int = Field(default=5, alias="WEATHER_CHANGE_FREQUENCY", gt=0)

    # Spatial configuration
    base_latitude: float = Field(default=13.758252, alias="BASE_LATITUDE")
    base_longitude: float = Field(default=100.687455, alias="BASE_LONGITUDE")
    
    # Location Configuration
    locations_file: str = Field(default="initial_locations.json", alias="LOCATIONS_FILE")

    @property
    def initial_locations_file(self) -> str:
        """Get the absolute path to the initial locations JSON file."""
        return str(PROJECT_ROOT / "src" / "smart_meter_simulator" / "config" / self.locations_file)


# Create singleton instance
_config_instance = None

def get_config() -> SimulatorConfig:
    """Get the singleton config instance."""
    global _config_instance
    if _config_instance is None:
        _config_instance = SimulatorConfig()
    return _config_instance


# Module-level __getattr__ for backward compatibility with UPPERCASE constants
def __getattr__(name: str) -> Any:
    """
    Handle module-level attribute access for backward compatibility.
    Allows: from config import SimulatorConfig; SimulatorConfig.KAFKA_TOPIC
    """
    if name.isupper():
        config = get_config()
        field_name = name.lower()
        if hasattr(config, field_name):
            return getattr(config, field_name)
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
