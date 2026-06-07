"""API v1 router for the GLM grid model simulator."""

from fastapi import APIRouter

from smart_meter_simulator.routers.grid_v1 import router as grid_router
from smart_meter_simulator.routers.history_v1 import router as history_router
from smart_meter_simulator.routers.meters_v1 import router as meters_router
from smart_meter_simulator.routers.simulation_v1 import router as simulation_router

router = APIRouter(prefix="/api/v1", tags=["API v1"])
router.include_router(simulation_router)
router.include_router(meters_router)
router.include_router(grid_router)
router.include_router(history_router)


@router.get("/quality/health")
async def quality_health():
    return {
        "status": "ok",
        "model": "glm_grid_simulator",
        "topology_source": "GridLAB-D GLM",
    }
