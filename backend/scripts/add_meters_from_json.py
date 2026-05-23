#!/usr/bin/env python3
"""
Script to add meters to the Smart Meter Simulator from a JSON file.
"""

import json
import sys
import os
import requests
import argparse

def add_meters(json_path, api_url):
    """Read JSON and post meters to the API."""
    if not os.path.exists(json_path):
        print(f"Error: File {json_path} not found.")
        return

    try:
        with open(json_path, 'r') as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error parsing JSON: {e}")
        return

    # Handle both {"meters": [...]}, {"locations": [...]}, and [...] formats
    if isinstance(data, dict):
        meters = data.get("meters") or data.get("locations") or []
    else:
        meters = data
    
    if not isinstance(meters, list):
        print("Error: JSON must contain a list of meters.")
        return

    print(f"Found {len(meters)} meters to register.")
    
    success_count = 0
    fail_count = 0

    for meter in meters:
        # Map fields if coming from init.json format
        payload = {
            "meter_type": meter.get("meter_type", "consumer"),
            "lat": meter.get("lat") or meter.get("latitude"),
            "lon": meter.get("lon") or meter.get("longitude"),
            "accuracy_class": meter.get("accuracy_class"),
            "battery_capacity_kwh": meter.get("battery_capacity_kwh") or meter.get("battery_capacity")
        }
        
        # Mapping frontend-style meter types to enum if necessary
        if payload["meter_type"] == "prosumer":
            payload["meter_type"] = "solar_prosumer"
        elif payload["meter_type"] == "consumer":
            payload["meter_type"] = "grid_consumer"

        try:
            response = requests.post(api_url, json=payload)
            if response.status_code in [200, 201]:
                print(f"✅ Registered {payload['meter_type']} at {payload['lat']}, {payload['lon']}")
                success_count += 1
            else:
                print(f"❌ Failed to register meter: {response.status_code} - {response.text}")
                fail_count += 1
        except Exception as e:
            print(f"❌ Connection error: {e}")
            fail_count += 1

    print("-" * 30)
    print(f"Registration complete.")
    print(f"Success: {success_count}")
    print(f"Failed: {fail_count}")

def main():
    parser = argparse.ArgumentParser(description="Add meters from JSON to simulator")
    parser.get_default("json_file")
    parser.add_argument("json_file", help="Path to the JSON file containing meters")
    parser.add_argument("--url", default="http://localhost:8082/api/v1/meters", help="API URL (default: http://localhost:8082/api/v1/meters)")
    
    args = parser.parse_args()
    
    add_meters(args.json_file, args.url)

if __name__ == "__main__":
    main()
