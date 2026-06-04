"""Loader for CINELDI/MATPOWER-style low-voltage reference-grid folders."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from smart_meter_simulator.core.topology import (
    GridBus,
    GridLine,
    GridLoad,
    GridTopology,
)


REFERENCE_GRID_SOURCES = {"reference-grid", "reference_grid", "matpower"}


def reference_bus_name(bus_id: str | int) -> str:
    """Return the simulator bus name for a MATPOWER bus id."""
    text = str(bus_id).strip()
    if text.startswith("ref_lv_bus_"):
        return text
    return f"ref_lv_bus_{int(float(text))}"


def reference_meter_id(bus_id: str | int) -> str:
    """Return the default meter id for a reference-grid load bus."""
    return reference_bus_name(bus_id)


def load_reference_grid_topology(grid_dir: str | Path) -> GridTopology:
    """Load a low-voltage reference-grid CSV folder into ``GridTopology``.

    The folder is expected to contain the files distributed with the CINELDI
    low-voltage reference grids: ``mpc_bus.csv``, ``mpc_branch.csv``,
    ``mpc_base_mva.csv``, ``p_load.csv``, ``q_load.csv`` and optional extra
    branch/load-bus metadata.
    """
    path = Path(grid_dir)
    if not path.exists():
        raise FileNotFoundError(f"Reference grid directory not found: {path}")
    if not path.is_dir():
        raise NotADirectoryError(f"Reference grid path is not a directory: {path}")

    buses = _load_buses(path)
    base_mva = _load_base_mva(path)
    branches = _load_branches(path, buses, base_mva)
    loads = _load_static_loads(path)

    topology = GridTopology(
        source="reference-grid",
        source_path=str(path),
        buses=buses,
        lines=branches,
        loads=loads,
        pvs=[],
        metadata={
            "format": "matpower_csv",
            "base_mva": base_mva,
            "load_source": str(path / "p_load.csv"),
            "reactive_load_source": str(path / "q_load.csv"),
        },
    )
    return topology


def load_reference_grid_load_buses(grid_dir: str | Path) -> List[Dict[str, str]]:
    """Return load-bus metadata rows from a reference-grid folder."""
    path = Path(grid_dir)
    extra = _optional_file(path, "load_bus_extra.csv", "load_bus_data_extra.csv")
    if extra:
        rows = _read_dicts(extra)
        result: List[Dict[str, str]] = []
        for row in rows:
            bus_id = _field(row, "bus_i")
            if bus_id:
                result.append(
                    {
                        "bus_i": bus_id,
                        "bus": reference_bus_name(bus_id),
                        "meter_id": reference_meter_id(bus_id),
                        "consumer_type": _field(row, "Consumer type"),
                    }
                )
        return result

    p_load = path / "p_load.csv"
    header = _read_header(p_load)
    return [
        {
            "bus_i": bus_id,
            "bus": reference_bus_name(bus_id),
            "meter_id": reference_meter_id(bus_id),
            "consumer_type": "",
        }
        for bus_id in header[1:]
    ]


def _load_buses(path: Path) -> List[GridBus]:
    rows = _read_dicts(path / "mpc_bus.csv")
    buses: List[GridBus] = []
    for row in rows:
        bus_i = _field(row, "bus_i")
        bus_type = int(float(_field(row, "type", default="1") or "1"))
        nominal_voltage = _float(row, "basekV") * 1000.0
        properties = _clean_row(row)
        if bus_type == 3:
            properties["bustype"] = "SWING"
        buses.append(
            GridBus(
                name=reference_bus_name(bus_i),
                phases="ABCN",
                nominal_voltage=nominal_voltage,
                source_type="meter",
                properties=properties,
            )
        )
    return buses


def _load_base_mva(path: Path) -> float:
    rows = _read_dicts(path / "mpc_base_mva.csv")
    if not rows:
        raise ValueError(f"No base MVA row found in {path / 'mpc_base_mva.csv'}")
    value = _field(rows[0], "Base MVA") or next(iter(rows[0].values()))
    return float(value)


def _load_branches(
    path: Path, buses: Iterable[GridBus], base_mva: float
) -> List[GridLine]:
    rows = _read_dicts(path / "mpc_branch.csv")
    extra_rows = _load_branch_extra(path)
    bus_base_kv = {
        int(float(bus.properties.get("bus_i", "0"))): bus.nominal_voltage / 1000.0
        for bus in buses
    }

    lines: List[GridLine] = []
    for idx, row in enumerate(rows):
        fbus = _field(row, "fbus")
        tbus = _field(row, "tbus")
        fbus_id = int(float(fbus))
        tbus_id = int(float(tbus))
        from_bus = reference_bus_name(fbus_id)
        to_bus = reference_bus_name(tbus_id)
        extra = _match_branch_extra(extra_rows, idx, fbus_id, tbus_id)
        length_km = float(extra.get("Length [km]", "0") or 0.0)
        base_kv = bus_base_kv.get(fbus_id) or bus_base_kv.get(tbus_id) or 0.23
        z_base_ohm = (base_kv * base_kv) / base_mva
        resistance_ohm = _float(row, "r") * z_base_ohm
        reactance_ohm = _float(row, "x") * z_base_ohm
        length_for_impedance = max(length_km, 1e-9)
        properties = {
            **_clean_row(extra),
            **_clean_row(row),
            "base_mva": str(base_mva),
            "base_kv": str(base_kv),
            "resistance_ohm": str(resistance_ohm),
            "reactance_ohm": str(reactance_ohm),
        }
        lines.append(
            GridLine(
                name=f"Line_{idx}",
                from_bus=from_bus,
                to_bus=to_bus,
                length=length_km,
                length_unit="km",
                resistance_ohm_per_km=resistance_ohm / length_for_impedance,
                reactance_ohm_per_km=reactance_ohm / length_for_impedance,
                capacity_kw=_float(row, "rateA") * 1000.0,
                phases="ABCN",
                source_type="overhead_line",
                properties=properties,
            )
        )
    return lines


def _load_static_loads(path: Path) -> List[GridLoad]:
    p_rows = _read_dicts(path / "p_load.csv")
    q_path = path / "q_load.csv"
    q_rows = _read_dicts(q_path) if q_path.exists() else []
    if not p_rows:
        return []

    p_first = p_rows[0]
    q_first = q_rows[0] if q_rows else {}
    load_bus_ids = [name for name in p_first if name != "Date" and name.strip()]
    loads: List[GridLoad] = []
    for idx, bus_id in enumerate(load_bus_ids):
        p_va = float(p_first.get(bus_id) or 0.0) * 1_000_000.0
        q_var = float(q_first.get(bus_id) or 0.0) * 1_000_000.0
        loads.append(
            GridLoad(
                name=f"Load_{idx}",
                parent=reference_bus_name(bus_id),
                constant_power=complex(p_va, q_var),
                phases="ABCN",
                nominal_voltage=230.0,
                source_type="load",
                properties={
                    "source": "p_load.csv",
                    "bus_i": str(bus_id),
                    "initial_p_mw": str(p_first.get(bus_id) or 0.0),
                    "initial_q_mvar": str(q_first.get(bus_id) or 0.0),
                },
            )
        )
    return loads


def _load_branch_extra(path: Path) -> List[Dict[str, str]]:
    extra = _optional_file(path, "branch_extra.csv", "branch_data_extra.csv")
    return _read_dicts(extra) if extra else []


def _match_branch_extra(
    rows: List[Dict[str, str]], idx: int, fbus: int, tbus: int
) -> Dict[str, str]:
    if idx < len(rows):
        row = rows[idx]
        if _field(row, "From Bus") and _field(row, "To Bus"):
            return row
    for row in rows:
        from_bus = _field(row, "From Bus")
        to_bus = _field(row, "To Bus")
        if not from_bus or not to_bus:
            continue
        if int(float(from_bus)) == fbus and int(float(to_bus)) == tbus:
            return row
    return {}


def _optional_file(path: Path, *names: str) -> Optional[Path]:
    for name in names:
        candidate = path / name
        if candidate.exists():
            return candidate
    return None


def _read_header(path: Path) -> List[str]:
    with path.open(newline="", encoding="utf-8") as fh:
        return next(csv.reader(fh))


def _read_dicts(path: Path) -> List[Dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as fh:
        return [dict(row) for row in csv.DictReader(fh)]


def _field(row: Dict[str, Any], name: str, default: str = "") -> str:
    value = row.get(name, default)
    if value is None:
        return default
    return str(value).strip()


def _float(row: Dict[str, Any], name: str, default: float = 0.0) -> float:
    value = _field(row, name)
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _clean_row(row: Dict[str, Any]) -> Dict[str, str]:
    return {
        str(key).strip(): str(value).strip()
        for key, value in row.items()
        if str(key).strip() and value is not None
    }
