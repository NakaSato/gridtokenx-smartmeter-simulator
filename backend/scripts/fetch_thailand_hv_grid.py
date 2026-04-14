"""
Fetch Thailand High Voltage Transmission Grid from OpenStreetMap.

Filters for EGAT-operated transmission lines (500kV, 230kV, 115kV)
and converts to formats compatible with pandapower simulation.

Usage:
    # Fetch small area (50km radius max recommended)
    uv run python scripts/fetch_thailand_hv_grid.py --mode fetch --lat 13.75 --lon 100.5 --dist 50000
    
    # Fetch large area using grid method (splits into multiple queries)
    uv run python scripts/fetch_thailand_hv_grid.py --mode fetch-grid --bbox 13.0,99.0,18.0,101.0
    
    # Convert to pandapower format
    uv run python scripts/fetch_thailand_hv_grid.py --mode convert --input data/thailand_hv_grid.geojson
"""

import osmnx as ox
import geopandas as gpd
import pandas as pd
import argparse
import json
import os
import time
from typing import Optional
from math import radians, sin, cos, sqrt, atan2

# Thailand HV voltage levels (in volts)
HV_VOLTAGES = ["500000", "230000", "115000"]
HV_VOLTAGE_KV = [500, 230, 115]

# EGAT operator identifiers
EGAT_OPERATOR_TH = "การไฟฟ้าฝ่ายผลิตแห่งประเทศไทย"
EGAT_WIKIDATA = "Q3050569"


def fetch_hv_transmission(
    lat: float,
    lon: float,
    dist: int = 50000,
    output_file: str = "data/thailand_hv_grid.geojson",
) -> Optional[gpd.GeoDataFrame]:
    """
    Fetch HV transmission lines from OSM using Overpass API.
    
    NOTE: dist should be <= 50000 (50km) to avoid Overpass timeout.
    For larger areas, use fetch_grid() instead.
    """
    print(f"Fetching HV transmission grid around ({lat}, {lon}) within {dist:,}m...")
    
    if dist > 50000:
        print(f"WARNING: dist {dist}m > 50km may timeout. Use --mode fetch-grid for large areas.")
        print("Proceeding anyway, but expect delays...")
    
    ox.settings.log_console = False
    ox.settings.use_cache = True
    
    hv_tags = {
        "power": "line",
        "voltage": HV_VOLTAGES,
    }
    
    try:
        print(f"Querying Overpass API...")
        grid_features = ox.features_from_point((lat, lon), tags=hv_tags, dist=dist)
        
        if grid_features.empty:
            print("No HV transmission lines found. Try increasing --dist or changing location.")
            return None
        
        print(f"Retrieved {len(grid_features)} HV transmission lines.")
        _print_summary(grid_features)
        
        os.makedirs(os.path.dirname(os.path.abspath(output_file)), exist_ok=True)
        grid_features.to_file(output_file, driver="GeoJSON")
        print(f"\nSaved to {output_file}")
        
        return grid_features
        
    except Exception as e:
        print(f"Error fetching OSM data: {e}")
        return None


def fetch_grid(
    south: float,
    west: float,
    north: float,
    east: float,
    step_deg: float = 0.5,
    output_file: str = "data/thailand_hv_grid.geojson",
) -> Optional[gpd.GeoDataFrame]:
    """
    Fetch HV grid over large bbox by splitting into smaller queries.
    
    step_deg: Grid step in degrees (~50km at equator). Smaller = more queries but better coverage.
    """
    print(f"Fetching HV grid in bbox: ({south}, {west}) to ({north}, {east})")
    print(f"Grid step: {step_deg}° (~{step_deg*111:.0f}km)")
    
    ox.settings.use_cache = True
    ox.settings.overpass_settings = {"timeout": 180}
    
    hv_tags = {
        "power": "line",
        "voltage": HV_VOLTAGES,
    }
    
    all_features = []
    query_count = 0
    
    # Generate grid of query points
    lat_range = list(range(int(south), int(north) + 1))
    lon_range = list(range(int(west), int(east) + 1))
    
    for lat in lat_range:
        for lon in lon_range:
            query_count += 1
            print(f"\nQuery {query_count}: ({lat}, {lon})")
            
            try:
                features = ox.features_from_point(
                    (lat, lon),
                    tags=hv_tags,
                    dist=int(step_deg * 111_000),  # Convert degrees to meters
                )
                
                if not features.empty:
                    all_features.append(features)
                    print(f"  Retrieved {len(features)} lines")
                else:
                    print(f"  No data")
                
                # Rate limit: Overpass allows ~2 queries/minute
                time.sleep(30)
                
            except Exception as e:
                print(f"  Error: {e}")
                time.sleep(60)  # Longer wait on error
    
    if not all_features:
        print("No data retrieved from any query point.")
        return None
    
    # Merge all features
    print(f"\nMerging {len(all_features)} query results...")
    merged_gdf = pd.concat(all_features, ignore_index=True)
    
    # Remove duplicates (same OSM ID may appear in multiple queries)
    if 'osmid' in merged_gdf.columns:
        before_dedup = len(merged_gdf)
        merged_gdf = merged_gdf.drop_duplicates(subset=['osmid'])
        print(f"Removed {before_dedup - len(merged_gdf)} duplicates")
    
    print(f"\nTotal unique HV transmission lines: {len(merged_gdf)}")
    _print_summary(merged_gdf)
    
    os.makedirs(os.path.dirname(os.path.abspath(output_file)), exist_ok=True)
    merged_gdf.to_file(output_file, driver="GeoJSON")
    print(f"Saved to {output_file}")
    
    return merged_gdf


def _print_summary(gdf: gpd.GeoDataFrame):
    """Print summary statistics of retrieved data."""
    if "voltage" in gdf.columns:
        print("\nVoltage breakdown:")
        voltage_counts = gdf["voltage"].value_counts().head(10)
        for volt, count in voltage_counts.items():
            kv = int(volt) / 1000 if str(volt).isdigit() else volt
            print(f"  - {kv} kV: {count}")
    
    if "operator" in gdf.columns:
        print("\nTop operators:")
        op_counts = gdf["operator"].value_counts().head(5)
        for op, count in op_counts.items():
            print(f"  - {op}: {count}")


def convert_to_pandapower_format(
    input_file: str,
    output_file: str = "data/pandapower_hv_grid.json",
) -> dict:
    """
    Convert OSM GeoJSON to pandapower-compatible format.
    
    Output format:
    {
        "buses": [{"id": "...", "lat": ..., "lon": ..., "voltage_kv": ...}],
        "lines": [
            {
                "from_bus": "...",
                "to_bus": "...",
                "length_km": ...,
                "voltage_kv": ...,
                "r_ohm_per_km": ...,
                "x_ohm_per_km": ...,
            }
        ],
        "substations": [...]
    }
    """
    print(f"Converting {input_file} to pandapower format...")
    
    gdf = gpd.read_file(input_file)
    
    buses = []
    lines = []
    bus_id_map = {}
    bus_counter = 0
    
    for idx, row in gdf.iterrows():
        geom = row.geometry
        
        if geom is None:
            continue
        
        voltage_str = str(row.get("voltage", "0"))
        voltage_kv = int(voltage_str) / 1000 if voltage_str.isdigit() else 0
        
        if hasattr(geom, 'geom_type'):
            if geom.geom_type in ['Point', 'MultiPoint']:
                # Substation point
                if geom.geom_type == 'MultiPoint':
                    geom = geom.geoms[0]
                
                bus_id = f"bus_{bus_counter}"
                buses.append({
                    "id": bus_id,
                    "lat": geom.y,
                    "lon": geom.x,
                    "voltage_kv": voltage_kv,
                    "type": "substation",
                })
                bus_id_map[f"point_{idx}"] = bus_id
                bus_counter += 1
                
            elif geom.geom_type in ['LineString', 'MultiLineString']:
                # Power line
                if geom.geom_type == 'MultiLineString':
                    coords = list(geom.geoms[0].coords)
                else:
                    coords = list(geom.coords)
                
                if len(coords) < 2:
                    continue
                
                start_coord = coords[0]
                end_coord = coords[-1]
                
                start_key = f"{start_coord[0]:.6f},{start_coord[1]:.6f}"
                end_key = f"{end_coord[0]:.6f},{end_coord[1]:.6f}"
                
                if start_key not in bus_id_map:
                    bus_id_map[start_key] = f"bus_{bus_counter}"
                    buses.append({
                        "id": bus_id_map[start_key],
                        "lat": start_coord[1],
                        "lon": start_coord[0],
                        "voltage_kv": voltage_kv,
                        "type": "line_endpoint",
                    })
                    bus_counter += 1
                
                if end_key not in bus_id_map:
                    bus_id_map[end_key] = f"bus_{bus_counter}"
                    buses.append({
                        "id": bus_id_map[end_key],
                        "lat": end_coord[1],
                        "lon": end_coord[0],
                        "voltage_kv": voltage_kv,
                        "type": "line_endpoint",
                    })
                    bus_counter += 1
                
                length_km = _haversine_distance(
                    start_coord[1], start_coord[0], end_coord[1], end_coord[0]
                )
                
                cable_type = str(row.get("cable", "no")).lower()
                r_ohm, x_ohm = _estimate_line_params(voltage_kv, cable_type)
                
                lines.append({
                    "from_bus": bus_id_map[start_key],
                    "to_bus": bus_id_map[end_key],
                    "length_km": length_km,
                    "voltage_kv": voltage_kv,
                    "conductor_type": row.get("line_type", "overhead"),
                    "cable": cable_type,
                    "r_ohm_per_km": r_ohm,
                    "x_ohm_per_km": x_ohm,
                    "osm_id": row.get("osmid", idx),
                })
    
    substations = _extract_substations(gdf, bus_id_map)
    
    result = {
        "buses": buses,
        "lines": lines,
        "substations": substations,
        "metadata": {
            "source": "OpenStreetMap via Overpass API",
            "total_buses": len(buses),
            "total_lines": len(lines),
            "total_substations": len(substations),
            "voltage_levels_kv": sorted(list(set(l["voltage_kv"] for l in lines if l["voltage_kv"] > 0))),
        },
    }
    
    os.makedirs(os.path.dirname(os.path.abspath(output_file)), exist_ok=True)
    with open(output_file, "w") as f:
        json.dump(result, f, indent=2)
    
    print(f"\nConverted to pandapower format:")
    print(f"  Buses: {len(buses)}")
    print(f"  Lines: {len(lines)}")
    print(f"  Substations: {len(substations)}")
    print(f"  Saved to {output_file}")
    
    return result


def _haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate Haversine distance between two points in km."""
    R = 6371.0  # Earth radius in km
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    
    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    
    return R * c


def _estimate_line_params(voltage_kv: int, cable_type: str) -> tuple[float, float]:
    """
    Estimate resistance (R) and reactance (X) per km.
    
    Typical overhead line parameters (ACSR):
    - 500 kV: R ≈ 0.06 Ω/km, X ≈ 0.35 Ω/km
    - 230 kV: R ≈ 0.12 Ω/km, X ≈ 0.40 Ω/km
    - 115 kV: R ≈ 0.18 Ω/km, X ≈ 0.42 Ω/km
    """
    if cable_type in ["yes", "underground"]:
        params = {
            500: (0.08, 0.25),
            230: (0.15, 0.28),
            115: (0.22, 0.32),
        }
    else:
        params = {
            500: (0.06, 0.35),
            230: (0.12, 0.40),
            115: (0.18, 0.42),
        }
    
    return params.get(voltage_kv, (0.2, 0.4))


def _extract_substations(gdf: gpd.GeoDataFrame, bus_id_map: dict) -> list[dict]:
    """Extract substation information."""
    substations = []
    
    if "power" in gdf.columns:
        substation_mask = gdf["power"] == "substation"
        substation_gdf = gdf[substation_mask]
        
        for idx, row in substation_gdf.iterrows():
            geom = row.geometry
            if geom is None:
                continue
            
            if hasattr(geom, "centroid"):
                geom = geom.centroid
            
            voltage_list = []
            if "voltage" in row:
                volt_str = str(row["voltage"])
                voltage_list = [
                    int(v) / 1000 for v in volt_str.split(";") if v.strip().isdigit()
                ]
            
            substations.append({
                "id": f"sub_{idx}",
                "lat": geom.y,
                "lon": geom.x,
                "voltage_kv": voltage_list,
                "name": row.get("name", ""),
                "operator": row.get("operator", ""),
                "osm_id": row.get("osmid", idx),
            })
    
    return substations


def main():
    parser = argparse.ArgumentParser(
        description="Fetch Thailand HV Transmission Grid from OSM"
    )
    parser.add_argument(
        "--mode",
        choices=["fetch", "convert", "fetch-convert", "fetch-grid"],
        default="fetch",
        help="Operation mode",
    )
    parser.add_argument("--lat", type=float, default=13.757559, help="Center latitude")
    parser.add_argument("--lon", type=float, default=100.688337, help="Center longitude")
    parser.add_argument("--dist", type=int, default=50000, help="Search radius (meters, max 50km recommended)")
    parser.add_argument("--bbox", type=str, help="Bounding box: south,west,north,east")
    parser.add_argument("--input", type=str, help="Input GeoJSON file (for convert mode)")
    parser.add_argument(
        "--output", type=str, default="data/thailand_hv_grid.geojson", help="Output file"
    )
    parser.add_argument(
        "--output-pandapower",
        type=str,
        default="data/pandapower_hv_grid.json",
        help="Pandapower output JSON",
    )
    parser.add_argument(
        "--step-deg",
        type=float,
        default=0.5,
        help="Grid step in degrees for fetch-grid mode (default: 0.5° ≈ 50km)",
    )
    
    args = parser.parse_args()
    
    # Mode: fetch (single point)
    if args.mode in ["fetch", "fetch-convert"]:
        gdf = fetch_hv_transmission(args.lat, args.lon, args.dist, args.output)
        
        if gdf is None and args.mode == "fetch":
            print("No data fetched. Exiting.")
            return
    
    # Mode: fetch-grid (large area)
    elif args.mode == "fetch-grid":
        if not args.bbox:
            print("ERROR: --bbox required for fetch-grid mode")
            print("Example: --bbox 13.0,99.0,18.0,101.0")
            return
        
        south, west, north, east = map(float, args.bbox.split(","))
        gdf = fetch_grid(south, west, north, east, args.step_deg, args.output)
        
        if gdf is None:
            print("No data fetched. Exiting.")
            return
    
    # Mode: convert
    if args.mode in ["convert", "fetch-convert", "fetch-grid"]:
        input_file = args.input if args.input else args.output
        
        if not os.path.exists(input_file):
            print(f"Input file not found: {input_file}")
            print("Run with --mode fetch first, or provide existing GeoJSON with --input")
            return
        
        convert_to_pandapower_format(input_file, args.output_pandapower)
    
    print("\nDone!")


if __name__ == "__main__":
    main()
