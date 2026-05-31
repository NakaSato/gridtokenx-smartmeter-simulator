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
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import Field, field_validator
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
        env_file=(str(PROJECT_ROOT / ".env"), str(PROJECT_ROOT / ".env.local")),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Kafka Configuration
    kafka_servers: str = Field(default="", alias="KAFKA_BOOTSTRAP_SERVERS")
    kafka_topic: str = Field(default="meter-readings", alias="KAFKA_TOPIC")

    # InfluxDB Configuration (Time-Series Database)
    influxdb_url: str = Field(default="", alias="INFLUXDB_URL")
    influxdb_token: str = Field(default="admin_token", alias="INFLUXDB_TOKEN")
    influxdb_org: str = Field(default="gridtokenx", alias="INFLUXDB_ORG")
    influxdb_bucket: str = Field(default="meter_readings", alias="INFLUXDB_BUCKET")

    # Database Configuration
    database_url: str = Field(
        default="postgresql://gridtokenx:gridtokenx_password@localhost:5432/gridtokenx",
        alias="DATABASE_URL",
    )

    # Redis Configuration
    redis_url: str = Field(default="redis://localhost:6379", alias="REDIS_URL")
    redis_cache_ttl: int = Field(default=300, alias="REDIS_CACHE_TTL")

    simulation_interval: int = Field(default=900, alias="SIMULATION_INTERVAL", gt=0)
    num_meters: int = Field(default=20, alias="NUM_METERS", gt=0)
    output_file: str = Field(default="./data/meter_readings.jsonl", alias="OUTPUT_FILE")
    autostart_simulation: bool = Field(default=True, alias="AUTOSTART_SIMULATION")

    # Solar Configuration
    solar_efficiency_min: float = Field(
        default=0.85, alias="SOLAR_PANEL_EFFICIENCY_MIN", ge=0, le=1
    )
    solar_efficiency_max: float = Field(
        default=0.95, alias="SOLAR_PANEL_EFFICIENCY_MAX", ge=0, le=1
    )
    base_generation_min: float = Field(
        default=2.0, alias="BASE_GENERATION_MIN", ge=0
    )  # Res. scale: 2 kW
    base_generation_max: float = Field(
        default=7.0, alias="BASE_GENERATION_MAX", ge=0
    )  # Res. scale: 7 kW

    # Consumption Configuration
    base_consumption_min: float = Field(
        default=0.5, alias="BASE_CONSUMPTION_MIN", ge=0
    )  # Res. scale: 0.5 kW
    base_consumption_max: float = Field(
        default=3.0, alias="BASE_CONSUMPTION_MAX", ge=0
    )  # Res. scale: 3.0 kW
    noise_factor_min: float = Field(default=0.05, alias="NOISE_FACTOR_MIN", ge=0, le=1)
    noise_factor_max: float = Field(default=0.15, alias="NOISE_FACTOR_MAX", ge=0, le=1)

    # Grid Configuration
    grid_purchase_rate: float = Field(default=0.28, alias="GRID_PURCHASE_RATE", ge=0)

    # Weather Configuration
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
    battery_capacity_min: float = Field(
        default=5.0, alias="BATTERY_CAPACITY_MIN", ge=0
    )  # Res. scale Powerwall: 5 kWh
    battery_capacity_max: float = Field(
        default=13.5, alias="BATTERY_CAPACITY_MAX", ge=0
    )  # Res. scale Powerwall: 13.5 kWh
    battery_efficiency_min: float = Field(
        default=0.90, alias="BATTERY_EFFICIENCY_MIN", ge=0, le=1
    )
    battery_efficiency_max: float = Field(
        default=0.95, alias="BATTERY_EFFICIENCY_MAX", ge=0, le=1
    )

    # EV Configuration
    ev_battery_capacity_min: float = Field(
        default=40.0, alias="EV_BATTERY_CAPACITY_MIN", ge=0
    )
    ev_battery_capacity_max: float = Field(
        default=80.0, alias="EV_BATTERY_CAPACITY_MAX", ge=0
    )
    ev_charge_rate_kw: float = Field(default=7.4, alias="EV_CHARGE_RATE_KW", ge=0)
    ev_v2g_discharge_rate_kw: float = Field(
        default=5.0, alias="EV_V2G_DISCHARGE_RATE_KW", ge=0
    )
    ev_v2g_threshold_soc: float = Field(
        default=0.4, alias="EV_V2G_THRESHOLD_SOC", ge=0, le=1
    )

    # DC Fast Charger Configuration
    dc_charge_rate_kw: float = Field(default=50.0, alias="DC_CHARGE_RATE_KW", ge=0)
    dc_charge_rate_tiers: List[int] = Field(
        default=[22, 50], alias="DC_CHARGE_RATE_TIERS"
    )  # Res./Light commercial DCFC
    dc_connector_count_min: int = Field(default=1, alias="DC_CONNECTOR_COUNT_MIN", ge=1)
    dc_connector_count_max: int = Field(default=2, alias="DC_CONNECTOR_COUNT_MAX", ge=1)
    dc_max_station_capacity_kw: float = Field(
        default=100.0, alias="DC_MAX_STATION_CAPACITY_KW", ge=0
    )
    dc_charger_ratio: float = Field(default=0.01, alias="DC_CHARGER_RATIO", ge=0, le=1)

    # Rust Acceleration
    rust_acceleration_enabled: bool = Field(
        default=True, alias="RUST_ACCELERATION_ENABLED"
    )

    # Meter Type Distribution
    solar_prosumer_ratio: float = Field(
        default=0.25, alias="SOLAR_PROSUMER_RATIO", ge=0, le=1
    )
    grid_consumer_ratio: float = Field(
        default=0.50, alias="GRID_CONSUMER_RATIO", ge=0, le=1
    )
    hybrid_prosumer_ratio: float = Field(
        default=0.15, alias="HYBRID_PROSUMER_RATIO", ge=0, le=1
    )
    battery_storage_ratio: float = Field(
        default=0.04, alias="BATTERY_STORAGE_RATIO", ge=0, le=1
    )
    ev_charger_ratio: float = Field(default=0.05, alias="EV_CHARGER_RATIO", ge=0, le=1)

    @field_validator("*", mode="before")
    @classmethod
    def expand_env_vars(cls, v: Any) -> Any:
        """Expand environment variables in string values."""
        if isinstance(v, str) and "${" in v:
            import re

            def replace_var(match):
                var_name = match.group(1)
                return os.getenv(var_name, match.group(0))

            return re.sub(r"\${([^}]+)}", replace_var, v)
        return v

    # WebSocket Configuration
    ws_enabled: bool = Field(default=True, alias="WS_ENABLED")
    ws_host: str = Field(default="localhost", alias="WS_HOST")
    ws_port: int = Field(default=8765, alias="WS_PORT", gt=0)

    # Logging Configuration
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    metrics_port: int = Field(default=9091, alias="METRICS_PORT", gt=0)
    health_check_interval: int = Field(default=60, alias="HEALTH_CHECK_INTERVAL", gt=0)

    # API Gateway Configuration (Oracle Bridge)
    api_gateway_url: str = Field(
        default="http://localhost:4030", alias="API_GATEWAY_URL"
    )
    submit_reading_endpoint: str = Field(default="/v1/ingest/telemetry")
    submit_batch_endpoint: str = Field(default="/v1/ingest/telemetry/batch")
    register_meter_endpoint: str = Field(default="/v1/query/meters/register")
    api_key: str = Field(default="gridtokenx_secret_key_2025", alias="API_KEY")
    c2c_api_key: str = Field(default="gridtokenx_c2c_live_feed", alias="C2C_API_KEY")

    # Transport Configuration
    transport_type: str = Field(
        default="grpc", alias="TRANSPORT_TYPE"
    )  # "grpc", "http", "kafka", "mqtt"
    grpc_gateway_host: str = Field(default="localhost", alias="GRPC_GATEWAY_HOST")
    grpc_gateway_port: int = Field(
        default=50051, alias="GRPC_GATEWAY_PORT"
    )  # Oracle Bridge gRPC port

    # MQTT Configuration (Industrial AMI)
    mqtt_broker_url: str = Field(default="localhost", alias="MQTT_BROKER_URL")
    mqtt_port: int = Field(default=1883, alias="MQTT_PORT")
    mqtt_username: Optional[str] = Field(default=None, alias="MQTT_USERNAME")
    mqtt_password: Optional[str] = Field(default=None, alias="MQTT_PASSWORD")
    mqtt_topic: str = Field(default="gridtokenx/ami/telemetry", alias="MQTT_TOPIC")

    # DLMS Configuration
    enable_dlms_binary: bool = Field(default=True, alias="ENABLE_DLMS_BINARY")

    # HELICS Co-Simulation Configuration
    helics_enabled: bool = Field(default=False, alias="HELICS_ENABLED")
    helics_federate_name: str = Field(default="SmartMeterSimulator", alias="HELICS_FEDERATE_NAME")
    helics_broker_address: str = Field(default="localhost", alias="HELICS_BROKER_ADDRESS")
    helics_broker_port: int = Field(default=23404, alias="HELICS_BROKER_PORT")
    helics_core_type: str = Field(default="zmq", alias="HELICS_CORE_TYPE")
    helics_time_period: float = Field(default=900.0, alias="HELICS_TIME_PERIOD")
    helics_data_flow: str = Field(default="individual", alias="HELICS_DATA_FLOW") # "individual" or "aggregate"
    helics_subscription_mappings: Dict[str, str] = Field(default_factory=dict, alias="HELICS_SUBSCRIPTION_MAPPINGS")

    # GridLAB-D / GLM Configuration
    glm_data_dir: str = Field(default="", alias="GLM_DATA_DIR")  # Path to GLM model files
    gridlabd_enabled: bool = Field(default=False, alias="GRIDLBD_ENABLED")
    gridlabd_mode: str = Field(default="standalone", alias="GRIDLBD_MODE")  # "standalone" | "co_sim" | "hybrid"
    gridlabd_glm_file: str = Field(default="", alias="GRIDLBD_GLM_FILE")
    gridlabd_executable: str = Field(default="gridlabd", alias="GRIDLBD_EXECUTABLE")

    # Transactive Market Configuration
    market_enabled: bool = Field(default=False, alias="MARKET_ENABLED")
    market_type: str = Field(default="double_auction", alias="MARKET_TYPE")  # "double_auction" | "tou_only" | "p2p"
    market_clearing_interval: int = Field(default=900, alias="MARKET_CLEARING_INTERVAL")
    market_price_cap: float = Field(default=8.0, alias="MARKET_PRICE_CAP")  # Baht/kWh
    market_price_floor: float = Field(default=0.0, alias="MARKET_PRICE_FLOOR")  # Baht/kWh
    tou_on_peak_rate: float = Field(default=5.79, alias="TOU_ON_PEAK_RATE")  # Baht/kWh
    tou_off_peak_rate: float = Field(default=2.65, alias="TOU_OFF_PEAK_RATE")  # Baht/kWh
    tou_on_peak_start: int = Field(default=9, alias="TOU_ON_PEAK_START")  # Hour (0-23)
    tou_on_peak_end: int = Field(default=22, alias="TOU_ON_PEAK_END")  # Hour (0-23)
    ft_adjustment: float = Field(default=0.94, alias="FT_ADJUSTMENT")  # Baht/kWh fuel tariff

    # Development Configuration
    simulation_speed_multiplier: float = Field(
        default=1.0, alias="SIMULATION_SPEED_MULTIPLIER", gt=0
    )
    random_seed: int = Field(default=42, alias="RANDOM_SEED")
    weather_change_frequency: int = Field(
        default=5, alias="WEATHER_CHANGE_FREQUENCY", gt=0
    )

    # Spatial configuration
    base_latitude: float = Field(default=13.758252, alias="BASE_LATITUDE")
    base_longitude: float = Field(default=100.687455, alias="BASE_LONGITUDE")

    # Load constraints
    min_load_kw: float = Field(default=0.1, alias="MIN_LOAD_KW", ge=0)
    max_load_kw: float = Field(default=500.0, alias="MAX_LOAD_KW", gt=0)


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
