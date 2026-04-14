import cv2
import numpy as np
import json
import argparse
import os

def analyze_shadow(img, contour, expansion=10):
    """
    Analyzes shadow proximity for a given contour.
    Uses edge detection to find nearby structural boundaries.
    """
    h, w, _ = img.shape
    mask = np.zeros((h, w), dtype=np.uint8)
    cv2.drawContours(mask, [contour], -1, 255, -1)
    
    # Expand the contour to check neighborhood
    kernel = np.ones((expansion, expansion), np.uint8)
    dilated_mask = cv2.dilate(mask, kernel, iterations=1)
    neighborhood_mask = cv2.subtract(dilated_mask, mask)
    
    # Edge detection on original image
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 50, 150)
    
    # Check edge density in the neighborhood
    neighborhood_edges = cv2.bitwise_and(edges, edges, mask=neighborhood_mask)
    edge_pixels = np.count_nonzero(neighborhood_edges)
    
    # Heuristic: if edge density is high, it's likely near a building edge (potential shadow)
    # This is a simplified proxy for shadow risk
    shadow_risk_score = min(1.0, edge_pixels / 500.0) 
    
    return round(float(shadow_risk_score), 2)

def process_village_solar(image_path, center_coord, gsd=0.3, output_geojson=None):
    """
    Simulates image processing for solar rooftop detection.
    image_path: Path to high-res satellite image
    center_coord: (lat, lon) of the village center
    gsd: Ground Sample Distance (meters per pixel)
    output_geojson: Path to save the GeoJSON file
    """
    if not os.path.exists(image_path):
        print(f"Error: Image not found at {image_path}")
        return None, []

    # 1. Load the satellite image
    img = cv2.imread(image_path)
    if img is None:
        print(f"Error: Could not decode image at {image_path}")
        return None, []
        
    h, w, _ = img.shape
    
    # 2. Pre-processing: Convert to HSV to isolate solar panel colors
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    
    # Define color range for solar panels (Adjust based on image quality)
    lower_solar = np.array([90, 50, 50])
    upper_solar = np.array([130, 255, 255])
    
    mask = cv2.inRange(hsv, lower_solar, upper_solar)
    
    # 2.1 Morphological operations to clean up noise
    kernel = np.ones((5,5), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    
    # 3. Find Contours (Houses and Panels)
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    detected_houses = []
    features = []
    
    for i, cnt in enumerate(contours):
        area_px = cv2.contourArea(cnt)
        if area_px > 100:  # Filter out noise
            # Calculate pixel center
            M = cv2.moments(cnt)
            if M["m00"] != 0:
                cX = int(M["m10"] / M["m00"])
                cY = int(M["m01"] / M["m00"])
                
                # 4. Coordinate Transformation (Pixel to Geo)
                lat_offset = (cY - (h/2)) * -0.00001 
                lon_offset = (cX - (w/2)) * 0.00001
                
                house_lat = center_coord[0] + lat_offset
                house_lon = center_coord[1] + lon_offset
                
                # 5. GSD Mapping and kWp Calculation
                # Area in m^2 = pixels * gsd^2
                area_m2 = area_px * (gsd ** 2)
                # kWp = Area * efficiency (assume 0.15 kW/m^2 as standard)
                kwp_potential = area_m2 * 0.15
                
                # 6. Shadow Analysis
                shadow_risk = analyze_shadow(img, cnt)
                
                house_data = {
                    "id": f"SET-H{i+1:03d}",
                    "lat": round(house_lat, 6),
                    "lon": round(house_lon, 6),
                    "solar_area_px": round(float(area_px), 2),
                    "solar_area_m2": round(float(area_m2), 2),
                    "kwp_potential": round(float(kwp_potential), 2),
                    "shadow_risk_score": shadow_risk
                }
                detected_houses.append(house_data)
                
                # GeoJSON Feature
                feature = {
                    "type": "Feature",
                    "properties": house_data,
                    "geometry": {
                        "type": "Point",
                        "coordinates": [round(house_lon, 6), round(house_lat, 6)]
                    }
                }
                features.append(feature)
                
                # Visual Feedback: Draw bounding box
                x, y, w_box, h_box = cv2.boundingRect(cnt)
                cv2.rectangle(img, (x, y), (x+w_box, y+h_box), (0, 255, 0), 2)
                label = f"{house_data['id']} ({house_data['kwp_potential']}kWp)"
                cv2.putText(img, label, (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 0), 1)

    # Save GeoJSON if path provided
    if output_geojson:
        geojson = {
            "type": "FeatureCollection",
            "features": features,
            "metadata": {
                "gsd_m_px": gsd,
                "village_center": center_coord
            }
        }
        with open(output_geojson, 'w') as f:
            json.dump(geojson, f, indent=2)
        print(f"GeoJSON results saved to {output_geojson}")

    return img, detected_houses

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Solar Rooftop Detection for GridTokenX (Enhanced)")
    parser.add_argument("--image", type=str, required=True, help="Path to satellite image")
    parser.add_argument("--lat", type=float, default=13.757559, help="Village center Latitude")
    parser.add_argument("--lon", type=float, default=100.688337, help="Village center Longitude")
    parser.add_argument("--gsd", type=float, default=0.3, help="Ground Sample Distance (m/pixel)")
    parser.add_argument("--output", type=str, default="solar_results_enhanced.json", help="Output GeoJSON path")
    parser.add_argument("--save-img", type=str, help="Path to save processed image")

    args = parser.parse_args()
    
    VILLAGE_CENTER = (args.lat, args.lon)
    
    print(f"Processing village solar at {VILLAGE_CENTER} with GSD={args.gsd}...")
    processed_img, results = process_village_solar(args.image, VILLAGE_CENTER, args.gsd, args.output)
    
    if results:
        print(f"Total Houses with Solar Detected: {len(results)}")
        # Print top 3 results
        for house in results[:3]:
            print(f"- {house['id']}: {house['kwp_potential']} kWp at ({house['lat']}, {house['lon']})")
            print(f"  Area: {house['solar_area_m2']} m2, Shadow Risk: {house['shadow_risk_score']}")
            
        if args.save_img and processed_img is not None:
            cv2.imwrite(args.save_img, processed_img)
            print(f"Processed image saved to {args.save_img}")
    else:
        print("No solar rooftops detected or image processing failed.")
