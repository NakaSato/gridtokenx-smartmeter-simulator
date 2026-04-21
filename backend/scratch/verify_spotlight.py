
import logging
import json
from smart_meter_simulator.adapters.egat_transmission import EGATTransmissionBuilder
from pathlib import Path

def verify_spotlight_data():
    logging.basicConfig(level=logging.INFO)
    builder = EGATTransmissionBuilder()
    
    # Path to the spotlight GeoJSON
    DATA_DIR = Path(__file__).parent.parent / "src/smart_meter_simulator/data"
    path = DATA_DIR / "spotlight_samui.geojson"
    
    print(f"Loading spotlight data from {path}...")
    builder.load_from_geojson(str(path))
    
    print("\nResults:")
    print(f"Total Substations: {len(builder.substations)}")
    print(f"Total Lines: {len(builder.lines)}")
    print(f"Total Power Plants: {len(builder.power_plants)}")
    
    # Check for Samui specific assets
    for lid, line in builder.lines.items():
        if "Samui" in line.line_id or (isinstance(line.notes, str) and "Samui" in line.notes):
             print(f"Found line: {lid} - {line.voltage_kv}kV")
             
    for pid, plant in builder.power_plants.items():
        print(f"Found plant: {pid} - {plant.capacity_mw}MW")

if __name__ == "__main__":
    verify_spotlight_data()
