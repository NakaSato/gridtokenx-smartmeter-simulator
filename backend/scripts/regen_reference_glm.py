"""Regenerate ``grid_bus_network.glm`` from the CINELDI LV reference-grid CSVs.

The shipped GLM was produced by ``scripts/export_glm.py`` from a pandapower net and
then hand-edited. That export path drops the two things a power-flow actually needs:
per-branch **impedance** (no ``line_configuration`` was emitted at all, so every line
fell back to the uniform ``LINE_RESISTANCE_OHM_PER_KM``/``LINE_REACTANCE_OHM_PER_KM``
defaults) and the **thermal rating** ``rateA``. On a 230 V IT network that matters:
the real conductors run 0.13-3.08 ohm/km against a 0.125 ohm/km fallback, so voltage
drop came out 2-10x optimistic.

This script rebuilds the same model straight from the MATPOWER-style CSVs, keeping
every hand-edit that the simulator depends on (see MODEL_EDITS below) and adding:

* exact per-branch ``resistance_ohm_per_km`` / ``reactance_ohm_per_km``, converted
  out of per-unit with Zbase = basekV^2 / baseMVA;
* ``capacity_kw`` from ``rateA``;
* three nominal ``line_configuration`` objects (one per conductor type) so the file
  is still readable by real GridLAB-D tooling -- the per-line explicit values win in
  this backend's parser, so the configs cost nothing in fidelity;
* ``transformer_configuration`` for the three PCC transformers, sized from the zone's
  own peak demand and PV.

Usage::

    uv run python scripts/regen_reference_glm.py \
        --grid-dir ../../../cineldi_lv_reference_system/lv_reference_grids/80_bus_rural_reference_grid \
        --output src/smart_meter_simulator/data/grids/grid_bus_network.glm

Validate afterwards::

    uv run cli --mode validate-topology --grid-topology glm:<output>
"""

from __future__ import annotations

import argparse
import collections
import csv
import math
from pathlib import Path
from typing import Dict, List, Optional, Tuple

FT_PER_KM = 3280.84

# --------------------------------------------------------------------------------
# Hand-edits carried over from the shipped GLM. These are deliberate departures from
# the CINELDI dataset, not artifacts of the export -- keep them in sync with the
# header comment written into the .glm.
# --------------------------------------------------------------------------------

# Bus 1 is an LV busbar (0.23 kV) in CINELDI. Here it is promoted to the MV substation
# busbar so the three feeders hanging off it become transformer-coupled microgrid zones.
MV_BUS = "1"
MV_VOLTAGE_V = 12700.00  # L-N; ~22 kV L-L on ABCN, matching TRANSFORMER_MV_KV

# CINELDI branches that become MV/LV transformers (the PCC each zone is islanded at).
# Keyed by mpc_branch row index -> transformer name.
PCC_BRANCHES: Dict[int, str] = {1: "pcc_1", 9: "pcc_2", 34: "pcc_3"}

# CINELDI has four feeders off bus 1; the fourth (78/79/80, a short DER-less stub) is
# re-parented onto zone 3 so the loader's line-only partition yields three zones.
# The stub used to reach bus 1 over its own service cable and bus 61 over another, so
# the re-parented segment is the two cables in series -- hence the third element, the
# mpc_branch row whose impedance and length are merged in.
# mpc_branch row index -> (new from, new to, row to splice in series).
REPARENT_BRANCHES: Dict[int, Tuple[str, str, Optional[int]]] = {54: ("61", "78", 34)}

# PV fleet added on top of the CINELDI dataset (which has no DER).
PV_BUSES: List[int] = [4, 10, 20, 27, 28, 29, 31, 32, 33, 48, 49, 56, 60, 62, 70]
PV_RATED_POWER_W = 10000.0
PV_INVERTER_EFFICIENCY = 0.96
PV_PANEL_EFFICIENCY = 0.20
PV_AREA_SF = 538.20

# Load snapshot taken from the p_load/q_load time series.
DEFAULT_SNAPSHOT = "2021-01-01 00:00:00"

# Standard Norwegian distribution-transformer sizes (kVA).
STANDARD_KVA = [50, 100, 200, 315, 500, 800, 1000]
# Short-circuit impedance assumed for a rural pole-mounted unit.
XFMR_VK_PERCENT = 4.0
XFMR_VKR_BY_KVA = {50: 1.9, 100: 1.6, 200: 1.3, 315: 1.2}
XFMR_SIZING_MARGIN = 1.25


def _read_dicts(path: Path) -> List[Dict[str, str]]:
    with path.open(newline="") as handle:
        return list(csv.DictReader(handle))


def _f(value: Optional[str]) -> Optional[float]:
    """Parse a float, returning None for the blank cells the dataset ships."""
    try:
        return float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None


def bus_name(bus_id: str | int) -> str:
    return f"ref_lv_bus_{int(float(str(bus_id)))}"


class Grid:
    """The CINELDI reference-grid CSVs, with per-unit values resolved to SI."""

    def __init__(self, grid_dir: Path):
        self.dir = grid_dir
        self.buses = _read_dicts(grid_dir / "mpc_bus.csv")
        self.branches = _read_dicts(grid_dir / "mpc_branch.csv")
        self.base_mva = float(
            (grid_dir / "mpc_base_mva.csv").read_text().strip().splitlines()[1]
        )
        extra_path = grid_dir / "branch_extra.csv"
        if not extra_path.exists():
            extra_path = grid_dir / "branch_data_extra.csv"
        self.branch_extra = _read_dicts(extra_path)
        if len(self.branch_extra) != len(self.branches):
            raise ValueError(
                f"branch extra rows ({len(self.branch_extra)}) != "
                f"mpc_branch rows ({len(self.branches)})"
            )
        self.p_load = _read_dicts(grid_dir / "p_load.csv")
        self.q_load = _read_dicts(grid_dir / "q_load.csv")
        self.load_buses = [c for c in self.p_load[0] if c != "Date"]

        self.base_kv = float(self.buses[0]["basekV"])
        self.z_base = self.base_kv**2 / self.base_mva

    def branch_rows(self):
        """Yield (index, from, to, length_km, conductor, r_ohm_km, x_ohm_km, kva)."""
        for idx, (branch, extra) in enumerate(zip(self.branches, self.branch_extra)):
            length_km = float(extra["Length [km]"])
            conductor = extra["Branch type"]
            r_pu, x_pu = float(branch["r"]), float(branch["x"])
            rate_mva = _f(branch["rateA"])
            yield (
                idx,
                branch["fbus"],
                branch["tbus"],
                length_km,
                conductor,
                r_pu * self.z_base / length_km,
                x_pu * self.z_base / length_km,
                None if rate_mva is None else rate_mva * 1000.0,
            )

    def snapshot(self, timestamp: str) -> Dict[str, Tuple[float, float]]:
        """Return {bus_id: (P_watt, Q_var)} at one timestamp of the load series."""
        p_row = next((r for r in self.p_load if r["Date"] == timestamp), None)
        q_row = next((r for r in self.q_load if r["Date"] == timestamp), None)
        if p_row is None or q_row is None:
            raise KeyError(f"timestamp {timestamp!r} not found in p_load/q_load")
        return {
            bus: (float(p_row[bus]) * 1e6, float(q_row[bus]) * 1e6)
            for bus in self.load_buses
        }

    def zone_members(self) -> Dict[str, set]:
        """Buses behind each PCC transformer, after the feeder re-parenting."""
        adjacency = collections.defaultdict(set)
        for idx, branch in enumerate(self.branches):
            if idx in PCC_BRANCHES:
                continue
            frm, to, _ = REPARENT_BRANCHES.get(
                idx, (branch["fbus"], branch["tbus"], None)
            )
            adjacency[frm].add(to)
            adjacency[to].add(frm)

        zones: Dict[str, set] = {}
        for idx, name in PCC_BRANCHES.items():
            branch = self.branches[idx]
            root = branch["tbus"] if branch["fbus"] == MV_BUS else branch["fbus"]
            seen, stack = {root}, [root]
            while stack:
                node = stack.pop()
                for neighbour in adjacency[node]:
                    if neighbour not in seen:
                        seen.add(neighbour)
                        stack.append(neighbour)
            zones[name] = seen
        return zones

    def zone_peak_kva(self, members: set) -> float:
        cols = [c for c in self.load_buses if c in members]
        if not cols:
            return 0.0
        return max(
            math.hypot(
                sum(float(pr[c]) for c in cols), sum(float(qr[c]) for c in cols)
            )
            for pr, qr in zip(self.p_load, self.q_load)
        ) * 1000.0


def resolve_ratings(rows: List[tuple]) -> Tuple[Dict[int, float], Dict[int, str]]:
    """Return {row: rating_kva} for every branch, filling the blank rateA cells.

    The dataset leaves rateA blank on a few branches. The rating is not a pure
    function of the conductor label (all three types carry a mix of 37.85/55.77/
    87.64 kVA), so the modal value for the type is the best available estimate --
    and every fill is recorded so the caller can report it rather than apply it
    silently.
    """
    by_conductor = collections.defaultdict(collections.Counter)
    for _, _, _, _, conductor, _, _, kva in rows:
        if kva is not None:
            by_conductor[conductor][round(kva, 2)] += 1

    ratings: Dict[int, float] = {}
    estimated: Dict[int, str] = {}
    for idx, frm, to, _, conductor, _, _, kva in rows:
        if kva is not None:
            ratings[idx] = kva
            continue
        counter = by_conductor.get(conductor)
        if not counter:
            continue
        value = counter.most_common(1)[0][0]
        ratings[idx] = value
        estimated[idx] = (
            f"branch {frm}-{to} ({conductor}): rateA blank in source, "
            f"filled with the modal {conductor} rating {value:.2f} kVA"
        )
    return ratings, estimated


def size_transformer(peak_kva: float, pv_kw: float) -> Tuple[int, float, float]:
    """Pick a standard kVA size and its per-unit R/X for a PCC transformer."""
    required = max(peak_kva, pv_kw) * XFMR_SIZING_MARGIN
    rating = next((k for k in STANDARD_KVA if k >= required), STANDARD_KVA[-1])
    vkr = XFMR_VKR_BY_KVA.get(rating, 1.2)
    r_pu = vkr / 100.0
    x_pu = math.sqrt(max((XFMR_VK_PERCENT / 100.0) ** 2 - r_pu**2, 0.0))
    return rating, r_pu, x_pu


def build_glm(grid: Grid, snapshot: str) -> Tuple[str, List[str]]:
    rows = list(grid.branch_rows())
    by_index = {r[0]: r for r in rows}
    ratings, estimated = resolve_ratings(rows)
    notes: List[str] = []
    loads = grid.snapshot(snapshot)
    zones = grid.zone_members()

    out: List[str] = []
    w = out.append

    conductors = sorted({r[4] for r in rows})
    config_name = {
        c: "lc_" + c.lower().replace(" ", "_").replace("x", "x") for c in conductors
    }

    # ---- header -------------------------------------------------------------
    w("// Generated GridLAB-D model from the CINELDI LV reference grid")
    w(f"// Source: {grid.dir}")
    w(f"// Regenerated by scripts/regen_reference_glm.py -- do not hand-edit;")
    w("// change the constants in that script and re-run instead.")
    w("//")
    w(f"// Base: {grid.base_kv:.2f} kV L-L, {grid.base_mva:.6f} MVA "
      f"-> Zbase {grid.z_base:.4f} ohm. Per-branch r/x are carried through exactly")
    w("// as resistance_ohm_per_km / reactance_ohm_per_km on each line; the")
    w("// line_configuration objects hold the nominal per-conductor values and exist")
    w("// for real GridLAB-D tooling (the explicit per-line values take priority in")
    w("// this backend's parser). capacity_kw comes from the MATPOWER rateA column.")
    w("//")
    w(f"// {bus_name(MV_BUS)} is the MV substation busbar ({MV_VOLTAGE_V/1000:.1f} kV L-N")
    w("// -> ~22 kV L-L on ABCN, matching TRANSFORMER_MV_KV). Its LV network hangs off")
    w("// three distribution transformers (pcc_1..pcc_3) rather than lines, which is")
    w("// what makes each group a microgrid zone: the loader partitions on the line-only")
    w("// graph, so everything behind a transformer is one zone, and that transformer is")
    w("// the PCC tripped to island it. Zone codes come from the transformer names (1..3)")
    w("// -- keep them below IOT_NUM_ZONES (default 10) or the parent bridge hashes them")
    w("// to an arbitrary zone_<n> stream instead of routing them.")
    w("//")
    w("// The grid has four physical feeders; the fourth (ref_lv_bus_78/79/80, a short")
    w("// DER-less stub) is served from zone 3 over Line_54 instead of taking its own")
    w("// PCC, so the model has three zones.")
    w("//")
    w(f"// Loads are the {snapshot} snapshot of p_load/q_load (VA), not a time series.")
    w(f"// PV ({len(PV_BUSES)} x {PV_RATED_POWER_W/1000:.0f} kW) is added on top of the")
    w("// dataset, which ships no DER.")
    w("module powerflow;")
    w("module generators;")
    w("")

    # ---- line configurations ------------------------------------------------
    w("// ---- conductor types (nominal; per-line values below take priority) ----")
    for conductor in conductors:
        members = [r for r in rows if r[4] == conductor]
        r_nom = sum(m[5] for m in members) / len(members)
        x_nom = sum(m[6] for m in members) / len(members)
        w("object line_configuration {")
        w(f'    name "{config_name[conductor]}";')
        w(f"    z11 {r_nom:.10g}+{x_nom:.10g}j ohm/km;")
        w(f"    resistance_ohm_per_km {r_nom:.10g};")
        w(f"    reactance_ohm_per_km {x_nom:.10g};")
        w("    impedance_length_unit km;")
        w(f"    // {conductor}, mean over {len(members)} branches")
        w("}")
        w("")

    # ---- buses --------------------------------------------------------------
    w("// ---- buses ----")
    for bus in grid.buses:
        bus_id = bus["bus_i"]
        voltage = MV_VOLTAGE_V if bus_id == MV_BUS else float(bus["basekV"]) * 1000
        w("object meter {")
        w(f'    name "{bus_name(bus_id)}";')
        w("    phases ABCN;")
        w(f"    nominal_voltage {voltage:.2f};")
        w("}")
        w("")

    # ---- transformers -------------------------------------------------------
    w("// ---- PCC transformers (CINELDI LV branches promoted to MV/LV units) ----")
    for idx, name in PCC_BRANCHES.items():
        branch = grid.branches[idx]
        lv_bus = branch["tbus"] if branch["fbus"] == MV_BUS else branch["fbus"]
        members = zones[name]
        peak_kva = grid.zone_peak_kva(members)
        pv_kw = sum(PV_RATED_POWER_W / 1000 for b in PV_BUSES if str(b) in members)
        rating, r_pu, x_pu = size_transformer(peak_kva, pv_kw)
        w("object transformer_configuration {")
        w(f'    name "{name}_cfg";')
        w("    connect_type WYE_WYE;")
        w(f"    power_rating {rating};")
        w(f"    primary_voltage {MV_VOLTAGE_V:.2f};")
        w(f"    secondary_voltage {grid.base_kv * 1000:.2f};")
        w(f"    resistance {r_pu:.5f};")
        w(f"    reactance {x_pu:.5f};")
        w(f"    // sized for zone peak {peak_kva:.1f} kVA / PV {pv_kw:.0f} kW")
        w(f"    // x {XFMR_SIZING_MARGIN} -> next standard size")
        w("}")
        w("")
        w("object transformer {")
        w(f'    name "{name}";')
        w("    phases ABCN;")
        w(f'    from "{bus_name(MV_BUS)}";')
        w(f'    to "{bus_name(lv_bus)}";')
        w(f'    configuration "{name}_cfg";')
        w(f"    // replaces CINELDI branch {branch['fbus']}-{branch['tbus']} "
          f"({float(grid.branch_extra[idx]['Length [km]']) * 1000:.1f} m cable)")
        w("}")
        w("")

    # ---- lines --------------------------------------------------------------
    w("// ---- lines ----")
    for idx, frm, to, length_km, conductor, r_km, x_km, kva in rows:
        if idx in PCC_BRANCHES:
            continue
        spliced: Optional[int] = None
        if idx in REPARENT_BRANCHES:
            frm, to, spliced = REPARENT_BRANCHES[idx]
        rating = ratings.get(idx)
        if idx in estimated:
            notes.append(f"Line_{idx}: {estimated[idx]}")
        if spliced is not None:
            # Series-combine in ohms, then re-normalise over the combined length.
            other = by_index[spliced]
            r_ohm = r_km * length_km + other[5] * other[3]
            x_ohm = x_km * length_km + other[6] * other[3]
            length_km += other[3]
            r_km, x_km = r_ohm / length_km, x_ohm / length_km
            if spliced in estimated:
                notes.append(f"Line_{idx} (spliced): {estimated[spliced]}")
            other_rating = ratings.get(spliced)
            if other_rating is not None:
                rating = other_rating if rating is None else min(rating, other_rating)
            conductor_note = (
                f"{conductor} + {other[4]}, {length_km * 1000:.1f} m "
                f"(CINELDI branches {idx} and {spliced} in series)"
            )
        else:
            conductor_note = f"{conductor}, {length_km * 1000:.1f} m"
        w("object overhead_line {")
        w(f'    name "Line_{idx}";')
        w("    phases ABCN;")
        w(f'    from "{bus_name(frm)}";')
        w(f'    to "{bus_name(to)}";')
        w(f"    length {length_km * FT_PER_KM:.2f} ft;")
        w(f'    configuration "{config_name[conductor]}";')
        w(f"    resistance_ohm_per_km {r_km:.10g};")
        w(f"    reactance_ohm_per_km {x_km:.10g};")
        w("    impedance_length_unit km;")
        if rating is not None:
            suffix = "" if kva is not None else "  // estimated: rateA blank in source"
            w(f"    capacity_kw {rating:.2f};{suffix}")
        w(f"    // {conductor_note}")
        w("}")
        w("")

    # ---- loads --------------------------------------------------------------
    w(f"// ---- loads ({snapshot} snapshot, VA) ----")
    for order, bus_id in enumerate(grid.load_buses):
        p_watt, q_var = loads[bus_id]
        w("object load {")
        w(f'    name "Load_{order}";')
        w(f'    parent "{bus_name(bus_id)}";')
        w("    phases ABCN;")
        # Sign-aware: "+" before a negative value would yield "+-1.0j", which the
        # parser reads as 0j. CINELDI ships no negative Q, but do not rely on it.
        w(f"    constant_power_A {p_watt:.1f}{q_var:+.1f}j;")
        w(f"    nominal_voltage {grid.base_kv * 1000:.2f};")
        w("}")
        w("")

    # ---- PV -----------------------------------------------------------------
    w("// ---- PV (inverter first, solar parented to it) ----")
    for bus_id in PV_BUSES:
        name = bus_name(bus_id)
        w("object inverter {")
        w(f'    name "PV_Inverter_{name}";')
        w(f'    parent "{name}";')
        w("    phases ABCN;")
        w("    generator_status ONLINE;")
        w("    generator_mode SUPPLY_DRIVEN;")
        w("    inverter_type FOUR_QUADRANT;")
        w("    four_quadrant_control_mode CONSTANT_PF;")
        w(f"    rated_power {PV_RATED_POWER_W:.1f};")
        w(f"    inverter_efficiency {PV_INVERTER_EFFICIENCY:.2f};")
        w("    power_factor 1.0;")
        w("}")
        w("")
        w("object solar {")
        w(f'    name "PV_{name}";')
        w(f'    parent "PV_Inverter_{name}";')
        w("    phases ABCN;")
        w("    generator_mode SUPPLY_DRIVEN;")
        w("    generator_status ONLINE;")
        w("    panel_type SINGLE_CRYSTAL_SILICON;")
        w("    SOLAR_POWER_MODEL FLATPLATE;")
        w("    SOLAR_TILT_MODEL SOLPOS;")
        w("    orientation FIXED_AXIS;")
        w("    tilt_angle 15.0;")
        w("    orientation_azimuth 180.0;")
        w(f"    efficiency {PV_PANEL_EFFICIENCY:.2f};")
        w(f"    area {PV_AREA_SF:.2f} sf;")
        w("}")
        w("")

    return "\n".join(out), notes


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Regenerate the reference GLM from CINELDI CSVs."
    )
    parser.add_argument("--grid-dir", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--snapshot", default=DEFAULT_SNAPSHOT)
    args = parser.parse_args()

    grid = Grid(args.grid_dir)
    text, notes = build_glm(grid, args.snapshot)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(text)

    n_lines = len(grid.branches) - len(PCC_BRANCHES)
    print(
        f"Wrote {args.output}: {len(grid.buses)} buses, {n_lines} lines, "
        f"{len(PCC_BRANCHES)} transformers, {len(grid.load_buses)} loads, "
        f"{len(PV_BUSES)} PV."
    )
    for note in notes:
        print(f"  estimated: {note}")


if __name__ == "__main__":
    main()
