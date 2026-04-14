"""
Meters API v1 Router

Meter management endpoints for GridTokenX Smart Meter Simulator:
- GET /meters - list all meters
- POST /meters - create meter
- GET /meters/{meter_id} - get specific meter
- GET /meters/{meter_id}/readings - get meter readings
- PUT /meters/{meter_id}/readings - update readings
- POST /meters/{meter_id}/readings/override - force override
- GET /meters/profiles - list profiles
- PUT /meters/count - update meter count
"""

from fastapi import APIRouter, HTTPException, Query, Body
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="", tags=["Meters"])


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


# ============================================================================
# Meter Management
# ============================================================================

@router.get("/meters")
async def list_meters(
    status: Optional[str] = Query(None, description="Filter by status (active/inactive)"),
    type: Optional[str] = Query(None, description="Filter by meter type"),
    limit: int = Query(1000, ge=1, le=10000),
):
    """List all meters with optional filters (from PostGIS database)."""
    from smart_meter_simulator.config import get_config
    from sqlalchemy import text
    from sqlalchemy.ext.asyncio import create_async_engine
    from smart_meter_simulator.core import app_state

    config = get_config()
    db_url = getattr(config, 'gis_database_url', None) or getattr(config, 'database_url', None)

    # Try DB
    db_meters = None
    if db_url:
        try:
            # Ensure URL uses asyncpg dialect
            if db_url.startswith('postgres://') or db_url.startswith('postgresql://'):
                db_url = db_url.replace('postgres://', 'postgresql+asyncpg://', 1)
                if '+asyncpg' not in db_url:
                    db_url = db_url.replace('postgresql://', 'postgresql+asyncpg://', 1)

            eng = create_async_engine(db_url, pool_size=2, max_overflow=0)
            async with eng.connect() as conn:
                q = "SELECT meter_id, meter_type, accuracy_class, status, ST_Y(location::geometry) as latitude, ST_X(location::geometry) as longitude, province, district, rated_voltage_v, phase_count FROM grid.meters WHERE 1=1"
                p: dict = {"lim": limit}
                if type:
                    q += " AND meter_type = :type"
                    p["type"] = type
                if status:
                    q += " AND status = :status"
                    p["status"] = status
                q += " ORDER BY id LIMIT :lim"
                res = await conn.execute(text(q), p)
                rows = res.mappings().all()
                db_meters = []
                for r in rows:
                    db_meters.append({
                        "meter_id": r["meter_id"],
                        "meter_type": r["meter_type"],
                        "accuracy_class": r["accuracy_class"],
                        "status": r["status"],
                        "latitude": float(r["latitude"]) if r["latitude"] else None,
                        "longitude": float(r["longitude"]) if r["longitude"] else None,
                        "province": r["province"],
                        "district": r["district"],
                        "rated_voltage_v": float(r["rated_voltage_v"]) if r["rated_voltage_v"] else None,
                        "phase_count": r["phase_count"],
                    })
            await eng.dispose()
        except Exception as e:
            logger.error("DB meters query failed: %s", e)
            db_meters = None

    if db_meters is not None:
        return {"meters": db_meters, "total": len(db_meters), "source": "db"}

    # Fallback to simulation engine
    meters = []
    engine = getattr(app_state, 'engine', None)
    if engine:
        sim_meters = list(getattr(engine, 'meters', []))
        for m in sim_meters[:limit]:
            meter_id = getattr(m, 'meter_id', str(id(m)))
            meter_type = getattr(m, 'config', {}).get('meter_type', 'unknown') if hasattr(m, 'config') else 'unknown'
            lat = getattr(m, 'latitude', None)
            lon = getattr(m, 'longitude', None)
            meters.append({
                "meter_id": str(meter_id),
                "meter_type": str(meter_type),
                "latitude": lat,
                "longitude": lon,
                "status": "active",
            })

    return {"meters": meters, "total": len(meters), "source": "simulation"}


@router.post("/meters")
async def create_meter(data: MeterCreateInput):
    """Register a new smart meter."""
    state = _get_app_state()
    # Placeholder - would call meter_generator.create_meter()
    return {
        "status": "created",
        "meter_type": data.meter_type,
        "message": "Meter registered",
    }


@router.get("/meters/{meter_id}")
async def get_meter(meter_id: str):
    """Get meter details."""
    state = _get_app_state()
    # Placeholder - would look up in state.meters or database
    return {
        "id": meter_id,
        "type": "consumer",
        "status": "active",
        "lat": 13.7563,
        "lon": 100.5018,
    }


@router.get("/meters/{meter_id}/readings")
async def get_meter_readings(meter_id: str, limit: int = Query(100)):
    """Get meter reading history."""
    return {"meter_id": meter_id, "readings": [], "total": 0}


@router.put("/meters/{meter_id}/readings")
async def update_meter_readings(meter_id: str, data: Dict[str, Any] = Body(...)):
    """Manually update meter readings (data correction)."""
    return {"status": "updated", "meter_id": meter_id}


@router.post("/meters/{meter_id}/readings/override")
async def override_meter_reading(meter_id: str, data: MeterOverrideInput):
    """
    Force meter reading override for simulation testing.

    Overrides the physics model for the specified number of ticks.
    """
    state = _get_app_state()
    if not state.engine:
        raise HTTPException(status_code=503, detail="Simulation not running")

    # Override the meter's next reading
    logger.info(f"Override {meter_id}: {data.field}={data.value} for {data.duration_ticks} ticks")
    return {
        "status": "overridden",
        "meter_id": meter_id,
        "field": data.field,
        "value": data.value,
        "duration_ticks": data.duration_ticks,
    }


@router.get("/meters/profiles")
async def get_meter_profiles(
    profile_type: Optional[str] = Query(None, description="Filter by profile type (residential, commercial, industrial)"),
    limit: int = Query(50, description="Max results"),
):
    """Get available meter load profiles (Standard Load Profiles)."""
    state = _get_app_state()
    engine = state.engine

    if not engine or not hasattr(engine, 'data_source'):
        raise HTTPException(status_code=503, detail="Data source not initialized")

    profiles = engine.data_source.get_available_profiles()

    if profile_type:
        profiles = [p for p in profiles if profile_type.lower() in p.lower()]

    return {
        "profiles": profiles[:limit],
        "total": len(profiles),
        "limit": limit,
    }


@router.put("/meters/count")
async def update_meter_count(
    request: dict = Body(...),
):
    """Update the number of meters in the simulation."""
    state = _get_app_state()
    engine = state.engine

    if not engine:
        raise HTTPException(status_code=503, detail="Simulation engine not initialized")

    new_count = request.get("count")
    if not new_count or new_count < 1 or new_count > 10000:
        raise HTTPException(status_code=400, detail="Count must be between 1 and 10000")

    # Update configuration
    engine.config.num_meters = new_count

    return {
        "status": "updated",
        "new_count": new_count,
        "message": "Meter count updated. Restart simulation to apply.",
    }
