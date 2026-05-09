"""
Analytics API v1 Router - Simplified
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

router = APIRouter(prefix="", tags=["Analytics"])

def _get_app_state():
    from smart_meter_simulator.core import app_state
    return app_state

@router.get("/analytics/summary")
async def analytics_summary():
    """Get analytics dashboard summary."""
    state = _get_app_state()
    engine = state.engine

    grid_health = 100.0
    market_activity = {"trades": 0, "volume_kwh": 0}
    lmp_stats = {"min": 0.28, "max": 0.28, "avg": 0.28}
    carbon_kgco2 = 250.0

    if engine:
        carbon_kgco2 = engine.grid.carbon_intensity
        lmp_stats = {"min": engine.grid.avg_nodal_price, "max": engine.grid.avg_nodal_price, "avg": engine.grid.avg_nodal_price}

    return {
        "grid_health": grid_health,
        "lmp_stats": lmp_stats,
        "market_activity": market_activity,
        "carbon_intensity_kgco2": carbon_kgco2,
        "simulation_running": bool(engine and engine.running),
        "financial_optimization": [],
        "ai_forecast": [],
        "message": "AI forecasting and optimization removed."
    }

@router.get("/analytics/solar-detection/inventory")
async def get_solar_inventory():
    """Simplified solar inventory."""
    return {"total_capacity_kw": 0, "meters_with_solar": 0, "message": "Advanced solar detection disabled."}

@router.post("/analytics/solar-detection/detect")
async def detect_solar_panels():
    """Solar detection disabled."""
    return {"status": "disabled", "message": "AI solar detection removed."}
