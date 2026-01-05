import sqlite3
import requests
import os
import json
from dotenv import load_dotenv

def sync_meters():
    # Load configuration
    load_dotenv()
    api_url = os.getenv("API_GATEWAY_URL", "http://127.0.0.1:4000")
    api_key = os.getenv("API_KEY")
    db_path = "smart_meter.db"

    if not api_key:
        print("Error: API_KEY not found in .env")
        return

    print(f"Syncing meters to Gateway: {api_url}")
    
    # Connect to local simulator DB
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Fetch all meters
    # Note: Column names lat/lon match seed_utcc_grid.py schema
    cursor.execute("SELECT meter_id, lat, lon, meter_type, config, zone_id FROM meters")
    meters = cursor.fetchall()
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    success_count = 0
    fail_count = 0
    already_exists = 0
    
    for meter_id, lat, lon, meter_type, config_json, zone_id in meters:
        # Prepare registration payload
        payload = {
            "serial_number": meter_id,
            "meter_type": meter_type,
            "location": f"Zone {zone_id}",
            "latitude": lat,
            "longitude": lon,
            "zone_id": zone_id
        }
        
        try:
            response = requests.post(f"{api_url}/api/v1/meters", headers=headers, json=payload)
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    success_count += 1
                    if success_count % 50 == 0:
                        print(f"Progress: {success_count} meters synced...")
                else:
                    if "already registered" in data.get("message", "").lower():
                        already_exists += 1
                    else:
                        print(f"Failed to sync {meter_id}: {data.get('message')}")
                        fail_count += 1
            elif response.status_code == 400:
                already_exists += 1
            else:
                print(f"Error syncing {meter_id}: HTTP {response.status_code} - {response.text}")
                fail_count += 1
        except Exception as e:
            print(f"Exception syncing {meter_id}: {e}")
            fail_count += 1
            
    print("\nSync Summary:")
    print(f"Total Meters: {len(meters)}")
    print(f"Newly Synced: {success_count}")
    print(f"Already Exist: {already_exists}")
    print(f"Failures: {fail_count}")

if __name__ == "__main__":
    sync_meters()
