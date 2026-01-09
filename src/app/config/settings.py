"""
Main application settings using Pydantic for validation.
"""

import os
from typing import Optional, List
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Main application settings."""
    
    # Application
    app_name: str = "Smart Meter Simulator"
    app_version: str = "2.0.0"
    debug: bool = False
    log_level: str = "DEBUG"
    
    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    
    # API Gateway
    api_gateway_url: str = "http://localhost:4000"
    api_key: str = "engineering-department-api-key-2025"
    
    # Simulation
    num_meters: int = 20
    simulation_interval: int = 10 * 60  # 10 minutes
    real_time_interval: int = 2  # 2 seconds
    
    # Database
    sqlite_db_path: str = "smart_meter.db"
    
    # CORS
    cors_origins: List[str] = ["*"]
    cors_allow_credentials: bool = True
    cors_allow_methods: List[str] = ["*"]
    cors_allow_headers: List[str] = ["*"]
    
    # Static files
    static_dir: str = "static"
    templates_dir: str = "templates"
    
    # Weather service
    weather_api_key: Optional[str] = None
    weather_api_url: str = "https://api.openweathermap.org/data/2.5/weather"
    
    # Wheeling Charges (THB/kWh)
    wheeling_intra_zone: float = 0.50      # Same zone
    wheeling_adjacent_zone: float = 1.00   # Adjacent zones (<2 km)
    wheeling_cross_zone: float = 1.50      # Cross zones (2-5 km)
    wheeling_remote_zone: float = 2.00     # Remote zones (>5 km)

    # Technical Losses (percentage 0.0-1.0)
    loss_intra_zone: float = 0.01          # 1%
    loss_adjacent_zone: float = 0.02       # 2%
    loss_cross_zone: float = 0.04          # 4%
    loss_remote_zone: float = 0.06         # 6%
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "allow",
    }


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get the global settings instance."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def reload_settings() -> Settings:
    """Reload settings from environment variables."""
    global _settings
    _settings = Settings()
    return _settings


def load_settings() -> Settings:
    """Load settings from environment variables."""
    return Settings()


def get_database_url(settings: Optional[Settings] = None) -> str:
    """Get database URL from settings or environment."""
    db_settings = settings or get_settings()
    return db_settings.database_url


class SimulatorConfig:
    """Legacy configuration constants for backward compatibility."""
    
    MAX_SELL_PRICE = 3.00  # THB/kWh
    MAX_BUY_PRICE = 4.80   # THB/kWh
    CARBON_OFFSET_RATE = 0.8
    API_GATEWAY_URL = os.getenv("API_GATEWAY_URL", "http://localhost:4000")
