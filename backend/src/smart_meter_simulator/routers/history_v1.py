"""Replay / history endpoints backed by the PostGIS reading store.

These surface persisted runs (``grid.meter_readings``) and the geo asset network
(``grid.export_network_geojson`` / ``grid.get_network_stats``). All return 503 when
``POSTGIS_ENABLED`` is off or the store failed to connect — persistence is optional.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

router = APIRouter(prefix="/history", tags=["History"])


async def get_store():
    from smart_meter_simulator.core import app_state

    engine = app_state.engine
    if engine is None:
        raise HTTPException(status_code=503, detail="Engine not initialized")
    store = getattr(engine, "reading_store", None)
    if store is None:
        raise HTTPException(
            status_code=503,
            detail="PostGIS persistence disabled (set POSTGIS_ENABLED=true)",
        )
    return store


@router.get("/readings")
async def list_readings(
    meter_id: Optional[str] = Query(None, description="Filter to one meter"),
    start: Optional[datetime] = Query(
        None, description="Inclusive lower bound (RFC 3339)"
    ),
    end: Optional[datetime] = Query(
        None, description="Inclusive upper bound (RFC 3339)"
    ),
    limit: int = Query(500, gt=0, le=10000),
    store=Depends(get_store),
):
    """Persisted meter readings, newest first, for replay/analysis."""
    rows = await store.fetch_readings(
        meter_id=meter_id, start=start, end=end, limit=limit
    )
    return {"count": len(rows), "readings": rows}


@router.get("/network/geojson")
async def network_geojson(
    voltage_min: float = Query(0.0, ge=0),
    voltage_max: float = Query(500.0, gt=0),
    store=Depends(get_store),
):
    """Asset network (substations/lines/transformers) as a GeoJSON FeatureCollection."""
    result = await store.network_geojson(voltage_min, voltage_max)
    return (
        result if result is not None else {"type": "FeatureCollection", "features": []}
    )


@router.get("/network/stats")
async def network_stats(store=Depends(get_store)):
    """Aggregate asset network statistics (counts, line-km, meters by type)."""
    return await store.network_stats() or {}
