from fastapi import APIRouter, Query, Body
from pydantic import BaseModel
import joblib, numpy as np
from pathlib import Path
from datetime import datetime, timezone
from smart_meter_simulator.core.forecaster import EdgeForecastingEngine
from smart_meter_simulator.core.ews import EarlyWarningSystem
import pandas as pd

forecast_router = APIRouter(prefix="/forecast", tags=["Forecast"])
optimize_router = APIRouter(prefix="/optimize", tags=["Optimize"])
ews_router      = APIRouter(prefix="/ews",      tags=["EWS"])

_ews = EarlyWarningSystem()
MODEL_PATH = Path("backend/data/pea_lgbm_model.pkl")

# ── Pillar 1 ─────────────────────────────────────────────────────────────────

@forecast_router.get("/24h")
def get_24h_forecast(
    node_id: str = Query("SAMUI-HUB-01"),
    current_load_mw: float = Query(15.0),
    temp_c: float = Query(33.0),
    cloud_cover: float = Query(10.0),
):
    forecaster = EdgeForecastingEngine(node_id)
    if MODEL_PATH.exists():
        artifact = joblib.load(MODEL_PATH)
        now = datetime.now()
        rows = [{"hour": (now.hour+i)%24, "dayofweek": now.weekday(),
                 "is_weekend": int(now.weekday()>=5), "month": now.month,
                 **{f"load_tao_mw_lag{l}h": current_load_mw for l in [1,2,3,24,48]},
                 **{f"capacity_115kv_mw_lag{l}h": 40.0 for l in [1,2,3,24,48]},
                 "load_tao_mw_roll24": current_load_mw,
                 "capacity_115kv_mw_roll24": 40.0
                 } for i in range(24)]
        
        # Load forecasts
        df = pd.DataFrame(rows)
        # Handle the case where some features might be missing in synthetic rows
        # For simplicity in this endpoint, we'll try to just pass what we can
        
        forecast_load_tao_mw = artifact["load_tao_mw"]["model"].predict(df[artifact["load_tao_mw"]["features"]])
        forecast_capacity_115kv_mw = artifact["capacity_115kv_mw"]["model"].predict(df[artifact["capacity_115kv_mw"]["features"]])
        
        forecast = forecast_load_tao_mw
        model_name = "lightgbm_dual_target"
        
        delta_mw = forecast_capacity_115kv_mw - forecast_load_tao_mw
        vpp_trigger_hours = [i for i, d in enumerate(delta_mw) if d < 0]
        
    else:
        forecast = forecaster.generate_24h_forecast(current_load_mw, {"temp_c": temp_c, "cloud_cover": cloud_cover})
        model_name = "rule_based"
        forecast_load_tao_mw = forecast
        forecast_capacity_115kv_mw = np.array([40.0] * 24)
        delta_mw = forecast_capacity_115kv_mw - forecast_load_tao_mw
        vpp_trigger_hours = []

    actuals = forecast * (1 + np.random.normal(0, 0.05, 24))
    mape = forecaster.calculate_mape(forecast, actuals)
    
    return {
        "node_id": node_id,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "mape_pct": round(mape, 2),
        "model": model_name,
        "forecast_load_tao_mw": forecast_load_tao_mw.tolist(),
        "forecast_capacity_115kv_mw": forecast_capacity_115kv_mw.tolist(),
        "delta_mw": delta_mw.tolist(),
        "vpp_trigger_hours": vpp_trigger_hours,
        "schedule": forecaster.get_recommended_schedule(forecast, capacity_mw=40.0),
        "estimated_diesel_savings_thb": len(vpp_trigger_hours) * 10 * 9000 # dummy calc
    }

@forecast_router.get("/mape")
def get_mape(node_id: str = Query("SAMUI-HUB-01")):
    forecaster = EdgeForecastingEngine(node_id)
    return {"node_id": node_id, "last_mape_pct": round(forecaster.last_mape, 2), "target_pct": 10.0}

@forecast_router.post("/train")
def train_model():
    import subprocess, sys
    result = subprocess.run([sys.executable, "backend/scripts/pea_lightgbm_trainer.py"], capture_output=True, text=True)
    return {"status": "ok" if result.returncode == 0 else "error", "output": result.stdout, "error": result.stderr}

# ── Pillar 2 ─────────────────────────────────────────────────────────────────

@optimize_router.get("/schedule")
def get_schedule(node_id: str = Query("SAMUI-HUB-01"), current_load_mw: float = Query(15.0)):
    # We must import run_opf_with_physics dynamically because this file is in routers
    # and the script is in scripts. We'll adjust the path import or rely on uv running in the backend root.
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent.parent.parent.parent))
    from scripts.pea_opf_optimizer import run_opf_with_physics
    
    forecast = EdgeForecastingEngine(node_id).generate_24h_forecast(
        current_load_mw, {"temp_c": 33.0, "cloud_cover": 10.0})
    return run_opf_with_physics(forecast)

@optimize_router.get("/savings")
def get_savings(node_id: str = Query("SAMUI-HUB-01"), current_load_mw: float = Query(15.0)):
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent.parent.parent.parent))
    from scripts.pea_opf_optimizer import run_opf_with_physics
    
    forecast = EdgeForecastingEngine(node_id).generate_24h_forecast(
        current_load_mw, {"temp_c": 33.0, "cloud_cover": 10.0})
    r = run_opf_with_physics(forecast)
    return {
        "node_id": node_id,
        "daily_savings_thb": r["total_savings_thb"],
        "monthly_savings_thb": r["total_savings_thb"] * 30,
        "baseline_thb": r["total_cost_baseline_thb"],
        "optimized_thb": r["total_cost_optimized_thb"],
    }

# ── Pillar 3 ─────────────────────────────────────────────────────────────────

class IncidentInput(BaseModel):
    line_id: str = "115kV KMB Circuit 3"
    line_capacity_mw: float = 70.0
    loading_pct: float = 98.0

@ews_router.get("/status")
def ews_status():
    return {
        "incident_active": _ews.incident_active,
        "alert_count": len(_ews.alert_history),
        "latest_alert": _ews.alert_history[-1] if _ews.alert_history else None,
    }

@ews_router.post("/simulate")
def ews_simulate(body: IncidentInput):
    alert = _ews.monitor_line_health(body.line_id, body.line_capacity_mw, body.loading_pct)
    if alert:
        return {
            "alert": alert,
            "emergency_response": {
                "action": "BESS switched to grid-forming mode",
                "bess_dispatch_mw": 20.0,
                "diesel_spinup_mw": max(0.0, body.line_capacity_mw * 0.3 - 20.0),
                "afrr_triggered": True,
            },
        }
    return {"alert": None, "status": "NORMAL"}

@ews_router.post("/reset")
def ews_reset():
    _ews.reset_incident()
    return {"status": "reset"}
