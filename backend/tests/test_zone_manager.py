"""Zone island/reconnect control tests.

``ZoneController`` islands a zone by tripping its PCC bus on the grid and reads
state straight back from the grid faults, so commanded-island status stays
consistent with the underlying fault set. End-to-end, islanding a zone in a real
engine tick must de-energize that zone's buses (they fall off the slack) while
leaving the rest of the feeder energized.
"""

import asyncio
from pathlib import Path

import pytest

from smart_meter_simulator.core.engine import SimulationEngine
from smart_meter_simulator.core.topology import GridTopology, ZoneSpec
from smart_meter_simulator.core.zone_manager import ZoneController


class _FakeGrid:
    """Minimal stand-in exposing the fault surface ZoneController touches."""

    def __init__(self, topology):
        self.topology = topology
        self.faulted_buses: set[str] = set()
        self.faulted_transformers: set[str] = set()
        # A MATPOWER reference grid's PCC is a *line* (its CSVs model no
        # transformer object), so ZoneController faults lines too.
        self.faulted_lines: set[str] = set()
        self.islanded_buses: set[str] = set()

    def apply_fault(self, element_type, name):
        if element_type == "bus":
            self.faulted_buses.add(name)
            return True
        if element_type == "transformer":
            self.faulted_transformers.add(name)
            return True
        if element_type == "line":
            self.faulted_lines.add(name)
            return True
        return False

    def clear_fault(self, element_type, name):
        if element_type == "bus" and name in self.faulted_buses:
            self.faulted_buses.discard(name)
            return True
        if element_type == "transformer" and name in self.faulted_transformers:
            self.faulted_transformers.discard(name)
            return True
        if element_type == "line" and name in self.faulted_lines:
            self.faulted_lines.discard(name)
            return True
        return False


def _topology() -> GridTopology:
    return GridTopology(
        zones={
            1: ZoneSpec(
                code=1,
                label="Zone_1",
                pcc_bus="z1_head",
                pcc_transformer="t1",
                member_buses=("z1_head", "z1_a"),
                islandable=True,
            ),
            2: ZoneSpec(
                code=2,
                label="Zone_2",
                member_buses=("z2_a", "z2_b"),
                islandable=False,
            ),
        }
    )


def test_island_opens_pcc_transformer_and_reports_commanded():
    grid = _FakeGrid(_topology())
    zc = ZoneController(grid)

    assert zc.is_islanded(1) is False
    zc.island(1)
    # Islanding opens the PCC coupling branch, leaving the head bus live.
    assert grid.faulted_transformers == {"t1"}
    assert grid.faulted_buses == set()
    assert zc.is_islanded(1) is True

    zc.reconnect(1)
    assert grid.faulted_transformers == set()
    assert zc.is_islanded(1) is False


def test_island_non_islandable_zone_rejected():
    grid = _FakeGrid(_topology())
    zc = ZoneController(grid)
    with pytest.raises(ValueError):
        zc.island(2)
    assert grid.faulted_buses == set()


def test_island_unknown_zone_raises_keyerror():
    zc = ZoneController(_FakeGrid(_topology()))
    with pytest.raises(KeyError):
        zc.island(99)
    with pytest.raises(KeyError):
        zc.reconnect(99)


def test_status_reports_electrical_islanded_from_grid():
    grid = _FakeGrid(_topology())
    zc = ZoneController(grid)
    grid.islanded_buses = {"z1_a"}  # a member is electrically cut off
    status = zc.status(1)
    assert status["islanded"] is True
    assert status["commanded_island"] is False  # PCC not tripped (yet)
    assert status["islandable"] is True
    assert {z["zone_code"] for z in zc.list_status()} == {1, 2}


# --- end-to-end against a real engine ---------------------------------------

REFERENCE_GLM = Path("src/smart_meter_simulator/data/grids/grid_bus_network.glm")


def test_engine_island_zone_deenergizes_its_buses(tmp_path):
    glm = tmp_path / "mz.glm"
    glm.write_text(
        """
        object node { name mv; bustype SWING; nominal_voltage 22000; }
        object node { name z1_head; groupid 1; nominal_voltage 230; }
        object node { name z1_a; groupid 1; nominal_voltage 230; }
        object node { name z2_head; groupid 2; nominal_voltage 230; }
        object node { name z2_a; groupid 2; nominal_voltage 230; }
        object transformer { name pcc1; from mv; to z1_head; }
        object transformer { name pcc2; from mv; to z2_head; }
        object overhead_line { name l1; from z1_head; to z1_a; length 100 ft; }
        object overhead_line { name l2; from z2_head; to z2_a; length 100 ft; }
        """,
        encoding="utf-8",
    )
    engine = SimulationEngine(grid_topology=f"glm:{glm}", num_meters=5)
    engine.grid.initialize_network(engine.meters)

    async def run():
        await engine.tick()
        # Both zones energized initially.
        zones0 = {z["zone_code"]: z for z in engine.last_tick_summary["zones"]}
        assert zones0[1]["islanded"] is False

        engine.zone_controller.island(1)
        await engine.tick()
        zones1 = {z["zone_code"]: z for z in engine.last_tick_summary["zones"]}
        # Zone 1 islanded + commanded; zone 2 stays connected.
        assert zones1[1]["commanded_island"] is True
        assert zones1[1]["islanded"] is True
        assert zones1[2]["islanded"] is False

        engine.zone_controller.reconnect(1)
        await engine.tick()
        zones2 = {z["zone_code"]: z for z in engine.last_tick_summary["zones"]}
        assert zones2[1]["commanded_island"] is False
        assert zones2[1]["islanded"] is False

    asyncio.run(run())
