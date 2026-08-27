"""Export a pandapower network to a GridLAB-D (.glm) file.

Standalone dev utility. Load a pandapower net from a JSON file (``pp.to_json``
output) and emit a GLM topology this backend's parser can read back without
losing the electrical data.

Earlier revisions of this script emitted only bus/line *connectivity* -- no
impedance, no ratings, and no transformers -- so every exported line silently
fell back to the uniform ``LINE_RESISTANCE_OHM_PER_KM`` /
``LINE_REACTANCE_OHM_PER_KM`` defaults at build time. On an LV feeder that is
the difference between 0.125 ohm/km and the 0.2-3.1 ohm/km the conductors
actually have, i.e. voltage drop several times too optimistic. What is carried
through now:

* ``line_configuration`` per pandapower std_type, plus explicit
  ``resistance_ohm_per_km`` / ``reactance_ohm_per_km`` on each line (the
  per-line values take priority in the parser, so a line with no std_type is
  still exact);
* ``capacity_kw`` from ``max_i_ka`` (x ``parallel``, x derating factor ``df``);
* ``transformer`` + ``transformer_configuration`` from ``net.trafo``, which the
  old exporter dropped entirely -- without them every LV bus behind a
  transformer looked like it hung straight off the slack;
* bus-to-bus switches from ``net.switch``, as controllable GLM ``switch`` edges;
* out-of-service elements are skipped rather than exported as live edges.

Note the voltage convention: pandapower ``vn_kv`` is line-to-line, and it is
written to ``nominal_voltage`` as-is (x1000), which GridLAB-D reads as
line-to-neutral. That matches the reference model shipped in
``data/grids/grid_bus_network.glm``; the ratio a transformer sees comes from the
two buses' ``nominal_voltage``, so both sides share the convention and the ratio
is right.

One caveat this export cannot fix: ``length`` is whatever the net carries. A net
that encodes impedance in **ohm** with ``length_km = 1`` -- which is what CINELDI's
own ``creategrid.py`` builds -- exports every line as a 1 km placeholder. The
electrical model is exact (the parser multiplies ohm/km by length), but the
geometry is meaningless, because the physical lengths live in ``branch_extra.csv``
and never reach pandapower.

For the CINELDI LV reference grids specifically, prefer
``scripts/regen_reference_glm.py``: it reads the published CSVs directly and
keeps the per-branch values exactly, with no pandapower round-trip in between.

Usage::

    uv run python scripts/export_glm.py --net mynet.json --output grid.glm
"""

import argparse
import math
import re
from typing import Dict, List, Optional

import pandas as pd

FT_PER_KM = 3280.84
SQRT3 = math.sqrt(3.0)


def _is_true(value, default: bool = True) -> bool:
    """pandapower's in_service/closed columns may be missing or NaN."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return default
    return bool(value)


def _num(value, default: float = 0.0) -> float:
    if value is None or pd.isna(value):
        return default
    return float(value)


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", str(text).strip().lower()).strip("_")


def bus_names(net) -> Dict[int, str]:
    """Map bus index -> GLM name, falling back to Bus_<idx> for unnamed buses."""
    names: Dict[int, str] = {}
    for idx, bus in net.bus.iterrows():
        name = bus["name"] if "name" in bus and pd.notna(bus["name"]) else None
        names[idx] = str(name) if name else f"Bus_{idx}"
    return names


def line_capacity_kw(line, vn_kv: float) -> float:
    """Thermal rating in kVA (== kW at unity pf) from max_i_ka.

    S = sqrt(3) * V_LL * I, scaled by the number of parallel circuits and the
    derating factor pandapower keeps in ``df``.
    """
    max_i_ka = _num(line.get("max_i_ka"))
    if max_i_ka <= 0 or vn_kv <= 0:
        return 0.0
    parallel = _num(line.get("parallel"), 1.0) or 1.0
    derating = _num(line.get("df"), 1.0) or 1.0
    return SQRT3 * vn_kv * max_i_ka * 1000.0 * parallel * derating


def transformer_pu(trafo) -> tuple:
    """(rating_kVA, R_pu, X_pu) for a transformer_configuration block."""
    sn_mva = _num(trafo.get("sn_mva"))
    vk = _num(trafo.get("vk_percent")) / 100.0
    vkr = _num(trafo.get("vkr_percent")) / 100.0
    x_pu = math.sqrt(max(vk**2 - vkr**2, 0.0))
    return sn_mva * 1000.0, vkr, x_pu


def export_to_glm(net, output_path: str) -> Dict[str, int]:
    """Export a pandapower network to a GridLAB-D (.glm) file."""
    out: List[str] = []
    w = out.append
    names = bus_names(net)
    counts = {
        "buses": 0,
        "lines": 0,
        "transformers": 0,
        "switches": 0,
        "loads": 0,
        "sgens": 0,
        "skipped": 0,
    }

    w("// Generated GridLAB-D model from Pandapower")
    w("// Impedance is carried per line (ohm/km); capacity_kw comes from max_i_ka.")
    w("// nominal_voltage holds pandapower's line-to-line vn_kv; transformer ratios")
    w("// are derived from the two buses, so the convention cancels out.")
    w("module powerflow;")
    w("")

    # ---- line configurations, one per std_type ------------------------------
    configs: Dict[str, str] = {}
    if "line" in net and not net.line.empty:
        for _, line in net.line.iterrows():
            std_type = line.get("std_type")
            if std_type is None or pd.isna(std_type) or not str(std_type).strip():
                continue
            key = str(std_type)
            if key in configs:
                continue
            config = f"lc_{_slug(key)}"
            configs[key] = config
            r = _num(line.get("r_ohm_per_km"))
            x = _num(line.get("x_ohm_per_km"))
            w("object line_configuration {")
            w(f'    name "{config}";')
            w(f"    z11 {r:.10g}+{x:.10g}j ohm/km;")
            w(f"    resistance_ohm_per_km {r:.10g};")
            w(f"    reactance_ohm_per_km {x:.10g};")
            w("    impedance_length_unit km;")
            w(f"    // pandapower std_type {key}")
            w("}")
            w("")

    # ---- buses --------------------------------------------------------------
    for idx, bus in net.bus.iterrows():
        if not _is_true(bus.get("in_service")):
            counts["skipped"] += 1
            continue
        w("object node {")
        w(f'    name "{names[idx]}";')
        w("    phases ABCN;")
        w(f"    nominal_voltage {_num(bus['vn_kv']) * 1000:.2f};")
        w("}")
        w("")
        counts["buses"] += 1

    # ---- lines --------------------------------------------------------------
    if "line" in net and not net.line.empty:
        for idx, line in net.line.iterrows():
            if not _is_true(line.get("in_service")):
                counts["skipped"] += 1
                continue
            from_bus, to_bus = int(line.from_bus), int(line.to_bus)
            vn_kv = _num(net.bus.at[from_bus, "vn_kv"])
            length_km = _num(line.get("length_km"))
            w("object overhead_line {")
            w(f'    name "Line_{idx}";')
            w("    phases ABCN;")
            w(f'    from "{names[from_bus]}";')
            w(f'    to "{names[to_bus]}";')
            w(f"    length {length_km * FT_PER_KM:.2f} ft;")
            std_type = line.get("std_type")
            if std_type is not None and pd.notna(std_type) and str(std_type) in configs:
                w(f'    configuration "{configs[str(std_type)]}";')
            # 10 significant digits, not fixed decimals: a net that encodes impedance
            # in ohm with length_km=1 has values down to ~1e-3, where %.6f would
            # keep only two significant digits.
            w(f"    resistance_ohm_per_km {_num(line.get('r_ohm_per_km')):.10g};")
            w(f"    reactance_ohm_per_km {_num(line.get('x_ohm_per_km')):.10g};")
            w("    impedance_length_unit km;")
            capacity = line_capacity_kw(line, vn_kv)
            if capacity > 0:
                w(f"    capacity_kw {capacity:.2f};")
            w(f"    // {length_km * 1000:.1f} m")
            w("}")
            w("")
            counts["lines"] += 1

    # ---- transformers -------------------------------------------------------
    if "trafo" in net and not net.trafo.empty:
        for idx, trafo in net.trafo.iterrows():
            if not _is_true(trafo.get("in_service")):
                counts["skipped"] += 1
                continue
            name = trafo.get("name")
            name = str(name) if pd.notna(name) and str(name).strip() else f"Trafo_{idx}"
            rating_kva, r_pu, x_pu = transformer_pu(trafo)
            hv, lv = int(trafo.hv_bus), int(trafo.lv_bus)
            if rating_kva > 0:
                w("object transformer_configuration {")
                w(f'    name "{_slug(name)}_cfg";')
                w("    connect_type WYE_WYE;")
                w(f"    power_rating {rating_kva:.2f};")
                w(f"    primary_voltage {_num(net.bus.at[hv, 'vn_kv']) * 1000:.2f};")
                w(f"    secondary_voltage {_num(net.bus.at[lv, 'vn_kv']) * 1000:.2f};")
                w(f"    resistance {r_pu:.10g};")
                w(f"    reactance {x_pu:.10g};")
                w("}")
                w("")
            w("object transformer {")
            w(f'    name "{name}";')
            w("    phases ABCN;")
            w(f'    from "{names[hv]}";')
            w(f'    to "{names[lv]}";')
            if rating_kva > 0:
                w(f'    configuration "{_slug(name)}_cfg";')
            w("}")
            w("")
            counts["transformers"] += 1

    # ---- bus-to-bus switches ------------------------------------------------
    # Only et == "b" switches are real edges; line/trafo switches are terminal
    # breakers on an element already exported above.
    if "switch" in net and not net.switch.empty:
        for idx, switch in net.switch.iterrows():
            if str(switch.get("et")) != "b":
                continue
            bus, element = int(switch.bus), int(switch.element)
            name = switch.get("name")
            name = (
                str(name) if pd.notna(name) and str(name).strip() else f"Switch_{idx}"
            )
            w("object switch {")
            w(f'    name "{name}";')
            w("    phases ABCN;")
            w(f'    from "{names[bus]}";')
            w(f'    to "{names[element]}";')
            w(f"    status {'CLOSED' if _is_true(switch.get('closed')) else 'OPEN'};")
            w("}")
            w("")
            counts["switches"] += 1

    # ---- loads --------------------------------------------------------------
    if "load" in net and not net.load.empty:
        for idx, load in net.load.iterrows():
            if not _is_true(load.get("in_service")):
                counts["skipped"] += 1
                continue
            bus = int(load.bus)
            scaling = _num(load.get("scaling"), 1.0) or 1.0
            p_va = _num(load.get("p_mw")) * 1e6 * scaling
            q_var = _num(load.get("q_mvar")) * 1e6 * scaling
            w("object load {")
            w(f'    name "Load_{idx}";')
            w(f'    parent "{names[bus]}";')
            w("    phases ABCN;")
            # Sign-aware: a literal "+" in front of a negative value yields "+-500.0j",
            # which the parser cannot read and silently turns into 0j.
            w(f"    constant_power_A {p_va:.1f}{q_var:+.1f}j;")
            w(f"    nominal_voltage {_num(net.bus.at[bus, 'vn_kv']) * 1000:.2f};")
            w("}")
            w("")
            counts["loads"] += 1

    # ---- static generators, as negative loads -------------------------------
    # A pandapower sgen is not necessarily PV, so it stays a negative load. Author
    # an inverter+solar pair by hand (see the glm-topology-authoring skill) when
    # the generation really is PV and should count towards pv_capacity_kw.
    if "sgen" in net and not net.sgen.empty:
        for idx, sgen in net.sgen.iterrows():
            if not _is_true(sgen.get("in_service")):
                counts["skipped"] += 1
                continue
            bus = int(sgen.bus)
            scaling = _num(sgen.get("scaling"), 1.0) or 1.0
            p_va = -_num(sgen.get("p_mw")) * 1e6 * scaling
            q_var = -_num(sgen.get("q_mvar")) * 1e6 * scaling
            w("object load { // negative load for pandapower sgen")
            w(f'    name "Sgen_{idx}";')
            w(f'    parent "{names[bus]}";')
            w("    phases ABCN;")
            # Sign-aware: a literal "+" in front of a negative value yields "+-500.0j",
            # which the parser cannot read and silently turns into 0j.
            w(f"    constant_power_A {p_va:.1f}{q_var:+.1f}j;")
            w(f"    nominal_voltage {_num(net.bus.at[bus, 'vn_kv']) * 1000:.2f};")
            w("}")
            w("")
            counts["sgens"] += 1

    with open(output_path, "w") as handle:
        handle.write("\n".join(out))
    return counts


def main() -> None:
    parser = argparse.ArgumentParser(description="Export a pandapower net to GLM.")
    parser.add_argument(
        "--net", required=True, help="Path to a pandapower JSON network (pp.to_json)."
    )
    parser.add_argument(
        "--output", default="exported_grid.glm", help="Output .glm path."
    )
    args = parser.parse_args()

    import pandapower as pp

    net = pp.from_json(args.net)
    counts = export_to_glm(net, args.output)
    summary = ", ".join(f"{v} {k}" for k, v in counts.items() if k != "skipped" and v)
    print(f"Exported {summary} to {args.output}")
    if counts["skipped"]:
        print(f"  skipped {counts['skipped']} out-of-service element(s)")


if __name__ == "__main__":
    main()
