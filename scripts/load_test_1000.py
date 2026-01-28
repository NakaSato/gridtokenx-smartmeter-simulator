import sqlite3
import httpx
import os
import json
import time
from datetime import datetime
from dotenv import load_dotenv

def send_load_test():
    # Load configuration
    load_dotenv()
    api_url = os.getenv("API_GATEWAY_URL", "http://localhost:4000")
    api_key = os.getenv("API_KEY", "engineering-department-api-key-2025")
    db_path = "smart_meter.db"

    print(f"🚀 Starting Load Test: Sending readings for 1000 meters to {api_url}")
    
    # Connect to local simulator DB
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Fetch 1000 meters
    cursor.execute("SELECT meter_id, meter_type, latitude, longitude, zone_id FROM meters LIMIT 1000")
    meters = cursor.fetchall()
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    readings = []
    for mid, mtype, lat, lon, zid in meters:
        # Generate some dummy reading data
        # Alternate between generation (prosumer) and consumption
        is_prosumer = "Prosumer" in mtype
        kwh = 2.5 if is_prosumer else -1.8
        
        reading = {
            "meter_serial": mid,
            "kwh": kwh,
            "meter_type": mtype,
            "latitude": lat,
            "longitude": lon,
            "zone_id": zid,
            "voltage": 230.5,
            "current": 10.0 if kwh > 0 else 8.0,
            "power_factor": 0.98,
            "frequency": 50.0,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "max_sell_price": 5.0,
            "max_buy_price": 3.0
        }
        readings.append(reading)

    # Split into batches of 100 to avoid huge payloads
    batch_size = 100
    success_total = 0
    fail_total = 0
    
    start_time = time.time()
    
    with httpx.Client(timeout=60.0) as client:
        for i in range(0, len(readings), batch_size):
            batch = readings[i:i + batch_size]
            payload = {"readings": batch}
            
            try:
                print(f"📦 Sending batch {i//batch_size + 1} ({len(batch)} readings)...")
                response = client.post(f"{api_url}/api/v1/public/meters/batch/readings", headers=headers, json=payload)
                
                if response.status_code == 200:
                    data = response.json()
                    success_total += data.get("success_count", 0)
                    fail_total += data.get("failed_count", 0)
                else:
                    print(f"❌ Batch {i//batch_size + 1} failed: HTTP {response.status_code} - {response.text}")
                    fail_total += len(batch)
            except Exception as e:
                print(f"❌ Exception sending batch {i//batch_size + 1}: {e}")
                fail_total += len(batch)

    end_time = time.time()
    duration = end_time - start_time
    
    print("\n" + "="*50)
    print("LOAD TEST SUMMARY")
    print("="*50)
    print(f"Total Attempted: {len(meters)}")
    print(f"Successfully Queued: {success_total}")
    print(f"Failed: {fail_total}")
    print(f"Time Taken: {duration:.2f} seconds")
    print(f"Throughput: {success_total / duration:.2f} readings/sec")
    print("="*50)
    print("Note: Readings are processed ASHYNCHRONOUSLY by the Gateway.")
    print("Check Gateway logs for blockchain submission status.")

if __name__ == "__main__":
    send_load_test()
