"""
Simulation control API endpoints.
"""

from fastapi import APIRouter
from typing import Dict, Any

from ..services.simulation_service import SimulationService
from ..container import get_container

router = APIRouter()


@router.get("/status")
async def get_simulation_status():
    """Get simulator status."""
    try:
        container = get_container()
        sim_service = container.get(SimulationService)
        return sim_service.get_simulation_status()
    except Exception as e:
        return {"error": str(e)}


@router.post("/start")
async def start_simulation():
    """Start simulation."""
    try:
        container = get_container()
        sim_service = container.get(SimulationService)
        return sim_service.start_simulation()
    except Exception as e:
        return {"success": False, "message": str(e)}


@router.post("/stop")
async def stop_simulation():
    """Stop simulation."""
    try:
        container = get_container()
        sim_service = container.get(SimulationService)
        return sim_service.stop_simulation()
    except Exception as e:
        return {"success": False, "message": str(e)}


@router.post("/pause")
async def pause_simulation():
    """Pause simulation."""
    try:
        container = get_container()
        sim_service = container.get(SimulationService)
        return sim_service.pause_simulation()
    except Exception as e:
        return {"success": False, "message": str(e)}


@router.post("/resume")
async def resume_simulation():
    """Resume simulation."""
    try:
        container = get_container()
        sim_service = container.get(SimulationService)
        return sim_service.resume_simulation()
    except Exception as e:
        return {"success": False, "message": str(e)}


@router.post("/restart")
async def restart_simulation():
    """Restart simulation."""
    try:
        container = get_container()
        sim_service = container.get(SimulationService)
        
        # Stop first (ignore if not running)
        if sim_service.is_running():
            sim_service.stop_simulation()
        
        # Small delay to ensure clean stop
        import asyncio
        await asyncio.sleep(0.5)
        
        # Start again
        start_result = sim_service.start_simulation()
        return {
            "success": start_result.get("success", False),
            "message": "Simulation restarted",
            "status": start_result.get("status", {}),
        }
    except Exception as e:
        return {"success": False, "message": str(e)}


@router.get("/parameters")
async def get_simulation_parameters():
    """Get current simulation parameters."""
    # TODO: Implement parameter management
    return {
        "success": True,
        "parameters": {
            "weather": "Auto",
            "solar_multiplier": 1.0,
            "consumption_multiplier": 1.0,
            "grid_buy_price": 0.28,
            "grid_sell_price": 0.12,
        }
    }


@router.post("/parameters")
async def update_simulation_parameters(request: Dict[str, Any]):
    """Update simulation parameters."""
    # TODO: Implement parameter management
    return {
        "success": True,
        "message": "Simulation parameters updated",
        "parameters": request
    }

