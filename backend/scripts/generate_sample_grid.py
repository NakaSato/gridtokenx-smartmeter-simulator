"""
Generate sample Thailand HV transmission grid data for testing.
Use this when Overpass API is unavailable or for development testing.

Based on real Thailand grid characteristics:
- 500 kV: Bulk transmission (EGAT)
- 230 kV: Major transmission (EGAT)
- 115 kV: Subtransmission (EGAT)
"""

import geopandas as gpd
import pandas as pd
import json
import os
from shapely.geometry import LineString, Point
import numpy as np

def generate_sample_thailand_grid(output_file="data/thailand_hv_grid_sample.geojson"):
    """
    Generate realistic sample HV transmission grid data for Thailand.
    Based on actual EGAT grid topology around Bangkok area.
    """
    print("Generating sample Thailand HV transmission grid...")
    
    # Real Thailand substations (approximate locations)
    substations = [
        {"name": "Bangkok North", "lat": 13.95, "lon": 100.60, "voltages": ["500000", "230000"]},
        {"name": "Bangkok South", "lat": 13.55, "lon": 100.55, "voltages": ["500000", "230000"]},
        {"name": "Nonthaburi", "lat": 13.86, "lon": 100.52, "voltages": ["230000", "115000"]},
        {"name": "Samut Prakan", "lat": 13.60, "lon": 100.70, "voltages": ["230000", "115000"]},
        {"name": "Pathum Thani", "lat": 14.02, "lon": 100.53, "voltages": ["230000", "115000"]},
        {"name": "Chonburi East", "lat": 13.36, "lon": 100.98, "voltages": ["500000", "230000"]},
        {"name": "Ayutthaya North", "lat": 14.35, "lon": 100.57, "voltages": ["500000", "230000"]},
        {"name": "Saraburi", "lat": 14.53, "lon": 100.92, "voltages": ["230000", "115000"]},
    ]
    
    # Transmission lines (connect substations)
    lines = [
        # 500 kV backbone
        {"from": "Bangkok North", "to": "Bangkok South", "voltage": "500000", "cable": "no"},
        {"from": "Bangkok North", "to": "Ayutthaya North", "voltage": "500000", "cable": "no"},
        {"from": "Bangkok South", "to": "Chonburi East", "voltage": "500000", "cable": "no"},
        
        # 230 kV transmission
        {"from": "Bangkok North", "to": "Nonthaburi", "voltage": "230000", "cable": "no"},
        {"from": "Bangkok North", "to": "Pathum Thani", "voltage": "230000", "cable": "no"},
        {"from": "Bangkok South", "to": "Samut Prakan", "voltage": "230000", "cable": "no"},
        {"from": "Ayutthaya North", "to": "Saraburi", "voltage": "230000", "cable": "no"},
        {"from": "Chonburi East", "to": "Samut Prakan", "voltage": "230000", "cable": "no"},
        
        # 115 kV subtransmission
        {"from": "Nonthaburi", "to": "Pathum Thani", "voltage": "115000", "cable": "no"},
        {"from": "Samut Prakan", "to": "Bangkok South", "voltage": "115000", "cable": "underground"},
    ]
    
    # Create substation lookup
    sub_lookup = {s["name"]: s for s in substations}
    
    # Build GeoJSON features
    features = []
    
    # Add substations
    for sub in substations:
        features.append({
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [sub["lon"], sub["lat"]]
            },
            "properties": {
                "osmid": f"sub_{sub['name'].lower().replace(' ', '_')}",
                "power": "substation",
                "voltage": ";".join(sub["voltages"]),
                "operator": "การไฟฟ้าฝ่ายผลิตแห่งประเทศไทย",
                "name": sub["name"],
                "substation": "transmission"
            }
        })
    
    # Add transmission lines
    for i, line in enumerate(lines):
        from_sub = sub_lookup[line["from"]]
        to_sub = sub_lookup[line["to"]]
        
        # Create line with intermediate points for realism
        num_intermediate = max(2, int(np.random.uniform(3, 8)))
        
        lats = np.linspace(from_sub["lat"], to_sub["lat"], num_intermediate + 2)
        lons = np.linspace(from_sub["lon"], to_sub["lon"], num_intermediate + 2)
        
        # Add slight randomness to simulate real tower positions
        lats += np.random.normal(0, 0.005, num_intermediate + 2)
        lons += np.random.normal(0, 0.005, num_intermediate + 2)
        
        coords = [[lon, lat] for lat, lon in zip(lats, lons)]
        
        features.append({
            "type": "Feature",
            "geometry": {
                "type": "LineString",
                "coordinates": coords
            },
            "properties": {
                "osmid": f"line_{i}",
                "power": "line",
                "voltage": line["voltage"],
                "operator": "การไฟฟ้าฝ่ายผลิตแห่งประเทศไทย",
                "cable": line["cable"],
                "line_type": "overhead" if line["cable"] == "no" else "underground",
                "frequency": "50",
                "ref": f"EGAT-{line['voltage']}-{i:03d}"
            }
        })
    
    # Create GeoDataFrame
    geojson = {
        "type": "FeatureCollection",
        "features": features
    }
    
    gdf = gpd.GeoDataFrame.from_features(geojson)
    
    # Save
    os.makedirs(os.path.dirname(os.path.abspath(output_file)), exist_ok=True)
    gdf.to_file(output_file, driver="GeoJSON")
    
    print(f"\nGenerated sample data:")
    print(f"  Substations: {len(substations)}")
    print(f"  Transmission lines: {len(lines)}")
    print(f"  Total features: {len(features)}")
    print(f"  Saved to {output_file}")
    
    # Voltage breakdown
    lines_gdf = gdf[gdf["power"] == "line"]
    print(f"\nVoltage breakdown:")
    for volt in ["500000", "230000", "115000"]:
        count = (lines_gdf["voltage"] == volt).sum()
        if count > 0:
            print(f"  - {int(volt)//1000} kV: {count} lines")
    
    return gdf


def convert_sample_to_pandapower(
    input_file="data/thailand_hv_grid_sample.geojson",
    output_file="data/pandapower_hv_grid_sample.json"
):
    """Convert sample data to pandapower format."""
    print(f"\nConverting {input_file} to pandapower format...")
    
    gdf = gpd.read_file(input_file)
    
    buses = []
    lines = []
    bus_id_map = {}
    bus_counter = 0
    
    for idx, row in gdf.iterrows():
        geom = row.geometry
        if geom is None:
            continue
        
        props = row.to_dict()
        
        if geom.geom_type == "Point":
            # Substation
            voltages = str(props.get("voltage", "0")).split(";")
            voltage_kv = int(voltages[0]) / 1000 if voltages[0].isdigit() else 0
            
            bus_id = f"bus_{bus_counter}"
            buses.append({
                "id": bus_id,
                "lat": geom.y,
                "lon": geom.x,
                "voltage_kv": voltage_kv,
                "type": "substation",
                "name": props.get("name", ""),
            })
            bus_id_map[f"sub_{idx}"] = bus_id
            bus_counter += 1
            
        elif geom.geom_type == "LineString":
            # Transmission line
            coords = list(geom.coords)
            if len(coords) < 2:
                continue
            
            start_coord = coords[0]
            end_coord = coords[-1]
            
            voltage_str = str(props.get("voltage", "0"))
            voltage_kv = int(voltage_str) / 1000 if voltage_str.isdigit() else 0
            
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
            
            # Calculate length
            from math import radians, sin, cos, sqrt, atan2
            lat1, lon1, lat2, lon2 = map(radians, [
                start_coord[1], start_coord[0], end_coord[1], end_coord[0]
            ])
            dlat = lat2 - lat1
            dlon = lon2 - lon1
            a = sin(dlat/2)**2 + cos(lat1)*cos(lat2)*sin(dlon/2)**2
            c = 2 * atan2(sqrt(a), sqrt(1-a))
            length_km = 6371.0 * c
            
            # Line parameters
            cable_type = str(props.get("cable", "no")).lower()
            if cable_type in ["yes", "underground"]:
                params = {500: (0.08, 0.25), 230: (0.15, 0.28), 115: (0.22, 0.32)}
            else:
                params = {500: (0.06, 0.35), 230: (0.12, 0.40), 115: (0.18, 0.42)}
            
            r_ohm, x_ohm = params.get(voltage_kv, (0.2, 0.4))
            
            lines.append({
                "from_bus": bus_id_map[start_key],
                "to_bus": bus_id_map[end_key],
                "length_km": length_km,
                "voltage_kv": voltage_kv,
                "conductor_type": props.get("line_type", "overhead"),
                "cable": cable_type,
                "r_ohm_per_km": r_ohm,
                "x_ohm_per_km": x_ohm,
                "osm_id": props.get("osmid", idx),
            })
    
    result = {
        "buses": buses,
        "lines": lines,
        "substations": [],
        "metadata": {
            "source": "Sample data (simulated EGAT grid)",
            "total_buses": len(buses),
            "total_lines": len(lines),
            "total_substations": 0,
            "voltage_levels_kv": sorted(list(set(l["voltage_kv"] for l in lines if l["voltage_kv"] > 0))),
        }
    }
    
    os.makedirs(os.path.dirname(os.path.abspath(output_file)), exist_ok=True)
    with open(output_file, "w") as f:
        json.dump(result, f, indent=2)
    
    print(f"Converted to pandapower format:")
    print(f"  Buses: {len(buses)}")
    print(f"  Lines: {len(lines)}")
    print(f"  Saved to {output_file}")
    
    return result


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["generate", "convert", "generate-convert"], default="generate-convert")
    parser.add_argument("--output", type=str, default="data/thailand_hv_grid_sample.geojson")
    parser.add_argument("--output-pandapower", type=str, default="data/pandapower_hv_grid_sample.json")
    
    args = parser.parse_args()
    
    if args.mode in ["generate", "generate-convert"]:
        gdf = generate_sample_thailand_grid(args.output)
    
    if args.mode in ["convert", "generate-convert"]:
        input_file = args.output
        convert_sample_to_pandapower(input_file, args.output_pandapower)
    
    print("\nDone!")
