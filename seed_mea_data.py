import json
import sqlite3
import pandas as pd
import sys
import os

def seed_thailand_data(csv_path, db_path='smart_meter.db'):
    """
    Reads the Thailand GIS CSV and seeds the SQLite database.
    WARNING: This will clear existing meters in the DB.
    """
    if not os.path.exists(csv_path):
        print(f"Error: File {csv_path} not found.")
        return

    print(f"Reading CSV data from {csv_path}...")
    try:
        df = pd.read_csv(csv_path)
    except Exception as e:
        print(f"Error reading CSV: {e}")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # 1. Clear existing Data
        print("Clearing existing meter data...")
        cursor.execute("DELETE FROM readings")
        cursor.execute("DELETE FROM meters")
        # Reset Auto-increment counters
        try:
            cursor.execute("DELETE FROM sqlite_sequence")
        except sqlite3.OperationalError:
            pass # Table might not exist if no auto-increments used yet
        
        print(f"Found {len(df)} meters in CSV to insert.")
        
        count = 0
        for idx, row in df.iterrows():
            meter_id = row['meter_id']
            meter_type = row['meter_type']
            # Map meter_type string to internal types if needed
            # CSV has: '5(15) A', '15(45) A', '30(100) A', '3-Phase / CT'
            # App expects: 'Solar_Prosumer', 'Grid_Consumer', 'Hybrid_Prosumer', 'Battery_Storage'
            # We will map randomly or based on rule to these logical types for simulation behavior
            
            # Simple heuristic mapping for demo variety:
            # '5(15) A' -> Grid_Consumer (Small)
            # '15(45) A' -> Solar_Prosumer (Standard House)
            # '30(100) A' -> Hybrid_Prosumer (Large House)
            # '3-Phase / CT' -> Grid_Consumer (Commercial - High Load) or Battery_Storage (Grid Support)
            
            sim_meter_type = "Grid_Consumer"
            if "5(15)" in meter_type:
                sim_meter_type = "Grid_Consumer"
            elif "15(45)" in meter_type:
                # mix of solar and consumer
                sim_meter_type = "Solar_Prosumer" if idx % 2 == 0 else "Grid_Consumer"
            elif "30(100)" in meter_type:
                sim_meter_type = "Hybrid_Prosumer"
            elif "3-Phase" in meter_type:
                sim_meter_type = "Battery_Storage" if idx % 10 == 0 else "Grid_Consumer" # Few battery storages

            # Build Config JSON
            user_type = "Consumer"
            if sim_meter_type in ["Solar_Prosumer", "Hybrid_Prosumer", "Battery_Storage"]:
                user_type = "Prosumer"

            config = {
                "meter_id": meter_id,
                "meter_type": sim_meter_type,
                "user_type": user_type,
                "location": f"Zone {int(row['transformer_id'])}",
                "latitude": float(row['lat']),
                "longitude": float(row['lon']),
                "zone_id": int(row['transformer_id']),
                "contract_capacity_kw": float(row['contract_capacity_kw']),
                "building_area_sqm": float(row['building_area']),
                "dist_to_transformer_m": float(row['dist_to_transformer_m']),
                "csv_meter_type": meter_type,
                # Defaults required by app
                "has_solar": sim_meter_type in ['Solar_Prosumer', 'Hybrid_Prosumer'],
                "has_battery": sim_meter_type in ['Hybrid_Prosumer', 'Battery_Storage'],
                "solar_capacity": float(row['contract_capacity_kw']) * 0.8 if sim_meter_type in ['Solar_Prosumer', 'Hybrid_Prosumer'] else 0.0,
                "battery_capacity": 10.0 if sim_meter_type in ['Hybrid_Prosumer', 'Battery_Storage'] else 0.0,
                "trading_preference": "Moderate"
            }
            
            config_json = json.dumps(config)
            
            cursor.execute("""
                INSERT INTO meters (
                    meter_id, meter_type, location, latitude, longitude, zone_id, config, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (
                meter_id,
                sim_meter_type,
                config['location'],
                config['latitude'],
                config['longitude'],
                config['zone_id'],
                config_json
            ))
            count += 1
            
        conn.commit()
        print(f"Successfully seeded {count} meters from Thailand CSV.")

    except Exception as e:
        print(f"Database error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    csv_path = "thailand_real_building_1meter.csv"
    if len(sys.argv) > 1:
        csv_path = sys.argv[1]
        
    seed_thailand_data(csv_path)
