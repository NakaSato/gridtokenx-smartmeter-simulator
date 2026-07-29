"""Zones derived from a MATPOWER reference grid's substation branches.

The CSVs model no transformer object, so ``_derive_zones`` partitions on the
line graph with the slack bus removed: each component is one feeder, its PCC is
the branch joining it to the substation. See
``gridtokenx-aggregator-bridge/docs/physics-zone-ids.md`` §3.2.1.
"""

from pathlib import Path

import pytest

from smart_meter_simulator.adapters.reference_grid_loader import (
    _derive_zones,
    load_reference_grid_topology,
)
from smart_meter_simulator.core.topology import GridBus, GridLine
from smart_meter_simulator.meter_registry import (
    build_meter_configs,
    load_meter_registry,
)

REFERENCE_GRID_DIR = Path("data/80_bus_rural_reference_grid")


# --- helpers for synthetic topologies (no CSV fixtures needed) ---------------


def _bus(bus_i: int, bus_type: int = 1) -> GridBus:
    return GridBus(
        name=f"ref_lv_bus_{bus_i}",
        nominal_voltage=230.0,
        properties={"bus_i": str(bus_i), "type": str(float(bus_type))},
    )


def _line(name: str, a: int, b: int, **props: str) -> GridLine:
    return GridLine(
        name=name,
        from_bus=f"ref_lv_bus_{a}",
        to_bus=f"ref_lv_bus_{b}",
        properties={"status": "1", "ratio": "0", **props},
    )


# --- the bundled 80-bus grid ------------------------------------------------


def test_reference_grid_derives_four_feeder_zones():
    topology = load_reference_grid_topology(REFERENCE_GRID_DIR)

    assert sorted(topology.zones) == [1, 2, 3, 4]
    assert [len(topology.zones[c].member_buses) for c in (1, 2, 3, 4)] == [
        29,
        30,
        17,
        3,
    ]
    # Codes ascend by head-bus id: the four branches leaving the substation.
    assert [topology.zones[c].pcc_bus for c in (1, 2, 3, 4)] == [
        "ref_lv_bus_2",
        "ref_lv_bus_31",
        "ref_lv_bus_61",
        "ref_lv_bus_78",
    ]
    assert [topology.zones[c].label for c in (1, 2, 3, 4)] == [
        "ref_pcc_2",
        "ref_pcc_31",
        "ref_pcc_61",
        "ref_pcc_78",
    ]


def test_reference_grid_zones_are_islandable_via_a_real_branch():
    topology = load_reference_grid_topology(REFERENCE_GRID_DIR)
    line_names = {line.name for line in topology.lines}

    for spec in topology.zones.values():
        # The grid is a tree, so each feeder hangs off exactly one branch.
        assert spec.islandable
        # The PCC must name a *real* element or islanding is a silent no-op.
        assert spec.pcc_transformer in line_names
        # No PV/BESS in the CSVs -> no island slack, so a zone goes dark.
        assert spec.der_bus == ""


def test_reference_grid_stamps_zone_code_on_every_bus():
    topology = load_reference_grid_topology(REFERENCE_GRID_DIR)
    code_by_name = {bus.name: bus.zone_code for bus in topology.buses}

    # The slack bus sits in front of every coupling branch -> unzoned.
    assert code_by_name["ref_lv_bus_1"] == 0
    assert code_by_name["ref_lv_bus_2"] == 1
    assert code_by_name["ref_lv_bus_31"] == 2
    assert code_by_name["ref_lv_bus_61"] == 3
    assert code_by_name["ref_lv_bus_80"] == 4

    # Every non-slack bus is zoned, and membership matches the specs exactly.
    assert sum(1 for code in code_by_name.values() if code == 0) == 1
    for code, spec in topology.zones.items():
        assert {name for name in spec.member_buses} == {
            name for name, c in code_by_name.items() if c == code
        }


# --- rule details on synthetic grids ----------------------------------------


def test_transformer_and_out_of_service_branches_are_cut():
    """``ratio != 0`` and ``status == 0`` branches do not merge zones.

    Cutting transformer branches is what makes this rule degenerate to the GLM
    loader's transformer-bounded partition on a dataset that models them.
    """
    buses = [_bus(1, bus_type=3), _bus(2), _bus(3), _bus(4), _bus(5)]
    lines = [
        _line("Line_0", 1, 2),
        _line("Line_1", 2, 3, ratio="1.05"),  # transformer -> cut
        _line("Line_2", 1, 4),
        _line("Line_3", 4, 5, status="0"),  # out of service -> cut
    ]

    stamped, zones = _derive_zones(buses, lines)
    code_by_name = {bus.name: bus.zone_code for bus in stamped}

    # bus 3 is behind a transformer and bus 5 behind a dead branch: both are
    # their own components with no branch to the substation -> unzoned.
    assert code_by_name == {
        "ref_lv_bus_1": 0,
        "ref_lv_bus_2": 1,
        "ref_lv_bus_3": 0,
        "ref_lv_bus_4": 2,
        "ref_lv_bus_5": 0,
    }
    assert sorted(zones) == [1, 2]
    assert zones[1].member_buses == ("ref_lv_bus_2",)


def test_multiply_fed_group_is_kept_but_not_islandable():
    """Two branches to the substation -> opening one will not island it."""
    buses = [_bus(1, bus_type=3), _bus(2), _bus(3)]
    lines = [_line("Line_0", 1, 2), _line("Line_1", 2, 3), _line("Line_2", 1, 3)]

    _, zones = _derive_zones(buses, lines)

    assert sorted(zones) == [1]
    assert zones[1].islandable is False
    assert zones[1].pcc_bus == "ref_lv_bus_2"  # lowest head-bus id
    assert len(zones[1].member_buses) == 2


def test_generation_table_selects_the_island_slack():
    buses = [_bus(1, bus_type=3), _bus(2), _bus(3)]
    lines = [_line("Line_0", 1, 2), _line("Line_1", 2, 3)]

    _, zones = _derive_zones(
        buses, lines, {"ref_lv_bus_2": 5.0, "ref_lv_bus_3": 42.0}
    )

    assert zones[1].der_bus == "ref_lv_bus_3"  # largest dispatchable capacity


def test_no_slack_bus_leaves_everything_unzoned():
    buses = [_bus(1), _bus(2)]
    lines = [_line("Line_0", 1, 2)]

    stamped, zones = _derive_zones(buses, lines)

    assert zones == {}
    assert all(bus.zone_code == 0 for bus in stamped)


def test_zone_codes_are_deterministic_across_loads():
    first = load_reference_grid_topology(REFERENCE_GRID_DIR)
    second = load_reference_grid_topology(REFERENCE_GRID_DIR)

    assert {c: s.member_buses for c, s in first.zones.items()} == {
        c: s.member_buses for c, s in second.zones.items()
    }


def test_derived_codes_stay_within_the_bridge_zone_bound():
    """Codes must be < IOT_NUM_ZONES or the bridge hash-routes them (G2)."""
    topology = load_reference_grid_topology(REFERENCE_GRID_DIR)

    assert max(topology.zones) < 10


@pytest.mark.parametrize("code", [1, 2, 3, 4])
def test_every_member_bus_carries_its_zone_code(code: int):
    topology = load_reference_grid_topology(REFERENCE_GRID_DIR)
    by_name = {bus.name: bus for bus in topology.buses}

    for name in topology.zones[code].member_buses:
        assert by_name[name].zone_code == code


def test_registry_pinned_meters_inherit_the_bus_zone():
    """A registry fleet must carry the topology's zone, not the round-robin.

    ``create_meter_config`` falls back to ``(meter_id % 10) + 1`` when a config
    has no zone, so without this wiring the derived partition never reaches the
    DLMS payload for a ``reference-grid:`` run.
    """
    topology = load_reference_grid_topology(REFERENCE_GRID_DIR)
    entries = load_meter_registry(f"reference-grid:{REFERENCE_GRID_DIR}")
    configs = build_meter_configs(entries, topology)

    zone_by_bus = {bus.name: bus.zone_code for bus in topology.buses}
    assert configs, "reference grid should yield load-bus meters"
    for config in configs:
        expected = zone_by_bus[config["node_id"]]
        # Zone 0 (the substation) stays falsy and round-robins — that is the
        # separate zero-is-falsy defect, not this rule's business.
        if expected:
            assert config["zone_code"] == expected
