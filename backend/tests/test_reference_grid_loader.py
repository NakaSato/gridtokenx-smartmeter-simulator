"""Tests for the MATPOWER/CINELDI reference-grid CSV loader."""

from __future__ import annotations

from pathlib import Path

import pytest

from smart_meter_simulator.adapters.reference_grid_loader import (
    load_reference_grid_load_buses,
    load_reference_grid_topology,
    reference_bus_name,
)
from smart_meter_simulator.core.topology_factory import (
    load_topology_spec,
    parse_topology_spec,
)


def _write(path: Path, text: str) -> None:
    path.write_text(text.strip() + "\n", encoding="utf-8")


@pytest.fixture
def grid_dir(tmp_path: Path) -> Path:
    """A minimal 3-bus / 2-branch reference grid with loads on buses 2 and 3."""
    _write(
        tmp_path / "mpc_base_mva.csv",
        "Base MVA\n1",
    )
    # bus 1 is the swing (type 3); all at 0.23 kV.
    _write(
        tmp_path / "mpc_bus.csv",
        "bus_i,type,basekV\n1,3,0.23\n2,1,0.23\n3,1,0.23",
    )
    _write(
        tmp_path / "mpc_branch.csv",
        "fbus,tbus,r,x,rateA\n1,2,0.5,0.2,0.1\n2,3,0.4,0.1,0.1",
    )
    # Branch lengths so per-km impedance is well defined (index-matched to mpc_branch).
    _write(
        tmp_path / "branch_extra.csv",
        "From Bus,To Bus,Length [km]\n1,2,2.0\n2,3,1.0",
    )
    # p_load/q_load: first column is the timestamp, remaining columns are load buses.
    _write(
        tmp_path / "p_load.csv",
        "Date,2,3\n2026-01-01 00:00,0.01,0.02",
    )
    _write(
        tmp_path / "q_load.csv",
        "Date,2,3\n2026-01-01 00:00,0.003,0.004",
    )
    return tmp_path


def test_loads_buses_lines_and_loads(grid_dir: Path) -> None:
    topo = load_reference_grid_topology(grid_dir)

    assert topo.source == "reference-grid"
    assert topo.metadata["format"] == "matpower_csv"
    assert topo.metadata["base_mva"] == 1.0

    # Buses: 3, all 230 V, named ref_lv_bus_N, with bus 1 marked SWING.
    assert [b.name for b in topo.buses] == [
        "ref_lv_bus_1",
        "ref_lv_bus_2",
        "ref_lv_bus_3",
    ]
    assert all(b.nominal_voltage == pytest.approx(230.0) for b in topo.buses)
    swing = next(b for b in topo.buses if b.name == "ref_lv_bus_1")
    assert swing.properties["bustype"] == "SWING"

    # Lines: 2, mapped to ref bus names.
    assert [ln.name for ln in topo.lines] == ["Line_0", "Line_1"]
    line0 = topo.lines[0]
    assert (line0.from_bus, line0.to_bus) == ("ref_lv_bus_1", "ref_lv_bus_2")
    assert line0.length == pytest.approx(2.0)
    assert line0.capacity_kw == pytest.approx(100.0)  # rateA (0.1) * 1000

    # Per-unit -> ohm: Z_base = base_kv^2 / base_mva = 0.23^2 / 1 = 0.0529 ohm.
    # r = 0.5 pu -> 0.02645 ohm over 2 km -> 0.013225 ohm/km.
    assert float(line0.properties["resistance_ohm"]) == pytest.approx(0.02645)
    assert line0.resistance_ohm_per_km == pytest.approx(0.013225)
    assert line0.reactance_ohm_per_km == pytest.approx(0.2 * 0.0529 / 2.0)

    # Loads: buses 2 and 3, P in MW -> VA (complex constant_power).
    assert {ld.parent for ld in topo.loads} == {"ref_lv_bus_2", "ref_lv_bus_3"}
    load2 = next(ld for ld in topo.loads if ld.parent == "ref_lv_bus_2")
    assert load2.constant_power.real == pytest.approx(0.01 * 1e6)
    assert load2.constant_power.imag == pytest.approx(0.003 * 1e6)

    # No PV in the reference CSVs.
    assert topo.pvs == []


def test_load_bus_metadata_from_p_load_header(grid_dir: Path) -> None:
    rows = load_reference_grid_load_buses(grid_dir)
    assert [r["bus_i"] for r in rows] == ["2", "3"]
    assert [r["meter_id"] for r in rows] == ["ref_lv_bus_2", "ref_lv_bus_3"]
    assert all(r["bus"] == reference_bus_name(r["bus_i"]) for r in rows)


def test_topology_factory_reference_grid_spec(grid_dir: Path) -> None:
    assert parse_topology_spec(f"reference-grid:{grid_dir}") == (
        "reference-grid",
        str(grid_dir),
    )
    topo = load_topology_spec(f"reference-grid:{grid_dir}")
    assert len(topo.buses) == 3
    assert len(topo.lines) == 2

    # matpower: alias resolves to the same loader.
    topo_alias = load_topology_spec(f"matpower:{grid_dir}")
    assert len(topo_alias.buses) == 3


def test_missing_directory_raises(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        load_reference_grid_topology(tmp_path / "does_not_exist")
