
import logging
from smart_meter_simulator.adapters.egat_transmission import EGATTransmissionBuilder

def test_integration():
    logging.basicConfig(level=logging.INFO)
    builder = EGATTransmissionBuilder()
    
    initial_subs = len(builder.substations)
    initial_lines = len(builder.lines)
    print(f"Initial state: {initial_subs} substations, {initial_lines} lines")
    
    # Fetch around Bangkok (smaller area for speed)
    print("Fetching from OSM...")
    builder.fetch_from_osm(location="Bangkok")
    
    final_subs = len(builder.substations)
    final_lines = len(builder.lines)
    print(f"Final state: {final_subs} substations, {final_lines} lines")
    print(f"Added {final_subs - initial_subs} substations and {final_lines - initial_lines} lines from OSM")

if __name__ == "__main__":
    test_integration()
