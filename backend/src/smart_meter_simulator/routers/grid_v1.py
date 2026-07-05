"""GLM grid topology and telemetry endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter

router = APIRouter(prefix="", tags=["Grid"])


def _get_app_state():
    from smart_meter_simulator.core import app_state

    return app_state


def _bus_visual_type(bus: Any, substation: str) -> str:
    bustype = str(getattr(bus, "properties", {}).get("bustype", "")).upper()
    source_type = str(getattr(bus, "source_type", "")).lower()
    if bus.name == substation or bustype == "SWING" or source_type == "substation":
        return "t"
    if float(getattr(bus, "nominal_voltage", 0.0) or 0.0) >= 1000.0:
        return "f"
    return "b"


def _bus_visual_kind(bus_type: str) -> str:
    if bus_type == "t":
        return "transformer"
    if bus_type == "f":
        return "feeder"
    return "service"


def _topology_graph_metadata(topology: Any, substation: str) -> dict[str, Any]:
    if not topology or not getattr(topology, "buses", None):
        return {
            "depth_by_bus": {},
            "parent_by_bus": {},
            "children_by_bus": {},
            "degree_by_bus": {},
        }

    import networkx as nx

    graph = topology.to_networkx().to_undirected()
    bus_names = [bus.name for bus in topology.buses]
    root = substation if substation in graph else (bus_names[0] if bus_names else "")
    depth_by_bus: dict[str, int] = {}
    parent_by_bus: dict[str, str | None] = {name: None for name in bus_names}
    children_by_bus: dict[str, list[str]] = {name: [] for name in bus_names}

    if root:
        depth_by_bus.update(nx.single_source_shortest_path_length(graph, root))
        for child, parent in nx.bfs_predecessors(graph, root):
            parent_by_bus[child] = parent
            children_by_bus.setdefault(parent, []).append(child)

    next_depth = (max(depth_by_bus.values()) + 1) if depth_by_bus else 0
    for bus_name in bus_names:
        if bus_name not in depth_by_bus:
            depth_by_bus[bus_name] = next_depth

    return {
        "depth_by_bus": depth_by_bus,
        "parent_by_bus": parent_by_bus,
        "children_by_bus": children_by_bus,
        "degree_by_bus": dict(graph.degree(bus_names)),
    }


def _line_flow_sign(
    core_topology: Any, depth_by_bus: dict[str, int]
) -> dict[str, float]:
    """Map line name -> flow sign (+1/-1) normalizing the solver's raw flow_kw
    (signed to the GLM-authored from→to / pandapower p_from) into the depth-oriented
    parent(shallow)→child(deep) frame. GLM authors line from/to inconsistently, so
    a child→parent line (from deeper than to) gets -1: its endpoints reorient and the
    sign follows. After this, downstream load reads positive and negative reliably
    means true reverse (PV backfeed up the feeder). Same rule as the /grid/topology
    `is_reversed` endpoint orientation — keep the two in lockstep."""
    signs: dict[str, float] = {}
    for line in getattr(core_topology, "lines", None) or []:
        if not line.name:
            continue
        from_depth = depth_by_bus.get(line.from_bus, 0)
        to_depth = depth_by_bus.get(line.to_bus, 0)
        signs[line.name] = -1.0 if from_depth > to_depth else 1.0
    return signs


def _meters_by_bus(engine: Any) -> dict[str, list[Any]]:
    meters_by_bus: dict[str, list[Any]] = {}
    topology = getattr(engine.grid, "topology", None)
    for meter in engine.meters:
        config = getattr(meter, "config", {})
        bus_name = config.get("node_id") or config.get("bus_name")
        if not bus_name:
            try:
                bus_idx = int(config.get("bus_idx"))
                bus_name = topology.buses[bus_idx].name if topology else None
            except (TypeError, ValueError, IndexError):
                bus_name = None
        if bus_name:
            meters_by_bus.setdefault(bus_name, []).append(meter)
    return meters_by_bus


def _line_status(line_state: dict[str, Any]) -> str:
    utilization = float(line_state.get("utilization_pct") or 0.0)
    if utilization > 80.0:
        return "congested"
    if utilization > 40.0:
        return "loaded"
    return "normal"


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
        return {
            "topology": {"mode": "uninitialized", "meters": 0},
            "buses": {},
            "lines": [],
            "graph": {"root": None, "nodes": [], "links": []},
        }

    topology = engine.grid.get_topology_summary()
    topology["meters"] = len(engine.meters)

    buses_dict = {}
    lines_list = []

    if engine.grid.topology:
        core_topology = engine.grid.topology
        substation = core_topology.get_substation_bus()
        bus_index = {bus.name: i for i, bus in enumerate(core_topology.buses)}
        graph_meta = _topology_graph_metadata(core_topology, substation)
        meters_by_bus = _meters_by_bus(engine)
        static_load_by_bus = core_topology.load_at_bus()
        pv_capacity_by_bus: dict[str, float] = {}
        for pv in core_topology.pvs:
            pv_capacity_by_bus[pv.bus] = pv_capacity_by_bus.get(pv.bus, 0.0) + float(
                pv.capacity_kw or 0.0
            )

        for i, bus in enumerate(core_topology.buses):
            bus_meters = meters_by_bus.get(bus.name, [])
            solar_meters = [
                meter
                for meter in bus_meters
                if getattr(meter, "config", {}).get("has_solar")
            ]
            bus_type = _bus_visual_type(bus, substation)
            meter_solar_capacity_kw = sum(
                float(getattr(meter, "config", {}).get("solar_capacity") or 0.0)
                for meter in solar_meters
            )
            topology_solar_capacity_kw = pv_capacity_by_bus.get(bus.name, 0.0)
            static_load = static_load_by_bus.get(bus.name, 0j)
            bus_state = engine.grid.get_bus_state(bus.name)
            buses_dict[str(i)] = {
                "node_id": bus.name,
                "name": bus.name,
                "vn_kv": bus.nominal_voltage / 1000.0 if bus.nominal_voltage else 0.4,
                "type": bus_type,
                "kind": _bus_visual_kind(bus_type),
                "source_type": bus.source_type,
                "phases": bus.phases,
                "is_substation": bus.name == substation,
                "depth": graph_meta["depth_by_bus"].get(bus.name, 0),
                "parent": graph_meta["parent_by_bus"].get(bus.name),
                "children": sorted(graph_meta["children_by_bus"].get(bus.name, [])),
                "degree": graph_meta["degree_by_bus"].get(bus.name, 0),
                "has_solar": bool(solar_meters) or topology_solar_capacity_kw > 0,
                "solar_capacity_kw": meter_solar_capacity_kw
                or topology_solar_capacity_kw,
                "meter_solar_capacity_kw": meter_solar_capacity_kw,
                "topology_solar_capacity_kw": topology_solar_capacity_kw,
                "static_load_kw": static_load.real / 1000.0,
                "static_load_kvar": static_load.imag / 1000.0,
                "voltage_pu": bus_state.get("voltage_pu", 1.0),
                "load_kw": bus_state.get("load_kw", 0.0),
                "load_kvar": bus_state.get("load_kvar", 0.0),
                "meter_ids": [meter.meter_id for meter in bus_meters],
            }

        for i, line in enumerate(core_topology.lines):
            if line.from_bus not in bus_index or line.to_bus not in bus_index:
                continue
            line_state = engine.grid.get_line_state(line.name)
            raw_from_depth = graph_meta["depth_by_bus"].get(line.from_bus, 0)
            raw_to_depth = graph_meta["depth_by_bus"].get(line.to_bus, 0)
            if raw_from_depth <= raw_to_depth:
                source_node = line.from_bus
                target_node = line.to_bus
                source_depth = raw_from_depth
                target_depth = raw_to_depth
                raw_direction = "downstream"
                is_reversed = False
            else:
                source_node = line.to_bus
                target_node = line.from_bus
                source_depth = raw_to_depth
                target_depth = raw_from_depth
                raw_direction = "upstream"
                is_reversed = True
            # Solver signs power relative to the raw GLM from→to. We reorient
            # endpoints parent(shallow)→child(deep) above, so when that swaps the
            # endpoints the flow sign must swap too — otherwise a normal downstream
            # load on an uphill-authored line reads negative and is indistinguishable
            # from true PV backfeed. Loss is I²R (direction-independent), left as-is.
            flow_sign = -1.0 if is_reversed else 1.0
            flow_kw = line_state.get("flow_kw", 0.0) * flow_sign
            flow_kvar = line_state.get("flow_kvar", 0.0) * flow_sign
            lines_list.append(
                {
                    "id": line.name or f"line-{i}",
                    "name": line.name,
                    "from_bus": bus_index[source_node],
                    "to_bus": bus_index[target_node],
                    "from_node": source_node,
                    "to_node": target_node,
                    "from_depth": source_depth,
                    "to_depth": target_depth,
                    "raw_from_node": line.from_bus,
                    "raw_to_node": line.to_bus,
                    "raw_direction": raw_direction,
                    "is_reversed": is_reversed,
                    "length_m": line.length,
                    "length_km": line_state.get(
                        "length_km", line.length / 1000.0 if line.length else 0.1
                    ),
                    "source_type": line.source_type,
                    "phases": line.phases,
                    "capacity_kw": line_state.get("capacity_kw", line.capacity_kw),
                    "resistance_ohm_per_km": line.resistance_ohm_per_km,
                    "reactance_ohm_per_km": line.reactance_ohm_per_km,
                    "flow_kw": flow_kw,
                    "flow_kvar": flow_kvar,
                    "utilization_pct": line_state.get("utilization_pct", 0.0),
                    "loss_kw": line_state.get("loss_kw", 0.0),
                    "status": _line_status(line_state),
                    "direction": "downstream",
                }
            )
        lines_list.sort(
            key=lambda line: (
                line.get("from_depth", 0),
                line.get("to_depth", 0),
                line.get("name") or "",
            )
        )

    graph = {
        "root": topology.get("substation"),
        "nodes": [
            {"id": key, **bus}
            for key, bus in sorted(buses_dict.items(), key=lambda item: int(item[0]))
        ],
        "links": lines_list,
    }

    return {
        "topology": topology,
        "buses": buses_dict,
        "lines": lines_list,
        "graph": graph,
    }


@router.get("/grid/telemetry")
async def grid_telemetry():
    state = _get_app_state()
    engine = state.engine
    if not engine:
        return {"summary": {}, "buses": {}, "lines": {}}

    # Orient live line flow into the same parent→child frame as /grid/topology so the
    # dashboard's live current matches the static layout: downstream load positive,
    # negative = true reverse (PV backfeed). Raw engine line_flows are signed to the
    # GLM-authored from→to, which is inconsistent across lines.
    lines_out = engine.grid.line_flows
    if engine.grid.topology:
        core_topology = engine.grid.topology
        depth_by_bus = _topology_graph_metadata(
            core_topology, core_topology.get_substation_bus()
        )["depth_by_bus"]
        signs = _line_flow_sign(core_topology, depth_by_bus)
        oriented: dict[str, Any] = {}
        for name, line_state in engine.grid.line_flows.items():
            sign = signs.get(name, 1.0)
            if sign != 1.0 and isinstance(line_state, dict):
                line_state = {
                    **line_state,
                    "flow_kw": line_state.get("flow_kw", 0.0) * sign,
                    "flow_kvar": line_state.get("flow_kvar", 0.0) * sign,
                }
            oriented[name] = line_state
        lines_out = oriented

    return {
        "summary": engine.last_tick_summary,
        "buses": {
            bus_name: engine.grid.get_bus_state(bus_name)
            for bus_name in engine.grid.bus_voltages
        },
        "lines": lines_out,
        "readings": (
            [r.model_dump() for r in engine.last_readings]
            if engine.last_readings
            else []
        ),
    }


# Flows below this magnitude (kW) are noise, not worth animating on the map.
_FLOW_MIN_KW = 0.1


@router.get("/grid/flows")
async def grid_flows():
    """Instantaneous meter↔zone energy flows for the trading-UI map.

    Raw-refs form of the map contract (gridtokenx-trading
    docs/MAP_REAL_DATA_API.md §3): each meter with a non-trivial net power
    contributes one flow toward its zone transformer. ``power_kw`` is signed
    from the meter's perspective: positive = surplus exported meter→zone,
    negative = deficit supplied zone→meter. Net power comes straight from the
    meter's last solved reading (generation − consumption), same conversion
    as /meters ``generation_kw``/``consumption_kw``.
    """
    from smart_meter_simulator.routers.meters_v1 import _to_kw

    state = _get_app_state()
    engine = state.engine
    if not engine:
        return {"flows": []}

    flows: list[dict[str, Any]] = []
    for meter in engine.meters:
        reading = getattr(meter, "last_reading", None)
        if reading is None:
            continue
        generation_kw = _to_kw(reading, "energy_generated")
        consumption_kw = _to_kw(reading, "energy_consumed")
        net_kw = round(generation_kw - consumption_kw, 3)
        if abs(net_kw) <= _FLOW_MIN_KW:
            continue
        config = getattr(meter, "config", {})
        try:
            zone_code = int(config.get("zone_code") or 0)
        except (TypeError, ValueError):
            zone_code = 0
        name = config.get("location_name") or meter.meter_id
        if net_kw > 0:
            description = f"{name}: exporting {net_kw:.1f} kW to zone {zone_code}"
        else:
            description = f"{name}: importing {-net_kw:.1f} kW from zone {zone_code}"
        flows.append(
            {
                "from_meter_id": meter.meter_id,
                "to_zone_id": zone_code,
                "power_kw": net_kw,
                "description": description,
            }
        )
    return {"flows": flows}


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
