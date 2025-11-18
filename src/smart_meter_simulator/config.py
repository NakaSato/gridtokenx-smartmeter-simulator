"""
Configuration module for Smart Meter Simulator
Centralizes all configuration and constants
"""

import os
from enum import Enum


class MeterType(Enum):
    """Meter type enumeration"""
    SOLAR_PROSUMER = "Solar_Prosumer"
    GRID_CONSUMER = "Grid_Consumer"
    HYBRID_PROSUMER = "Hybrid_Prosumer"
    BATTERY_STORAGE = "Battery_Storage"


class WeatherCondition(Enum):
    """Weather condition enumeration"""
    SUNNY = "Sunny"
    PARTLY_CLOUDY = "Partly_Cloudy"
    CLOUDY = "Cloudy"
    OVERCAST = "Overcast"
    RAINY = "Rainy"


class GridConnectionStatus(Enum):
    """Grid connection status enumeration"""
    CONNECTED = "Connected"
    DISCONNECTED = "Disconnected"
    MAINTENANCE = "Maintenance"


class SimulatorConfig:
    """Simulator configuration from environment variables"""

    # Kafka Configuration
    KAFKA_SERVERS = os.getenv(
        'KAFKA_BOOTSTRAP_SERVERS',
        'localhost:9092'
    )

    # Database Configuration
    DATABASE_URL = os.getenv(
        'DATABASE_URL',
        'postgresql://p2p_user:p2p_password@localhost:5432/p2p_energy_trading'
    )

    # InfluxDB Configuration
    INFLUXDB_URL = os.getenv('INFLUXDB_URL', 'http://localhost:8086')
    INFLUXDB_TOKEN = os.getenv('INFLUXDB_TOKEN', '')
    INFLUXDB_ORG = os.getenv('INFLUXDB_ORG', 'gridtoken')
    INFLUXDB_BUCKET = os.getenv('INFLUXDB_BUCKET', 'energy_readings')

    # Simulation Configuration
    SIMULATION_INTERVAL = int(os.getenv('SIMULATION_INTERVAL', '30'))
    NUM_METERS = int(os.getenv('NUM_METERS', '20'))
    OUTPUT_FILE = os.getenv('OUTPUT_FILE', './data/meter_readings.jsonl')

    # Solar Configuration
    SOLAR_EFFICIENCY_MIN = float(
        os.getenv('SOLAR_PANEL_EFFICIENCY_MIN', '0.85')
    )
    SOLAR_EFFICIENCY_MAX = float(
        os.getenv('SOLAR_PANEL_EFFICIENCY_MAX', '0.95')
    )
    BASE_GENERATION_MIN = float(os.getenv('BASE_GENERATION_MIN', '3.0'))
    BASE_GENERATION_MAX = float(os.getenv('BASE_GENERATION_MAX', '12.0'))

    # Consumption Configuration
    BASE_CONSUMPTION_MIN = float(os.getenv('BASE_CONSUMPTION_MIN', '1.5'))
    BASE_CONSUMPTION_MAX = float(os.getenv('BASE_CONSUMPTION_MAX', '8.0'))
    NOISE_FACTOR_MIN = float(os.getenv('NOISE_FACTOR_MIN', '0.05'))
    NOISE_FACTOR_MAX = float(os.getenv('NOISE_FACTOR_MAX', '0.15'))

    # Trading Configuration
    MIN_SELL_PRICE = float(os.getenv('MIN_SELL_PRICE', '0.15'))
    MAX_SELL_PRICE = float(os.getenv('MAX_SELL_PRICE', '0.35'))
    MIN_BUY_PRICE = float(os.getenv('MIN_BUY_PRICE', '0.20'))
    MAX_BUY_PRICE = float(os.getenv('MAX_BUY_PRICE', '0.40'))
    GRID_FEED_IN_RATE = float(os.getenv('GRID_FEED_IN_RATE', '0.12'))
    GRID_PURCHASE_RATE = float(os.getenv('GRID_PURCHASE_RATE', '0.28'))

    # Weather Configuration
    WEATHER_WEIGHTS = {
        WeatherCondition.SUNNY: float(
            os.getenv('WEATHER_SUNNY_WEIGHT', '0.4')
        ),
        WeatherCondition.PARTLY_CLOUDY: float(
            os.getenv('WEATHER_PARTLY_CLOUDY_WEIGHT', '0.3')
        ),
        WeatherCondition.CLOUDY: float(
            os.getenv('WEATHER_CLOUDY_WEIGHT', '0.15')
        ),
        WeatherCondition.OVERCAST: float(
            os.getenv('WEATHER_OVERCAST_WEIGHT', '0.1')
        ),
        WeatherCondition.RAINY: float(
            os.getenv('WEATHER_RAINY_WEIGHT', '0.05')
        ),
    }

    # Battery Configuration
    BATTERY_CAPACITY_MIN = float(
        os.getenv('BATTERY_CAPACITY_MIN', '10.0')
    )
    BATTERY_CAPACITY_MAX = float(
        os.getenv('BATTERY_CAPACITY_MAX', '30.0')
    )
    BATTERY_EFFICIENCY_MIN = float(
        os.getenv('BATTERY_EFFICIENCY_MIN', '0.90')
    )
    BATTERY_EFFICIENCY_MAX = float(
        os.getenv('BATTERY_EFFICIENCY_MAX', '0.95')
    )

    # Meter Type Distribution
    SOLAR_PROSUMER_RATIO = float(
        os.getenv('SOLAR_PROSUMER_RATIO', '0.40')
    )
    GRID_CONSUMER_RATIO = float(
        os.getenv('GRID_CONSUMER_RATIO', '0.35')
    )
    HYBRID_PROSUMER_RATIO = float(
        os.getenv('HYBRID_PROSUMER_RATIO', '0.20')
    )
    BATTERY_STORAGE_RATIO = float(
        os.getenv('BATTERY_STORAGE_RATIO', '0.05')
    )

    # REC Configuration
    REC_CERTIFICATION_ENABLED = os.getenv(
        'REC_CERTIFICATION_ENABLED',
        'true'
    ).lower() == 'true'
    CARBON_OFFSET_RATE = float(os.getenv('CARBON_OFFSET_RATE', '0.7'))

    # WebSocket Configuration
    WS_ENABLED = os.getenv('WS_ENABLED', 'true').lower() == 'true'
    WS_HOST = os.getenv('WS_HOST', 'localhost')
    WS_PORT = int(os.getenv('WS_PORT', '8765'))

    # Logging Configuration
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    METRICS_PORT = int(os.getenv('METRICS_PORT', '9091'))
    HEALTH_CHECK_INTERVAL = int(os.getenv('HEALTH_CHECK_INTERVAL', '60'))

    # Development Configuration
    SIMULATION_SPEED_MULTIPLIER = float(
        os.getenv('SIMULATION_SPEED_MULTIPLIER', '1.0')
    )
    RANDOM_SEED = int(os.getenv('RANDOM_SEED', '42'))
    WEATHER_CHANGE_FREQUENCY = int(
        os.getenv('WEATHER_CHANGE_FREQUENCY', '5')
    )
    ENABLE_MARKET_DYNAMICS = os.getenv(
        'ENABLE_MARKET_DYNAMICS',
        'true'
    ).lower() == 'true'
