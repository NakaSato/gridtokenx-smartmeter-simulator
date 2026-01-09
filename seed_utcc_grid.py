import sqlite3
import pandas as pd
import json
import os

def seed_utcc_grid(meters_csv="utcc_dataset_meters.csv", trans_csv="utcc_dataset_transformer_sizing.csv", db_path="smart_meter.db"):
    """
    Seeds primary 'meters' and 'transformers' tables from UTCC datasets.
    Also clears 'readings' to maintain data integrity for the new grid.
    """
    if not os.path.exists(meters_csv):
        print(f"Error: {meters_csv} not found.")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # --- 0. PREPARE PRIMARY TABLES ---
        print("Setting up database tables...")
        
        # Ensure meters table exists with correct schema
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS meters (
                meter_id TEXT PRIMARY KEY,
                meter_type TEXT,
                location TEXT,
                latitude REAL,
                longitude REAL,
                zone_id INTEGER,
                config TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Ensure transformers table exists
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS transformers (
                transformer_id INTEGER PRIMARY KEY,
                lat REAL, lon REAL,
                agg_peak_kw REAL, installed_kva INTEGER,
                utilization REAL, meter_count INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Clear old data
        print("Cleaning up old data...")
        cursor.execute("DELETE FROM meters WHERE meter_id LIKE 'UTCC-%';")
        cursor.execute("DELETE FROM transformers;")

        # --- 1. SEED METERS ---
        print(f"Loading meters from {meters_csv}...")
        df_m = pd.read_csv(meters_csv)
        
        print(f"Inserting {len(df_m)} meters into primary 'meters' table...")
        for _, row in df_m.iterrows():
            sim_meter_type = "Grid_Consumer"
            if row['has_solar']: sim_meter_type = "Solar_Prosumer"
            if row['node_type'] == 'EV_Station': sim_meter_type = "Battery_Storage"
            
            u_type = row['usage_type']
            
            config = {
                "meter_id": row['meter_id'], 
                "meter_type": sim_meter_type,
                "user_type": u_type,
                "location": [float(row['lat']), float(row['lon'])],
                "latitude": float(row['lat']),
                "longitude": float(row['lon']),
                "has_solar": bool(row['has_solar']),
                "solar_capacity": float(row['solar_kw']),
                "has_battery": False,
                "battery_capacity": 0.0,
                "trading_preference": "Moderate",
                "max_sell_price": 3.5,
                "max_buy_price": 4.5,
            }
            config_json = json.dumps(config)

            cursor.execute("""
                INSERT INTO meters (
                    meter_id, meter_type, location, latitude, longitude, zone_id, config
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                row['meter_id'], 
                sim_meter_type,
                f"{row.get('building_name', 'Building')} - Zone {row['transformer_id']}",
                float(row['lat']), 
                float(row['lon']),
                int(row['transformer_id']), 
                config_json
            ))

        # --- 2. SEED TRANSFORMERS ---
        if os.path.exists(trans_csv):
            print(f"Loading transformers from {trans_csv}...")
            df_t = pd.read_csv(trans_csv)

            print(f"Inserting {len(df_t)} transformers...")
            for _, row in df_t.iterrows():
                cursor.execute("""
                    INSERT INTO transformers (
                        transformer_id, lat, lon, agg_peak_kw, 
                        installed_kva, utilization, meter_count
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    int(row['transformer_id']), float(row['lat']), float(row['lon']),
                    float(row['agg_peak_kw']), int(row['installed_kva']),
                    float(row['utilization']), int(row['meter_count'])
                ))

        conn.commit()
        print("SUCCESS: Database seeded with UTCC Grid Dataset.")

    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    seed_utcc_grid()
