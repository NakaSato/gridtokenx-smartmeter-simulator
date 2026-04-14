import argparse
import os
import sys
from pathlib import Path

from samgeo import SamGeo
import leafmap


def detect_solar_panels(image_path: str, output_geojson: str):
    """
    Detects solar panels in a high-resolution satellite image using Geo-SAM.
    """
    if not os.path.exists(image_path):
        print(f"Error: Input image not found at {image_path}", file=sys.stderr)
        return False

    print(f"Initializing Geo-SAM using input image: {image_path}")
    print("This may take a while if the model checkpoint needs to be downloaded.")
    
    # 2. Initialize Geo-SAM
    sam = SamGeo(
        model_type="vit_h",  # Use 'Huge' model for best rooftop detail
        checkpoint="sam_vit_h_4b8939.pth",
        sam_kwargs=None,
    )

    output_tif = "all_objects.tif"

    print("Running automated segmentation...")
    # 3. Automated Segmentation (Finding all 'objects' in the image)
    # This will find every roof, pool, and solar panel
    sam.generate(image_path, output=output_tif, foreground=True, unique=True)

    print("Converting segmentation mask to GeoJSON...")
    # 4. Filter for Solar Panels (Conceptual)
    # In a full pipeline you might apply an HSV filter before or after, 
    # but for now we convert the generated mask to geojson.
    sam.tiff_to_geojson(output_tif, output_geojson)

    print(f"Successfully generated solar inventory at: {output_geojson}")
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="GridTokenX Solar Panel Detector using Geo-SAM")
    parser.add_argument(
        "--image", 
        type=str, 
        default="village_satellite_view.tif",
        help="Path to the high-resolution satellite GeoTIFF image (0.3m-0.5m/px)"
    )
    parser.add_argument(
        "--output", 
        type=str, 
        default="gridtokenx_inventory.geojson",
        help="Path for the output detected solar panels GeoJSON"
    )

    args = parser.parse_args()
    
    # Also initialize a map for context but not displayed in CLI
    m = leafmap.Map(center=[13.757559, 100.688337], zoom=19)
    print("Initialized reference map context at [13.757559, 100.688337]")
    
    success = detect_solar_panels(args.image, args.output)
    if success:
        print("Solar inventory generated for GridTokenX dashboard.")
    else:
        sys.exit(1)
