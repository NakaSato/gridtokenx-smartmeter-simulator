from fastapi import APIRouter, Query, HTTPException, status
from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List
import joblib
import numpy as np
from pathlib import Path
from datetime import datetime, timezone
from smart_meter_simulator.core.forecaster import EdgeForecastingEngine
from smart_meter_simulator.core.ews import EarlyWarningSystem
from smart_meter_simulator.services.ai_service import AIService, ValidationError, ForecastError, AIServiceError
from smart_meter_simulator.ai.forecasting_engine import ModelType
import pandas as pd
import logging

logger = logging.getLogger(__name__)

forecast_router = APIRouter(prefix="/forecast", tags=["Forecast"])
optimize_router = APIRouter(prefix="/optimize", tags=["Optimize"])
ews_router      = APIRouter(prefix="/ews",      tags=["EWS"])

_ews = EarlyWarningSystem()
MODEL_PATH = Path(__file__).parent.parent.parent.parent / "data" / "pea_lgbm_model.pkl"
_ai_service = AIService(str(MODEL_PATH))

class ScenarioInput(BaseModel):
    temp_delta: float = Field(0.0, ge=-10.0, le=10.0, description="Temperature offset in Celsius")
    tourist_surge_pct: float = Field(0.0, ge=-50.0, le=200.0, description="Percentage surge in tourist population")
    nomad_growth_pct: float = Field(0.0, ge=-50.0, le=500.0, description="Percentage growth in digital nomad population")
    is_full_moon: Optional[bool] = Field(None, description="Force Full Moon Party window (True/False)")
    current_load_kw: float = Field(15000.0, ge=0, le=100000)
    start_time: Optional[str] = Field(None, description="ISO format start time")
    model_type: Optional[str] = Field(ModelType.ENSEMBLE, description="Model Architecture to use")

@forecast_router.post("/scenario")
def post_scenario_forecast(body: ScenarioInput):
    """Perform 'What-If' scenario analysis on a specific AI model."""
    try:
        start = datetime.fromisoformat(body.start_time) if body.start_time else None
        params = {
            "temp_delta": body.temp_delta,
            "tourist_surge_pct": body.tourist_surge_pct,
            "nomad_growth_pct": body.nomad_growth_pct,
            "is_full_moon": body.is_full_moon
        }
        result = _ai_service.get_scenario_forecast(start, body.current_load_kw, params, model_type=body.model_type)
        return result
    except Exception as e:
        logger.error(f"Unexpected error in scenario endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Scenario error: {e}")

@forecast_router.get("/24h")
def get_24h_forecast(
    current_load_kw: float = Query(15000.0, ge=0, le=100000, description="Current load on Koh Tao (kW)"),
    start_time: str = Query(None, description="ISO format start time"),
    model_type: str = Query(ModelType.ENSEMBLE, description="Model Architecture Selection")
):
    """Generate 24-hour dual-target forecast using selected AI Multi-Model architecture."""
    try:
        start = datetime.fromisoformat(start_time) if start_time else None
        result = _ai_service.get_24h_forecast(start, current_load_kw, model_type=model_type)
        return result
    except Exception as e:
        logger.error(f"Forecast generation failed: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to generate forecast: {e}")

@forecast_router.get("/dual-target")
def get_dual_target_legacy(
    current_load_kw: float = Query(15000.0),
    start_time: str = Query(None)
):
    """Legacy endpoint mapping to the new Multi-Model system."""
    return get_24h_forecast(current_load_kw, start_time, model_type=ModelType.ENSEMBLE)

@forecast_router.get("/constraints")
def get_constraints(
    current_load_kw: float = Query(15000.0, description="Current load on Koh Tao (kW)"),
    start_time: str = Query(None, description="ISO format start time")
):
    """Get active grid constraints for the next 24 hours."""
    try:
        start = datetime.fromisoformat(start_time) if start_time else None
        forecast_data = _ai_service.get_24h_forecast(start, current_load_kw)
        constraints = [f for f in forecast_data["forecasts"] if f["constraint_active"]]
        return {
            "status": "warning" if constraints else "normal",
            "constraint_hours": len(constraints),
            "details": constraints
        }
    except Exception as e:
        logger.error(f"Failed to get constraints: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@forecast_router.get("/demographics")
def get_demographics(start_time: str = Query(None, description="ISO format time")):
    """Get demographic and base load estimations."""
    try:
        start = datetime.fromisoformat(start_time) if start_time else datetime.now()
        demo = _ai_service.engine._calculate_demographics(start)
        return {
            "timestamp": start.isoformat(),
            "daily_active_population": demo["DAP"],
            "base_load_kw": demo["Load_base_kw"]
        }
    except Exception as e:
        logger.error(f"Failed to get demographics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@forecast_router.post("/train")
def train_model():
    """Trigger AI model retraining (mock endpoint)."""
    return {
        "status": "training_job_submitted",
        "message": "Model retraining job has been queued in the background.",
        "job_id": "train_job_lgbm_edge_001"
    }

# Optimization Endpoints
@optimize_router.get("/schedule")
def get_schedule(node_id: str = Query("SAMUI-HUB-01"), current_load_mw: float = Query(15.0)):
    # Simple redirect to local OPF decision engine
    from scripts.pea_opf_optimizer import run_opf_milp
    # Generate 24h load array for MILP
    forecast_data = _ai_service.get_24h_forecast(current_load_kw=current_load_mw*1000)
    load_mw_array = np.array([f["Load_Tao"]/1000 for f in forecast_data["forecasts"]])
    
    result = run_opf_milp(load_mw_array)
    return {
        "node_id": node_id,
        "model_architecture": forecast_data["model_architecture"],
        "schedule": result["schedule"],
        "total_savings_thb": result["total_savings_thb"],
        "total_cost_baseline_thb": result["total_cost_baseline_thb"],
        "total_cost_optimized_thb": result["total_cost_optimized_thb"]
    }

@optimize_router.get("/savings")
def get_savings(node_id: str = Query("SAMUI-HUB-01"), current_load_mw: float = Query(15.0)):
    result = get_schedule(node_id, current_load_mw)
    return {
        "node_id": node_id,
        "daily_savings_thb": result["total_savings_thb"],
        "monthly_savings_thb": result["total_savings_thb"] * 30,
        "cost_reduction_pct": round((1 - result["total_cost_optimized_thb"] / result["total_cost_baseline_thb"]) * 100, 1)
    }

# EWS Endpoints
@ews_router.get("/status")
def ews_status():
    return {"incident_active": _ews.incident_active, "alert_count": len(_ews.alert_history),
            "latest_alert": _ews.alert_history[-1] if _ews.alert_history else None}

@ews_router.post("/simulate")
def ews_simulate(line_capacity_mw: float = 70.0, loading_pct: float = 98.0):
    alert = _ews.monitor_line_health("115kV KMB Circuit 3", line_capacity_mw, loading_pct)
    return {"alert": alert, "status": "INCIDENT" if alert else "NORMAL"}

@ews_router.post("/reset")
def ews_reset():
    _ews.reset_incident()
    return {"status": "reset"}
