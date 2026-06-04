"""GLM grid topology and telemetry endpoints."""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="", tags=["Grid"])


def _get_app_state():
    from smart_meter_simulator.core import app_state

    return app_state


@router.get("/grid/status")
async def grid_status():
    state = _get_app_state()
    engine = state.engine
    if not engine:
        return {"status": "stopped", "meters_online": 0, "topology": None}

    return {
        "status": "running" if engine.running else "ready",
        "meters_online": len(engine.meters),
        "weather": engine.weather_mode,
        "grid_stress_multiplier": engine.grid_stress_multiplier,
        "topology": engine.grid.get_topology_summary(),
    }


@router.get("/grid/topology")
async def grid_topology():
    state = _get_app_state()
    engine = state.engine
    if not engine:
        return {"topology": {"mode": "uninitialized", "meters": 0}}

    topology = engine.grid.get_topology_summary()
    topology["meters"] = len(engine.meters)

    buses_dict = {}
    lines_list = []

    if engine.grid.topology:
        meters_by_bus = {}
        for meter in engine.meters:
            config = getattr(meter, "config", {})
            bus_name = config.get("node_id") or config.get("bus_name")
            if not bus_name:
                try:
                    bus_idx = int(config.get("bus_idx"))
                    bus_name = engine.grid.topology.buses[bus_idx].name
                except (TypeError, ValueError, IndexError):
                    bus_name = None
            if bus_name:
                meters_by_bus.setdefault(bus_name, []).append(meter)

        for i, bus in enumerate(engine.grid.topology.buses):
            bus_meters = meters_by_bus.get(bus.name, [])
            solar_meters = [
                meter
                for meter in bus_meters
                if getattr(meter, "config", {}).get("has_solar")
            ]
            buses_dict[str(i)] = {
                "node_id": bus.name,
                "name": bus.name,
                "vn_kv": bus.nominal_voltage / 1000.0 if bus.nominal_voltage else 0.4,
                "type": "b",
                "has_solar": bool(solar_meters),
                "solar_capacity_kw": sum(
                    float(getattr(meter, "config", {}).get("solar_capacity") or 0.0)
                    for meter in solar_meters
                ),
                "meter_ids": [meter.meter_id for meter in bus_meters],
            }

        for line in engine.grid.topology.lines:
            try:
                from_idx = next(
                    i
                    for i, b in enumerate(engine.grid.topology.buses)
                    if b.name == line.from_bus
                )
                to_idx = next(
                    i
                    for i, b in enumerate(engine.grid.topology.buses)
                    if b.name == line.to_bus
                )
                lines_list.append(
                    {
                        "name": line.name,
                        "from_bus": from_idx,
                        "to_bus": to_idx,
                        "length_km": line.length / 1000.0 if line.length else 0.1,
                    }
                )
            except StopIteration:
                pass

    return {"topology": topology, "buses": buses_dict, "lines": lines_list}


@router.get("/grid/telemetry")
async def grid_telemetry():
    state = _get_app_state()
    engine = state.engine
    if not engine:
        return {"summary": {}, "buses": {}, "lines": {}}

    return {
        "summary": engine.last_tick_summary,
        "buses": {
            bus_name: engine.grid.get_bus_state(bus_name)
            for bus_name in engine.grid.bus_voltages
        },
        "lines": engine.grid.line_flows,
        "readings": (
            [r.model_dump() for r in engine.last_readings]
            if engine.last_readings
            else []
        ),
    }


@router.get("/grid/stats")
async def grid_statistics():
    state = _get_app_state()
    engine = state.engine
    if not engine:
        return {"total_meters": 0, "mode": "uninitialized"}

    topology = engine.grid.get_topology_summary()
    return {
        "total_meters": len(engine.meters),
        "mode": topology.get("mode", "glm_topology"),
        "topology": topology,
        "last_tick": engine.last_tick_summary,
    }
