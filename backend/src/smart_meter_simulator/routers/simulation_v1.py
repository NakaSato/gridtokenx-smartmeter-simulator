"""Simulation control endpoints for the GLM grid model simulator."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException

from smart_meter_simulator.config import SimulationMode
from smart_meter_simulator.config.enums import MeterType

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
        # Deterministic-run identity: the pinned sim-clock start + the Influx run_id.
        "deterministic": getattr(engine, "is_deterministic", False),
        "seed": engine.config.random_seed,
        "start_time": engine.sim_start_time.isoformat(),
        "end_time": (engine.sim_end_time.isoformat() if engine.sim_end_time else None),
        "run_id": engine.run_id,
        "interval_seconds": engine.interval,
        # Run progress: ticks executed, simulated-clock elapsed, real runtime.
        "tick_count": engine.tick_count,
        "sim_elapsed_seconds": engine.sim_elapsed_seconds(),
        "sim_progress": engine.sim_progress(),
        "runtime_seconds": round(engine.runtime_seconds(), 3),
        "topology": engine.grid.get_topology_summary(),
        "last_tick": engine.last_tick_summary,
        # InfluxDB write-path health: null when persistence is disabled/unconfigured,
        # otherwise {connected, writes_ok, writes_failed, last_error} so a
        # "connected but not saving" run is visible from the status endpoint.
        "influx": (
            engine.influx_store.health() if engine.influx_store is not None else None
        ),
    }


@router.get("/simulation/runtime")
async def simulation_runtime(engine=Depends(get_engine)):
    """How long the simulation has run: ticks, simulated-clock span, real time.

    - ``tick_count`` — ticks executed since the last (deterministic) reset.
    - ``sim_elapsed_seconds`` — simulated-clock seconds advanced
      (``current_sim_time - start_time``; equals ``tick_count * interval``).
    - ``runtime_seconds`` — real wall-clock seconds the loop has been running,
      accumulated across start/stop and counting while paused, frozen once
      stopped.
    """
    sim_elapsed = engine.sim_elapsed_seconds()
    runtime = engine.runtime_seconds()
    return {
        "running": engine.running,
        "paused": engine.paused,
        "tick_count": engine.tick_count,
        "interval_seconds": engine.interval,
        "start_time": engine.sim_start_time.isoformat(),
        "end_time": (engine.sim_end_time.isoformat() if engine.sim_end_time else None),
        "current_sim_time": engine.current_sim_time.isoformat(),
        "sim_elapsed_seconds": sim_elapsed,
        "sim_elapsed_human": _humanize(sim_elapsed),
        "sim_progress": engine.sim_progress(),
        "runtime_seconds": round(runtime, 3),
        "runtime_human": _humanize(runtime),
    }


def _humanize(seconds: float) -> str:
    """Render a second count as ``H:MM:SS`` (days prefix when ≥1 day)."""
    total = int(seconds)
    days, rem = divmod(total, 86400)
    hours, rem = divmod(rem, 3600)
    minutes, secs = divmod(rem, 60)
    if days:
        return f"{days}d {hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


@router.post("/simulation/actions/start")
async def simulation_start(engine=Depends(get_engine)):
    await engine.start()
    return {"status": "started"}


@router.post("/simulation/actions/start-deterministic")
async def simulation_start_deterministic(
    seed: Optional[int] = Body(
        None, description="RNG seed. Same seed + start_time => byte-identical replay."
    ),
    start_time: Optional[str] = Body(
        None, description="ISO-8601 sim-clock start, e.g. 2026-06-10T08:00:00+00:00."
    ),
    end_time: Optional[str] = Body(
        None,
        description=(
            "ISO-8601 sim-clock end. The run auto-stops on reaching it, bounding "
            "the window to [start, end). Mutually exclusive with time_range."
        ),
    ),
    time_range: Optional[str] = Body(
        None,
        description=(
            "Window preset instead of an explicit end_time: one of hour, day, "
            "week, month, year (sim-clock duration from start; month/year are "
            "calendar-aware)."
        ),
    ),
    interval: Optional[int] = Body(None, description="Tick interval seconds (>0)."),
    num_meters: Optional[int] = Body(
        None,
        description=(
            "Requested fleet size (>0). Soft: IEEE meter generation is bus-bound, "
            "so with PV_ON_EVERY_BUS the fleet is one meter per topology bus and "
            "this is capped at the bus count (e.g. 80-bus grid => 80 meters)."
        ),
    ),
    autostart: bool = Body(True, description="Start the tick loop after configuring."),
    engine=Depends(get_engine),
):
    """Re-seed + pin the clock, rebuild the fleet, and (re)start a deterministic run.

    Any run launched with the same ``seed`` + ``start_time`` (+ same interval/meters
    /topology) reproduces identical readings.
    """
    try:
        result = await engine.reset_deterministic(
            seed=seed,
            start_time=start_time,
            end_time=end_time,
            time_range=time_range,
            interval=interval,
            num_meters=num_meters,
            autostart=autostart,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"status": "started" if autostart else "configured", **result}


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


@router.get("/simulation/faults")
async def list_faults(engine=Depends(get_engine)):
    """Active line/bus faults and the resulting islanded buses (last tick)."""
    return engine.grid.fault_status()


@router.post("/simulation/faults")
async def trip_fault(
    element_type: str = Body(..., embed=True, description="'line' or 'bus'"),
    name: str = Body(..., embed=True, description="Line or bus name to trip"),
    engine=Depends(get_engine),
):
    """Trip a line or bus out of service (N-1 contingency). Effective next tick."""
    if not engine.grid.apply_fault(element_type, name):
        raise HTTPException(
            status_code=404,
            detail=f"Unknown {element_type} '{name}' (or invalid element_type)",
        )
    return {
        "status": "tripped",
        "element_type": element_type,
        "name": name,
        **engine.grid.fault_status(),
    }


@router.delete("/simulation/faults")
async def clear_faults(
    element_type: Optional[str] = Body(None, embed=True),
    name: Optional[str] = Body(None, embed=True),
    engine=Depends(get_engine),
):
    """Restore a specific faulted element, or all faults when no name is given."""
    if name is None or element_type is None:
        cleared = engine.grid.clear_all_faults()
        return {
            "status": "cleared_all",
            "cleared": cleared,
            **engine.grid.fault_status(),
        }
    if not engine.grid.clear_fault(element_type, name):
        raise HTTPException(
            status_code=404, detail=f"{element_type} '{name}' was not faulted"
        )
    return {
        "status": "cleared",
        "element_type": element_type,
        "name": name,
        **engine.grid.fault_status(),
    }


def _parse_sim_time(value: str, field: str) -> datetime:
    """Parse an ISO-8601 sim-clock instant; a naive value is treated as UTC."""
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise HTTPException(
            status_code=400, detail=f"Invalid {field} {value!r}; expected ISO-8601"
        ) from exc
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


@router.get("/simulation/demand-response")
async def list_demand_response(engine=Depends(get_engine)):
    """Active + scheduled demand-response (load-shed) events at the current sim time."""
    return engine.dr_controller.status(engine.current_sim_time)


@router.post("/simulation/demand-response")
async def schedule_demand_response(
    reduction_fraction: float = Body(
        ...,
        embed=True,
        description="Share of participating load to shed while active, in (0, 1].",
    ),
    start: Optional[str] = Body(
        None,
        embed=True,
        description="ISO-8601 sim-clock start. Defaults to the current sim time.",
    ),
    end: Optional[str] = Body(
        None,
        embed=True,
        description="ISO-8601 sim-clock end. Pass this or duration_minutes.",
    ),
    duration_minutes: Optional[float] = Body(
        None,
        embed=True,
        description="Window length from start (sim minutes). Pass this or end.",
    ),
    target_meter_types: Optional[List[str]] = Body(
        None,
        embed=True,
        description=(
            "Meter-type values to curtail (e.g. Residential, Commercial). "
            "Omit to shed every meter."
        ),
    ),
    label: str = Body("", embed=True, description="Human-readable event label."),
    engine=Depends(get_engine),
):
    """Schedule a demand-response load-shed event over a sim-clock window.

    The event curtails ``reduction_fraction`` of each participating meter's load
    while the sim clock is inside ``[start, end)`` — relieving the feeder. Effective
    on the next tick whose timestamp enters the window.
    """
    start_dt = (
        _parse_sim_time(start, "start")
        if start is not None
        else engine.current_sim_time
    )

    if end is not None and duration_minutes is not None:
        raise HTTPException(
            status_code=400, detail="Pass either end or duration_minutes, not both"
        )
    if end is not None:
        end_dt = _parse_sim_time(end, "end")
    elif duration_minutes is not None:
        if duration_minutes <= 0:
            raise HTTPException(status_code=400, detail="duration_minutes must be > 0")
        end_dt = start_dt + timedelta(minutes=duration_minutes)
    else:
        raise HTTPException(status_code=400, detail="Provide end or duration_minutes")

    if target_meter_types is not None:
        valid = {m.value for m in MeterType}
        unknown = [t for t in target_meter_types if t not in valid]
        if unknown:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown meter type(s) {unknown}; valid: {sorted(valid)}",
            )

    try:
        event = engine.dr_controller.schedule(
            start=start_dt,
            end=end_dt,
            reduction_fraction=reduction_fraction,
            target_meter_types=target_meter_types,
            label=label,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {
        "status": "scheduled",
        "event": event.to_dict(),
        **engine.dr_controller.status(engine.current_sim_time),
    }


@router.delete("/simulation/demand-response")
async def cancel_demand_response(
    event_id: Optional[str] = Body(None, embed=True),
    engine=Depends(get_engine),
):
    """Cancel a DR event by id, or clear every event when no id is given."""
    if event_id is None:
        cleared = engine.dr_controller.clear()
        return {
            "status": "cleared_all",
            "cleared": cleared,
            **engine.dr_controller.status(engine.current_sim_time),
        }
    if not engine.dr_controller.cancel(event_id):
        raise HTTPException(
            status_code=404, detail=f"No demand-response event '{event_id}'"
        )
    return {
        "status": "cancelled",
        "event_id": event_id,
        **engine.dr_controller.status(engine.current_sim_time),
    }


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
        engine.grid.clear_all_faults()  # old element names no longer valid
        engine.grid.initialize_network(engine.meters)
        # Re-register the rebuilt fleet in PostGIS so reading inserts keep a valid
        # grid.meters foreign key after a hot-swap (no-op when persistence is off).
        if getattr(engine, "reading_store", None) is not None:
            await engine.reading_store.register_meters(engine.meters)
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
