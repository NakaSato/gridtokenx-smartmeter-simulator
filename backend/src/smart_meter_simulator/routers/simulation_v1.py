"""
Simulation Control Router v1

REST API for simulation control, FDI attacks, environment, and mode:
- /api/v1/simulation/       - Control, scenarios, environment, mode
"""

from fastapi import APIRouter, Depends, HTTPException, Body, Header
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="", tags=["Simulation"])


# ============================================================================
# Shared State Access
# ============================================================================


def _get_app_state():
    """Get the global app state (lazy import to avoid circular dependency)."""
    from smart_meter_simulator.core import app_state

    return app_state


async def get_engine():
    """Dependency that returns the simulation engine, or raises 503 if not available."""
    state = _get_app_state()
    engine = getattr(state, "engine", None)
    if engine is None:
        raise HTTPException(status_code=503, detail="Engine not initialized")
    return engine


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
async def simulation_status(engine=Depends(get_engine)):
    """Get simulator status, meter list, grid metrics, WebSocket connections."""
    try:
        from smart_meter_simulator.core import app_state

        # Safely get meter data - convert to primitive types immediately
        meter_list = []
        if engine is not None:
            meters = getattr(engine, "meters", None)
            if meters is not None:
                for m in list(meters)[:20]:
                    # SmartMeter stores meter_id directly and meter_type in config
                    mid = getattr(m, "meter_id", None)
                    if mid is None:
                        mid = str(id(m))
                    else:
                        mid = str(mid)
                    # Get meter_type from config
                    config = getattr(m, "config", {})
                    mtype = config.get("meter_type", "unknown") if config else "unknown"
                    meter_list.append({"id": mid, "type": str(mtype)})

        # Get primitive values only - avoid accessing complex objects
        running = False
        weather = None
        grid_stress = 1.0
        is_islanded = False
        ws_count = 0
        total_meters = 0

        if engine is not None:
            running = bool(getattr(engine, "running", False))
            total_meters = len(getattr(engine, "meters", []))
            w = getattr(engine, "weather_mode", None)
            weather = str(w) if w is not None else None
            gs = getattr(engine, "grid_stress_multiplier", 1.0)
            grid_stress = float(gs) if gs is not None else 1.0
            is_islanded = bool(getattr(engine, "is_islanded", False))

            # WebSocket count - access carefully
            wm = getattr(app_state, "websocket_manager", None)
            if wm is not None:
                try:
                    ws_count = int(getattr(wm, "active_connections", 0))
                except Exception:
                    ws_count = 0

        return {
            "running": running,
            "weather": weather,
            "grid_stress_multiplier": grid_stress,
            "total_meters": total_meters,
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
async def simulation_status_full(engine=Depends(get_engine)):
    """Get full simulator status with all details."""
    try:
        state = _get_app_state()
        ws_count = 0
        if state.websocket_manager:
            ws_count = getattr(state.websocket_manager, "active_connections", 0)
            if ws_count == 0:
                ws_count = len(getattr(state.websocket_manager, "clients", []))

        grid_info = {}
        if engine and hasattr(engine, "net") and engine.net:
            net = engine.net
            grid_info = {
                "buses": len(net.bus) if hasattr(net, "bus") else 0,
                "lines": len(net.line) if hasattr(net, "line") else 0,
                "loads": len(net.load) if hasattr(net, "load") else 0,
                "sgens": len(net.sgen) if hasattr(net, "sgen") else 0,
            }

        meters = []
        if engine:
            for m in getattr(engine, "meters", [])[:20]:
                meters.append(
                    {
                        "id": getattr(m, "meter_id", str(id(m))),
                        "type": getattr(m, "meter_type", "unknown"),
                    }
                )

        rust_status = {
            "enabled": False,
            "active": False,
            "engine_type": "Python (fallback)",
            "expected_speedup": "1x (baseline)",
        }

        try:
            from smart_meter_simulator.core.rust_engine import (
                get_engine_status,
                USE_RUST_ENGINE,
            )

            rust_status = get_engine_status()
            rust_status["active"] = USE_RUST_ENGINE
        except ImportError:
            pass

        weather = None
        grid_stress = 1.0
        is_running = False
        is_islanded = False

        if engine:
            is_running = getattr(engine, "running", False)
            weather = getattr(engine, "weather_mode", None) or getattr(
                engine, "weather", None
            )
            grid_stress = getattr(engine, "grid_stress_multiplier", 1.0)
            is_islanded = getattr(engine, "is_islanded", False) or getattr(
                engine, "islanded", False
            )

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
            "rust_acceleration": {
                "enabled": False,
                "active": False,
                "engine_type": "Python",
                "expected_speedup": "1x",
            },
            "error": str(e),
        }


@router.get("/simulation/acceleration")
async def simulation_acceleration_status():
    """Get detailed Rust acceleration status and performance metrics."""
    try:
        from smart_meter_simulator.core.rust_engine import (
            get_engine_status,
            USE_RUST_ENGINE,
        )

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
        raise HTTPException(
            status_code=503, detail="Rust acceleration engine not available"
        )


@router.post("/simulation/actions/start")
async def simulation_start(engine=Depends(get_engine)):
    """Start the simulation."""
    await engine.start()
    return {"status": "started"}


@router.post("/simulation/actions/stop")
async def simulation_stop(engine=Depends(get_engine)):
    """Stop the simulation."""
    await engine.stop()
    return {"status": "stopped"}


@router.post("/simulation/actions/pause")
async def simulation_pause(engine=Depends(get_engine)):
    """Pause the simulation."""
    await engine.pause_simulation()
    return {"status": "paused"}


@router.post("/simulation/actions/resume")
async def simulation_resume(engine=Depends(get_engine)):
    """Resume the simulation."""
    await engine.resume_simulation()
    return {"status": "resumed"}


@router.post("/simulation/actions/step")
async def simulation_step(engine=Depends(get_engine)):
    """Manually step the simulation forward one interval."""
    await engine.step_simulation()
    return {"status": "stepped"}


@router.post("/simulation/scenarios/island")
async def island_grid(engine=Depends(get_engine)):
    """Disconnect the grid (islanding mode)."""
    if hasattr(engine, "disconnect_grid"):
        engine.disconnect_grid()
        return {"status": "islanded"}
    raise HTTPException(status_code=501, detail="Islanding not supported")


@router.post("/simulation/scenarios/reconnect")
async def reconnect_grid(engine=Depends(get_engine)):
    """Reconnect the grid after islanding."""
    if hasattr(engine, "reconnect_grid"):
        engine.reconnect_grid()
        return {"status": "reconnected"}
    raise HTTPException(status_code=501, detail="Reconnect not supported")


# ============================================================================
# Load Shedding Scenarios
# ============================================================================


@router.get("/simulation/scenarios/loadshed/status")
async def get_loadshed_status(engine=Depends(get_engine)):
    """Get the current load shedding scenario status."""
    service = engine.loadshed_scenario
    return {
        "is_active": service.is_active,
        "scenario_loaded": len(service.active_scenario) > 0,
        "steps_count": len(service.active_scenario),
        "executed_steps": service.executed_steps,
        "latency_enabled": service.latency_enabled,
        "pending_actions_count": len(service.pending_actions)
    }


@router.post("/simulation/scenarios/loadshed/load")
async def load_loadshed_scenario(
    payload: Dict[str, Any] = Body(...),
    engine=Depends(get_engine)
):
    """Load a new load shedding scenario."""
    scenario_data = payload.get("scenario")
    if not scenario_data:
        raise HTTPException(status_code=400, detail="Missing 'scenario' in payload")
    
    latency_enabled = payload.get("latency_enabled", False)
    latency_per_hop = payload.get("latency_per_hop_seconds", 1.0)
    
    success = engine.loadshed_scenario.load_scenario(
        scenario_data, 
        latency_enabled=latency_enabled,
        latency_per_hop_seconds=latency_per_hop
    )
    
    if not success:
        raise HTTPException(status_code=400, detail="Failed to parse scenario data")
        
    return {"success": True, "message": "Scenario loaded successfully"}


@router.post("/simulation/scenarios/loadshed/start")
async def start_loadshed_scenario(engine=Depends(get_engine)):
    """Start the loaded load shedding scenario."""
    if not engine.loadshed_scenario.active_scenario:
        raise HTTPException(status_code=400, detail="No scenario loaded. Call /load first.")
    
    engine.loadshed_scenario.start(engine.current_sim_time)
    return {"success": True, "message": "Scenario execution started"}


@router.post("/simulation/scenarios/loadshed/stop")
async def stop_loadshed_scenario(engine=Depends(get_engine)):
    """Stop the running load shedding scenario."""
    engine.loadshed_scenario.stop()
    return {"success": True, "message": "Scenario execution stopped"}


# ============================================================================
# Environment
# ============================================================================


@router.patch("/simulation/environment")
async def update_environment(
    weather: Optional[str] = Body(
        None, description="Weather mode (sunny, cloudy, rainy)"
    ),
    grid_stress: Optional[float] = Body(None, description="Grid stress multiplier"),
    scenario: Optional[str] = Body(None, description="Grid topology scenario (ieee123, ieee8500)"),
    engine=Depends(get_engine),
):
    """Update simulation environment (weather, grid stress, scenario)."""
    from smart_meter_simulator.adapters.pandapower_adapter import PandapowerAdapter
    from smart_meter_simulator.meter_generator import MeterGenerator
    from smart_meter_simulator.devices.ami import SmartMeter

    result = {}
    if weather is not None:
        engine.weather_mode = weather.lower()
        result["weather"] = weather
    if grid_stress is not None:
        engine.grid_stress_multiplier = grid_stress
        result["grid_stress"] = grid_stress
    
    if scenario is not None:
        logger.info(f"Switching simulation scenario to {scenario}")
        adapter = PandapowerAdapter()
        net = None
        if scenario == "ieee123":
            net = adapter.build_ieee_123_node()
        elif scenario == "ieee8500":
            net = adapter.build_ieee_8500_node()
        
        if net is not None:
            # Re-generate meters for the new scenario
            generator = MeterGenerator(len(engine.meters))
            meter_configs = generator.generate_ieee_meters(num_nodes=len(net.bus), target_meters=len(engine.meters))
            new_meters = [SmartMeter(config) for config in meter_configs]
            
            # Update engine
            engine.grid.adapter = adapter
            engine.grid.initialize_network(new_meters)
            engine.meters = new_meters
            engine.vpp_handler.register_meters(new_meters)
            if engine.market_handler:
                engine.market_handler.register_meters(new_meters)
            
            result["scenario"] = scenario

    return {"status": "updated", **result}


# ============================================================================
# Simulation Mode
# ============================================================================


@router.get("/simulation/mode")
async def get_simulation_mode(engine=Depends(get_engine)):
    """Get current simulation mode."""
    from smart_meter_simulator.core.engine import SimulationMode

    return {
        "mode": engine.mode.value
        if hasattr(engine.mode, "value")
        else str(engine.mode),
        "available_modes": [
            m.value if hasattr(m, "value") else str(m) for m in SimulationMode
        ],
        "interval_seconds": engine.interval,
        "autostart": engine.config.autostart_simulation,
    }


@router.put("/simulation/mode")
async def set_simulation_mode(
    request: dict = Body(...),
    engine=Depends(get_engine),
):
    """Change simulation mode."""
    from smart_meter_simulator.core.engine import SimulationMode

    new_mode = request.get("mode")
    if not new_mode:
        raise HTTPException(status_code=400, detail="Mode is required")

    try:
        mode_enum = SimulationMode(new_mode)
    except ValueError:
        valid = [m.value for m in SimulationMode]
        raise HTTPException(
            status_code=400, detail=f"Invalid mode '{new_mode}'. Valid: {valid}"
        )

    engine.mode = mode_enum

    return {
        "status": "updated",
        "mode": mode_enum.value,
        "message": f"Simulation mode changed to {mode_enum.value}",
    }


# ============================================================================
# C2C Ingest
# ============================================================================


@router.post("/simulation/c2c/ingest")
async def ingest_c2c_data(
    data: C2CIngestInput,
    api_key: Optional[str] = Header(None, alias="X-API-Key"),
    engine=Depends(get_engine),
):
    """
    Cloud-to-Cloud data ingestion: submit meter readings and create market orders.
    """
    _verify_api_key(api_key)

    ingested = 0
    for reading in data.readings:
        # Find the meter and apply the reading
        for meter in getattr(engine, "meters", []):
            meter_id = meter.meter_id if hasattr(meter, "meter_id") else ""
            if meter_id == reading.meter_id:
                if hasattr(meter, "manual_override_gen"):
                    meter.manual_override_gen = reading.generation_kwh
                if hasattr(meter, "manual_override_cons"):
                    meter.manual_override_cons = reading.consumption_kwh
                ingested += 1
                break

    return {
        "status": "ingested",
        "readings_processed": len(data.readings),
        "meters_updated": ingested,
    }
