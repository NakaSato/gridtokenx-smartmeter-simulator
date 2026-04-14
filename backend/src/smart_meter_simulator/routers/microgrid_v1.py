"""
Microgrid API v1 Router

Endpoints for microgrid boundary management:
- GET    /api/v1/microgrid/boundary       - GeoJSON boundary polygon
- GET    /api/v1/microgrid/feeders        - Feeder network topology
- GET    /api/v1/microgrid/pcc            - PCC location and status
- POST   /api/v1/microgrid/pcc/mode       - Switch grid-tied/islanded mode
- GET    /api/v1/microgrid/status         - Full electrical status
- GET    /api/v1/microgrid/center         - Geographic center point
"""

from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel
from typing import Optional
import logging

from smart_meter_simulator.core.microgrid_core import MicrogridCore, GridMode

logger = logging.getLogger(__name__)

router = APIRouter(prefix="", tags=["Microgrid"])

# Singleton instance
_microgrid: Optional[MicrogridCore] = None


def _get_microgrid() -> MicrogridCore:
    """Get or create microgrid core instance"""
    global _microgrid
    if _microgrid is None:
        _microgrid = MicrogridCore()
    return _microgrid


def _ensure_populated():
    """Lazy populate from DB on first request"""
    mg = _get_microgrid()
    if mg._meters:
        return  # Already populated
    _populate_from_db()


def _populate_from_db():
    """Populate microgrid from database meters"""
    try:
        from smart_meter_simulator.config import get_config
        from sqlalchemy import text
        from sqlalchemy.ext.asyncio import create_async_engine
        import asyncio

        config = get_config()
        db_url = getattr(config, 'gis_database_url', None) or getattr(config, 'database_url', None)
        if not db_url:
            return

        async def _fetch():
            engine = create_async_engine(db_url)
            try:
                async with engine.connect() as conn:
                    q = """
                        SELECT meter_id, ST_X(location::geometry) as longitude, 
                               ST_Y(location::geometry) as latitude
                        FROM grid.meters WHERE 1=1
                    """
                    result = await conn.execute(text(q))
                    rows = result.mappings().all()
                    meters = [dict(r) for r in rows]
                    _get_microgrid().update_meters(meters)
                    logger.info(f"Loaded {len(meters)} meters into microgrid from DB")
            finally:
                await engine.dispose()

        loop = asyncio.new_event_loop()
        try:
            loop.run_until_complete(_fetch())
        finally:
            loop.close()
    except Exception as e:
        logger.warning(f"Failed to populate microgrid from DB: {e}")


# ── Request Models ───────────────────────────────────────────────────────

class ModeSwitchRequest(BaseModel):
    mode: str  # "grid-tied" or "islanded"


# ── Endpoints ────────────────────────────────────────────────────────────

@router.get("/boundary")
async def get_boundary():
    """Get microgrid geographic boundary as GeoJSON"""
    _ensure_populated()
    return _get_microgrid().boundary_geojson()


@router.get("/feeders")
async def get_feeders():
    """Get feeder network topology as GeoJSON"""
    _ensure_populated()
    return _get_microgrid().compute_feeders()


@router.get("/pcc")
async def get_pcc():
    """Get Point of Common Coupling location and status"""
    _ensure_populated()
    return _get_microgrid().pcc


@router.post("/pcc/mode")
async def set_pcc_mode(req: ModeSwitchRequest):
    """
    Switch PCC operating mode.
    mode: "grid-tied" or "islanded"
    """
    _ensure_populated()
    mode_map = {
        "grid-tied": GridMode.GRID_TIED,
        "islanded": GridMode.ISLANDED,
        "transitioning": GridMode.TRANSITIONING,
    }
    mode = mode_map.get(req.mode.lower())
    if not mode:
        raise HTTPException(status_code=400, detail=f"Invalid mode: {req.mode}. Use: grid-tied, islanded")

    status = _get_microgrid().set_mode(mode)
    return {"status": "ok", "pcc": status}


@router.get("/status")
async def get_status():
    """Get full electrical boundary status"""
    _ensure_populated()
    return _get_microgrid().electrical_status()


@router.get("/center")
async def get_center():
    """Get geographic center of microgrid"""
    _ensure_populated()
    return _get_microgrid().center
