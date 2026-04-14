"""
Quick fetch of Thailand HV transmission grid using direct Overpass QL query.
Faster than osmnx.features_from_point for large areas.
"""

import requests
import geopandas as gpd
import json
import os
from io import StringIO

# Thailand HV voltage levels
HV_VOLTAGES = ["500000", "230000", "115000"]

# Bangkok area
BANGKOK_LAT = 13.757559
BANGKOK_LON = 100.688337
SEARCH_RADIUS_KM = 50  # ~0.45 degrees


def fetch_via_overpass_qql(lat, lon, radius_km, output_file):
    """
    Fetch HV transmission lines using direct Overpass QL query.
    Much faster than osmnx for large areas.
    """
    # Convert km to degrees (rough approximation)
    radius_deg = radius_km / 111.0
    
    south = lat - radius_deg
    north = lat + radius_deg
    west = lon - radius_deg
    east = lon + radius_deg
    
    # Overpass QL query
    query = f"""
    [out:json][timeout:120];
    (
      way["power"="line"]["voltage"="500000"]({south},{west},{north},{east});
      way["power"="line"]["voltage"="230000"]({south},{west},{north},{east});
      way["power"="line"]["voltage"="115000"]({south},{west},{north},{east});
    );
    out geom;
    """
    
    print(f"Fetching HV transmission lines near ({lat}, {lon})...")
    print(f"BBox: ({south:.4f}, {west:.4f}) to ({north:.4f}, {east:.4f})")
    print(f"Querying Overpass API (api.overpass-api.de)...")
    
    try:
        # Send query to Overpass API
        response = requests.post(
            "https://api.overpass-api.de/api/interpreter",
            data={"data": query},
            timeout=120
        )
        
        if response.status_code != 200:
            print(f"Error: HTTP {response.status_code}")
            print(response.text[:500])
            return None
        
        data = response.json()
        print(f"Retrieved {len(data['elements'])} elements")
        
        # Convert to GeoJSON
        features = []
        for elem in data["elements"]:
            if elem["type"] != "way" or "geometry" not in elem:
                continue
            
            coords = [(p["lon"], p["lat"]) for p in elem["geometry"]]
            
            if len(coords) < 2:
                continue
            
            feature = {
                "type": "Feature",
                "geometry": {
                    "type": "LineString",
                    "coordinates": coords
                },
                "properties": {
                    "osm_id": elem["id"],
                    "power": elem.get("power", "line"),
                    "voltage": elem.get("voltage", ""),
                    "operator": elem.get("operator", ""),
                    "cable": elem.get("cable", "no"),
                }
            }
            features.append(feature)
        
        if not features:
            print("No HV transmission lines found in this area.")
            return None
        
        print(f"Converted {len(features)} ways to GeoJSON features")
        
        # Create GeoDataFrame
        geojson = {
            "type": "FeatureCollection",
            "features": features
        }
        
        gdf = gpd.GeoDataFrame.from_features(geojson)
        
        # Save
        os.makedirs(os.path.dirname(os.path.abspath(output_file)), exist_ok=True)
        gdf.to_file(output_file, driver="GeoJSON")
        print(f"\nSaved to {output_file}")
        
        # Summary
        if "voltage" in gdf.columns:
            print("\nVoltage breakdown:")
            for volt in gdf["voltage"].unique():
                count = (gdf["voltage"] == volt).sum()
                kv = int(volt) / 1000 if str(volt).isdigit() else volt
                print(f"  - {kv} kV: {count}")
        
        return gdf
        
    except requests.Timeout:
        print("ERROR: Request timed out. Try smaller radius or wait and retry.")
        return None
    except Exception as e:
        print(f"ERROR: {e}")
        return None


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--lat", type=float, default=BANGKOK_LAT)
    parser.add_argument("--lon", type=float, default=BANGKOK_LON)
    parser.add_argument("--radius-km", type=int, default=50)
    parser.add_argument("--output", type=str, default="data/thailand_hv_grid.geojson")
    
    args = parser.parse_args()
    
    fetch_via_overpass_qql(args.lat, args.lon, args.radius_km, args.output)
