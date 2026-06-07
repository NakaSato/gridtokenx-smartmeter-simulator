"""Line-flow orientation contract between the grid endpoints.

The dashboard draws the static feeder from ``/grid/topology`` but animates live
current from ``/grid/telemetry``. The two MUST sign line flow the same way — into
the depth-oriented parent(shallow)->child(deep) frame — or the arrows and colors
desync: a normal downstream load on a GLM line authored child->parent reads
negative and is indistinguishable from true PV backfeed.

Regression guard for the bug where ``/grid/telemetry`` returned the raw engine
``line_flows`` (signed to the inconsistent GLM from->to / pandapower p_from) while
``/grid/topology`` reoriented endpoints — so the live UI sign never got corrected.
"""

from __future__ import annotations

import asyncio
from pathlib import Path

import pytest

from smart_meter_simulator.core import app_state
from smart_meter_simulator.core.engine import SimulationEngine
from smart_meter_simulator.routers import grid_v1

REFERENCE_GLM_FILE = Path("src/smart_meter_simulator/data/grids/grid_bus_network.glm")


@pytest.fixture
def grid_endpoints():
    """Tick a real reference-feeder engine once, wire it into app_state, and return
    (engine, topology_response, telemetry_response)."""
    previous = getattr(app_state, "engine", None)
    engine = SimulationEngine(
        grid_topology=f"glm:{REFERENCE_GLM_FILE}", num_meters=40
    )
    engine.grid.initialize_network(engine.meters)
    asyncio.run(engine.tick())
    app_state.engine = engine
    try:
        topology = asyncio.run(grid_v1.grid_topology())
        telemetry = asyncio.run(grid_v1.grid_telemetry())
        yield engine, topology, telemetry
    finally:
        app_state.engine = previous


def test_telemetry_flow_sign_matches_topology(grid_endpoints):
    _engine, topology, telemetry = grid_endpoints
    links = {link["name"]: link for link in topology["graph"]["links"]}
    tele_lines = telemetry["lines"]

    checked = 0
    for name, link in links.items():
        if name not in tele_lines:
            continue
        checked += 1
        assert tele_lines[name]["flow_kw"] == pytest.approx(
            link["flow_kw"], abs=1e-6
        ), f"{name}: telemetry/topology flow_kw desync"
    assert checked > 0


def test_reversed_lines_flip_the_raw_solver_sign(grid_endpoints):
    engine, topology, telemetry = grid_endpoints
    raw = engine.grid.line_flows
    tele_lines = telemetry["lines"]

    reversed_seen = 0
    for link in topology["graph"]["links"]:
        name = link["name"]
        if name not in raw or name not in tele_lines:
            continue
        raw_flow = raw[name].get("flow_kw", 0.0)
        if link["is_reversed"]:
            reversed_seen += 1
            assert tele_lines[name]["flow_kw"] == pytest.approx(
                -raw_flow, abs=1e-6
            ), f"{name}: reversed line should negate raw flow"
        else:
            assert tele_lines[name]["flow_kw"] == pytest.approx(
                raw_flow, abs=1e-6
            ), f"{name}: forward line should keep raw flow"
    # The reference feeder authors several lines child->parent (uphill); if none are
    # flagged reversed the orientation logic has silently stopped firing.
    assert reversed_seen > 0


def test_leaf_flow_sign_tracks_net_injection(grid_endpoints):
    """A degree-1 leaf's single line carries exactly that bus's net injection, so
    its sign is regime-independent: consuming leaf -> power flows in (+), generating
    leaf (PV) -> power flows out (-). This pins the polarity, not just consistency."""
    engine, topology, telemetry = grid_endpoints
    graph = topology["graph"]
    nodes = {node["name"]: node for node in graph["nodes"]}
    tele_lines = telemetry["lines"]

    incident: dict[str, list] = {}
    for link in graph["links"]:
        incident.setdefault(link["from_node"], []).append(link)
        incident.setdefault(link["to_node"], []).append(link)

    substation = engine.grid.topology.get_substation_bus()
    leaves = [
        name
        for name, links in incident.items()
        if len(links) == 1 and name != substation
    ]
    assert leaves

    for name in leaves:
        node = nodes[name]
        link = incident[name][0]
        flow = tele_lines.get(link["name"], {}).get("flow_kw", 0.0)
        # Power into the leaf in the oriented source->target frame.
        into_leaf = flow if link["to_node"] == name else -flow
        if abs(into_leaf) > 0.05 and abs(node["load_kw"]) > 0.05:
            assert (into_leaf > 0) == (
                node["load_kw"] > 0
            ), f"{name}: leaf flow sign disagrees with net injection"
