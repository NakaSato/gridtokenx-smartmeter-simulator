"""Export a pandapower network to a GridLAB-D (.glm) file.

Standalone dev utility. Load a pandapower net from a JSON file (``pp.to_json``
output) and emit an approximate GLM topology (nodes, overhead_lines, loads, and
sgens mapped to negative loads).

Usage::

    uv run python scripts/export_glm.py --net mynet.json --output grid.glm
"""

import argparse

import pandapower as pp
import pandas as pd


def export_to_glm(net, output_path: str) -> None:
    """Export a basic pandapower network to a GridLAB-D (.glm) file.

    Supports basic mapping of buses, lines, loads, and sgens.
    """
    lines = []
    lines.append("// Generated GridLAB-D model from Pandapower")
    lines.append("module powerflow;")
    lines.append("")

    # Export Buses -> Nodes
    for idx, bus in net.bus.iterrows():
        bus_name = (
            bus["name"] if "name" in bus and pd.notna(bus["name"]) else f"Bus_{idx}"
        )
        vn_kv = bus["vn_kv"] * 1000  # Convert to Volts
        lines.append("object node {")
        lines.append(f'    name "{bus_name}";')
        lines.append("    phases ABCN;")
        lines.append(f"    nominal_voltage {vn_kv:.2f};")
        lines.append("}")
        lines.append("")

    # Export Lines -> overhead_line
    for idx, line in net.line.iterrows():
        from_bus = net.bus.loc[line.from_bus, "name"]
        if pd.isna(from_bus):
            from_bus = f"Bus_{line.from_bus}"
        to_bus = net.bus.loc[line.to_bus, "name"]
        if pd.isna(to_bus):
            to_bus = f"Bus_{line.to_bus}"

        lines.append("object overhead_line {")
        lines.append(f'    name "Line_{idx}";')
        lines.append("    phases ABCN;")
        lines.append(f'    from "{from_bus}";')
        lines.append(f'    to "{to_bus}";')
        lines.append(f"    length {line.length_km * 3280.84:.2f}; // km to ft")
        lines.append("}")
        lines.append("")

    # Export Loads
    for idx, load in net.load.iterrows():
        bus_name = net.bus.loc[load.bus, "name"]
        if pd.isna(bus_name):
            bus_name = f"Bus_{load.bus}"

        q_var = load.q_mvar * 1e6 if pd.notna(load.q_mvar) else 0
        lines.append("object load {")
        lines.append(f'    name "Load_{idx}";')
        lines.append(f'    parent "{bus_name}";')
        lines.append("    phases ABCN;")
        lines.append(f"    constant_power_A {load.p_mw * 1e6}+{q_var}j;")
        lines.append(
            f'    nominal_voltage {net.bus.loc[load.bus, "vn_kv"] * 1000:.2f};'
        )
        lines.append("}")
        lines.append("")

    # Export Generators (sgen) as negative loads
    if "sgen" in net and not net.sgen.empty:
        for idx, sgen in net.sgen.iterrows():
            bus_name = net.bus.loc[sgen.bus, "name"]
            if pd.isna(bus_name):
                bus_name = f"Bus_{sgen.bus}"

            p_va = -sgen.p_mw * 1e6
            q_var = -sgen.q_mvar * 1e6 if pd.notna(sgen.q_mvar) else 0
            lines.append("object load { // Using negative load for sgen")
            lines.append(f'    name "Sgen_{idx}";')
            lines.append(f'    parent "{bus_name}";')
            lines.append("    phases ABCN;")
            lines.append(f"    constant_power_A {p_va}+{q_var}j;")
            lines.append(
                f'    nominal_voltage {net.bus.loc[sgen.bus, "vn_kv"] * 1000:.2f};'
            )
            lines.append("}")
            lines.append("")

    with open(output_path, "w") as f:
        f.write("\n".join(lines))
    print(
        f"Exported {len(net.bus)} buses, {len(net.line)} lines, "
        f"{len(net.load)} loads to {output_path}"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Export a pandapower net to GLM.")
    parser.add_argument(
        "--net", required=True, help="Path to a pandapower JSON network (pp.to_json)."
    )
    parser.add_argument(
        "--output", default="exported_grid.glm", help="Output .glm path."
    )
    args = parser.parse_args()

    net = pp.from_json(args.net)
    export_to_glm(net, args.output)
    print(f"Successfully exported to {args.output}")


if __name__ == "__main__":
    main()
