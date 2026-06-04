"""Simulation control endpoints for the GLM grid model simulator."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Body, Depends, HTTPException

from smart_meter_simulator.config import SimulationMode

router = APIRouter(prefix="", tags=["Simulation"])


async def get_engine():
    from smart_meter_simulator.core import app_state

    engine = app_state.engine
    if engine is None:
        raise HTTPException(status_code=503, detail="Engine not initialized")
    return engine


@router.get("/simulation/status")
async def simulation_status(engine=Depends(get_engine)):
    return {
        "running": engine.running,
        "paused": engine.paused,
        "weather": engine.weather_mode,
        "grid_stress_multiplier": engine.grid_stress_multiplier,
        "total_meters": len(engine.meters),
        "mode": engine.mode.value,
        "current_sim_time": engine.current_sim_time.isoformat(),
        "topology": engine.grid.get_topology_summary(),
        "last_tick": engine.last_tick_summary,
    }


@router.post("/simulation/actions/start")
async def simulation_start(engine=Depends(get_engine)):
    await engine.start()
    return {"status": "started"}


@router.post("/simulation/actions/stop")
async def simulation_stop(engine=Depends(get_engine)):
    await engine.stop()
    return {"status": "stopped"}


@router.post("/simulation/actions/pause")
async def simulation_pause(engine=Depends(get_engine)):
    await engine.pause_simulation()
    return {"status": "paused"}


@router.post("/simulation/actions/resume")
async def simulation_resume(engine=Depends(get_engine)):
    await engine.resume_simulation()
    return {"status": "resumed"}


@router.post("/simulation/actions/step")
async def simulation_step(engine=Depends(get_engine)):
    await engine.step_simulation()
    return {"status": "stepped", "last_tick": engine.last_tick_summary}


@router.patch("/simulation/environment")
async def update_environment(
    weather: Optional[str] = Body(None),
    grid_stress: Optional[float] = Body(None),
    topology: Optional[str] = Body(
        None,
        description="Topology override spec. Only glm:path/to/file.glm is supported.",
    ),
    engine=Depends(get_engine),
):
    from smart_meter_simulator.core.topology_factory import load_topology_spec
    from smart_meter_simulator.devices.ami import SmartMeter
    from smart_meter_simulator.meter_generator import MeterGenerator

    result = {}
    if weather is not None:
        engine.weather_mode = weather
        result["weather"] = weather
    if grid_stress is not None:
        engine.grid_stress_multiplier = grid_stress
        result["grid_stress"] = grid_stress

    if topology is not None:
        if not topology.startswith("glm:"):
            raise HTTPException(
                status_code=400,
                detail="Unsupported topology spec. Use glm:path/to/file.glm.",
            )

        next_topology = load_topology_spec(topology)
        generator = MeterGenerator(len(engine.meters))
        pv_capacity_by_node = {pv.bus: pv.capacity_kw for pv in next_topology.pvs}
        configs = generator.generate_ieee_meters(
            num_nodes=len(next_topology.buses),
            target_meters=len(engine.meters),
            pv_on_every_bus=engine.config.pv_on_every_bus,
            node_ids=[bus.name for bus in next_topology.buses],
            pv_capacity_kw_by_node=pv_capacity_by_node,
        )
        engine.meters = [SmartMeter(config) for config in configs]
        engine.grid.adapter = None
        engine.grid.topology = next_topology
        engine.grid.initialize_network(engine.meters)
        result["topology_spec"] = topology
        result["topology"] = engine.grid.get_topology_summary()

    return {"status": "updated", **result}


@router.get("/simulation/mode")
async def get_simulation_mode(engine=Depends(get_engine)):
    return {
        "mode": engine.mode.value,
        "available_modes": [mode.value for mode in SimulationMode],
        "interval_seconds": engine.interval,
    }


@router.put("/simulation/mode")
async def set_simulation_mode(request: dict = Body(...), engine=Depends(get_engine)):
    new_mode = request.get("mode")
    if not new_mode:
        raise HTTPException(status_code=400, detail="Mode is required")

    try:
        mode = SimulationMode(new_mode)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid mode '{new_mode}'. Valid: {[m.value for m in SimulationMode]}",
        ) from None

    engine.mode = mode
    return {"status": "updated", "mode": mode.value}
