import leafmap
import os

print("Starting sample image download...")
try:
    bbox = [100.687, 13.756, 100.689, 13.758]
    leafmap.tms_to_geotiff(
        output="village_satellite_view.tif",
        bbox=bbox,
        zoom=19,
        source="Satellite",
        overwrite=True
    )
    if os.path.exists("village_satellite_view.tif"):
        print("Success! image downloaded.")
    else:
        print("File was not created.")
except Exception as e:
    print(f"Error downloading: {e}")
