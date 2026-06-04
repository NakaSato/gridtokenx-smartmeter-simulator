import sys

with open('scripts/plot_bus_network.py', 'r') as f:
    content = f.read()

# Add style parameter to write_svg
content = content.replace(
    'def write_svg(\n    topology: GridTopology,\n    rows: List[Dict[str, object]],\n    output: Path,\n    reference_branches: Dict[Tuple[str, str], BranchInfo] | None = None,\n    load_buses: Set[str] | None = None,\n) -> None:',
    'def write_svg(\n    topology: GridTopology,\n    rows: List[Dict[str, object]],\n    output: Path,\n    reference_branches: Dict[Tuple[str, str], BranchInfo] | None = None,\n    load_buses: Set[str] | None = None,\n    style: str = "standard",\n) -> None:'
)

svg_build_old = """    elements: List[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        "<style>",
        "text { font-family: 'Times New Roman', Times, serif; fill: #111111; }",
        ".edge-shadow { display: none; }",
        ".edge { stroke: #1f2933; stroke-linecap: square; }",
        ".feeder-1, .feeder-2, .feeder-3, .feeder-4 { stroke: #1f2933; }",
        ".cable-25 { stroke-width: 1.35; stroke-dasharray: 3 3; }",
        ".cable-50 { stroke-width: 1.9; stroke-dasharray: 8 4; }",
        ".cable-95 { stroke-width: 2.55; }",
        ".bus-shell { fill: #ffffff; stroke: #111111; stroke-width: 1.1; }",
        ".root-shell { fill: #d9d9d9; stroke: #111111; stroke-width: 1.3; }",
        ".busbar { stroke: #111111; stroke-width: 1.25; stroke-linecap: square; }",
        ".root-busbar { stroke: #111111; stroke-width: 1.45; stroke-linecap: square; }",
        ".pv-dot { fill: #ffffff; stroke: #111111; stroke-width: 1.05; }",
        ".load-dot { fill: #111111; stroke: #ffffff; stroke-width: 0.7; }",
        ".node-label { fill: #111111; font-size: 8px; font-weight: 600; text-anchor: middle; dominant-baseline: central; }",
        ".root-label { fill: #111111; font-size: 9px; font-weight: 700; text-anchor: middle; dominant-baseline: central; }",
        ".feeder-label { font-size: 10.5px; font-weight: 700; fill: #111111; }",
        ".title { font-size: 22px; font-weight: 700; }",
        ".meta { font-size: 12px; fill: #333333; }",
        ".caption { font-size: 12px; fill: #333333; }",
        ".legend-box { fill: #ffffff; stroke: #111111; stroke-width: 0.8; }",
        "</style>",
        f'<rect width="{width}" height="{height}" fill="#ffffff"/>',
        '<text x="34" y="38" class="title">80-Bus Rural LV Reference Feeder</text>',
        (
            f'<text x="34" y="60" class="meta">'
            f"{len(topology.buses)} nodes · {len(topology.lines)} lines · "
            f"{len(rows)} solar nodes · {total_solar_kw:.1f} kW PV"
            "</text>"
        ),
        (
            f'<text x="34" y="78" class="meta">'
            f"Reference grid: {len(reference_branches)} branches"
            f"{f' · {total_line_km:.2f} km LV line' if reference_branches else ''}"
            f"{f' · {len(load_buses)} load-profile buses' if load_buses else ''}"
            "</text>"
        ),
        (
            f'<text x="34" y="{height - 30}" class="caption">'
            "Figure: schematic single-line representation of the 80-bus rural low-voltage feeder. "
            "Line style encodes conductor type; segment spacing is scaled from reference branch length."
            "</text>"
        ),
    ]"""

svg_build_new = """    elements: List[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
    ]

    if style == "modern":
        elements.extend([
            "<defs>",
            '<pattern id="soft-grid" width="32" height="32" patternUnits="userSpaceOnUse">',
            '<path d="M 32 0 L 0 0 0 32" fill="none" stroke="#e5edf6" stroke-width="1"/>',
            "</pattern>",
            '<filter id="node-shadow" x="-35%" y="-35%" width="170%" height="170%">',
            '<feDropShadow dx="0" dy="2" stdDeviation="2" flood-color="#0f172a" flood-opacity="0.16"/>',
            "</filter>",
            "</defs>",
            "<style>",
            "text { font-family: Arial, Helvetica, sans-serif; fill: #0f172a; }",
            ".edge-shadow { stroke: #dbe6f3; stroke-width: 7; stroke-linecap: round; opacity: 0.72; }",
            ".edge { stroke: #64748b; stroke-linecap: round; }",
            ".feeder-1 { stroke: #2563eb; }",
            ".feeder-2 { stroke: #0f766e; }",
            ".feeder-3 { stroke: #7c3aed; }",
            ".feeder-4 { stroke: #dc2626; }",
            ".cable-25 { stroke-width: 2.0; stroke-dasharray: 3 4; }",
            ".cable-50 { stroke-width: 3.0; stroke-dasharray: 8 5; }",
            ".cable-95 { stroke-width: 4.0; }",
            ".bus-shell { fill: #ffffff; stroke: #0f766e; stroke-width: 1.8; filter: url(#node-shadow); }",
            ".root-shell { fill: #ef4444; stroke: #7f1d1d; stroke-width: 2.1; filter: url(#node-shadow); }",
            ".busbar { stroke: #0f172a; stroke-width: 2.0; stroke-linecap: round; }",
            ".root-busbar { stroke: #ffffff; stroke-width: 2.4; stroke-linecap: round; }",
            ".pv-dot { fill: #facc15; stroke: #c2410c; stroke-width: 1.35; }",
            ".load-dot { fill: #111827; stroke: #ffffff; stroke-width: 0.9; }",
            ".node-label { fill: #0f172a; font-size: 8.5px; font-weight: 700; text-anchor: middle; dominant-baseline: central; }",
            ".root-label { fill: #ffffff; font-size: 9.5px; font-weight: 700; text-anchor: middle; dominant-baseline: central; }",
            ".feeder-label { font-size: 11px; font-weight: 800; fill: #334155; }",
            ".title { font-size: 24px; font-weight: 800; }",
            ".meta { font-size: 12.5px; fill: #475569; }",
            ".caption { font-size: 12px; fill: #64748b; }",
            ".legend-box { fill: #ffffff; stroke: #d7e0ea; stroke-width: 1.0; filter: url(#node-shadow); }",
            "</style>",
            f'<rect width="{width}" height="{height}" fill="#f8fafc"/>',
            f'<rect x="0" y="0" width="{width}" height="{height}" fill="url(#soft-grid)" opacity="0.62"/>',
            '<text x="34" y="38" class="title">80-Bus Rural LV Feeder - Modern View</text>',
        ])
    else:
        elements.extend([
            "<style>",
            "text { font-family: 'Times New Roman', Times, serif; fill: #111111; }",
            ".edge-shadow { display: none; }",
            ".edge { stroke: #1f2933; stroke-linecap: square; }",
            ".feeder-1, .feeder-2, .feeder-3, .feeder-4 { stroke: #1f2933; }",
            ".cable-25 { stroke-width: 1.35; stroke-dasharray: 3 3; }",
            ".cable-50 { stroke-width: 1.9; stroke-dasharray: 8 4; }",
            ".cable-95 { stroke-width: 2.55; }",
            ".bus-shell { fill: #ffffff; stroke: #111111; stroke-width: 1.1; }",
            ".root-shell { fill: #d9d9d9; stroke: #111111; stroke-width: 1.3; }",
            ".busbar { stroke: #111111; stroke-width: 1.25; stroke-linecap: square; }",
            ".root-busbar { stroke: #111111; stroke-width: 1.45; stroke-linecap: square; }",
            ".pv-dot { fill: #ffffff; stroke: #111111; stroke-width: 1.05; }",
            ".load-dot { fill: #111111; stroke: #ffffff; stroke-width: 0.7; }",
            ".node-label { fill: #111111; font-size: 8px; font-weight: 600; text-anchor: middle; dominant-baseline: central; }",
            ".root-label { fill: #111111; font-size: 9px; font-weight: 700; text-anchor: middle; dominant-baseline: central; }",
            ".feeder-label { font-size: 10.5px; font-weight: 700; fill: #111111; }",
            ".title { font-size: 22px; font-weight: 700; }",
            ".meta { font-size: 12px; fill: #333333; }",
            ".caption { font-size: 12px; fill: #333333; }",
            ".legend-box { fill: #ffffff; stroke: #111111; stroke-width: 0.8; }",
            "</style>",
            f'<rect width="{width}" height="{height}" fill="#ffffff"/>',
            '<text x="34" y="38" class="title">80-Bus Rural LV Reference Feeder</text>',
        ])

    elements.extend([
        (
            f'<text x="34" y="60" class="meta">'
            f"{len(topology.buses)} nodes · {len(topology.lines)} lines · "
            f"{len(rows)} solar nodes · {total_solar_kw:.1f} kW PV"
            "</text>"
        ),
        (
            f'<text x="34" y="78" class="meta">'
            f"Reference grid: {len(reference_branches)} branches"
            f"{f' · {total_line_km:.2f} km LV line' if reference_branches else ''}"
            f"{f' · {len(load_buses)} load-profile buses' if load_buses else ''}"
            "</text>"
        ),
        (
            f'<text x="34" y="{height - 30}" class="caption">'
            "Figure: schematic single-line representation of the 80-bus rural low-voltage feeder. "
            "Line style encodes conductor type; segment spacing is scaled from reference branch length."
            "</text>"
        ),
    ])"""

content = content.replace(svg_build_old, svg_build_new)

legend_box_old = 'f\'<rect class="legend-box" x="{legend_x}" y="{legend_y}" width="242" height="182"/>\','
legend_box_new = 'f\'<rect class="legend-box" x="{legend_x}" y="{legend_y}" width="242" height="182" {"rx=\\"10\\"" if style == "modern" else ""}/>\','

content = content.replace(legend_box_old, legend_box_new)

argparse_old = """    parser.add_argument(
        "--print-nodes",
        action="store_true",
        help="Print every node with installed PV",
    )
    return parser.parse_args()"""
argparse_new = """    parser.add_argument(
        "--print-nodes",
        action="store_true",
        help="Print every node with installed PV",
    )
    parser.add_argument(
        "--style",
        type=str,
        choices=["standard", "modern"],
        default="standard",
        help="Style of the SVG plot",
    )
    return parser.parse_args()"""
content = content.replace(argparse_old, argparse_new)

main_old = """    write_solar_exports(rows, args.out_dir)
    svg_path = args.out_dir / "grid_bus_network.svg"
    write_svg(
        topology,
        rows,
        svg_path,
        reference_branches=reference_branches,
        load_buses=load_buses,
    )"""
main_new = """    write_solar_exports(rows, args.out_dir)
    svg_name = "grid_bus_network.svg" if args.style == "standard" else f"grid_bus_network_{args.style}.svg"
    svg_path = args.out_dir / svg_name
    write_svg(
        topology,
        rows,
        svg_path,
        reference_branches=reference_branches,
        load_buses=load_buses,
        style=args.style,
    )"""
content = content.replace(main_old, main_new)

with open('scripts/plot_bus_network.py', 'w') as f:
    f.write(content)

print("Patched plot_bus_network.py successfully.")
