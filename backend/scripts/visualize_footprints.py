import osmnx as ox
import matplotlib.pyplot as plt
import contextily as cx
import pandas as pd
import os

# 1. Configuration
# Location: Setthasiri Krungthep Kreetha village
CENTER_LAT = 13.757559025848558
CENTER_LON = 100.68833784695282
DISTANCE = 400  # Radius in meters

def visualize_village():
    # 2. Retrieve Building Footprints (Free from OpenStreetMap)
    print("Fetching building data...")
    try:
        buildings = ox.features_from_point((CENTER_LAT, CENTER_LON), tags={'building': True}, dist=DISTANCE)
    except Exception as e:
        print(f"Error fetching data: {e}")
        return

    if buildings.empty:
        print("No buildings found in the specified area.")
        return

    # Convert to a standard projection for distance calculations
    # 3857 is Web Mercator (meters), good for contextily basemaps and distance
    buildings_3857 = buildings.to_crs(epsg=3857)

    # 3. Extract Centroid Locations (Latitude/Longitude)
    # Using the standard EPSG:4326 (WGS84) for latitude/longitude, fixing the user's epsg=4323 typo
    buildings_wgs84 = buildings_3857.to_crs(epsg=4326)
    buildings_wgs84['latitude'] = buildings_wgs84.centroid.y
    buildings_wgs84['longitude'] = buildings_wgs84.centroid.x

    # 4. Visualization with Satellite Basemap
    fig, ax = plt.subplots(figsize=(12, 12))

    # Plot the building outlines (using the 3857 projection so it matches contextily's default)
    buildings_3857.plot(ax=ax, facecolor='none', edgecolor='cyan', linewidth=1.5, alpha=0.8, label="Houses")

    # Add a free high-quality satellite basemap (Esri World Imagery)
    try:
        cx.add_basemap(ax, source=cx.providers.Esri.WorldImagery)
    except Exception as e:
        print(f"Warning: Could not load basemap: {e}")

    plt.title(f"GridTokenX: {len(buildings_wgs84)} Houses Detected at {CENTER_LAT}, {CENTER_LON}", fontsize=15, color='black')
    
    # Text color might need tweaking since we're saving to a file, let's make it a bit more visible against satellite/white background
    # Added a dark background to title for visibility or just black
    
    ax.set_axis_off()

    # Save the plot
    os.makedirs('data', exist_ok=True)
    plot_path = "data/village_footprints.png"
    plt.savefig(plot_path, bbox_inches='tight', dpi=300)
    print(f"Saved visualization to {plot_path}")

    # Save the location data to CSV for your P2P model
    csv_path = "data/village_house_locations.csv"
    buildings_wgs84[['latitude', 'longitude']].to_csv(csv_path, index=False)

    print(f"Success! {len(buildings_wgs84)} house coordinates saved to '{csv_path}'.")

if __name__ == "__main__":
    visualize_village()
