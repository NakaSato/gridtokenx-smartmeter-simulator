#!/bin/bash

# Configuration for Khanom Power Station Simulation
export LOCATIONS_FILE="initial_locations_khanom.json"
export BASE_LATITUDE=9.234959
export BASE_LONGITUDE=99.860229
export NUM_METERS=5
export TRANSPORT_TYPE="no-db" # Run without DB for now due to Docker status

echo "🚀 Starting GridTokenX Simulator: Khanom Scenario"
echo "📍 Location: Khanom Power Station, South Thailand"
echo "📄 Profile: $LOCATIONS_FILE"

# Run the simulator using uv (recommended in README)
uv run uvicorn smart_meter_simulator.app:app --host 0.0.0.0 --port 8082
