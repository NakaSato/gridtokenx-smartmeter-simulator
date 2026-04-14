#!/usr/bin/env python3
"""
Convert OSM power grid data (from Overpass API) to simulator-compatible format.

Maps OSM power=* tags to simulator templates:
- power=line/cable → power_lines_template.json
- power=substation → substations_template.json
- power=transformer → transformers_template.json
- power=generator → meters (as generation sources)

OSM tagging reference: https://wiki.openstreetmap.org/wiki/Key:power
"""

import json
import logging
from pathlib import Path
from typing import Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def parse_voltage(v: str | list[str] | None) -> list[int]:
    """Parse OSM voltage tag (can be semicolon-separated)"""
    if not v:
        return []
    if isinstance(v, list):
        v = ";".join(v)
    return [int(x.strip()) for x in str(v).split(";") if x.strip().isdigit()]


def get_substation_type(tags: dict) -> str:
    """Determine substation type from tags"""
    if tags.get("substation"):
        return tags["substation"]
    # Infer from voltage
    voltages = parse_voltage(tags.get("voltage"))
    if voltages and max(voltages) >= 69000:
        return "transmission"
    return "distribution"


def convert_osm_substation(elem: dict) -> dict:
    """Convert OSM substation to simulator format"""
    tags = elem.get("tags", {})
    voltages = parse_voltage(tags.get("voltage"))

    # Extract location - handle both node and way types
    lat = elem.get("lat")
    lon = elem.get("lon")

    if lat is None or lon is None:
        # For way-type, calculate center from geometry
        if "geometry" in elem and elem["geometry"]:
            lat = sum(p.get("lat", 0) for p in elem["geometry"]) / len(elem["geometry"])
            lon = sum(p.get("lon", 0) for p in elem["geometry"]) / len(elem["geometry"])
        elif "center" in elem:
            lat = elem["center"].get("lat")
            lon = elem["center"].get("lon")

    return {
        "name": tags.get("name", tags.get("ref", f"SUB-{elem['id']}")),
        "code": f"SUB-OSM-{elem['id']}",
        "osm_id": str(elem["id"]),
        "osm_power": "substation",
        "substation_type": get_substation_type(tags),
        "voltage": max(voltages) if voltages else None,
        "voltages": voltages if len(voltages) > 1 else None,
        "operator": tags.get("operator", tags.get("operator:en")),
        "location": {
            "latitude": lat,
            "longitude": lon,
        },
        "raw_tags": {k: v for k, v in tags.items() if k not in ["name", "ref", "operator", "operator:en"]},
    }


def convert_osm_power_line(elem: dict) -> dict:
    """Convert OSM power line to simulator format"""
    tags = elem.get("tags", {})
    voltages = parse_voltage(tags.get("voltage"))

    # Extract coordinates
    coords = []
    if "geometry" in elem:
        coords = [[p.get("lon", 0), p.get("lat", 0)] for p in elem["geometry"]]

    return {
        "code": f"LINE-OSM-{elem['id']}",
        "osm_id": str(elem["id"]),
        "osm_power": tags.get("power", "line"),
        "name": tags.get("name"),
        "voltage": max(voltages) if voltages else None,
        "voltages": voltages if len(voltages) > 1 else None,
        "frequency": int(tags["frequency"]) if tags.get("frequency", "").isdigit() else 50,
        "type": "overhead" if tags.get("power") == "line" else "underground",
        "location": tags.get("location", "overhead" if tags.get("power") == "line" else "underground"),
        "operator": tags.get("operator", tags.get("operator:en")),
        "circuits": int(tags["circuits"]) if tags.get("circuits", "").isdigit() else None,
        "cables": int(tags["cables"]) if tags.get("cables", "").isdigit() else None,
        "wires": tags.get("wires"),
        "coordinates": coords,
        "num_points": len(coords),
        "raw_tags": {k: v for k, v in tags.items() if k not in ["name", "operator", "operator:en"]},
    }


def convert_osm_generator(elem: dict) -> dict:
    """Convert OSM generator to simulator meter/generator format"""
    tags = elem.get("tags", {})

    return {
        "code": f"GEN-OSM-{elem['id']}",
        "osm_id": str(elem["id"]),
        "osm_power": "generator",
        "source": tags.get("generator:source", tags.get("plant:source", "unknown")),
        "method": tags.get("generator:method"),
        "output_electric": tags.get("generator:output:electric"),
        "name": tags.get("name"),
        "operator": tags.get("operator", tags.get("operator:en")),
        "location": {
            "latitude": elem.get("lat", elem.get("center", {}).get("lat")),
            "longitude": elem.get("lon", elem.get("center", {}).get("lon")),
        },
        "raw_tags": {k: v for k, v in tags.items() if k not in ["name", "operator", "operator:en"]},
    }


def convert_osm_transformer(elem: dict) -> dict:
    """Convert OSM transformer to simulator format"""
    tags = elem.get("tags", {})
    voltage_primary = parse_voltage(tags.get("voltage:primary"))
    voltage_secondary = parse_voltage(tags.get("voltage:secondary"))

    return {
        "code": f"TRF-OSM-{elem['id']}",
        "osm_id": str(elem["id"]),
        "osm_power": "transformer",
        "voltage_primary": voltage_primary[0] if voltage_primary else None,
        "voltage_secondary": voltage_secondary[0] if voltage_secondary else None,
        "phases": tags.get("transformer:phases"),
        "location": {
            "latitude": elem.get("lat", elem.get("center", {}).get("lat")),
            "longitude": elem.get("lon", elem.get("center", {}).get("lon")),
        },
        "raw_tags": tags,
    }


def convert_osm_to_simulator(osm_data: dict) -> dict:
    """Convert full OSM Overpass response to simulator templates"""
    result = {
        "power_lines": [],
        "substations": [],
        "generators": [],
        "transformers": [],
        "towers": [],
        "poles": [],
        "other": [],
    }

    for elem in osm_data.get("elements", []):
        elem_type = elem.get("type")
        tags = elem.get("tags", {})
        power_type = tags.get("power")

        if not power_type:
            continue

        if elem_type == "way" and power_type in ("line", "cable", "minor_line"):
            result["power_lines"].append(convert_osm_power_line(elem))

        elif power_type == "substation":
            result["substations"].append(convert_osm_substation(elem))

        elif power_type == "generator":
            result["generators"].append(convert_osm_generator(elem))

        elif power_type == "transformer":
            result["transformers"].append(convert_osm_transformer(elem))

        elif power_type == "tower":
            result["towers"].append({
                "osm_id": str(elem["id"]),
                "location": {"latitude": elem.get("lat"), "longitude": elem.get("lon")},
                "ref": tags.get("ref"),
            })

        elif power_type == "pole":
            result["poles"].append({
                "osm_id": str(elem["id"]),
                "location": {"latitude": elem.get("lat"), "longitude": elem.get("lon")},
                "ref": tags.get("ref"),
            })

        else:
            result["other"].append({
                "osm_id": str(elem["id"]),
                "power_type": power_type,
                "location": {"latitude": elem.get("lat"), "longitude": elem.get("lon")},
                "tags": tags,
            })

    return result


def generate_pandapower_lines(simulator_data: dict) -> list[dict]:
    """Convert simulator power lines to pandapower format"""
    pandapower_lines = []

    for line in simulator_data["power_lines"]:
        voltage_kv = (line.get("voltage") or 22000) / 1000

        pandapower_lines.append({
            "name": line["code"],
            "voltage_kv": voltage_kv,
            "type": line.get("type", "overhead"),
            "length_km": None,  # Would need to calculate from coordinates
            "conductor": line.get("conductor", "ACSR 240"),
            "coordinates": line.get("coordinates", []),
            "from_substation": None,
            "to_substation": None,
        })

    return pandapower_lines


def main():
    """Convert OSM data files to simulator format"""
    data_dir = Path(__file__).parent / "data" / "korat"

    # Process way 402761973
    way_file = data_dir / "way_402761973.json"
    if way_file.exists():
        with open(way_file) as f:
            way_obj = json.load(f)

        way_elem = {
            "type": "way",
            "id": way_obj["osm_id"],
            "tags": way_obj["tags"],
            "geometry": way_obj["geometry"],
        }

        osm_data = {"elements": [way_elem]}
        result = convert_osm_to_simulator(osm_data)

        out_path = data_dir / "way_402761973_simulator.json"
        with open(out_path, "w") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)

        logger.info(f"Converted way 402761973 → {out_path}")
        print(f"\n=== Converted: Way 402761973 ===")
        print(f"  Power lines: {len(result['power_lines'])}")
        if result["power_lines"]:
            line = result["power_lines"][0]
            print(f"  Code: {line['code']}")
            print(f"  Voltage: {line['voltage']}V")
            print(f"  Operator: {line['operator']}")
            print(f"  Points: {line['num_points']}")

    # Process full Korat area
    korat_file = data_dir / "korat_power_grid.json"
    if korat_file.exists():
        with open(korat_file) as f:
            korat_data = json.load(f)

        result = convert_osm_to_simulator(korat_data)

        out_path = data_dir / "korat_simulator.json"
        with open(out_path, "w") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)

        logger.info(f"Converted Korat area → {out_path}")
        print(f"\n=== Converted: Korat Area ===")
        print(f"  Power lines: {len(result['power_lines'])}")
        print(f"  Substations: {len(result['substations'])}")
        print(f"  Generators: {len(result['generators'])}")
        print(f"  Transformers: {len(result['transformers'])}")
        print(f"  Towers: {len(result['towers'])}")
        print(f"  Poles: {len(result['poles'])}")


if __name__ == "__main__":
    main()
