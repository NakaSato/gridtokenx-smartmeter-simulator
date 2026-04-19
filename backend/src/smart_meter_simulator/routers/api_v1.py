"""
Consolidated API v1 Router

Unified REST API for GridTokenX Smart Meter Simulator.
All endpoint logic split into focused sub-routers:

- /api/v1/simulation/      - Control, scenarios, environment
- /api/v1/meters/          - Meter management, readings
- /api/v1/grid/            - Physical infrastructure, topology, telemetry
- /api/v1/billing/         - Billing, TOU tariffs, ERC ladder
- /api/v1/price/           - Price comparison, utility rates, P2P
- /api/v1/vpp/             - Virtual Power Plant
- /api/v1/analytics/       - Analytics summary, solar detection
- /api/v1/registry/        - Thailand power plant registry
- /api/v1/quality/         - Quality & validation
"""

from fastapi import APIRouter, HTTPException, Query, Body, Header
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

# ── Sub-routers ─────────────────────────────────────────────────────────────
from .simulation_v1 import router as simulation_router
from .meters_v1 import router as meters_router
from .grid_v1 import router as grid_router
from .billing_v1 import router as billing_router
from .price_v1 import router as price_router
from .vpp_v1 import router as vpp_router
from .analytics_v1 import router as analytics_router
from .registry_v1 import router as registry_router
from .microgrid_v1 import router as microgrid_router
from .forecast_v1 import forecast_router, optimize_router, ews_router

router = APIRouter(prefix="/api/v1", tags=["API v1"])

# Mount all sub-routers
router.include_router(simulation_router)
router.include_router(meters_router)
router.include_router(grid_router)
router.include_router(billing_router)
router.include_router(price_router)
router.include_router(vpp_router)
router.include_router(analytics_router)
router.include_router(registry_router)
router.include_router(microgrid_router, prefix="/microgrid")
router.include_router(forecast_router)
router.include_router(optimize_router)
router.include_router(ews_router)

# ============================================================================
# Shared State Access (kept for any endpoint that still needs direct access)
# ============================================================================

def _get_app_state():
    """Get the global app state (lazy import to avoid circular dependency)."""
    from smart_meter_simulator.core import app_state
    return app_state


async def _get_postgis_repo():
    """Get PostGIS repository if available."""
    from smart_meter_simulator.database import PostGISRepository
    return PostGISRepository()


def _verify_api_key(x_api_key: Optional[str] = Header(None)):
    """Verify C2C API key if configured."""
    import os
    expected = os.environ.get("C2C_API_KEY")
    if expected and x_api_key != expected:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return True


# ============================================================================
# Pydantic Models (shared across sub-routers where needed)
# ============================================================================

class MeterCreateInput(BaseModel):
    """Create new meter."""
    meter_type: str = "consumer"
    lat: Optional[float] = None
    lon: Optional[float] = None
    accuracy_class: Optional[str] = None
    battery_capacity_kwh: Optional[float] = None


class MeterOverrideInput(BaseModel):
    """Force meter reading override."""
    value: float
    field: str = "consumption"
    duration_ticks: Optional[int] = None


class VPPDispatchInput(BaseModel):
    """VPP dispatch command."""
    cluster_id: Optional[str] = None
    action: str  # curtail, charge, discharge, shed
    setpoint_kw: float


class C2CMeterReading(BaseModel):
    """C2C meter reading for ingestion."""
    meter_id: str
    generation_kwh: float = 0.0
    consumption_kwh: float = 0.0
    battery_kwh: float = 0.0


class C2CIngestInput(BaseModel):
    """Cloud-to-Cloud data ingestion."""
    readings: List[C2CMeterReading]
    market_orders: Optional[List[Dict[str, Any]]] = None


# ============================================================================
# Quality & Validation
# ============================================================================

@router.get("/quality/health")
async def quality_health():
    """Quality service health check."""
    return {
        "status": "ok",
        "version": "v1",
        "analysers": [
            "power_substation",
            "power_line_connectivity",
            "duplicate_detection",
            "meter_conflation",
        ],
    }
