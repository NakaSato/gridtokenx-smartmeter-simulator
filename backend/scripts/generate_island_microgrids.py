import json
import random
import math
import os

def generate_cluster(name_prefix, center_lat, center_lon, count, start_index=1, radius_km=1.0, zone="unknown"):
    locations = []
    for i in range(start_index, start_index + count):
        # Random distance and angle
        r = radius_km * math.sqrt(random.random())
        theta = random.random() * 2 * math.pi
        
        # Approximate offset (1 degree lat ~= 111km, 1 degree lon ~= 111km * cos(lat))
        lat_offset = (r * math.cos(theta)) / 111.0
        lon_offset = (r * math.sin(theta)) / (111.0 * math.cos(math.radians(center_lat)))
        
        building_types = ["residential", "commercial", "industrial"]
        weights = [0.75, 0.2, 0.05]
        b_type = random.choices(building_types, weights=weights)[0]
        
        locations.append({
            "meter_id": f"{name_prefix}-{i:03d}",
            "name": f"{name_prefix} {i:03d}",
            "latitude": center_lat + lat_offset,
            "longitude": center_lon + lon_offset,
            "phase": random.choice(["A", "B", "C"]),
            "building_type": b_type,
            "zone": zone,
            "meter_type": "hybrid_prosumer" if random.random() < 0.4 else "grid_consumer",
            "has_solar": random.random() < 0.3,
            "has_battery": random.random() < 0.2,
            "solar_capacity": random.uniform(3, 10) if b_type == "residential" else random.uniform(20, 100),
            "battery_capacity": random.uniform(5, 15) if b_type == "residential" else random.uniform(30, 200)
        })
    return locations

def main():
    # Base path for output
    base_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(base_dir, "../src/smart_meter_simulator/config/initial_locations_islands.json")
    
    all_locations = []
    
    # 1. Koh Samui Distribution Hub (Resilient Node)
    # 50 MWh BESS and EGAT Generator are modeled as special high-capacity meters
    samui_meters = generate_cluster("SAMUI-DIST", 9.512, 100.012, 35, start_index=100, radius_km=4.0, zone="Samui")
    
    # Inject 50 MWh BESS at Samui Substation
    all_locations.append({
        "meter_id": "SAMUI-BESS-01",
        "name": "Koh Samui 50MWh BESS",
        "latitude": 9.535,
        "longitude": 100.060,
        "meter_type": "battery_storage",
        "has_battery": True,
        "battery_capacity": 50000.0, # 50 MWh
        "max_power_kw": 20000.0,    # 20 MW inverter
        "zone": "Samui",
        "priority": 1,
        "is_critical": True
    })
    
    # Inject EGAT Central Generator at Samui
    all_locations.append({
        "meter_id": "SAMUI-GEN-EGAT",
        "name": "Samui EGAT Main Gen",
        "latitude": 9.536,
        "longitude": 100.061,
        "meter_type": "solar_prosumer", # Using this type for general injection
        "has_solar": True,
        "solar_capacity": 25000.0, # 25 MW
        "zone": "Samui",
        "priority": 1
    })
    
    all_locations.extend(samui_meters)
    
    # 2. Koh Phangan
    all_locations.extend(generate_cluster("KPG-DIST", 9.712, 99.985, 20, start_index=300, radius_km=2.5, zone="Phangan"))
    
    # 3. Koh Tao (Isolated/Constrained Node)
    # Local 10 MW Diesel Gen and 5-10 MW load
    tao_meters = generate_cluster("TAO-DIST", 10.095, 99.833, 10, start_index=500, radius_km=1.5, zone="Tao")
    
    # Inject 10 MW Diesel Generator at Tao
    all_locations.append({
        "meter_id": "TAO-GEN-DIESEL",
        "name": "Koh Tao Diesel Power Plant",
        "latitude": 10.100,
        "longitude": 99.830,
        "meter_type": "solar_prosumer",
        "has_solar": True,
        "solar_capacity": 10000.0, # 10 MW
        "zone": "Tao",
        "priority": 1
    })
    
    all_locations.extend(tao_meters)
    
    # 4. Mainland Khanom Substation (The Supply Source)
    # Modeling the mainland as a reference point
    all_locations.append({
        "meter_id": "KHANOM-SUB-MAIN",
        "name": "Khanom Mainland Substation (EGAT)",
        "latitude": 9.235,
        "longitude": 99.859,
        "meter_type": "substation",
        "zone": "Mainland",
        "is_slack": True
    })

    output = {
        "scenario": "Gulf of Thailand Island Hub",
        "description": "Khanom -> Samui -> Phangan -> Tao transmission corridor with bottleneck constraints",
        "base_location": {
            "name": "Samui-Kanom-Pha-ngan Grid Hub",
            "lat": 9.45,
            "lng": 100.0,
            "phase": "MAIN"
        },
        "locations": all_locations
    }
    
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, "w") as f:
        json.dump(output, f, indent=4)
    
    print(f"Successfully generated {len(all_locations)} locations across 4 zones.")
    print(f"Scenario: {output['scenario']}")
    print(f"Output saved to: {output_path}")

if __name__ == "__main__":
    main()
