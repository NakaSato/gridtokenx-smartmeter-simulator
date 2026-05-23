"""
Analytics API v1 Router - Simplified
"""

from fastapi import APIRouter
import logging

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
        lmp_stats = {
            "min": engine.grid.avg_nodal_price,
            "max": engine.grid.avg_nodal_price,
            "avg": engine.grid.avg_nodal_price,
        }

    return {
        "grid_health": grid_health,
        "lmp_stats": lmp_stats,
        "market_activity": market_activity,
        "carbon_intensity_kgco2": carbon_kgco2,
        "simulation_running": bool(engine and engine.running),
    }
