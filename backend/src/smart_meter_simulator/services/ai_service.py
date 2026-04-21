"""
AI Service - Centralized Multi-Model Forecasting Integration

Integrates AIForecastingEngine with the simulation engine and provides
unified interface for dual-target multi-model forecasting.
"""

import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from smart_meter_simulator.ai.forecasting_engine import AIForecastingEngine, ModelType

logger = logging.getLogger(__name__)

class AIServiceError(Exception):
    pass

class ForecastError(AIServiceError):
    pass

class ValidationError(AIServiceError):
    pass

class AIService:
    """
    Service layer for Multi-Model AI forecasting operations.
    Supports ENSEMBLE, TFT, LSTM, and HEURISTIC architectures.
    """
    
    def __init__(self, model_path: Optional[str] = None):
        try:
            self.engine = AIForecastingEngine(model_path)
            logger.info("AI Multi-Model Service initialized")
        except Exception as e:
            logger.error(f"Failed to initialize AI Service: {e}")
            raise AIServiceError(f"Initialization failed: {e}")
    
    def _validate_load(self, load_kw: float) -> None:
        if not 0 <= load_kw <= 100000:
            raise ValidationError(f"Invalid load: {load_kw} kW (must be 0-100000)")
    
    def _validate_timestamp(self, timestamp: Optional[datetime]) -> datetime:
        if timestamp is None:
            return datetime.now()
        if not isinstance(timestamp, datetime):
            raise ValidationError("Timestamp must be datetime object")
        return timestamp
    
    def get_24h_forecast(
        self, 
        start_time: Optional[datetime] = None,
        current_load_kw: float = 15000.0,
        model_type: str = ModelType.ENSEMBLE
    ) -> Dict[str, Any]:
        """Generate 24-hour dual-target forecast using selected AI model."""
        try:
            self._validate_load(current_load_kw)
            start_time = self._validate_timestamp(start_time)
            
            forecasts = self.engine.forecast_next_24_hours(start_time, current_load_kw, model_type=model_type)
            
            if not forecasts:
                raise ForecastError("No forecast data generated")
            
            constraint_hours = sum(1 for f in forecasts if f["constraint_active"])
            total_deficit_kw = sum(abs(f["delta"]) for f in forecasts if f["delta"] < 0)
            avg_load = sum(f["Load_Tao"] for f in forecasts) / len(forecasts)
            
            logger.info(f"Multi-Model Forecast: {model_type} | {constraint_hours}/24 constraint hours")
            
            return {
                "generated_at": datetime.now().isoformat(),
                "forecast_start": start_time.isoformat(),
                "model_type": model_type,
                "model_architecture": forecasts[0]["model_architecture"],
                "deployment_tier": forecasts[0]["deployment_tier"],
                "mape": forecasts[0]["mape"],
                "forecasts": forecasts,
                "summary": {
                    "constraint_hours": constraint_hours,
                    "total_deficit_kw": round(total_deficit_kw, 2),
                    "avg_load_kw": round(avg_load, 2),
                    "peak_load_kw": max(f["Load_Tao"] for f in forecasts)
                }
            }
        except Exception as e:
            logger.error(f"Multi-Model Forecast generation failed: {e}", exc_info=True)
            raise ForecastError(f"Failed to generate forecast: {e}")

    def get_scenario_forecast(
        self,
        start_time: Optional[datetime] = None,
        current_load_kw: float = 15000.0,
        scenario_params: Dict[str, Any] = None,
        model_type: str = ModelType.ENSEMBLE
    ) -> Dict[str, Any]:
        """Comparison between baseline and scenario using specific AI architecture."""
        try:
            self._validate_load(current_load_kw)
            start_time = self._validate_timestamp(start_time)
            
            # Baseline & Scenario
            baseline = self.get_24h_forecast(start_time, current_load_kw, model_type=model_type)
            scenario_forecasts = self.engine.forecast_next_24_hours(
                start_time, current_load_kw, scenario_params, model_type=model_type
            )
            
            scenario_total_deficit_kw = sum(abs(f["delta"]) for f in scenario_forecasts if f["delta"] < 0)
            
            return {
                "generated_at": datetime.now().isoformat(),
                "model_type": model_type,
                "scenario_params": scenario_params,
                "baseline_summary": baseline["summary"],
                "scenario_summary": {
                    "total_deficit_kw": round(scenario_total_deficit_kw, 2),
                    "avg_load_kw": round(sum(f["Load_Tao"] for f in scenario_forecasts) / 24, 2)
                },
                "forecasts": {
                    "baseline": baseline["forecasts"],
                    "scenario": scenario_forecasts
                }
            }
        except Exception as e:
            logger.error(f"Scenario forecast failed: {e}")
            raise ForecastError(f"Failed to generate scenario forecast: {e}")
