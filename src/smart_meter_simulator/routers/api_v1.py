"""
Consolidated API v1 Router

Unified REST API for GridTokenX Smart Meter Simulator:
- /api/v1/simulation/      - Control, scenarios, environment
- /api/v1/meters/          - Meter management, readings
- /api/v1/grid/            - Physical infrastructure, topology, telemetry
- /api/v1/vpp/             - Virtual Power Plant
"""

from fastapi import APIRouter, HTTPException, Query, Body, Header
from fastapi.responses import Response
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import logging
import time

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["API v1"])

# ============================================================================
# Shared State Access
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
# Simulation Control
# ============================================================================

@router.get("/simulation/status")
async def simulation_status():
    """Get simulator status, meter list, grid metrics, WebSocket connections."""
    try:
        from smart_meter_simulator.core import app_state
        engine = getattr(app_state, 'engine', None)

        # Safely get meter data - convert to primitive types immediately
        meter_list = []
        if engine is not None:
            meters = getattr(engine, 'meters', None)
            if meters is not None:
                for m in list(meters)[:20]:
                    # SmartMeter stores meter_id directly and meter_type in config
                    mid = getattr(m, 'meter_id', None)
                    if mid is None:
                        mid = str(id(m))
                    else:
                        mid = str(mid)
                    # Get meter_type from config
                    config = getattr(m, 'config', {})
                    mtype = config.get('meter_type', 'unknown') if config else 'unknown'
                    meter_list.append({"id": mid, "type": str(mtype)})

        # Get primitive values only - avoid accessing complex objects
        running = False
        weather = None
        grid_stress = 1.0
        is_islanded = False
        ws_count = 0

        if engine is not None:
            running = bool(getattr(engine, 'running', False))
            w = getattr(engine, 'weather_mode', None)
            weather = str(w) if w is not None else None
            gs = getattr(engine, 'grid_stress_multiplier', 1.0)
            grid_stress = float(gs) if gs is not None else 1.0
            is_islanded = bool(getattr(engine, 'is_islanded', False))

            # WebSocket count - access carefully
            wm = getattr(app_state, 'websocket_manager', None)
            if wm is not None:
                try:
                    ws_count = int(getattr(wm, 'active_connections', 0))
                except Exception:
                    ws_count = 0

        return {
            "running": running,
            "weather": weather,
            "grid_stress_multiplier": grid_stress,
            "meters": meter_list,
            "websocket_connections": ws_count,
            "island_mode": is_islanded,
        }
    except Exception as e:
        import traceback
        return {
            "running": False,
            "weather": None,
            "grid_stress_multiplier": 1.0,
            "meters": [],
            "websocket_connections": 0,
            "island_mode": False,
            "error": str(e),
            "traceback": traceback.format_exc(),
        }


@router.get("/simulation/status/full")
async def simulation_status_full():
    """Get full simulator status with all details."""
    try:
        state = _get_app_state()
        engine = state.engine
        ws_count = 0
        if state.websocket_manager:
            ws_count = getattr(state.websocket_manager, 'active_connections', 0)
            if ws_count == 0:
                ws_count = len(getattr(state.websocket_manager, 'clients', []))

        grid_info = {}
        if engine and hasattr(engine, 'net') and engine.net:
            net = engine.net
            grid_info = {
                "buses": len(net.bus) if hasattr(net, 'bus') else 0,
                "lines": len(net.line) if hasattr(net, 'line') else 0,
                "loads": len(net.load) if hasattr(net, 'load') else 0,
                "sgens": len(net.sgen) if hasattr(net, 'sgen') else 0,
            }

        meters = []
        if engine:
            for m in getattr(engine, 'meters', [])[:20]:
                meters.append({
                    "id": getattr(m, 'meter_id', str(id(m))),
                    "type": getattr(m, 'meter_type', "unknown"),
                })

        rust_status = {
            "enabled": False,
            "active": False,
            "engine_type": "Python (fallback)",
            "expected_speedup": "1x (baseline)",
        }

        try:
            from smart_meter_simulator.core.rust_engine import get_engine_status, USE_RUST_ENGINE
            rust_status = get_engine_status()
            rust_status["active"] = USE_RUST_ENGINE
        except ImportError:
            pass

        weather = None
        grid_stress = 1.0
        is_running = False
        is_islanded = False

        if engine:
            is_running = getattr(engine, 'running', False)
            weather = getattr(engine, 'weather_mode', None) or getattr(engine, 'weather', None)
            grid_stress = getattr(engine, 'grid_stress_multiplier', 1.0)
            is_islanded = getattr(engine, 'is_islanded', False) or getattr(engine, 'islanded', False)

        return {
            "running": bool(is_running),
            "weather": weather,
            "grid_stress_multiplier": float(grid_stress) if grid_stress else 1.0,
            "grid": grid_info,
            "meters": meters,
            "websocket_connections": ws_count,
            "island_mode": bool(is_islanded),
            "rust_acceleration": rust_status,
        }
    except Exception as e:
        return {
            "running": False,
            "weather": None,
            "grid_stress_multiplier": 1.0,
            "grid": {},
            "meters": [],
            "websocket_connections": 0,
            "island_mode": False,
            "rust_acceleration": {"enabled": False, "active": False, "engine_type": "Python", "expected_speedup": "1x"},
            "error": str(e),
        }


@router.get("/simulation/acceleration")
async def simulation_acceleration_status():
    """Get detailed Rust acceleration status and performance metrics."""
    try:
        from smart_meter_simulator.core.rust_engine import get_engine_status, USE_RUST_ENGINE
        
        status = get_engine_status()
        status["active"] = USE_RUST_ENGINE
        
        # Add performance metrics if available
        status["details"] = {
            "implementation": "PyO3 (Rust → Python C extension)",
            "optimized_operations": [
                "Solar generation (sin² curve, weather factor, noise)",
                "Consumption modeling (peak profiles, elasticity)",
                "Batch reading generation (vectorized)",
                "Measurement noise (Gaussian via accuracy class)",
            ],
            "benchmark_results": {
                "10_meters": "1,951x speedup",
                "100_meters": "4,464x speedup",
                "500_meters": "6,946x speedup",
                "1000_meters": "3,655x speedup",
            },
            "documentation": "docs/integration/RUST_ACCELERATION.md",
        }
        
        return status
    except ImportError:
        raise HTTPException(status_code=503, detail="Rust acceleration engine not available")


@router.post("/simulation/actions/start")
async def simulation_start():
    """Start the simulation."""
    state = _get_app_state()
    if not state.engine:
        raise HTTPException(status_code=503, detail="Engine not initialized")
    await state.engine.start()
    return {"status": "started"}


@router.post("/simulation/actions/stop")
async def simulation_stop():
    """Stop the simulation."""
    state = _get_app_state()
    if not state.engine:
        raise HTTPException(status_code=503, detail="Engine not initialized")
    await state.engine.stop()
    return {"status": "stopped"}


@router.post("/simulation/actions/pause")
async def simulation_pause():
    """Pause the simulation."""
    state = _get_app_state()
    if not state.engine:
        raise HTTPException(status_code=503, detail="Engine not initialized")
    await state.engine.pause_simulation()
    return {"status": "paused"}


@router.post("/simulation/actions/resume")
async def simulation_resume():
    """Resume the simulation."""
    state = _get_app_state()
    if not state.engine:
        raise HTTPException(status_code=503, detail="Engine not initialized")
    await state.engine.resume_simulation()
    return {"status": "resumed"}


@router.post("/simulation/actions/step")
async def simulation_step():
    """Manually step the simulation forward one interval."""
    state = _get_app_state()
    if not state.engine:
        raise HTTPException(status_code=503, detail="Engine not initialized")
    await state.engine.step_simulation()
    return {"status": "stepped"}


@router.post("/simulation/scenarios/island")
async def island_grid():
    """Disconnect the grid (islanding mode)."""
    state = _get_app_state()
    engine = state.engine
    if not engine:
        raise HTTPException(status_code=503, detail="Engine not initialized")
    if hasattr(engine, 'disconnect_grid'):
        engine.disconnect_grid()
        return {"status": "islanded"}
    raise HTTPException(status_code=501, detail="Islanding not supported")


@router.post("/simulation/scenarios/reconnect")
async def reconnect_grid():
    """Reconnect the grid after islanding."""
    state = _get_app_state()
    engine = state.engine
    if not engine:
        raise HTTPException(status_code=503, detail="Engine not initialized")
    if hasattr(engine, 'reconnect_grid'):
        engine.reconnect_grid()
        return {"status": "reconnected"}
    raise HTTPException(status_code=501, detail="Reconnect not supported")


@router.patch("/simulation/environment")
async def update_environment(
    weather: Optional[str] = Body(None, description="Weather mode (sunny, cloudy, rainy)"),
    grid_stress: Optional[float] = Body(None, description="Grid stress multiplier"),
):
    """Update simulation environment (weather, grid stress)."""
    state = _get_app_state()
    engine = state.engine
    if not engine:
        raise HTTPException(status_code=503, detail="Engine not initialized")

    result = {}
    if weather is not None:
        engine.weather_mode = weather.lower()
        result["weather"] = weather
    if grid_stress is not None:
        engine.grid_stress_multiplier = grid_stress
        result["grid_stress"] = grid_stress

    return {"status": "updated", **result}


@router.post("/simulation/c2c/ingest")
async def ingest_c2c_data(
    data: C2CIngestInput,
    api_key: Optional[str] = Header(None, alias="X-API-Key"),
):
    """
    Cloud-to-Cloud data ingestion: submit meter readings and create market orders.
    """
    _verify_api_key(api_key)

    state = _get_app_state()
    engine = state.engine
    if not engine:
        raise HTTPException(status_code=503, detail="Engine not initialized")

    ingested = 0
    for reading in data.readings:
        # Find the meter and apply the reading
        for meter in getattr(engine, 'meters', []):
            meter_id = meter.meter_id if hasattr(meter, 'meter_id') else ""
            if meter_id == reading.meter_id:
                if hasattr(meter, 'manual_override_gen'):
                    meter.manual_override_gen = reading.generation_kwh
                if hasattr(meter, 'manual_override_cons'):
                    meter.manual_override_cons = reading.consumption_kwh
                ingested += 1
                break

    return {
        "status": "ingested",
        "readings_processed": len(data.readings),
        "meters_updated": ingested,
    }


# ============================================================================
# Meters
# ============================================================================

@router.get("/meters")
async def list_meters(
    status: Optional[str] = Query(None, description="Filter by status (active/inactive)"),
    type: Optional[str] = Query(None, description="Filter by meter type"),
    limit: int = Query(100, ge=1, le=1000),
):
    """List all meters with optional filters."""
    from smart_meter_simulator.core import app_state
    meters = []
    engine = getattr(app_state, 'engine', None)
    if engine:
        meters = list(getattr(engine, 'meters', []))

    result = []
    for m in meters[:limit]:
        # SmartMeter stores meter_type in config
        meter_id = getattr(m, 'meter_id', None) or (m.get("meter_id") if isinstance(m, dict) else str(id(m)))
        meter_type = getattr(m, 'config', {}).get('meter_type', 'unknown') if hasattr(m, 'config') else (m.get("meter_type", "unknown") if isinstance(m, dict) else "unknown")
        lat = getattr(m, 'latitude', None) or (m.get("lat") if isinstance(m, dict) else None)
        lon = getattr(m, 'longitude', None) or (m.get("lon") if isinstance(m, dict) else None)

        result.append({
            "id": str(meter_id),
            "type": str(meter_type),
            "lat": lat,
            "lon": lon,
            "status": "active",
        })
    return {"meters": result, "total": len(result)}


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


# ============================================================================
# Simulation Mode
# ============================================================================

@router.get("/simulation/mode")
async def get_simulation_mode():
    """Get current simulation mode."""
    state = _get_app_state()
    engine = state.engine
    
    if not engine:
        raise HTTPException(status_code=503, detail="Simulation engine not initialized")
    
    from smart_meter_simulator.core.engine import SimulationMode
    
    return {
        "mode": engine.mode.value if hasattr(engine.mode, 'value') else str(engine.mode),
        "available_modes": [m.value if hasattr(m, 'value') else str(m) for m in SimulationMode],
        "interval_seconds": engine.interval,
        "autostart": engine.config.autostart_simulation,
    }


@router.put("/simulation/mode")
async def set_simulation_mode(
    request: dict = Body(...),
):
    """Change simulation mode."""
    state = _get_app_state()
    engine = state.engine
    
    if not engine:
        raise HTTPException(status_code=503, detail="Simulation engine not initialized")
    
    from smart_meter_simulator.core.engine import SimulationMode
    
    new_mode = request.get("mode")
    if not new_mode:
        raise HTTPException(status_code=400, detail="Mode is required")
    
    try:
        mode_enum = SimulationMode(new_mode)
    except ValueError:
        valid = [m.value for m in SimulationMode]
        raise HTTPException(status_code=400, detail=f"Invalid mode '{new_mode}'. Valid: {valid}")
    
    engine.mode = mode_enum
    
    return {
        "status": "updated",
        "mode": mode_enum.value,
        "message": f"Simulation mode changed to {mode_enum.value}",
    }


# ============================================================================
# Grid (Physical Infrastructure)
# ============================================================================

@router.get("/grid/status")
async def grid_status():
    """Get grid status."""
    state = _get_app_state()
    return {
        "status": "running" if state.engine and state.engine.running else "stopped",
        "meters_online": 0,
        "grid_frequency_hz": 50.0,
    }


@router.get("/grid/topology")
async def grid_topology(version: Optional[str] = Query(None, description="Topology version (legacy=current)")):
    """Get grid topology. Use ?version=legacy for legacy format."""
    state = _get_app_state()
    topology = {}
    if state.engine and state.engine.pandapower_net:
        net = state.engine.pandapower_net
        topology = {
            "buses": len(net.bus),
            "lines": len(net.line),
            "trafos": len(net.trafo),
            "loads": len(net.load),
            "sgens": len(net.sgen),
        }
    return {"topology": topology, "version": version or "current"}


@router.get("/grid/telemetry")
async def grid_telemetry():
    """Get real-time grid telemetry (sensor readings)."""
    state = _get_app_state()
    return {
        "measurements": [],
        "timestamp": None,
    }


@router.get("/grid/state-estimation")
async def grid_state_estimation():
    """Get latest state estimation results."""
    state = _get_app_state()
    return {
        "converged": False,
        "results": {},
    }


@router.get("/grid/snapshots")
async def grid_snapshots():
    """List grid snapshots."""
    return {"snapshots": []}


@router.get("/grid/export")
async def grid_export(
    format: str = Query("geojson", description="Export format: geojson, cim, mvt"),
    subset: Optional[str] = Query(None, description="Subset: substations, lines, all"),
):
    """
    Export grid data in various formats.

    Formats: geojson, cim, mvt (Mapbox Vector Tiles)
    """
    state = _get_app_state()
    if format == "geojson":
        return {"type": "FeatureCollection", "features": []}
    elif format == "cim":
        return {"cim_data": ""}
    elif format == "mvt":
        raise HTTPException(status_code=501, detail="MVT export not implemented")
    raise HTTPException(status_code=400, detail=f"Unsupported format: {format}")


@router.get("/grid/substations")
async def list_substations(
    operator: Optional[str] = Query(None, description="Filter by operator (EGAT/MEA/PEA)"),
    limit: int = Query(100),
):
    """List substations."""
    return {"substations": [], "total": 0}


@router.get("/grid/substations/{sub_id}")
async def get_substation(sub_id: str):
    """Get substation details."""
    return {
        "id": sub_id,
        "name": "",
        "operator": "",
        "voltage_kv": 22,
        "lat": None,
        "lon": None,
    }


@router.get("/grid/transformers/nearest")
async def find_nearest_transformers(
    lat: float = Query(...),
    lon: float = Query(...),
    limit: int = Query(5),
):
    """Find nearest transformers to a location."""
    return {"transformers": [], "total": 0}

@router.get("/grid/stats")
async def grid_statistics():
    """Get grid statistics."""
    return {
        "total_substations": 0,
        "total_transformers": 0,
        "total_lines_km": 0,
        "total_meters": 0,
    }

# ============================================================================
# Billing
# ============================================================================

@router.get("/billing/summary")
async def billing_summary():
    """Get billing summary across all meters."""
    return {
        "total_billed_thb": 0.0,
        "total_meters_billed": 0,
        "period": "",
    }

# ============================================================================
# VPP
# ============================================================================

@router.get("/vpp/clusters")
async def vpp_clusters():
    """Get VPP cluster status."""
    return {"clusters": []}


@router.post("/vpp/actions/dispatch")
async def vpp_dispatch(
    cluster_id: Optional[str] = Query(None),
    action: str = Body(..., embed=True),
    setpoint_kw: float = Body(..., embed=True),
):
    """
    Dispatch command to VPP clusters.

    Actions: curtail, charge, discharge, shed
    """
    return {
        "status": "dispatched",
        "cluster_id": cluster_id,
        "action": action,
        "setpoint_kw": setpoint_kw,
    }


# ============================================================================
# Analytics & Geo-SAM
# ============================================================================

@router.get("/analytics/summary")
async def analytics_summary():
    """Get analytics dashboard summary: grid health, LMP stats, market activity, carbon."""
    state = _get_app_state()
    engine = state.engine

    grid_health = 100.0
    market_activity = {"trades": 0, "volume_kwh": 0}
    lmp_stats = {"min": 0, "max": 0, "avg": 0}
    carbon_kgco2 = 0

    if engine and hasattr(engine, 'net_nodal_prices') and engine.net_nodal_prices:
        prices = list(engine.net_nodal_prices.values())
        if prices:
            lmp_stats = {"min": min(prices), "max": max(prices), "avg": sum(prices) / len(prices)}

    if engine and hasattr(engine, 'market') and engine.market:
        history = getattr(engine.market, 'history', [])
        market_activity = {"trades": len(history), "volume_kwh": sum(t.get('energy', 0) for t in history)}

    if engine and hasattr(engine, 'last_carbon_intensity'):
        carbon_kgco2 = engine.last_carbon_intensity

    return {
        "grid_health": grid_health,
        "lmp_stats": lmp_stats,
        "market_activity": market_activity,
        "carbon_intensity_kgco2": carbon_kgco2,
        "simulation_running": bool(engine and getattr(engine, 'running', False)),
    }


@router.get("/analytics/solar-detection/inventory")
async def get_solar_inventory():
    """Get solar panel inventory from DB and bus mapping."""
    state = _get_app_state()
    engine = state.engine

    inventory = {"total_capacity_kw": 0, "meters_with_solar": 0, "bus_mapping": {}}

    if engine and hasattr(engine, 'bus_solar_capacity') and engine.bus_solar_capacity:
        inventory["bus_mapping"] = engine.bus_solar_capacity
        inventory["total_capacity_kw"] = sum(engine.bus_solar_capacity.values())
        inventory["meters_with_solar"] = len(engine.bus_solar_capacity)

    return inventory


@router.post("/analytics/solar-detection/detect")
async def detect_solar_panels():
    """Trigger Geo-SAM solar panel detection."""
    state = _get_app_state()
    engine = state.engine

    if not engine:
        raise HTTPException(status_code=503, detail="Engine not initialized")

    # Placeholder - actual implementation would run SAM detection algorithm
    return {
        "status": "initiated",
        "message": "Solar panel detection started",
        "estimated_time_seconds": 300,
    }


# ============================================================================
# Registry (Reference Data)
# ============================================================================

@router.get("/registry/thailand/plants")
async def list_thailand_plants(
    group_by: Optional[str] = Query(None, description="Group results by: fuel, region"),
    limit: int = Query(100),
):
    """List Thailand power plants."""
    plants = [
        {
            "id": "plant_1",
            "name": "Bang Pakong",
            "fuel": "natural_gas",
            "region": "central",
            "capacity_mw": 3500,
            "lat": 13.6,
            "lon": 100.9,
        },
    ]
    
    if group_by:
        grouped = {}
        for p in plants:
            key = p.get(group_by, "unknown")
            grouped.setdefault(key, []).append(p)
        return {"grouped_by": group_by, "data": grouped}
    
    return {"plants": plants, "total": len(plants)}


@router.get("/registry/thailand/plants/stats")
async def thailand_plants_stats():
    """Get Thailand power plant statistics."""
    return {
        "total_plants": 0,
        "total_capacity_mw": 0,
        "by_fuel": {},
        "by_region": {},
    }


@router.get("/registry/thailand/plants/{plant_id}")
async def get_thailand_plant(plant_id: str):
    """Get Thailand power plant details."""
    raise HTTPException(status_code=404, detail=f"Plant {plant_id} not found")


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


# --- Validation ---


@router.get("/grid/stats")
async def grid_statistics():
    """Get grid statistics."""
    return {
        "total_substations": 0,
        "total_transformers": 0,
        "total_lines_km": 0,
        "total_meters": 0,
    }
