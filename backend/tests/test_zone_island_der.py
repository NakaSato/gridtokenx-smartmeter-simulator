"""Self-supporting islanded-zone tests (Phase 4).

When a zone with a DER bus is islanded, a local slack at that bus holds the
zone's voltage so it runs as a microgrid island instead of de-energizing. A zone
with no DER still goes dark on island (Phase 2 behaviour).
"""

import asyncio
from pathlib import Path

from smart_meter_simulator.adapters.glm_topology_loader import load_glm_topology
from smart_meter_simulator.core.engine import SimulationEngine

# Zone 1 carries a 50 kW PV on z1_a (its DER bus); zone 2 has none.
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
object inverter { name inv1; parent z1_a; rated_power 50000; }
object solar { name pv1; parent inv1; rated_power 50000; }
"""


def _write_glm(tmp_path) -> Path:
    glm = tmp_path / "mz.glm"
    glm.write_text(MZ_GLM, encoding="utf-8")
    return glm


def test_loader_picks_largest_pv_member_as_der_bus(tmp_path):
    topo = load_glm_topology(_write_glm(tmp_path))
    zones = topo.zones
    assert zones[1].der_bus == "z1_a"  # the only PV-bearing member
    assert zones[1].islandable is True
    assert zones[2].der_bus == ""  # no PV in zone 2


def test_islanded_zone_with_der_stays_energized(tmp_path):
    engine = SimulationEngine(grid_topology=f"glm:{_write_glm(tmp_path)}", num_meters=5)
    engine.grid.initialize_network(engine.meters)

    async def run():
        engine.zone_controller.island(1)
        await engine.tick()
        zones = {z["zone_code"]: z for z in engine.last_tick_summary["zones"]}
        # Commanded island, but DER slack holds it -> not electrically islanded.
        assert zones[1]["commanded_island"] is True
        assert zones[1]["island_capable"] is True
        assert zones[1]["islanded"] is False
        # The DER bus carries voltage (local slack ~1.0 pu).
        assert engine.grid.bus_voltages.get("z1_a", 0.0) > 0.0
        # Island opens the PCC transformer, NOT the head bus — so the zone head
        # stays a live load bus fed by the island's DER (regression: it used to
        # de-energize when islanding faulted the head bus directly).
        assert "pcc1" in engine.grid.faulted_transformers
        assert engine.grid.bus_voltages.get("z1_head", 0.0) > 0.0

    asyncio.run(run())


def test_islanded_zone_without_der_goes_dark(tmp_path):
    engine = SimulationEngine(grid_topology=f"glm:{_write_glm(tmp_path)}", num_meters=5)
    engine.grid.initialize_network(engine.meters)

    async def run():
        engine.zone_controller.island(2)
        await engine.tick()
        zones = {z["zone_code"]: z for z in engine.last_tick_summary["zones"]}
        # No DER -> island de-energizes (Phase 2 disconnect semantics).
        assert zones[2]["commanded_island"] is True
        assert zones[2]["island_capable"] is False
        assert zones[2]["islanded"] is True
        assert engine.grid.bus_voltages.get("z2_a", 1.0) == 0.0

    asyncio.run(run())


def test_reconnect_drops_island_slack(tmp_path):
    engine = SimulationEngine(grid_topology=f"glm:{_write_glm(tmp_path)}", num_meters=5)
    engine.grid.initialize_network(engine.meters)

    async def run():
        engine.zone_controller.island(1)
        await engine.tick()
        assert engine.grid._island_ext_grid_idx  # a slack was added

        engine.zone_controller.reconnect(1)
        await engine.tick()
        # Island slack removed; zone 1 back on the grid, energized, not islanded.
        assert engine.grid._island_ext_grid_idx == []
        zones = {z["zone_code"]: z for z in engine.last_tick_summary["zones"]}
        assert zones[1]["commanded_island"] is False
        assert zones[1]["islanded"] is False
        assert engine.grid.bus_voltages.get("z1_a", 0.0) > 0.0

    asyncio.run(run())
