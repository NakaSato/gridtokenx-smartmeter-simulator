from fastapi import APIRouter

from .meters import router as meters_router
from .grid import router as grid_router
from .control import router as control_router
from .vpp import router as vpp_router
from .market import router as market_router

router = APIRouter()

router.include_router(meters_router)
router.include_router(grid_router)
router.include_router(control_router)
router.include_router(vpp_router)
router.include_router(market_router)
