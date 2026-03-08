import osmnx as ox
import argparse
import os

def fetch_building_footprints(lat, lon, dist=500, output_file="village_houses.geojson"):
    """
    Fetches building footprints from OpenStreetMap within a given distance 
    from a central coordinate and saves them as a GeoJSON file.
    """
    print(f"Fetching building footprints around ({lat}, {lon}) within {dist}m...")
    point = (lat, lon)
    
    # Configure OSMnx to be less chatty
    ox.settings.log_console = False
    ox.settings.use_cache = True
    
    try:
        # Fetch geometries with the 'building' tag
        buildings = ox.features_from_point(point, tags={'building': True}, dist=dist)
        
        if buildings.empty:
            print("No buildings found in this area.")
            return None
            
        print(f"Successfully retrieved {len(buildings)} building footprints.")
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(os.path.abspath(output_file)), exist_ok=True)
        
        # Save to GeoJSON
        buildings.to_file(output_file, driver='GeoJSON')
        print(f"Saved building footprints to {output_file}")
        
        return buildings
        
    except Exception as e:
        print(f"Error fetching data from OSM: {e}")
        return None

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch OSM Building Footprints for GridTokenX")
    parser.add_argument("--lat", type=float, default=13.757559, help="Village center Latitude")
    parser.add_argument("--lon", type=float, default=100.688337, help="Village center Longitude")
    parser.add_argument("--dist", type=int, default=500, help="Search radius in meters")
    parser.add_argument("--output", type=str, default="data/village_buildings.geojson", help="Output GeoJSON path")

    args = parser.parse_args()
    
    fetch_building_footprints(args.lat, args.lon, args.dist, args.output)
