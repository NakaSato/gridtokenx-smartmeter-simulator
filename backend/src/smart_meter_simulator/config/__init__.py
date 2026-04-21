"""
Configuration module for Smart Meter Simulator

This module provides type-safe configuration using Pydantic BaseSettings.
The configuration is split into separate modules to avoid circular imports:

- enums: MeterType, AccuracyClass, WeatherCondition, GridConnectionStatus
- channels: METER_TYPE_CHANNELS mapping
- settings: SimulatorConfig with environment variable loading

For backward compatibility, UPPERCASE constants can be accessed directly:
    from smart_meter_simulator.config import SOLAR_PROSUMER_RATIO
    from smart_meter_simulator.config import SimulatorConfig  # The class
"""

from .enums import (
    MeterType,
    AccuracyClass,
    WeatherCondition,
    GridConnectionStatus,
    SimulationMode,
)

from .channels import METER_TYPE_CHANNELS

from .settings import SimulatorConfig, get_config

# Re-export module-level __getattr__ for UPPERCASE constant access
import sys
_settings_module = sys.modules['smart_meter_simulator.config.settings']

def __getattr__(name: str):
    """Handle module-level attribute access for backward compatibility."""
    return getattr(_settings_module, name)

def __dir__():
    """Include settings module attributes for IDE autocomplete."""
    return list(globals().keys()) + [
        'SOLAR_PROSUMER_RATIO', 'GRID_CONSUMER_RATIO', 'HYBRID_PROSUMER_RATIO',
        'BATTERY_STORAGE_RATIO', 'EV_CHARGER_RATIO', 'KAFKA_SERVERS', 'KAFKA_TOPIC',
        'DATABASE_URL', 'INFLUXDB_URL', 'INFLUXDB_TOKEN', 'INFLUXDB_ORG', 'INFLUXDB_BUCKET',
        'SIMULATION_INTERVAL', 'NUM_METERS', 'OUTPUT_FILE', 'AUTOSTART_SIMULATION',
        'API_GATEWAY_URL', 'API_KEY', 'C2C_API_KEY', 'WS_ENABLED', 'WS_HOST', 'WS_PORT',
        'LOG_LEVEL', 'METRICS_PORT', 'HEALTH_CHECK_INTERVAL',
        'SOLAR_EFFICIENCY_MIN', 'SOLAR_EFFICIENCY_MAX',
        'BASE_GENERATION_MIN', 'BASE_GENERATION_MAX',
        'BASE_CONSUMPTION_MIN', 'BASE_CONSUMPTION_MAX',
        'NOISE_FACTOR_MIN', 'NOISE_FACTOR_MAX',
        'MIN_SELL_PRICE', 'MAX_SELL_PRICE', 'MIN_BUY_PRICE', 'MAX_BUY_PRICE',
        'GRID_FEED_IN_RATE', 'GRID_PURCHASE_RATE',
        'BATTERY_CAPACITY_MIN', 'BATTERY_CAPACITY_MAX',
        'BATTERY_EFFICIENCY_MIN', 'BATTERY_EFFICIENCY_MAX',
        'REC_CERTIFICATION_ENABLED', 'CARBON_OFFSET_RATE',
        'SIMULATION_SPEED_MULTIPLIER', 'RANDOM_SEED', 'WEATHER_CHANGE_FREQUENCY',
        'ENABLE_MARKET_DYNAMICS', 'INITIAL_LOCATIONS_FILE',
        'WEATHER_SUNNY_WEIGHT', 'WEATHER_PARTLY_CLOUDY_WEIGHT', 'WEATHER_CLOUDY_WEIGHT',
        'WEATHER_OVERCAST_WEIGHT', 'WEATHER_RAINY_WEIGHT',
        'EV_BATTERY_CAPACITY_MIN', 'EV_BATTERY_CAPACITY_MAX',
        'EV_CHARGE_RATE_KW', 'EV_V2G_DISCHARGE_RATE_KW', 'EV_V2G_THRESHOLD_SOC',
        'SUBMIT_READING_ENDPOINT', 'SUBMIT_BATCH_ENDPOINT', 'REGISTER_METER_ENDPOINT',
        'AUCTION_BID_ENDPOINT', 'DEFAULT_AUCTION_BATCH',
    ]

__all__ = [
    "MeterType",
    "AccuracyClass",
    "WeatherCondition",
    "GridConnectionStatus",
    "METER_TYPE_CHANNELS",
    "SimulatorConfig",
    "get_config",
]
