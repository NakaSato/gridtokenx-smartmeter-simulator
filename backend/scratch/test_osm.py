
import osmnx as ox
import geopandas as gpd

def test_osm_fetch():
    # Bangkok center
    lat, lon = 13.7563, 100.5018
    tags = {"power": "line"}
    try:
        # Fetch a small area
        gdf = ox.features_from_point((lat, lon), tags=tags, dist=1000)
        print(f"Success! Found {len(gdf)} power lines near Bangkok center.")
        print(gdf.head())
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_osm_fetch()
