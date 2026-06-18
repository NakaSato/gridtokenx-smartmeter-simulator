"""Tie-switch reconfiguration tests (Phase 4b).

A normally-open tie-switch between two feeders/zones carries no flow until
closed. Closing it transfers load — e.g. restoring a zone whose own feed was
lost by feeding it from a healthy neighbour.
"""

import asyncio
from pathlib import Path

from smart_meter_simulator.adapters.glm_topology_loader import load_glm_topology
from smart_meter_simulator.core.engine import SimulationEngine

# Two grid-fed zones plus a normally-open tie between z1_a and z2_a.
MZ_GLM = """
object node { name mv; bustype SWING; nominal_voltage 22000; }
object node { name z1_head; groupid 1; nominal_voltage 230; }
object node { name z1_a; groupid 1; nominal_voltage 230; }
object node { name z2_head; groupid 2; nominal_voltage 230; }
object node { name z2_a; groupid 2; nominal_voltage 230; }
object transformer { name pcc1; from mv; to z1_head; }
object transformer { name pcc2; from mv; to z2_head; }
object overhead_line { name l1; from z1_head; to z1_a; length 100 ft; }
object overhead_line { name l2; from z2_head; to z2_a; length 100 ft; }
object switch { name tie_1_2; from z1_a; to z2_a; status OPEN; }
"""


def _write_glm(tmp_path) -> Path:
    glm = tmp_path / "tie.glm"
    glm.write_text(MZ_GLM, encoding="utf-8")
    return glm


def test_loader_parses_normally_open_switch(tmp_path):
    topo = load_glm_topology(_write_glm(tmp_path))
    tie = next(line for line in topo.lines if line.name == "tie_1_2")
    assert tie.is_switch is True
    assert tie.normally_open is True
    assert (tie.from_bus, tie.to_bus) == ("z1_a", "z2_a")


def test_grid_initializes_switch_open_and_toggles(tmp_path):
    engine = SimulationEngine(grid_topology=f"glm:{_write_glm(tmp_path)}", num_meters=5)
    engine.grid.initialize_network(engine.meters)
    grid = engine.grid

    assert grid.switch_lines == {"tie_1_2"}
    assert grid.open_switches == {"tie_1_2"}  # normally open
    status = {s["name"]: s["closed"] for s in grid.switch_status()["switches"]}
    assert status["tie_1_2"] is False

    assert grid.set_switch("tie_1_2", closed=True) is True
    assert grid.open_switches == set()
    assert grid.set_switch("tie_1_2", closed=False) is True
    assert grid.open_switches == {"tie_1_2"}
    assert grid.set_switch("nope", closed=True) is False


def test_closing_tie_restores_de_energized_zone(tmp_path):
    engine = SimulationEngine(grid_topology=f"glm:{_write_glm(tmp_path)}", num_meters=5)
    engine.grid.initialize_network(engine.meters)

    async def run():
        # Island zone 2 (no DER) -> it goes dark with the tie still open.
        engine.zone_controller.island(2)
        await engine.tick()
        assert engine.grid.bus_voltages.get("z2_a", 1.0) == 0.0
        zones = {z["zone_code"]: z for z in engine.last_tick_summary["zones"]}
        assert zones[2]["islanded"] is True

        # Close the tie from healthy zone 1 -> zone 2 fed through it, re-energized.
        engine.grid.set_switch("tie_1_2", closed=True)
        await engine.tick()
        assert engine.grid.bus_voltages.get("z2_a", 0.0) > 0.0
        zones = {z["zone_code"]: z for z in engine.last_tick_summary["zones"]}
        assert zones[2]["islanded"] is False

    asyncio.run(run())
