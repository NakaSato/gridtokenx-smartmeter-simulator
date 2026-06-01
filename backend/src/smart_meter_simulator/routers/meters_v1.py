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
from typing import Optional, Dict, Any
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
    status: Optional[str] = Query(
        None, description="Filter by status (active/inactive)"
    ),
    type: Optional[str] = Query(None, description="Filter by meter type"),
    limit: int = Query(1000, ge=1, le=10000),
):
    """List all meters with optional filters (from PostGIS database)."""
    from smart_meter_simulator.config import get_config
    from sqlalchemy import text
    from sqlalchemy.ext.asyncio import create_async_engine
    from smart_meter_simulator.core import app_state

    config = get_config()
    db_url = getattr(config, "gis_database_url", None) or getattr(
        config, "database_url", None
    )

    # Try DB
    db_meters = None
    if db_url:
        try:
            # Ensure URL uses asyncpg dialect
            if db_url.startswith("postgres://") or db_url.startswith("postgresql://"):
                db_url = db_url.replace("postgres://", "postgresql+asyncpg://", 1)
                if "+asyncpg" not in db_url:
                    db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)

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
                    db_meters.append(
                        {
                            "meter_id": r["meter_id"],
                            "meter_type": r["meter_type"],
                            "accuracy_class": r["accuracy_class"],
                            "status": r["status"],
                            "latitude": float(r["latitude"]) if r["latitude"] else None,
                            "longitude": float(r["longitude"])
                            if r["longitude"]
                            else None,
                            "province": r["province"],
                            "district": r["district"],
                            "rated_voltage_v": float(r["rated_voltage_v"])
                            if r["rated_voltage_v"]
                            else None,
                            "phase_count": r["phase_count"],
                        }
                    )
            await eng.dispose()
        except Exception as e:
            logger.error("DB meters query failed: %s", e)
            db_meters = None

    if db_meters is not None:
        return {"meters": db_meters, "total": len(db_meters), "source": "db"}

    # Fallback to simulation engine
    meters = []
    engine = getattr(app_state, "engine", None)
    if engine:
        sim_meters = list(getattr(engine, "meters", []))
        for m in sim_meters[:limit]:
            m_config = getattr(m, "config", {})
            meter_id = getattr(m, "meter_id", str(id(m)))
            meter_type = m_config.get("meter_type", "unknown")
            lat = m_config.get("latitude")
            lon = m_config.get("longitude")
            meters.append(
                {
                    "meter_id": str(meter_id),
                    "meter_type": str(meter_type),
                    "latitude": lat,
                    "longitude": lon,
                    "status": "active",
                }
            )

    return {"meters": meters, "total": len(meters), "source": "simulation"}


@router.post("/meters")
async def create_meter(data: MeterCreateInput):
    """Register a new smart meter."""
    from smart_meter_simulator.meter_generator import MeterGenerator
    from smart_meter_simulator.devices.ami import SmartMeter

    state = _get_app_state()
    engine = getattr(state, "engine", None)
    if not engine:
        raise HTTPException(status_code=503, detail="Simulation engine not initialized")

    # 1. Generate config for the new meter
    # We use a dummy count since we only need the create_meter method
    generator = MeterGenerator(num_meters=1)
    meter_config = generator.create_meter(
        meter_type=data.meter_type,
        lat=data.lat,
        lon=data.lon,
        accuracy_class=data.accuracy_class,
        battery_capacity=data.battery_capacity_kwh,
    )

    # 2. Instantiate SmartMeter
    new_meter = SmartMeter(meter_config)

    # 3. Add to engine
    success = await engine.add_meter(new_meter)

    if not success:
        raise HTTPException(status_code=500, detail="Failed to add meter to simulation")

    return {
        "status": "created",
        "meter_id": new_meter.meter_id,
        "meter_type": new_meter.config.get("meter_type"),
        "message": f"Meter {new_meter.meter_id} registered and added to simulation",
    }


@router.delete("/meters/{meter_id}")
async def remove_meter(meter_id: str):
    """Remove a specific smart meter."""
    state = _get_app_state()
    engine = getattr(state, "engine", None)
    if not engine:
        raise HTTPException(status_code=503, detail="Simulation engine not initialized")

    success = await engine.remove_meter(meter_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Meter {meter_id} not found")

    return {"status": "deleted", "meter_id": meter_id}


@router.delete("/meters")
async def clear_meters():
    """Remove all smart meters from the simulation."""
    state = _get_app_state()
    engine = getattr(state, "engine", None)
    if not engine:
        raise HTTPException(status_code=503, detail="Simulation engine not initialized")

    await engine.clear_meters()
    return {"status": "cleared", "message": "All meters removed from simulation"}


@router.get("/meters/{meter_id}")
async def get_meter(meter_id: str):
    """Get meter details from simulation state."""
    # Fetch from simulation engine
    state = _get_app_state()
    engine = getattr(state, "engine", None)
    if engine:
        for m in engine.meters:
            if getattr(m, "meter_id", None) == meter_id:
                m_config = getattr(m, "config", {})
                return {
                    "meter_id": meter_id,
                    "meter_type": m_config.get("meter_type", "unknown"),
                    "location_name": m_config.get("location_name", "Unknown"),
                    "latitude": m_config.get("latitude"),
                    "longitude": m_config.get("longitude"),
                    "phase": m_config.get("phase"),
                    "status": "active",
                }

    raise HTTPException(status_code=404, detail=f"Meter {meter_id} not found")


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
    logger.info(
        f"Override {meter_id}: {data.field}={data.value} for {data.duration_ticks} ticks"
    )
    return {
        "status": "overridden",
        "meter_id": meter_id,
        "field": data.field,
        "value": data.value,
        "duration_ticks": data.duration_ticks,
    }


@router.get("/meters/profiles")
async def get_meter_profiles(
    profile_type: Optional[str] = Query(
        None, description="Filter by profile type (residential, commercial, industrial)"
    ),
    limit: int = Query(50, description="Max results"),
):
    """Get available meter load profiles (Standard Load Profiles)."""
    state = _get_app_state()
    engine = state.engine

    if not engine or not hasattr(engine, "data_source"):
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
    """Update the number of meters and their distribution in the simulation."""
    from smart_meter_simulator.meter_generator import MeterGenerator
    from smart_meter_simulator.devices.ami import SmartMeter

    state = _get_app_state()
    engine = state.engine

    if not engine:
        raise HTTPException(status_code=503, detail="Simulation engine not initialized")

    new_count = request.get("count", len(engine.meters))
    if new_count < 1 or new_count > 10000:
        raise HTTPException(status_code=400, detail="Count must be between 1 and 10000")

    # Re-generate meters
    try:
        generator = MeterGenerator(new_count)
        
        # Optional ratio updates - update the generator's config directly
        if "solar_ratio" in request:
            generator.config.solar_prosumer_ratio = float(request["solar_ratio"])
        if "consumer_ratio" in request:
            generator.config.grid_consumer_ratio = float(request["consumer_ratio"])
        if "hybrid_ratio" in request:
            generator.config.hybrid_prosumer_ratio = float(request["hybrid_ratio"])
        if "battery_ratio" in request:
            generator.config.battery_storage_ratio = float(request["battery_ratio"])
        if "ev_ratio" in request:
            generator.config.ev_charger_ratio = float(request["ev_ratio"])
        # Power range updates
        if "gen_min" in request:
            generator.config.base_generation_min = float(request["gen_min"])
        if "gen_max" in request:
            generator.config.base_generation_max = float(request["gen_max"])

        # If we have an active grid adapter with a network, use IEEE node generation
        if engine.grid.adapter and engine.grid.net:
            meter_configs = generator.generate_ieee_meters(
                num_nodes=len(engine.grid.net.bus), 
                target_meters=new_count
            )
        else:
            meter_configs = generator.generate_meters()
            
        new_meters = [SmartMeter(config) for config in meter_configs]
        
        # Update engine state
        engine.meters = new_meters
        
        # Re-initialize the grid manager with new meters
        engine.grid.initialize_network(new_meters)
        
        engine.vpp_handler.register_meters(new_meters)
        if engine.market_handler:
            engine.market_handler.register_meters(new_meters)
            
        from smart_meter_simulator.core.metrics import ACTIVE_METERS
        ACTIVE_METERS.set(len(new_meters))

        return {
            "status": "updated",
            "new_count": new_count,
            "message": f"Meter configuration updated. {len(new_meters)} meters re-generated.",
        }
    except Exception as e:
        logger.exception(f"Error updating meters: {e}")
        raise HTTPException(status_code=500, detail=str(e))
