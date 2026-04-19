import json
import logging
from pathlib import Path
import osmnx as ox
import geopandas as gpd
from shapely.geometry import Point

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
GEOJSON_OUT = DATA_DIR / "koh_samui_grid_infrastructure.geojson"
MAPPING_OUT = DATA_DIR / "meter_to_grid_mapping.json"
REAL_LOCATIONS = BASE_DIR / "real_location.json"
ISLAND_LOCATIONS = BASE_DIR / "initial_locations_islands.json"

import requests
from shapely.geometry import LineString, Point, Polygon
import warnings
warnings.filterwarnings('ignore', category=UserWarning)

def fetch_grid_infrastructure():
    """Fetch high-voltage and local transmission lines from OSM via Overpass API."""
    if GEOJSON_OUT.exists():
        logger.info(f"Loading cached infrastructure from {GEOJSON_OUT}")
        return gpd.read_file(GEOJSON_OUT)
        
    logger.info("Fetching grid infrastructure for Koh Samui cluster via Overpass API...")
    
    overpass_urls = [
        "https://overpass-api.de/api/interpreter",
        "https://z.overpass-api.de/api/interpreter",
        "https://lz4.overpass-api.de/api/interpreter"
    ]
    
    # We use 'out geom;' to automatically fetch the coordinates for ways
    overpass_query = """
    [out:json][timeout:60];
    (
      way["power"="cable"](9.4000,99.7500,10.1500,100.1500);
      way["power"="line"](9.4000,99.7500,10.1500,100.1500);
      way["power"="minor_line"](9.4000,99.7500,10.1500,100.1500);
      node["power"="substation"](9.4000,99.7500,10.1500,100.1500);
      way["power"="substation"](9.4000,99.7500,10.1500,100.1500);
      node["power"="generator"](9.4000,99.7500,10.1500,100.1500);
      way["power"="generator"](9.4000,99.7500,10.1500,100.1500);
    );
    out geom;
    """
    
    import time
    data = None
    for url in overpass_urls:
        try:
            logger.info(f"Trying Overpass API: {url}")
            response = requests.post(url, data=overpass_query.encode('utf-8'), headers={'User-Agent': 'GridTokenX-Sim'})
            response.raise_for_status()
            data = response.json()
            break
        except Exception as e:
            logger.warning(f"Failed on {url}: {e}")
            time.sleep(2)
            
    if not data:
        raise Exception("All Overpass API endpoints failed.")
    
    features = []
    for element in data.get("elements", []):
        tags = element.get("tags", {})
        osm_id = element.get("id")
        osm_type = element.get("type")
        
        geom = None
        if osm_type == "node":
            geom = Point(element["lon"], element["lat"])
        elif osm_type == "way":
            geometry_nodes = element.get("geometry", [])
            if len(geometry_nodes) >= 2:
                coords = [(node["lon"], node["lat"]) for node in geometry_nodes if "lon" in node and "lat" in node]
                if coords:
                    if len(coords) >= 4 and coords[0] == coords[-1] and tags.get("power") in ["substation", "generator"]:
                        geom = Polygon(coords)
                    else:
                        geom = LineString(coords)
                        
        if geom:
            feature_data = {
                "osmid": str(osm_id),
                "element_type": osm_type,
                "geometry": geom
            }
            # Add all tags
            feature_data.update(tags)
            features.append(feature_data)
            
    gdf = gpd.GeoDataFrame(features, geometry="geometry", crs="EPSG:4326")
    logger.info(f"Retrieved {len(gdf)} physical power infrastructure features.")
    
    # Save to GeoJSON
    gdf.to_file(GEOJSON_OUT, driver="GeoJSON")
    logger.info(f"Successfully saved GeoJSON to {GEOJSON_OUT}")
    
    return gdf

def load_meter_coordinates():
    """Load simulated meter coordinates."""
    file_to_load = ISLAND_LOCATIONS if ISLAND_LOCATIONS.exists() else REAL_LOCATIONS
    logger.info(f"Loading meter locations from {file_to_load}")
    
    with open(file_to_load, "r") as f:
        # Check if it's a list of "lat, lon" strings or something else
        # real_location.json has format: [ "13.75, 100.66", ... ]
        try:
            content = f.read()
            # Try parsing as JSON first
            if content.strip().startswith('['):
                locations = json.loads(content)
            else:
                # Fallback if it's malformed like real_location.json (missing brackets in view_file)
                # Actually real_location.json had missing commas in the view_file output. We will manually parse.
                # Just extract any line that looks like "lat, lon"
                locations = []
                for line in content.split('\n'):
                    line = line.strip().strip(',').strip('"').strip("'")
                    if line and ',' in line:
                        locations.append(line)
        except Exception as e:
            logger.error(f"Failed to parse {file_to_load}: {e}")
            locations = []
            
    meters = []
    for i, loc in enumerate(locations):
        parts = loc.split(',')
        if len(parts) == 2:
            lat = float(parts[0].strip())
            lon = float(parts[1].strip())
            meters.append({
                "meter_id": f"T-{i+1:02d}",
                "lat": lat,
                "lon": lon,
                "geometry": Point(lon, lat) # lon, lat for Shapely
            })
            
    return gpd.GeoDataFrame(meters, geometry="geometry", crs="EPSG:4326")

def map_meters_to_grid(meters_gdf, grid_gdf):
    """Spatially match meters to the nearest transmission line."""
    logger.info("Spatially matching meters to physical grid infrastructure...")
    
    # Filter grid to lines and cables (the transmission paths)
    lines_gdf = grid_gdf[grid_gdf.geom_type.isin(['LineString', 'MultiLineString'])]
    
    if lines_gdf.empty:
        logger.warning("No line strings found in grid infrastructure!")
        lines_gdf = grid_gdf
        
    # Reproject to a projected CRS (UTM Zone 47N for Thailand) for accurate distance calculation in meters
    meters_proj = meters_gdf.to_crs("EPSG:32647")
    lines_proj = lines_gdf.to_crs("EPSG:32647")
    
    # Perform nearest spatial join
    # sjoin_nearest returns the index of the nearest geometry
    mapped = gpd.sjoin_nearest(meters_proj, lines_proj, how="left", distance_col="distance_to_line_m")
    
    results = []
    for idx, row in mapped.iterrows():
        # Get OSM ID or Way ID if available
        osm_id = row.get('osmid')
        if isinstance(osm_id, list):
            osm_id = osm_id[0]
            
        results.append({
            "meter_id": row["meter_id"],
            "lat": row["lat"],
            "lon": row["lon"],
            "nearest_infrastructure": {
                "osm_id": str(osm_id) if osm_id else None,
                "type": str(row.get("power", "unknown")),
                "voltage": str(row.get("voltage", "unknown")),
                "distance_meters": round(row["distance_to_line_m"], 2)
            }
        })
        
    # Save the mapping
    with open(MAPPING_OUT, "w") as f:
        json.dump(results, f, indent=2)
        
    logger.info(f"Successfully mapped {len(results)} meters to the grid.")
    logger.info(f"Mapping saved to {MAPPING_OUT}")

def main():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    # 1. Fetch grid
    grid_gdf = fetch_grid_infrastructure()
    
    # 2. Load meters
    meters_gdf = load_meter_coordinates()
    
    if not meters_gdf.empty:
        # 3. Map meters to grid
        map_meters_to_grid(meters_gdf, grid_gdf)
    else:
        logger.warning("No meter locations loaded. Skipping spatial mapping.")

if __name__ == "__main__":
    main()
