import json
import argparse
import os
from shapely.geometry import shape

def convert_geojson_to_locations(geojson_path, output_path):
    """
    Converts a GeoJSON file of building footprints into the 
    Simulator's initial_locations.json format.
    """
    if not os.path.exists(geojson_path):
        print(f"Error: {geojson_path} not found.")
        return

    print(f"Loading building footprints from {geojson_path}...")
    with open(geojson_path, 'r') as f:
        data = json.load(f)
        
    features = data.get('features', [])
    if not features:
        print("No features found in GeoJSON.")
        return
        
    locations = []
    
    # Use the first feature's center as the base location for the village
    first_geom = shape(features[0]['geometry'])
    base_center = first_geom.centroid
    base_location = {
        "lat": base_center.y,
        "lng": base_center.x
    }
    
    for i, feature in enumerate(features):
        props = feature.get('properties', {})
        geom = shape(feature['geometry'])
        
        # Calculate the centroid of the building polygon
        centroid = geom.centroid
        
        # Try to get a meaningful name from OSM tags
        name = props.get('name')
        if not name:
            housenumber = props.get('addr:housenumber', '')
            street = props.get('addr:street', '')
            if housenumber or street:
                name = f"House {housenumber} {street}".strip()
            else:
                name = f"OSM_Building_{props.get('id', i)}"
        
        location_data = {
            "meter_index": i + 1,
            "name": name,
            "latitude": centroid.y,
            "longitude": centroid.x
        }
        
        # Include the area in m2 (approximate, since EPSG:4326 is degrees, 
        # this is just for relative sizing unless projected, but we'll store the geometry area)
        # For a rough estimate in m2 near equator, multiply by 111320^2
        # A more rigorous approach requires projecting to a local CRS, 
        # but for simple footprint tagging, the raw area in degrees is okay to keep natively
        # or we just rely on the shape.
        
        locations.append(location_data)

    output_data = {
        "base_location": base_location,
        "locations": locations
    }
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump(output_data, f, indent=4, ensure_ascii=False)
        
    print(f"Successfully converted {len(locations)} locations.")
    print(f"Saved to {output_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert OSM GeoJSON to Simulator Locations")
    parser.add_argument("--input", type=str, default="data/village_houses.geojson", help="Input GeoJSON path")
    parser.add_argument("--output", type=str, default="src/smart_meter_simulator/config/initial_locations.json", help="Output locations JSON path")

    args = parser.parse_args()
    
    convert_geojson_to_locations(args.input, args.output)
