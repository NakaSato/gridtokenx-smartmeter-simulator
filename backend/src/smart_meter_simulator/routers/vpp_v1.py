"""
VPP v1 Router

Virtual Power Plant API endpoints:
- /api/v1/vpp/clusters       - Get VPP cluster status
- /api/v1/vpp/actions/dispatch - VPP dispatch command
"""

from fastapi import APIRouter, Body, Query
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="", tags=["VPP"])


# ============================================================================
# Shared State Access
# ============================================================================

def _get_app_state():
    """Get the global app state (lazy import to avoid circular dependency)."""
    from smart_meter_simulator.core import app_state
    return app_state


# ============================================================================
# Request/Response Models
# ============================================================================

class VPPDispatchInput(BaseModel):
    """VPP dispatch command."""
    cluster_id: Optional[str] = None
    action: str  # curtail, charge, discharge, shed
    setpoint_kw: float


# ============================================================================
# VPP
# ============================================================================

@router.get("/vpp/clusters")
async def vpp_clusters():
    """Get VPP cluster status."""
    state = _get_app_state()
    engine = state.engine

    if engine and engine.vpp and engine.vpp.clusters:
        statuses = engine.vpp.get_all_cluster_statuses()
        cluster_list = []
        for cid, info in statuses.items():
            if isinstance(info, dict) and info.get("status") != "Not Found":
                cluster_list.append({
                    "cluster_id": cid,
                    "num_resources": info.get("num_resources", 0),
                    "total_capacity_kwh": info.get("total_capacity_kwh", 0),
                    "current_soc_percent": round(info.get("current_soc_percent", 0), 2),
                    "flexibility_up_kw": round(info.get("flexibility_up_kw", 0), 2),
                    "flexibility_down_kw": round(info.get("flexibility_down_kw", 0), 2),
                    "total_cons_kw": round(info.get("total_cons_kw", 0), 2),
                    "total_gen_kw": round(info.get("total_gen_kw", 0), 2),
                    "health_score": round(info.get("health_score", 0), 2),
                    "carbon_saved_g": round(info.get("carbon_saved_g", 0), 2),
                })
        return {"clusters": cluster_list, "total": len(cluster_list)}

    return {"clusters": [], "total": 0}


@router.post("/vpp/actions/dispatch")
async def vpp_dispatch(
    cluster_id: Optional[str] = Query(None),
    action: str = Body(..., embed=True),
    setpoint_kw: float = Body(..., embed=True),
):
    """
    Dispatch command to VPP clusters.

    Actions: curtail, charge, discharge, shed
    """
    return {
        "status": "dispatched",
        "cluster_id": cluster_id,
        "action": action,
        "setpoint_kw": setpoint_kw,
    }
