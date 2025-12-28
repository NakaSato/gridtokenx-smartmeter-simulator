import sqlite3
import pandas as pd
import json
import os
import sys

def seed_static_grid(meters_csv="dataset_meters.csv", trans_csv="dataset_transformer_sizing.csv", db_path="smart_meter.db"):
    """
    Seeds primary 'meters' and 'transformers' tables.
    Also clears 'readings' to maintain data integrity.
    """
    if not os.path.exists(meters_csv):
        print(f"Error: {meters_csv} not found.")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # --- 0. PREPARE PRIMARY TABLES ---
        print("Dropping all primary tables for a fresh start...")
        cursor.execute("DROP TABLE IF EXISTS readings;")
        cursor.execute("DROP TABLE IF EXISTS meters;")
        cursor.execute("DROP TABLE IF EXISTS transformers;")
        cursor.execute("DROP TABLE IF EXISTS meters_static;") # Cleanup old static table

        # Recreate 'readings' table (empty)
        print("Re-creating 'readings' table...")
        cursor.execute("""
            CREATE TABLE readings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                meter_id TEXT,
                timestamp DATETIME,
                energy_generated REAL,
                energy_consumed REAL,
                surplus_energy REAL,
                deficit_energy REAL,
                battery_level REAL,
                location TEXT,
                meter_type TEXT,
                user_type TEXT,
                voltage REAL,
                current REAL,
                frequency REAL,
                temperature REAL,
                power_factor REAL,
                max_sell_price REAL,
                max_buy_price REAL,
                rec_eligible BOOLEAN,
                carbon_offset REAL,
                net_emission REAL,
                weather_condition TEXT,
                wallet_address TEXT,
                meter_signature TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # Recreate 'meters' table with full engineering schema
        print("Re-creating 'meters' table with new schema...")
        schema = """
            CREATE TABLE meters (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                meter_id TEXT UNIQUE,
                lat REAL, lon REAL, utm_x REAL, utm_y REAL,
                node_type TEXT, user_type TEXT, meter_size TEXT,
                tariff_code TEXT, phase_conn TEXT, phase_id TEXT,
                peak_load_kw REAL, has_solar BOOLEAN, solar_kw REAL, has_ev BOOLEAN,
                zone_id INTEGER, dist_m REAL, line_R REAL, line_X REAL,
                v_actual REAL, v_drop_pct REAL, config TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """
        cursor.execute(schema)

        # --- 1. SEED METERS ---
        print(f"Loading meters from {meters_csv}...")
        df_m = pd.read_csv(meters_csv)
        
        print(f"Inserting {len(df_m)} meters into primary 'meters' table...")
        for _, row in df_m.iterrows():
            # Heuristic mapping for 'meter_type' used in some app views
            sim_meter_type = "Grid_Consumer"
            if row['has_solar']: sim_meter_type = "Solar_Prosumer"
            if row['node_type'] == 'EV_Station': sim_meter_type = "Battery_Storage"
            
            # Map 'usage_type' to 'user_type' for compatibility
            u_type = row['usage_type']
            
            config = {
                "meter_id": row['meter_id'], 
                "phase_id": row['phase_id'],
                "user_type": u_type,
                "v_actual": float(row['v_actual']), 
                "v_drop_pct": float(row['v_drop_pct']),
                "meter_type": sim_meter_type, # Compatibility
                "location": [float(row['lat']), float(row['lon'])],
                "zone_id": int(row['transformer_id']),
                "name": str(row['building_name']) if pd.notnull(row.get('building_name')) else "",
                "building_code": str(row['building_code']) if pd.notnull(row.get('building_code')) else "",
                "dist_m": float(row['dist_m']),
                "line_R": float(row['line_R']),
                "line_X": float(row['line_X'])
            }
            config_json = json.dumps(config)

            cursor.execute("""
                INSERT INTO meters (
                    meter_id, lat, lon, utm_x, utm_y, node_type, user_type, 
                    meter_size, tariff_code, phase_conn, phase_id, 
                    peak_load_kw, has_solar, solar_kw, has_ev, 
                    zone_id, dist_m, line_R, line_X, v_actual, v_drop_pct, config
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                row['meter_id'], float(row['lat']), float(row['lon']), 
                float(row['utm_x']), float(row['utm_y']), row['node_type'], u_type,
                row['meter_size'], row['tariff_code'], row['phase_conn'], row['phase_id'],
                float(row['peak_load_kw']), int(row['has_solar']), float(row['solar_kw']), 
                int(row['has_ev']), int(row['transformer_id']), float(row['dist_m']), 
                float(row['line_R']), float(row['line_X']), float(row['v_actual']), 
                float(row['v_drop_pct']), config_json
            ))

        # --- 2. SEED TRANSFORMERS ---
        if os.path.exists(trans_csv):
            print(f"Loading transformers from {trans_csv}...")
            df_t = pd.read_csv(trans_csv)
            
            print("Re-creating 'transformers' table...")
            cursor.execute("DROP TABLE IF EXISTS transformers;")
            cursor.execute("""
                CREATE TABLE transformers (
                    transformer_id INTEGER PRIMARY KEY,
                    lat REAL, lon REAL,
                    agg_peak_kw REAL, installed_kva INTEGER,
                    utilization REAL, meter_count INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

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
        print("SUCCESS: Primary 'meters' replaced with Complex MEA dataset.")

    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    seed_static_grid()
