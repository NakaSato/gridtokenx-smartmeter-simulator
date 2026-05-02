import requests
import json
import os

BASE_URL = "https://gisportal.egat.co.th/arcgis/rest/services/Hosted"

LAYERS = {
    "substations": f"{BASE_URL}/Power_LOAD/FeatureServer/0",
    "district_load": f"{BASE_URL}/Power_LOAD/FeatureServer/1",
    "power_plants": f"{BASE_URL}/Power_GEN/FeatureServer/0",
    "gen_zones": f"{BASE_URL}/Power_GEN/FeatureServer/1",
    "gen_data": f"{BASE_URL}/Power_GEN/FeatureServer/2",
    "lines_section1": f"{BASE_URL}/Section1_Line/FeatureServer/0",
    "lines_section2": f"{BASE_URL}/Section2_Line/FeatureServer/0",
    "lines_section3": f"{BASE_URL}/Section3_Line/FeatureServer/0",
    "lines_section4": f"{BASE_URL}/Section4_Line/FeatureServer/0",
    "towers_section1": f"{BASE_URL}/Section1_Tower/FeatureServer/0",
    "towers_section2": f"{BASE_URL}/Section2_Tower/FeatureServer/0",
    "towers_section3": f"{BASE_URL}/Section3_Tower/FeatureServer/0",
    "towers_section4": f"{BASE_URL}/Section4_Tower/FeatureServer/0",
}

def fetch_layer(url, name):
    print(f"Fetching {name}...")
    all_features = []
    offset = 0
    limit = 1000
    
    # First get metadata to determine geometry type
    try:
        meta_res = requests.get(f"{url}?f=json")
        meta = meta_res.json()
        geom_type = meta.get("geometryType")
    except Exception as e:
        print(f"  Error getting metadata for {name}: {e}")
        return [], None

    while True:
        query_url = f"{url}/query"
        params = {
            "where": "1=1",
            "outFields": "*",
            "outSR": "4326",
            "f": "json",
            "resultOffset": offset,
            "resultRecordCount": limit
        }
        
        try:
            response = requests.get(query_url, params=params)
            if response.status_code != 200:
                print(f"  Error fetching {name}: {response.status_code}")
                break
                
            data = response.json()
            features = data.get("features", [])
            if not features:
                break
                
            all_features.extend(features)
            print(f"  Retrieved {len(all_features)} features...")
            
            if not data.get("exceededTransferLimit"):
                break
        except Exception as e:
            print(f"  Request failed for {name}: {e}")
            break
            
        offset += limit
        
    return all_features, geom_type

def esri_to_geojson(esri_features, geometry_type):
    geojson_features = []
    for feat in esri_features:
        attributes = feat.get("attributes", {})
        geometry = feat.get("geometry", {})
        
        if not geometry:
            continue

        if geometry_type == "esriGeometryPoint":
            coords = [geometry.get("x"), geometry.get("y")]
            geom = {"type": "Point", "coordinates": coords}
        elif geometry_type == "esriGeometryPolyline":
            paths = geometry.get("paths", [])
            if len(paths) == 1:
                geom = {"type": "LineString", "coordinates": paths[0]}
            elif len(paths) > 1:
                geom = {"type": "MultiLineString", "coordinates": paths}
            else:
                continue
        elif geometry_type == "esriGeometryPolygon":
            rings = geometry.get("rings", [])
            if len(rings) == 1:
                geom = {"type": "Polygon", "coordinates": rings}
            elif len(rings) > 1:
                geom = {"type": "MultiPolygon", "coordinates": [[r] for r in rings]}
            else:
                continue
        else:
            continue
            
        geojson_features.append({
            "type": "Feature",
            "geometry": geom,
            "properties": attributes
        })
        
    return {
        "type": "FeatureCollection",
        "features": geojson_features
    }

def main():
    output_dir = "data/geojson"
    os.makedirs(output_dir, exist_ok=True)
    
    # Fetch categorized data
    categories = {
        "load": ["substations", "district_load"],
        "gen": ["power_plants", "gen_zones", "gen_data"],
        "lines": ["lines_section1", "lines_section2", "lines_section3", "lines_section4"],
        "towers": ["towers_section1", "towers_section2", "towers_section3", "towers_section4"]
    }

    for cat_name, layer_keys in categories.items():
        all_cat_features = []
        for key in layer_keys:
            esri_feats, geom_type = fetch_layer(LAYERS[key], key.replace("_", " ").title())
            if esri_feats and geom_type:
                geojson = esri_to_geojson(esri_feats, geom_type)
                # Also save individual files
                with open(os.path.join(output_dir, f"egat_{key}.geojson"), "w") as f:
                    json.dump(geojson, f, indent=2)
                all_cat_features.extend(geojson["features"])
        
        # Save combined category file
        combined = {
            "type": "FeatureCollection",
            "features": all_cat_features
        }
        with open(os.path.join(output_dir, f"egat_combined_{cat_name}.geojson"), "w") as f:
            json.dump(combined, f, indent=2)

if __name__ == "__main__":
    main()

if __name__ == "__main__":
    main()
