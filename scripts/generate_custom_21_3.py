
import pandas as pd
import numpy as np
import random
import os

# Configuration
CENTER_LAT = 13.780157
CENTER_LON = 100.560237

# Output files
METERS_CSV = "utcc_dataset_meters.csv"
TRANSFORMERS_CSV = "utcc_dataset_transformer_sizing.csv"

def generate_grid():
    print("Generating custom grid: 21 meters, 3 transformers...")

    # 1. Define 3 Transformers
    transformers = [
        {"id": 0, "lat": CENTER_LAT + 0.001, "lon": CENTER_LON + 0.001}, # NE
        {"id": 1, "lat": CENTER_LAT - 0.001, "lon": CENTER_LON - 0.001}, # SW
        {"id": 2, "lat": CENTER_LAT + 0.001, "lon": CENTER_LON - 0.001}, # NW
    ]

    # 2. Generate 21 Meters (7 per transformer)
    meters = []
    
    meter_count = 0
    for tx in transformers:
        for i in range(7):
            # Spread meters around transformer (~50-100m radius)
            # 1 deg lat approx 111km, 0.0001 deg approx 11m
            d_lat = random.uniform(-0.0005, 0.0005)
            d_lon = random.uniform(-0.0005, 0.0005)
            
            lat = tx["lat"] + d_lat
            lon = tx["lon"] + d_lon
            
            # Simple distance calculation (Pythagorean on deg)
            dist_deg = np.sqrt(d_lat**2 + d_lon**2)
            dist_m = dist_deg * 111000 # Approx conversion
            
            # Electrical Params (Mock)
            line_R = (dist_m / 1000.0) * 0.32
            line_X = (dist_m / 1000.0) * 0.28
            
            meter_id = f"UTCC-20{meter_count:02d}"
            
            meters.append({
                "meter_id": meter_id,
                "lat": lat,
                "lon": lon,
                "utm_x": 0.0, # Placeholder
                "utm_y": 0.0, # Placeholder
                "node_type": "Building",
                "usage_type": "Commercial",
                "meter_size": "3-Phase 30(100) A",
                "tariff_code": "3.1",
                "phase_conn": "3-Phase",
                "phase_id": "ABC",
                "peak_load_kw": random.uniform(20.0, 150.0),
                "has_solar": random.choice([True, False]),
                "solar_kw": random.uniform(5.0, 50.0),
                "has_ev": random.choice([True, False]),
                "transformer_id": tx["id"],
                "dist_m": dist_m,
                "line_R": line_R,
                "line_X": line_X,
                "v_actual": 230.0 - (dist_m * 0.02), # Mock voltage drop
                "v_drop_pct": (dist_m * 0.02) / 230.0 * 100,
                "building_name": f"Building {meter_count+1}",
                "building_code": f"B-{meter_count+1:02d}"
            })
            meter_count += 1

    # 3. Create DataFrame and Save Meters
    df_meters = pd.DataFrame(meters)
    # Fix solar if has_solar is False
    df_meters.loc[~df_meters['has_solar'], 'solar_kw'] = 0.0
    
    df_meters.to_csv(METERS_CSV, index=False)
    print(f"Saved {len(df_meters)} meters to {METERS_CSV}")

    # 4. Calculate Transformer Sizing
    tx_data = []
    for tx in transformers:
        tx_meters = df_meters[df_meters['transformer_id'] == tx["id"]]
        agg_peak = tx_meters['peak_load_kw'].sum()
        meter_count = len(tx_meters)
        
        # Sizing logic
        required_kva = agg_peak / 0.85 # Assumed PF
        installed_kva = 500 # Default
        if required_kva > 500: installed_kva = 1000
        if required_kva > 1000: installed_kva = 1500
        
        utilization = (agg_peak / (installed_kva * 0.85)) * 100
        
        tx_data.append({
            "transformer_id": tx["id"],
            "lat": tx["lat"],
            "lon": tx["lon"],
            "agg_peak_kw": agg_peak,
            "required_kva": required_kva,
            "installed_kva": installed_kva,
            "utilization": utilization,
            "meter_count": meter_count
        })

    # 5. Save Transformers
    df_tx = pd.DataFrame(tx_data)
    df_tx.to_csv(TRANSFORMERS_CSV, index=False)
    print(f"Saved {len(df_tx)} transformers to {TRANSFORMERS_CSV}")

if __name__ == "__main__":
    generate_grid()
