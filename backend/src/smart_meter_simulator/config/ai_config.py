"""
Production-grade AI configuration
"""
from pydantic import BaseModel, Field
from typing import Optional
import os

class AIConfig(BaseModel):
    """AI Service Configuration"""
    
    # Model settings
    model_path: Optional[str] = Field(
        default=None,
        description="Path to trained LightGBM model"
    )
    
    # Forecast settings
    forecast_horizon_hours: int = Field(
        default=24,
        ge=1,
        le=168,
        description="Forecast horizon in hours"
    )
    
    # Validation limits
    min_load_kw: float = Field(default=0.0, ge=0)
    max_load_kw: float = Field(default=100000.0, le=1000000)
    
    # Cache settings
    cache_enabled: bool = Field(default=True)
    cache_ttl_seconds: int = Field(default=300, ge=0)
    cache_max_size: int = Field(default=128, ge=1)
    
    # Performance settings
    max_concurrent_forecasts: int = Field(default=10, ge=1, le=100)
    forecast_timeout_seconds: int = Field(default=30, ge=1)
    
    # Logging
    log_level: str = Field(default="INFO")
    log_forecasts: bool = Field(default=True)
    log_performance: bool = Field(default=True)
    
    # Monitoring
    enable_metrics: bool = Field(default=True)
    metrics_prefix: str = Field(default="ai_forecast")
    
    # BESS requirements
    bess_capacity_buffer: float = Field(default=1.2, ge=1.0, le=2.0)
    bess_power_buffer: float = Field(default=1.1, ge=1.0, le=2.0)
    
    class Config:
        env_prefix = "AI_"

def get_ai_config() -> AIConfig:
    """Get AI configuration from environment"""
    return AIConfig(
        model_path=os.getenv("AI_MODEL_PATH"),
        forecast_horizon_hours=int(os.getenv("AI_FORECAST_HORIZON", "24")),
        cache_enabled=os.getenv("AI_CACHE_ENABLED", "true").lower() == "true",
        cache_ttl_seconds=int(os.getenv("AI_CACHE_TTL", "300")),
        log_level=os.getenv("AI_LOG_LEVEL", "INFO"),
        enable_metrics=os.getenv("AI_ENABLE_METRICS", "true").lower() == "true"
    )
