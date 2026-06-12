"""Replay / history endpoints.

Two backings:
- **PostGIS** (``/readings``, ``/network/*``) — persisted runs + geo asset network.
- **InfluxDB** (``/runs``, ``/run/*``) — deterministic-run time-series for plotting.

Each returns 503 when its store is disabled (``POSTGIS_ENABLED`` / ``INFLUX_ENABLED``)
or failed to connect — persistence is optional.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

router = APIRouter(prefix="/history", tags=["History"])


async def _get_engine():
    from smart_meter_simulator.core import app_state

    engine = app_state.engine
    if engine is None:
        raise HTTPException(status_code=503, detail="Engine not initialized")
    return engine


async def get_store():
    engine = await _get_engine()
    store = getattr(engine, "reading_store", None)
    if store is None:
        raise HTTPException(
            status_code=503,
            detail="PostGIS persistence disabled (set POSTGIS_ENABLED=true)",
        )
    return store


async def get_influx():
    engine = await _get_engine()
    store = getattr(engine, "influx_store", None)
    if store is None:
        raise HTTPException(
            status_code=503,
            detail="InfluxDB persistence disabled (set INFLUX_ENABLED=true)",
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


# ---- InfluxDB run time-series (deterministic-run plotting) ----------------


@router.get("/run/current")
async def current_run():
    """The id of the run the engine is currently configured for (Influx tag)."""
    engine = await _get_engine()
    return {"run_id": getattr(engine, "run_id", None)}


@router.get("/runs")
async def list_runs(store=Depends(get_influx)):
    """Distinct run_ids present in InfluxDB, for the run picker."""
    runs = await store.list_runs()
    return {"count": len(runs), "runs": runs}


@router.get("/run/series")
async def run_series(
    run_id: Optional[str] = Query(
        None, description="Run id to plot; defaults to the engine's current run"
    ),
    meter_id: Optional[str] = Query(
        None, description="When set, return that meter's series, not fleet totals"
    ),
    store=Depends(get_influx),
):
    """Time-series for a deterministic run.

    Without ``meter_id``: fleet-wide per-tick totals (gen/con/net) + mean frequency.
    With ``meter_id``: that meter's gen/con/voltage over sim time.
    """
    if run_id is None:
        engine = await _get_engine()
        run_id = getattr(engine, "run_id", None)
    if not run_id:
        raise HTTPException(status_code=400, detail="No run_id available")
    if meter_id:
        series = await store.meter_series(run_id, meter_id)
    else:
        series = await store.aggregate_series(run_id)
    return {
        "run_id": run_id,
        "meter_id": meter_id,
        "count": len(series),
        "series": series,
    }
