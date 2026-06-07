"""Fault/outage injection tests against the reference GLM feeder.

Tripping a line or bus out of service must reroute or island the radial feeder:
buses cut off from the substation slack are de-energized (voltage 0) and reported
as islanded. Clearing the fault restores them on the next tick.
"""

import asyncio
from pathlib import Path

import networkx as nx

from smart_meter_simulator.core.engine import SimulationEngine

REFERENCE_GLM_FILE = Path("src/smart_meter_simulator/data/grids/grid_bus_network.glm")


def _engine(meters: int = 40) -> SimulationEngine:
    engine = SimulationEngine(
        grid_topology=f"glm:{REFERENCE_GLM_FILE}", num_meters=meters
    )
    engine.grid.initialize_network(engine.meters)
    return engine


def _pick_islanding_line(engine):
    """Return (line_name, expected_islanded) for a line whose removal islands a
    proper, non-empty subset of buses (computed independently from the topology)."""
    grid = engine.grid
    sub = grid.topology.get_substation_bus()
    base = grid.topology_graph.to_undirected()
    all_buses = set(grid.pp_bus_map.keys())
    for name, state in grid.line_flows.items():
        frm, to = state["from"], state["to"]
        if not base.has_edge(frm, to):
            continue
        g2 = base.copy()
        g2.remove_edge(frm, to)
        reachable = (
            set(nx.node_connected_component(g2, sub)) if g2.has_node(sub) else set()
        )
        islanded = (all_buses - reachable) & all_buses
        if 0 < len(islanded) < len(all_buses):
            return name, islanded
    return None, set()


def test_trip_line_islands_downstream_buses():
    engine = _engine()
    asyncio.run(engine.tick())  # baseline
    assert engine.grid.fault_status()["fault_count"] == 0
    assert not engine.grid.islanded_buses

    line_name, expected = _pick_islanding_line(engine)
    assert line_name is not None, "no islanding line found in radial feeder"

    assert engine.grid.apply_fault("line", line_name) is True
    asyncio.run(engine.tick())

    assert engine.grid.islanded_buses == expected
    # islanded buses are de-energized
    for bus in expected:
        assert engine.grid.bus_voltages[bus] == 0.0
    # summary reflects the fault
    assert engine.last_tick_summary["fault_count"] == 1
    assert engine.last_tick_summary["islanded_bus_count"] == len(expected)


def test_clear_fault_restores_energization():
    engine = _engine()
    line_name, expected = _pick_islanding_line(engine)
    assert line_name is not None

    engine.grid.apply_fault("line", line_name)
    asyncio.run(engine.tick())
    assert engine.grid.islanded_buses == expected

    assert engine.grid.clear_fault("line", line_name) is True
    asyncio.run(engine.tick())
    assert not engine.grid.islanded_buses
    # previously islanded buses are energized again
    for bus in expected:
        assert engine.grid.bus_voltages[bus] > 0.0


def test_trip_bus_deenergizes_it():
    engine = _engine()
    asyncio.run(engine.tick())
    # pick any non-substation bus
    sub = engine.grid.topology.get_substation_bus()
    target = next(b for b in engine.grid.pp_bus_map if b != sub)

    assert engine.grid.apply_fault("bus", target) is True
    asyncio.run(engine.tick())
    assert engine.grid.bus_voltages[target] == 0.0
    assert target in engine.grid.fault_status()["faulted_buses"]


def test_apply_fault_unknown_name_returns_false():
    engine = _engine()
    assert engine.grid.apply_fault("line", "NO_SUCH_LINE") is False
    assert engine.grid.apply_fault("bus", "NO_SUCH_BUS") is False
    assert engine.grid.apply_fault("widget", "x") is False
    assert engine.grid.fault_status()["fault_count"] == 0


def test_clear_all_faults():
    engine = _engine()
    line_name, _ = _pick_islanding_line(engine)
    engine.grid.apply_fault("line", line_name)
    sub = engine.grid.topology.get_substation_bus()
    bus = next(b for b in engine.grid.pp_bus_map if b != sub)
    engine.grid.apply_fault("bus", bus)
    assert engine.grid.fault_status()["fault_count"] == 2

    cleared = engine.grid.clear_all_faults()
    assert cleared == 2
    assert engine.grid.fault_status()["fault_count"] == 0
    assert engine.grid.clear_fault("line", line_name) is False  # nothing to clear
