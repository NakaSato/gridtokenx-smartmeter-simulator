"""
AI Service - Centralized Forecasting Integration

Integrates AIForecastingEngine with the simulation engine and provides
unified interface for dual-target forecasting (Load_Tao + Capacity_115kV).
"""

import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from functools import lru_cache
from smart_meter_simulator.ai.forecasting_engine import AIForecastingEngine

logger = logging.getLogger(__name__)

class AIServiceError(Exception):
    """Base exception for AI service errors"""
    pass

class ForecastError(AIServiceError):
    """Forecast generation failed"""
    pass

class ValidationError(AIServiceError):
    """Input validation failed"""
    pass

class AIService:
    """
    Service layer for AI forecasting operations.
    Bridges the centralized AIForecastingEngine with the simulation engine.
    """
    
    def __init__(self, model_path: Optional[str] = None):
        try:
            self.engine = AIForecastingEngine(model_path)
            logger.info("AI Service initialized with centralized forecasting engine")
        except Exception as e:
            logger.error(f"Failed to initialize AI Service: {e}")
            raise AIServiceError(f"Initialization failed: {e}")
    
    def _validate_load(self, load_kw: float) -> None:
        """Validate load input"""
        if not 0 <= load_kw <= 100000:
            raise ValidationError(f"Invalid load: {load_kw} kW (must be 0-100000)")
    
    def _validate_timestamp(self, timestamp: Optional[datetime]) -> datetime:
        """Validate and normalize timestamp"""
        if timestamp is None:
            return datetime.now()
        if not isinstance(timestamp, datetime):
            raise ValidationError("Timestamp must be datetime object")
        return timestamp
    
    @lru_cache(maxsize=128)
    def _get_cached_forecast(self, start_iso: str, load_kw: float) -> tuple:
        """Cache forecast results for 5 minutes"""
        start_time = datetime.fromisoformat(start_iso)
        forecasts = self.engine.forecast_next_24_hours(start_time, load_kw)
        return tuple(tuple(f.items()) for f in forecasts)
    
    def get_24h_forecast(
        self, 
        start_time: Optional[datetime] = None,
        current_load_kw: float = 15000.0
    ) -> Dict[str, Any]:
        """
        Generate 24-hour dual-target forecast.
        
        Returns:
            {
                "forecasts": List of hourly predictions,
                "summary": Aggregated metrics,
                "constraints": Constraint violation analysis
            }
        """
        try:
            self._validate_load(current_load_kw)
            start_time = self._validate_timestamp(start_time)
            
            forecasts = self.engine.forecast_next_24_hours(start_time, current_load_kw)
            
            if not forecasts:
                raise ForecastError("No forecast data generated")
            
            # Calculate summary metrics
            constraint_hours = sum(1 for f in forecasts if f["constraint_active"])
            total_deficit_kw = sum(abs(f["delta"]) for f in forecasts if f["delta"] < 0)
            avg_load = sum(f["Load_Tao"] for f in forecasts) / len(forecasts)
            avg_capacity = sum(f["Capacity_115kV"] for f in forecasts) / len(forecasts)
            
            logger.info(f"Forecast generated: {constraint_hours}/24 constraint hours, "
                       f"avg_load={avg_load:.2f}kW, avg_capacity={avg_capacity:.2f}kW")
            
            return {
                "generated_at": datetime.now().isoformat(),
                "forecast_start": start_time.isoformat(),
                "forecasts": forecasts,
                "summary": {
                    "constraint_hours": constraint_hours,
                    "total_deficit_kw": round(total_deficit_kw, 2),
                    "avg_load_kw": round(avg_load, 2),
                    "avg_capacity_kw": round(avg_capacity, 2),
                    "peak_load_kw": max(f["Load_Tao"] for f in forecasts),
                    "min_capacity_kw": min(f["Capacity_115kV"] for f in forecasts)
                },
                "constraints": [
                    {
                        "hour": f["hour_offset"],
                        "timestamp": f["timestamp"],
                        "deficit_kw": abs(f["delta"]),
                        "required_bess_kw": abs(f["delta"])
                    }
                    for f in forecasts if f["constraint_active"]
                ]
            }
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Forecast generation failed: {e}", exc_info=True)
            raise ForecastError(f"Failed to generate forecast: {e}")
    
    def get_constraint_analysis(
        self,
        start_time: Optional[datetime] = None,
        current_load_kw: float = 15000.0
    ) -> Dict[str, Any]:
        """
        Analyze constraint violations and BESS dispatch requirements.
        """
        try:
            forecast_result = self.get_24h_forecast(start_time, current_load_kw)
            constraints = forecast_result["constraints"]
            
            if not constraints:
                logger.info("No capacity constraints detected")
                return {
                    "status": "NO_CONSTRAINTS",
                    "message": "No capacity constraints detected in 24h horizon",
                    "bess_required": False
                }
            
            # Calculate BESS requirements
            max_deficit = max(c["deficit_kw"] for c in constraints)
            total_energy_deficit = sum(c["deficit_kw"] for c in constraints)
            
            logger.warning(f"Constraints detected: {len(constraints)} hours, "
                          f"max_deficit={max_deficit:.2f}kW, total={total_energy_deficit:.2f}kWh")
            
            return {
                "status": "CONSTRAINTS_DETECTED",
                "constraint_count": len(constraints),
                "bess_required": True,
                "bess_requirements": {
                    "peak_power_kw": round(max_deficit, 2),
                    "total_energy_kwh": round(total_energy_deficit, 2),
                    "recommended_capacity_kwh": round(total_energy_deficit * 1.2, 2),
                    "recommended_power_kw": round(max_deficit * 1.1, 2)
                },
                "critical_hours": [
                    {
                        "hour": c["hour"],
                        "timestamp": c["timestamp"],
                        "deficit_kw": c["deficit_kw"]
                    }
                    for c in sorted(constraints, key=lambda x: x["deficit_kw"], reverse=True)[:5]
                ]
            }
        except ValidationError:
            raise
        except ForecastError:
            raise
        except Exception as e:
            logger.error(f"Constraint analysis failed: {e}", exc_info=True)
            raise AIServiceError(f"Failed to analyze constraints: {e}")
    def get_scenario_forecast(
        self,
        start_time: Optional[datetime] = None,
        current_load_kw: float = 15000.0,
        scenario_params: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Generate a comparison between a baseline forecast and a scenario forecast.
        """
        try:
            self._validate_load(current_load_kw)
            start_time = self._validate_timestamp(start_time)
            
            # 1. Baseline Forecast
            baseline = self.get_24h_forecast(start_time, current_load_kw)
            
            # 2. Scenario Forecast
            scenario_forecasts = self.engine.forecast_next_24_hours(
                start_time, current_load_kw, scenario_params
            )
            
            # 3. Analyze Scenario
            scenario_constraint_hours = sum(1 for f in scenario_forecasts if f["constraint_active"])
            scenario_total_deficit_kw = sum(abs(f["delta"]) for f in scenario_forecasts if f["delta"] < 0)
            
            # 4. Compare
            deficit_increase_kw = scenario_total_deficit_kw - baseline["summary"]["total_deficit_kw"]
            hour_increase = scenario_constraint_hours - baseline["summary"]["constraint_hours"]
            
            # Calculate estimated financial impact (Diesel Cost: 13 THB/kWh)
            baseline_diesel_cost = baseline["summary"]["total_deficit_kw"] * 13.0
            scenario_diesel_cost = scenario_total_deficit_kw * 13.0
            financial_impact_thb = scenario_diesel_cost - baseline_diesel_cost
            
            return {
                "generated_at": datetime.now().isoformat(),
                "scenario_params": scenario_params,
                "baseline_summary": baseline["summary"],
                "scenario_summary": {
                    "constraint_hours": scenario_constraint_hours,
                    "total_deficit_kw": round(scenario_total_deficit_kw, 2),
                    "avg_load_kw": round(sum(f["Load_Tao"] for f in scenario_forecasts) / 24, 2),
                    "peak_load_kw": max(f["Load_Tao"] for f in scenario_forecasts),
                    "thermal_derating_avg_kw": round(sum(f["thermal_derating_kw"] for f in scenario_forecasts) / 24, 2)
                },
                "impact": {
                    "additional_deficit_kw": round(deficit_increase_kw, 2),
                    "additional_constraint_hours": hour_increase,
                    "estimated_financial_impact_thb": round(financial_impact_thb, 2),
                    "risk_level": "HIGH" if hour_increase > 2 or financial_impact_thb > 50000 else "MEDIUM" if hour_increase > 0 else "LOW"
                },
                "forecasts": {
                    "baseline": baseline["forecasts"],
                    "scenario": scenario_forecasts
                }
            }
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Scenario forecast failed: {e}", exc_info=True)
            raise ForecastError(f"Failed to generate scenario forecast: {e}")
