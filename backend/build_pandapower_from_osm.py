#!/usr/bin/env python3
"""
Build pandapower network topology from real OSM power grid data.

Converts OSM power lines, substations, and towers into pandapower network elements:
- power=substation → buses (with voltage levels)
- power=line → lines (with voltage-appropriate cable types)
- power=tower/pole → bus geo coordinates (optional detail nodes)
- External grid connection at transmission substations

OSM → pandapower mapping:
- voltage ≥ 69kV → HV bus (transmission)
- voltage 1-69kV → MV bus (distribution)
- voltage < 1kV → LV bus (low voltage)

Usage:
    uv run python build_pandapower_from_osm.py
"""

import json
import logging
from pathlib import Path
from typing import Any

import numpy as np

try:
    import pandapower as pp
    PANDAPOWER_AVAILABLE = True
except ImportError:
    PANDAPOWER_AVAILABLE = False
    print("Warning: pandapower not installed. Run: uv sync")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_voltage_category(voltage_v: int | None) -> tuple[str, float]:
    """Classify voltage into HV/MV/LV and return nominal voltage in kV"""
    if voltage_v is None:
        return "distribution", 115.0  # Default to transmission-level for unknown substations

    voltage_kv = voltage_v / 1000

    if voltage_kv >= 69:
        return "transmission", voltage_kv
    elif voltage_kv >= 1:
        return "distribution", voltage_kv
    else:
        return "low_voltage", voltage_kv


def get_cable_type(voltage_kv: float) -> str:
    """Get pandapower standard cable type for voltage level"""
    if voltage_kv >= 110:
        return "N2XS(FL)2Y 1x120 RM/35 64/110 kV"
    elif voltage_kv >= 20:
        return "NA2XS2Y 1x185 RM/25 12/20 kV"
    elif voltage_kv >= 1:
        return "NAYY 4x50 SE"
    else:
        return "NAYY 4x50 SE"


def calculate_line_length_km(coords: list[list[float]]) -> float:
    """Calculate approximate line length from coordinates using Haversine formula"""
    if len(coords) < 2:
        return 0.0

    total = 0.0
    for i in range(len(coords) - 1):
        lon1, lat1 = coords[i]
        lon2, lat2 = coords[i + 1]

        # Haversine approximation
        dlat = np.radians(lat2 - lat1)
        dlon = np.radians(lon2 - lon1)
        a = (
            np.sin(dlat / 2) ** 2
            + np.cos(np.radians(lat1)) * np.cos(np.radians(lat2)) * np.sin(dlon / 2) ** 2
        )
        c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))
        total += 6371 * c  # Earth radius in km

    return total


def build_pandapower_from_osm(osm_data: dict, network_name: str = "OSM Power Grid") -> dict:
    """
    Build pandapower network from OSM power grid data.

    Args:
        osm_data: Converted OSM data (from convert_osm_to_simulator.py output)
        network_name: Name for the pandapower network

    Returns:
        dict with 'network' (pandapower net), 'stats', and 'mapping'
    """
    if not PANDAPOWER_AVAILABLE:
        raise ImportError("pandapower required. Install with: uv sync")

    net = pp.create_empty_network(name=network_name)

    mapping = {
        "substations": {},  # osm_id -> bus_idx
        "power_lines": {},  # osm_id -> line_idx
        "towers": {},
        "poles": {},
    }

    stats = {
        "buses_created": 0,
        "lines_created": 0,
        "transformers_created": 0,
        "external_grids": 0,
        "errors": [],
    }

    # 1. Create buses from substations
    logger.info(f"Creating {len(osm_data['substations'])} substation buses...")
    for sub in osm_data["substations"]:
        osm_id = sub["osm_id"]
        voltage = sub.get("voltage")
        sub_type = sub.get("substation_type", "distribution")
        category, vn_kv = get_voltage_category(voltage)

        loc = sub.get("location", {})
        lat = loc.get("latitude")
        lon = loc.get("longitude")

        try:
            bus_idx = pp.create_bus(
                net,
                vn_kv=vn_kv,
                name=f"{sub.get('name', f'SUB-{osm_id}')} ({sub_type})",
                geodata=(lon or 0, lat or 0) if lat and lon else None,
            )

            mapping["substations"][osm_id] = {
                "bus_idx": int(bus_idx),
                "voltage": voltage,
                "category": category,
                "vn_kv": vn_kv,
            }
            stats["buses_created"] += 1

            # Add external grid connection for transmission substations
            if sub_type == "transmission" or category == "transmission":
                pp.create_ext_grid(
                    net,
                    bus=bus_idx,
                    vm_pu=1.0,
                    va_degree=0.0,
                    name=f"Grid_{sub.get('name', osm_id)}",
                )
                stats["external_grids"] += 1
                logger.info(f"  Added external grid at transmission substation: {sub.get('name', osm_id)}")

        except Exception as e:
            stats["errors"].append(f"Substation {osm_id}: {e}")
            logger.error(f"  Failed to create bus for substation {osm_id}: {e}")

    # 2. Create lines from power lines
    logger.info(f"Creating {len(osm_data['power_lines'])} power lines...")

    # Find transmission substation(s) - these are connected to slack
    slack_buses = set()
    for sub in osm_data["substations"]:
        if sub.get("substation_type") == "transmission":
            osm_id = sub["osm_id"]
            if osm_id in mapping["substations"]:
                slack_buses.add(mapping["substations"][osm_id]["bus_idx"])

    if not slack_buses:
        logger.warning("No transmission substations found, using first substation as slack reference")
        if mapping["substations"]:
            slack_buses.add(next(iter(mapping["substations"].values()))["bus_idx"])

    for line in osm_data["power_lines"]:
        osm_id = line["osm_id"]
        voltage = line.get("voltage")
        coords = line.get("coordinates", [])
        category, vn_kv = get_voltage_category(voltage)
        cable_type = get_cable_type(vn_kv)

        try:
            # Find nearest substations for from/to bus connection
            # Use line midpoint to find closest substations
            if coords:
                mid_lon = np.mean([c[0] for c in coords])
                mid_lat = np.mean([c[1] for c in coords])
            else:
                stats["errors"].append(f"Line {osm_id}: No coordinates")
                continue

            # Find nearest substations - prefer transmission substations for at least one end
            distances = []
            for sub_osm_id, sub_info in mapping["substations"].items():
                bus_idx = sub_info["bus_idx"]
                # Get substation location
                loc = next((s.get("location", {}) for s in osm_data["substations"] if s["osm_id"] == sub_osm_id), {})
                sub_lon = loc.get("longitude", 0)
                sub_lat = loc.get("latitude", 0)

                dist = np.sqrt((sub_lon - mid_lon) ** 2 + (sub_lat - mid_lat) ** 2)
                distances.append((dist, sub_osm_id, sub_info))

            if len(distances) < 2:
                stats["errors"].append(f"Line {osm_id}: Not enough nearby substations")
                continue

            distances.sort(key=lambda x: x[0])

            # Prefer connecting to a transmission substation if one exists
            from_sub = None
            to_sub = None

            # Find closest transmission substation
            tx_subs = [(d, s, i) for d, s, i in distances if i["bus_idx"] in slack_buses]
            other_subs = [(d, s, i) for d, s, i in distances if i["bus_idx"] not in slack_buses]

            if tx_subs:
                from_sub = tx_subs[0]  # Connect to nearest transmission sub
                # Find nearest non-tx sub for the other end (or second tx if only tx exists)
                if other_subs:
                    to_sub = other_subs[0]
                elif len(tx_subs) > 1:
                    to_sub = tx_subs[1]
                else:
                    to_sub = tx_subs[0]  # Both ends same sub (will be skipped as duplicate)
            else:
                from_sub = distances[0]
                to_sub = distances[1]

            # Calculate line length
            length_km = calculate_line_length_km(coords)
            if length_km < 0.01:
                length_km = 0.1  # Minimum length

            # Create from_bus to midpoint bus line
            from_bus_idx = from_sub[2]["bus_idx"]

            # Create intermediate bus at line midpoint if needed
            if to_sub:
                from_bus_idx = from_sub[2]["bus_idx"]
                to_bus_idx = to_sub[2]["bus_idx"]

                # Skip if both ends are the same bus
                if from_bus_idx == to_bus_idx:
                    logger.info(f"  Skipping line {osm_id}: both ends connect to same bus")
                    stats["lines_created"] += 1
                    continue

                # Check if line already exists between these buses (either direction)
                existing_lines = net.line[
                    ((net.line.from_bus == from_bus_idx) & (net.line.to_bus == to_bus_idx)) |
                    ((net.line.from_bus == to_bus_idx) & (net.line.to_bus == from_bus_idx))
                ]
                if len(existing_lines) > 0:
                    logger.info(f"  Skipping duplicate line {osm_id}: {from_sub[1]} ↔ {to_sub[1]} (already exists)")
                    stats["lines_created"] += 1
                    mapping["power_lines"][osm_id] = {
                        "line_idx": int(existing_lines.index[0]),
                        "from_substation": from_sub[1],
                        "to_substation": to_sub[1],
                        "length_km": length_km,
                        "voltage_kv": vn_kv,
                        "duplicate": True,
                    }
                    continue

                line_idx = pp.create_line(
                    net,
                    from_bus=from_bus_idx,
                    to_bus=to_bus_idx,
                    length_km=length_km,
                    std_type=cable_type,
                    name=f"LINE_{osm_id}",
                )
                mapping["power_lines"][osm_id] = {
                    "line_idx": int(line_idx),
                    "from_substation": from_sub[1],
                    "to_substation": to_sub[1],
                    "length_km": length_km,
                    "voltage_kv": vn_kv,
                }
                stats["lines_created"] += 1
                logger.info(f"  Created line {osm_id}: {from_sub[1]} → {to_sub[1]} ({length_km:.2f} km, {vn_kv:.0f}kV)")
            else:
                # Create load at end of line
                mid_bus_idx = pp.create_bus(
                    net,
                    vn_kv=vn_kv,
                    name=f"LINE_END_{osm_id}",
                    geodata=(mid_lon, mid_lat),
                )
                line_idx = pp.create_line(
                    net,
                    from_bus=from_bus_idx,
                    to_bus=mid_bus_idx,
                    length_km=length_km,
                    std_type=cable_type,
                    name=f"LINE_{osm_id}",
                )
                mapping["power_lines"][osm_id] = {
                    "line_idx": int(line_idx),
                    "from_substation": from_sub[1],
                    "to_substation": None,
                    "length_km": length_km,
                    "voltage_kv": vn_kv,
                }
                stats["lines_created"] += 1
                logger.info(f"  Created line {osm_id}: {from_sub[1]} → endpoint ({length_km:.2f} km)")

        except Exception as e:
            stats["errors"].append(f"Line {osm_id}: {e}")
            logger.error(f"  Failed to create line {osm_id}: {e}")

    # 4. Add loads at each bus (simulated demand)
    logger.info("Adding loads at each bus...")
    for bus_idx, bus_row in net.bus.iterrows():
        vn_kv = bus_row.vn_kv
        # Simulate realistic load: 10-50 MW for transmission, 1-10 MW for distribution
        if vn_kv >= 69:
            p_mw = np.random.uniform(20, 50)
        else:
            p_mw = np.random.uniform(2, 10)

        load_idx = pp.create_load(
            net,
            bus=bus_idx,
            p_mw=p_mw,
            q_mvar=p_mw * 0.33,  # PF ≈ 0.95
            name=f"Load_{bus_row['name']}",
        )
        stats["loads_created"] = stats.get("loads_created", 0) + 1
        logger.info(f"  Added {p_mw:.1f} MW load at bus {bus_idx} ({bus_row['name']})")

    # 5. Record towers/poles (optional detail - not modeled as buses)
    for tower in osm_data.get("towers", []):
        mapping["towers"][tower["osm_id"]] = tower["location"]

    for pole in osm_data.get("poles", []):
        mapping["poles"][pole["osm_id"]] = pole["location"]

    return {
        "network": net,
        "stats": stats,
        "mapping": mapping,
    }


def save_pandapower_network(net: pp.pandapowerNet, output_dir: Path):
    """Save pandapower network to JSON"""
    output_dir.mkdir(parents=True, exist_ok=True)
    pp.to_json(net, str(output_dir / "pandapower_network.json"))
    logger.info(f"Saved pandapower network to {output_dir}")


def main():
    if not PANDAPOWER_AVAILABLE:
        logger.error("pandapower not installed. Run: uv sync")
        return

    data_dir = Path(__file__).parent / "data" / "korat"

    # Load converted OSM data
    korat_sim_file = data_dir / "korat_simulator.json"
    if not korat_sim_file.exists():
        logger.error(f"Korat simulator data not found: {korat_sim_file}")
        logger.info("Run convert_osm_to_simulator.py first")
        return

    with open(korat_sim_file) as f:
        korat_data = json.load(f)

    logger.info(f"Building pandapower network from Korat OSM data...")
    logger.info(f"  Substations: {len(korat_data['substations'])}")
    logger.info(f"  Power lines: {len(korat_data['power_lines'])}")

    try:
        result = build_pandapower_from_osm(korat_data, "Korat Power Grid (OSM)")

        net = result["network"]
        stats = result["stats"]
        mapping = result["mapping"]

        # Print summary
        print(f"\n=== Pandapower Network Summary ===")
        print(f"  Buses: {len(net.bus)}")
        print(f"  Lines: {len(net.line)}")
        print(f"  External grids: {len(net.ext_grid)}")
        print(f"  Transformers: {len(getattr(net, 'trafo', []))}")
        print(f"  Loads: {len(net.load)}")
        print(f"  Static generators: {len(getattr(net, 'sgen', []))}")

        print(f"\n=== Conversion Stats ===")
        print(f"  Buses created: {stats['buses_created']}")
        print(f"  Lines created: {stats['lines_created']}")
        print(f"  External grids: {stats['external_grids']}")
        if stats["errors"]:
            print(f"  Errors: {len(stats['errors'])}")
            for err in stats["errors"][:5]:
                print(f"    - {err}")

        # Save network
        save_pandapower_network(net, data_dir)

        # Save mapping
        mapping_out = {
            "substations": {k: v for k, v in mapping["substations"].items()},
            "power_lines": {k: v for k, v in mapping["power_lines"].items()},
            "stats": stats,
        }
        with open(data_dir / "pandapower_mapping.json", "w") as f:
            json.dump(mapping_out, f, indent=2, ensure_ascii=False)

        logger.info(f"\nSaved mapping to {data_dir / 'pandapower_mapping.json'}")

    except Exception as e:
        logger.error(f"Failed to build pandapower network: {e}", exc_info=True)


if __name__ == "__main__":
    main()
