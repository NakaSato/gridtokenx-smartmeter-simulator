"""
Grid Infrastructure API v1 Router - Simplified
"""

from fastapi import APIRouter, Query
from typing import Optional
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="", tags=["Grid"])


def _get_app_state():
    from smart_meter_simulator.core import app_state

    return app_state


@router.get("/grid/status")
async def grid_status():
    """Get grid status."""
    state = _get_app_state()
    return {
        "status": "running" if state.engine and state.engine.running else "stopped",
        "meters_online": len(state.engine.meters) if state.engine else 0,
        "grid_frequency_hz": 50.0,
    }


@router.get("/grid/topology")
async def grid_topology(
    version: Optional[str] = Query(None, description="Topology version"),
):
    """Simplified topology summary."""
    state = _get_app_state()
    return {
        "topology": {
            "meters": len(state.engine.meters) if state.engine else 0,
            "mode": "ami_only",
        }
    }


@router.get("/grid/telemetry")
async def grid_telemetry():
    """Simplified telemetry."""
    return {"measurements": [], "timestamp": None}


@router.get("/grid/state-estimation")
async def grid_state_estimation():
    """State estimation removed."""
    return {
        "converged": False,
        "results": {},
        "message": "State estimation disabled (ML/AI removal)",
    }


@router.get("/grid/map")
async def grid_map(format: str = Query("geojson")):
    """Map service simplified."""
    return {"type": "FeatureCollection", "features": []}


@router.get("/grid/substations")
async def list_substations():
    """Substations list (Legacy fallback)."""
    return {
        "substations": [
            {
                "id": "TH-SUB-001",
                "name": "Bangkhen Substation",
                "operator": "MEA",
                "voltage_kv": 22.0,
            },
            {
                "id": "TH-SUB-002",
                "name": "Pathumwan Substation",
                "operator": "MEA",
                "voltage_kv": 22.0,
            },
        ],
        "total": 2,
    }


@router.get("/grid/egat/transmission")
async def egat_transmission_network():
    """EGAT transmission disabled."""
    return {"message": "EGAT transmission module removed (ML/AI removal)"}


@router.get("/grid/stats")
async def grid_statistics():
    """Simplified statistics."""
    state = _get_app_state()
    return {
        "total_meters": len(state.engine.meters) if state.engine else 0,
        "mode": "simplified",
    }


@router.get("/grid/events")
async def grid_events(limit: int = Query(50)):
    """Retrieve historical grid events."""
    state = _get_app_state()
    if not state.engine or not state.engine.db_manager:
        return {"events": []}
    events = await state.engine.db_manager.get_grid_events(limit=limit)
    return {"events": events, "count": len(events)}
