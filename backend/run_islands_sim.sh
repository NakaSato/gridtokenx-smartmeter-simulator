#!/bin/bash

# Configuration for Samui-Kanom-Pha-ngan Island Microgrid Simulation
export LOCATIONS_FILE="initial_locations_islands.json"
export BASE_LATITUDE=9.45
export BASE_LONGITUDE=100.0
export NUM_METERS=60
export TRANSPORT_TYPE="no-db"

echo "🚀 Starting GridTokenX Simulator: Island Microgrid Scenario"
echo "📍 Location: Samui-Kanom-Pha-ngan Archipelago"
echo "📄 Profile: $LOCATIONS_FILE"
echo "📊 Meters: $NUM_METERS"

# Run the simulator using uv
uv run uvicorn smart_meter_simulator.app:app --host 0.0.0.0 --port 8082 --reload
