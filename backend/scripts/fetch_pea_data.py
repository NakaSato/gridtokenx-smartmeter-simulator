import requests
import json
import os

BASE_URL = "https://gisportal.pea.co.th/arcgis/rest/services/Hosted/TPM_GIS_Data/FeatureServer"

def fetch_layer(layer_id, name):
    print(f"Fetching {name} (Layer {layer_id})...")
    url = f"{BASE_URL}/{layer_id}"
    all_features = []
    offset = 0
    limit = 1000
    
    # Get metadata
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
    
    # Layers identified from FeatureServer metadata
    layers = {
        0: "HVCOND_MERE_F",
        1: "HVCOND_MERGE",
        2: "HVMVCOND_Merge",
        3: "HVMVCOND_Merge_F",
        4: "NOHV_MVCOND_MERGE",
        5: "NOHV_MVCOND_MERGE_F",
        6: "GIS_T_STATION",
        7: "HVEGAT_LINK_HVCB",
        8: "HVEGAT_LINK_HVCB_L_Merge_F",
        9: "HVEGAT_LINK_HVCB_Merge_F",
        10: "HVEGAT_LINK_MVCB",
        11: "HVEGAT_LINK_MVCB_Merge_F",
        12: "MVEGAT_LINK_MVCB",
        13: "MVEGAT_LINK_MVCB_Merge_F",
        14: "PartGen_Grid_Capa_PEA_AVAL"
    }

    for layer_id, layer_name in layers.items():
        esri_feats, geom_type = fetch_layer(layer_id, layer_name)
        if esri_feats and geom_type:
            geojson = esri_to_geojson(esri_feats, geom_type)
            output_file = os.path.join(output_dir, f"pea_{layer_name.lower()}.geojson")
            with open(output_file, "w") as f:
                json.dump(geojson, f, indent=2)
            print(f"  Saved to {output_file}")

if __name__ == "__main__":
    main()
