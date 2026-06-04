"""Plot the GLM bus network and export nodes with installed PV."""

from __future__ import annotations

import argparse
import csv
import json
from collections import deque
from dataclasses import dataclass
from html import escape
from pathlib import Path
from typing import Dict, Iterable, List, Set, Tuple

from smart_meter_simulator.core.topology import GridTopology
from smart_meter_simulator.core.topology_factory import load_glm_core_topology


DEFAULT_GLM = Path("src/smart_meter_simulator/data/grids/grid_bus_network.glm")
DEFAULT_ARTIFACT_DIR = Path("artifacts")
DEFAULT_REFERENCE_GRID = Path("data/80_bus_rural_reference_grid")


@dataclass(frozen=True)
class BranchInfo:
    length_km: float
    branch_type: str


def node_sort_key(node_id: str) -> Tuple[str, int, int | str]:
    prefix, _, suffix = node_id.rpartition("_")
    if suffix.isdigit():
        return prefix, 0, int(suffix)
    return prefix, 1, suffix


def bus_label(node_id: str) -> str:
    return node_id.replace("ref_lv_bus_", "")


def reference_bus_name(bus_id: str) -> str:
    return f"ref_lv_bus_{int(float(bus_id))}"


def edge_key(from_bus: str, to_bus: str) -> Tuple[str, str]:
    return tuple(sorted((from_bus, to_bus), key=node_sort_key))


def cable_class(branch_type: str) -> str:
    if "3x25" in branch_type:
        return "cable-25"
    if "3x50" in branch_type:
        return "cable-50"
    if "3x95" in branch_type:
        return "cable-95"
    return ""


def load_reference_grid(
    reference_dir: Path,
) -> Tuple[Dict[Tuple[str, str], BranchInfo], Set[str]]:
    """Load optional MATPOWER reference-grid metadata for plotting."""
    branches: Dict[Tuple[str, str], BranchInfo] = {}
    load_buses: Set[str] = set()
    branch_path = reference_dir / "branch_extra.csv"
    load_bus_path = reference_dir / "load_bus_extra.csv"

    if branch_path.exists():
        with branch_path.open(newline="", encoding="utf-8") as file:
            for row in csv.DictReader(file):
                from_bus = reference_bus_name(str(row["From Bus"]))
                to_bus = reference_bus_name(str(row["To Bus"]))
                branches[edge_key(from_bus, to_bus)] = BranchInfo(
                    length_km=float(row["Length [km]"]),
                    branch_type=str(row["Branch type"]),
                )

    if load_bus_path.exists():
        with load_bus_path.open(newline="", encoding="utf-8") as file:
            for row in csv.DictReader(file):
                load_buses.add(reference_bus_name(str(row["bus_i"])))

    return branches, load_buses


def solar_nodes(topology: GridTopology) -> List[Dict[str, object]]:
    """Return one row per GLM node/bus with installed solar."""
    rows = []
    for pv in sorted(topology.pvs, key=lambda item: node_sort_key(item.bus)):
        rows.append(
            {
                "node_id": pv.bus,
                "pv_name": pv.name,
                "inverter_name": pv.inverter_name,
                "capacity_kw": round(pv.capacity_kw, 6),
            }
        )
    return rows


def write_solar_exports(rows: List[Dict[str, object]], artifact_dir: Path) -> None:
    """Write solar node list as CSV and JSON."""
    artifact_dir.mkdir(parents=True, exist_ok=True)
    csv_path = artifact_dir / "solar_nodes.csv"
    json_path = artifact_dir / "solar_nodes.json"

    with csv_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=["node_id", "pv_name", "inverter_name", "capacity_kw"],
        )
        writer.writeheader()
        writer.writerows(rows)

    json_path.write_text(json.dumps(rows, indent=2), encoding="utf-8")


def rooted_tree(
    topology: GridTopology,
) -> Tuple[str, Dict[str, List[str]], Dict[str, int]]:
    """Return a deterministic rooted tree and feeder branch number for each bus."""
    graph = topology.to_networkx().to_undirected()
    if not graph.nodes:
        return "", {}, {}

    root = topology.get_substation_bus() or sorted(graph.nodes, key=node_sort_key)[0]
    children: Dict[str, List[str]] = {str(node): [] for node in graph.nodes}
    feeder_by_node: Dict[str, int] = {root: 0}
    queue: deque[Tuple[str, str | None, int]] = deque([(root, None, 0)])

    while queue:
        node, parent, feeder_id = queue.popleft()
        neighbors = sorted(
            (neighbor for neighbor in graph.neighbors(node) if neighbor != parent),
            key=node_sort_key,
        )
        for idx, neighbor in enumerate(neighbors, start=1):
            child_feeder_id = idx if node == root else feeder_id
            children[node].append(neighbor)
            feeder_by_node[neighbor] = child_feeder_id
            queue.append((neighbor, node, child_feeder_id))

    return root, children, feeder_by_node


def subtree_metrics(
    children: Dict[str, List[str]],
) -> Tuple[Dict[str, int], Dict[str, int]]:
    heights: Dict[str, int] = {}
    sizes: Dict[str, int] = {}

    def walk(node: str) -> Tuple[int, int]:
        if node in heights:
            return heights[node], sizes[node]
        child_metrics = [walk(child) for child in children.get(node, [])]
        heights[node] = (
            0 if not child_metrics else 1 + max(height for height, _ in child_metrics)
        )
        sizes[node] = 1 + sum(size for _, size in child_metrics)
        return heights[node], sizes[node]

    for node in children:
        walk(node)
    return heights, sizes


def electrical_positions(
    topology: GridTopology,
    width: int,
    height: int,
    reference_branches: Dict[Tuple[str, str], BranchInfo] | None = None,
    margin_x: float = 82.0,
    margin_top: float = 172.0,
    margin_bottom: float = 76.0,
) -> Dict[str, Tuple[float, float]]:
    """Create deterministic orthogonal LV single-line coordinates."""
    root, children, _ = rooted_tree(topology)
    if not root:
        return {}

    heights, sizes = subtree_metrics(children)
    raw_positions: Dict[str, Tuple[float, float]] = {root: (0.0, 0.0)}
    directions = [(-1.0, 0.0), (0.0, -1.0), (1.0, 0.0), (0.0, 1.0)]
    reference_branches = reference_branches or {}

    def best_trunk_key(node: str) -> Tuple[int, int, Tuple[str, int, int | str]]:
        return heights.get(node, 0), sizes.get(node, 0), node_sort_key(node)

    def branch_step(from_bus: str, to_bus: str) -> float:
        branch = reference_branches.get(edge_key(from_bus, to_bus))
        if not branch:
            return 1.0
        return 0.75 + min(branch.length_km, 0.18) * 5.0

    def place_subtree(node: str, direction: Tuple[float, float]) -> None:
        child_nodes = children.get(node, [])
        if not child_nodes:
            return

        trunk = max(child_nodes, key=best_trunk_key)
        side_nodes = [child for child in child_nodes if child != trunk]
        x, y = raw_positions[node]
        dx, dy = direction
        px, py = -dy, dx

        for idx, child in enumerate(side_nodes):
            sign = 1.0 if idx % 2 == 0 else -1.0
            offset = branch_step(node, child) + 0.35 + idx // 2 * 0.9
            side_direction = (px * sign, py * sign)
            raw_positions[child] = (
                x + side_direction[0] * offset,
                y + side_direction[1] * offset,
            )
            place_subtree(child, side_direction)

        trunk_step = branch_step(node, trunk)
        raw_positions[trunk] = (x + dx * trunk_step, y + dy * trunk_step)
        place_subtree(trunk, direction)

    for idx, child in enumerate(children.get(root, [])):
        direction = directions[idx % len(directions)]
        child_step = branch_step(root, child)
        raw_positions[child] = (
            raw_positions[root][0] + direction[0] * child_step,
            raw_positions[root][1] + direction[1] * child_step,
        )
        place_subtree(child, direction)

    xs = [x for x, _ in raw_positions.values()]
    ys = [y for _, y in raw_positions.values()]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    x_span = max(max_x - min_x, 1e-9)
    y_span = max(max_y - min_y, 1e-9)

    positions: Dict[str, Tuple[float, float]] = {}
    for node, (raw_x, raw_y) in raw_positions.items():
        x = margin_x + (float(raw_x) - min_x) / x_span * (width - margin_x * 2)
        y = margin_top + (float(raw_y) - min_y) / y_span * (
            height - margin_top - margin_bottom
        )
        positions[str(node)] = (x, y)
    return positions


def resolve_symbol_overlaps(
    positions: Dict[str, Tuple[float, float]],
    fixed_nodes: Set[str] | None = None,
    min_dx: float = 44.0,
    min_dy: float = 30.0,
    iterations: int = 12,
) -> Dict[str, Tuple[float, float]]:
    """Separate nearby bus symbols while keeping the schematic deterministic."""
    fixed_nodes = fixed_nodes or set()
    adjusted = {node: [x, y] for node, (x, y) in positions.items()}
    nodes = sorted(adjusted, key=node_sort_key)

    for _ in range(iterations):
        moved = False
        for left_idx, left in enumerate(nodes):
            for right in nodes[left_idx + 1 :]:
                left_x, left_y = adjusted[left]
                right_x, right_y = adjusted[right]
                dx = right_x - left_x
                dy = right_y - left_y
                if abs(dx) >= min_dx or abs(dy) >= min_dy:
                    continue

                push_x = (min_dx - abs(dx)) / 2.0 + 0.8
                push_y = (min_dy - abs(dy)) / 2.0 + 0.8
                move_x = push_x <= push_y
                sign = 1.0 if (dx if move_x else dy) >= 0 else -1.0
                if dx == 0 and move_x:
                    sign = 1.0 if node_sort_key(right) > node_sort_key(left) else -1.0
                if dy == 0 and not move_x:
                    sign = 1.0 if node_sort_key(right) > node_sort_key(left) else -1.0

                if left not in fixed_nodes:
                    if move_x:
                        adjusted[left][0] -= sign * push_x
                    else:
                        adjusted[left][1] -= sign * push_y
                if right not in fixed_nodes:
                    if move_x:
                        adjusted[right][0] += sign * push_x
                    else:
                        adjusted[right][1] += sign * push_y
                moved = True
        if not moved:
            break

    return {node: (coords[0], coords[1]) for node, coords in adjusted.items()}


def write_svg(
    topology: GridTopology,
    rows: List[Dict[str, object]],
    output: Path,
    reference_branches: Dict[Tuple[str, str], BranchInfo] | None = None,
    load_buses: Set[str] | None = None,
    style: str = "standard",
) -> None:
    """Render a dependency-free SVG bus graph network plot."""
    width = 1500
    height = 1040
    reference_branches = reference_branches or {}
    load_buses = load_buses or set()
    root, children, feeder_by_node = rooted_tree(topology)
    positions = electrical_positions(
        topology,
        width=width,
        height=height,
        reference_branches=reference_branches,
    )
    if not positions:
        raise ValueError("Topology has no bus positions to plot.")
    positions = resolve_symbol_overlaps(positions, fixed_nodes={root})

    solar_by_node = {str(row["node_id"]): row for row in rows}
    total_solar_kw = sum(float(row["capacity_kw"]) for row in rows)
    total_line_km = sum(branch.length_km for branch in reference_branches.values())

    elements: List[str] = [
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
    ])

    for line in topology.lines:
        if line.from_bus not in positions or line.to_bus not in positions:
            continue
        x1, y1 = positions[line.from_bus]
        x2, y2 = positions[line.to_bus]
        if line.from_bus == root:
            feeder_id = feeder_by_node.get(line.to_bus, 0)
        elif line.to_bus == root:
            feeder_id = feeder_by_node.get(line.from_bus, 0)
        else:
            feeder_id = feeder_by_node.get(
                line.from_bus, feeder_by_node.get(line.to_bus, 0)
            )
        feeder_class = f"feeder-{feeder_id}" if 1 <= feeder_id <= 4 else ""
        branch = reference_branches.get(edge_key(line.from_bus, line.to_bus))
        cable_type_class = cable_class(branch.branch_type) if branch else ""
        line_title = (
            f"{line.from_bus} to {line.to_bus}"
            if not branch
            else (
                f"{line.from_bus} to {line.to_bus} · "
                f"{branch.length_km * 1000:.1f} m · {branch.branch_type}"
            )
        )
        elements.append("<g>")
        elements.append(f"<title>{escape(line_title)}</title>")
        elements.append(
            f'<line class="edge-shadow" x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}"/>'
        )
        elements.append(
            f'<line class="edge {feeder_class} {cable_type_class}" '
            f'x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}"/>'
        )
        elements.append("</g>")

    for child in children.get(root, []):
        if root not in positions or child not in positions:
            continue
        feeder_id = feeder_by_node.get(child, 0)
        x1, y1 = positions[root]
        x2, y2 = positions[child]
        dx = x2 - x1
        dy = y2 - y1
        if abs(dx) >= abs(dy):
            label_x = x2 + (18 if dx > 0 else -18)
            label_y = y2 - 16
        else:
            label_x = x2 + 18
            label_y = y2 + (18 if dy > 0 else -18)
        elements.append(
            f'<text class="feeder-label" x="{label_x:.2f}" y="{label_y:.2f}">F{feeder_id}</text>'
        )

    for bus in sorted(topology.buses, key=lambda item: node_sort_key(item.name)):
        if bus.name not in positions:
            continue
        x, y = positions[bus.name]
        row = solar_by_node.get(bus.name)
        has_load = bus.name in load_buses
        is_root = bus.name == root
        node_width = 42 if is_root else 30
        node_height = 24 if is_root else 20
        shell_class = "root-shell" if is_root else "bus-shell"
        bar_class = "root-busbar" if is_root else "busbar"
        label_class = "root-label" if is_root else "node-label"

        elements.append("<g>")
        title_parts = [bus.name]
        if row:
            title_parts.append(f"PV {float(row['capacity_kw']):.3f} kW")
        if has_load:
            title_parts.append("reference load profile")
        elements.append(f"<title>{escape(' · '.join(title_parts))}</title>")
        elements.append(
            f'<rect class="{shell_class}" x="{x - node_width / 2:.2f}" '
            f'y="{y - node_height / 2:.2f}" width="{node_width}" '
            f'height="{node_height}" rx="3"/>'
        )
        elements.append(
            f'<line class="{bar_class}" x1="{x - node_width / 2 + 5:.2f}" '
            f'y1="{y:.2f}" x2="{x + node_width / 2 - 5:.2f}" y2="{y:.2f}"/>'
        )
        if row:
            elements.append(
                f'<circle class="pv-dot" cx="{x + node_width / 2 - 2:.2f}" '
                f'cy="{y - node_height / 2 + 2:.2f}" r="4.5"/>'
            )
        if has_load:
            elements.append(
                f'<circle class="load-dot" cx="{x - node_width / 2 + 2:.2f}" '
                f'cy="{y + node_height / 2 - 2:.2f}" r="3.8"/>'
            )
        elements.append(
            f'<text class="{label_class}" x="{x:.2f}" y="{y:.2f}">'
            f"{escape(bus_label(bus.name))}</text>"
        )
        elements.append("</g>")

    legend_x = width - 282
    legend_y = 34
    rx_attr = ' rx="10"' if style == "modern" else ""
    elements.extend(
        [
            f'<rect class="legend-box" x="{legend_x}" y="{legend_y}" width="242" height="182"{rx_attr}/>',
            f'<rect class="root-shell" x="{legend_x + 10}" y="{legend_y + 15}" width="30" height="20" rx="3"/>',
            f'<line class="root-busbar" x1="{legend_x + 15}" y1="{legend_y + 25}" x2="{legend_x + 35}" y2="{legend_y + 25}"/>',
            f'<text x="{legend_x + 48}" y="{legend_y + 32}" class="meta">PCC bus</text>',
            f'<rect class="bus-shell" x="{legend_x + 10}" y="{legend_y + 49}" width="30" height="20" rx="3"/>',
            f'<line class="busbar" x1="{legend_x + 15}" y1="{legend_y + 59}" x2="{legend_x + 35}" y2="{legend_y + 59}"/>',
            f'<circle class="pv-dot" cx="{legend_x + 38}" cy="{legend_y + 51}" r="4.5"/>',
            f'<text x="{legend_x + 48}" y="{legend_y + 64}" class="meta">PV bus</text>',
            f'<circle class="load-dot" cx="{legend_x + 25}" cy="{legend_y + 88}" r="4"/>',
            f'<text x="{legend_x + 48}" y="{legend_y + 93}" class="meta">Load-profile bus</text>',
            f'<line class="edge cable-95" x1="{legend_x + 12}" y1="{legend_y + 120}" x2="{legend_x + 38}" y2="{legend_y + 120}"/>',
            f'<text x="{legend_x + 48}" y="{legend_y + 125}" class="meta">EX 3x95 Al</text>',
            f'<line class="edge cable-50" x1="{legend_x + 12}" y1="{legend_y + 146}" x2="{legend_x + 38}" y2="{legend_y + 146}"/>',
            f'<text x="{legend_x + 48}" y="{legend_y + 151}" class="meta">EX 3x50 Al</text>',
            f'<line class="edge cable-25" x1="{legend_x + 12}" y1="{legend_y + 170}" x2="{legend_x + 38}" y2="{legend_y + 170}"/>',
            f'<text x="{legend_x + 48}" y="{legend_y + 175}" class="meta">EX 3x25 Al</text>',
        ]
    )
    elements.append("</svg>")

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(elements), encoding="utf-8")


def print_solar_nodes(rows: Iterable[Dict[str, object]]) -> None:
    for row in rows:
        print(
            f'{row["node_id"]}: {row["capacity_kw"]:.3f} kW '
            f'({row["pv_name"]}, {row["inverter_name"]})'
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Plot GLM bus network and export nodes with installed solar PV.",
    )
    parser.add_argument(
        "--glm", type=Path, default=DEFAULT_GLM, help="GLM file to plot"
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=DEFAULT_ARTIFACT_DIR,
        help="Artifact output directory",
    )
    parser.add_argument(
        "--reference-grid",
        type=Path,
        default=DEFAULT_REFERENCE_GRID,
        help="Reference-grid folder with branch_extra.csv and load_bus_extra.csv",
    )
    parser.add_argument(
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
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    topology = load_glm_core_topology(args.glm)
    rows = solar_nodes(topology)
    reference_branches, load_buses = load_reference_grid(args.reference_grid)

    write_solar_exports(rows, args.out_dir)
    svg_name = "grid_bus_network.svg" if args.style == "standard" else f"grid_bus_network_{args.style}.svg"
    svg_path = args.out_dir / svg_name
    write_svg(
        topology,
        rows,
        svg_path,
        reference_branches=reference_branches,
        load_buses=load_buses,
        style=args.style,
    )

    print(f"Loaded GLM: {args.glm}")
    print(f"Loaded reference grid: {args.reference_grid}")
    print(f"Nodes: {len(topology.buses)}")
    print(f"Lines: {len(topology.lines)}")
    print(
        f"Reference branches: {len(reference_branches)} "
        f"({sum(branch.length_km for branch in reference_branches.values()):.3f} km)"
    )
    print(f"Reference load buses: {len(load_buses)}")
    print(f"Solar nodes: {len(rows)}")
    print(
        f"Solar capacity total: {sum(float(row['capacity_kw']) for row in rows):.3f} kW"
    )
    print(f"Wrote: {args.out_dir / 'solar_nodes.csv'}")
    print(f"Wrote: {args.out_dir / 'solar_nodes.json'}")
    print(f"Wrote: {svg_path}")

    if args.print_nodes:
        print_solar_nodes(rows)


if __name__ == "__main__":
    main()
