import osmnx as ox
import argparse
import os
import json

def fetch_osm_grid(lat, lon, dist=1000, output_file="data/osm_electrical_grid.geojson"):
    """
    Fetches electrical grid infrastructure from OpenStreetMap within a given distance 
    from a central coordinate and saves them as a GeoJSON file.
    
    Tags:
    - power=line, minor_line
    - power=substation, transformer
    - power=tower, pole
    - power=generator, plant
    """
    print(f"Fetching OSM electrical grid infrastructure around ({lat}, {lon}) within {dist}m...")
    point = (lat, lon)
    
    # Configure OSMnx
    ox.settings.log_console = False
    ox.settings.use_cache = True
    
    # Define tags for electrical grid
    grid_tags = {
        'power': [
            'line', 'minor_line', 'substation', 'transformer', 
            'tower', 'pole', 'generator', 'plant', 'cable'
        ]
    }
    
    try:
        # Fetch geometries with the power tags
        print(f"Querying Overpass API for power tags in {dist}m radius...")
        grid_features = ox.features_from_point(point, tags=grid_tags, dist=dist)
        
        if grid_features.empty:
            print("No electrical grid infrastructure found in this area in OSM.")
            return None
            
        print(f"Successfully retrieved {len(grid_features)} grid elements from OSM.")
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(os.path.abspath(output_file)), exist_ok=True)
        
        # Save to GeoJSON
        # We need to drop some complex types that might fail GeoJSON export if needed, 
        # but usually geopandas handles it well.
        grid_features.to_file(output_file, driver='GeoJSON')
        print(f"Saved electrical grid to {output_file}")
        
        # Summary of types found
        if 'power' in grid_features.columns:
            counts = grid_features['power'].value_counts()
            print("\nInfrastructure Summary:")
            for p_type, count in counts.items():
                print(f" - {p_type}: {count}")
        
        return grid_features
        
    except Exception as e:
        print(f"Error fetching data from OSM: {e}")
        return None

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch OSM Electrical Grid Infrastructure for GridTokenX")
    parser.add_argument("--lat", type=float, default=13.757559, help="Center Latitude")
    parser.add_argument("--lon", type=float, default=100.688337, help="Center Longitude")
    parser.add_argument("--dist", type=int, default=1000, help="Search radius in meters")
    parser.add_argument("--output", type=str, default="data/osm_electrical_grid.geojson", help="Output GeoJSON path")

    args = parser.parse_args()
    
    fetch_osm_grid(args.lat, args.lon, args.dist, args.output)
