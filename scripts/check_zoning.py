
import asyncio
import sys
import os
import json
import logging
import numpy as np
from tabulate import tabulate

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from app.services.zoning_service import MicrogridZoningService, ZoneInfo
from app.config.settings import load_settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("check_zoning")

def load_simulated_meters():
    """Load mock meters from UTCC data if available, or generate random."""
    # Try to load real data if exists
    try:
        # Try loading from the newly generated CSV first (more accurate than the json file)
        import pandas as pd
        if os.path.exists("utcc_dataset_meters.csv"):
            df = pd.read_csv("utcc_dataset_meters.csv")
            return list(zip(df['lat'], df['lon']))

        with open("utcc_real_data.json", "r") as f:
            data = json.load(f)
            meters = []
            # Check structure (list or dict with 'meterNodes')
            nodes = data.get("meterNodes", data) if isinstance(data, dict) else data
            
            for m in nodes:
                if "latitude" in m and "longitude" in m:
                    meters.append((m["latitude"], m["longitude"]))
            return meters
    except FileNotFoundError:
        pass

    # Fallback: Generate random points around Bangkok
    logger.info("Using random generated points")
    center_lat, center_lon = 13.779261, 100.556488  # UTCC
    points = []
    for _ in range(100):
        # Result in ~5km spread
        lat = center_lat + np.random.uniform(-0.04, 0.04) 
        lon = center_lon + np.random.uniform(-0.04, 0.04)
        points.append((lat, lon))
    return points

def print_matrix(zoning_service, zone_count):
    headers = ["From\\To"] + [f"Zone {i}" for i in range(zone_count)]
    
    # Distance Matrix
    print("\n📏 Manhattan Distance Matrix (km) - 'Side of Road':")
    dist_table = []
    for i in range(zone_count):
        row = [f"Zone {i}"]
        for j in range(zone_count):
            dist = zoning_service.calculate_zone_distance(i, j)
            row.append(f"{dist:.2f}")
        dist_table.append(row)
    print(tabulate(dist_table, headers=headers, tablefmt="grid"))

    # Wheeling Charge Matrix
    print("\n💰 Wheeling Charge Matrix (THB/kWh):")
    charge_table = []
    for i in range(zone_count):
        row = [f"Zone {i}"]
        for j in range(zone_count):
            # Pass 1.0 kWh to get the rate
            rate = zoning_service.calculate_wheeling_charge(i, j, 1.0)
            row.append(f"{rate:.2f}")
        charge_table.append(row)
    print(tabulate(charge_table, headers=headers, tablefmt="grid"))
    
    # Classification Matrix
    print("\n🏷️  Zone Relationship Classification:")
    class_table = []
    for i in range(zone_count):
        row = [f"Zone {i}"]
        for j in range(zone_count):
            dist = zoning_service.calculate_zone_distance(i, j)
            if i == j:
                cls = "INTRA"
            elif dist < 2.0:
                cls = "ADJACENT"
            elif dist < 5.0:
                cls = "CROSS"
            else:
                cls = "REMOTE"
            row.append(cls)
        class_table.append(row)
    print(tabulate(class_table, headers=headers, tablefmt="grid"))

def main():
    print("🏙️  Checking Microgrid Zoning Configuration...")
    
    # 1. Load Settings (to get Wheeling rates)
    settings = load_settings()
    print(f"Loaded Settings: Intra={settings.wheeling_intra_zone}, Adj={settings.wheeling_adjacent_zone}, Cross={settings.wheeling_cross_zone}, Remote={settings.wheeling_remote_zone}")

    # 2. Init Service
    num_zones = 3
    zoning = MicrogridZoningService(num_zones=num_zones)
    
    # 3. Load & Fit Data
    coords = load_simulated_meters()
    print(f"📍 Loaded {len(coords)} meter coordinates.")
    
    zoning.fit(coords)
    
    # 4. Show Zone Summary
    summary = zoning.get_zone_summary()
    print("\n📊 Zone Summary:")
    summary_data = []
    for zid, info in summary.items():
        summary_data.append([
            zid, 
            info.meter_count, 
            f"{info.centroid_lat:.5f}, {info.centroid_lon:.5f}",
            info.transformer_name
        ])
    print(tabulate(summary_data, headers=["Zone ID", "Meters", "Centroid (Lat, Lon)", "Transformer"], tablefmt="simple"))

    # 5. Show Matrices
    print_matrix(zoning, num_zones)

if __name__ == "__main__":
    main()
