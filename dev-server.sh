#!/bin/bash
# Development server startup script

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}Starting Smart Meter Simulator in Development Mode${NC}"

# Set environment variables
export DEV_MODE=true
export PYTHONPATH=$(pwd)/src
export PORT=8080

# Activate virtual environment
source .venv/bin/activate

# Start the server
echo -e "${GREEN}Starting FastAPI backend on port 8001...${NC}"
echo -e "${BLUE}PYTHONPATH: $PYTHONPATH${NC}"
echo -e "${BLUE}DEV_MODE: $DEV_MODE${NC}"
echo ""
echo -e "${GREEN}Backend will be available at: http://localhost:8001${NC}"
echo -e "${GREEN}In another terminal, run: npm run dev${NC}"
echo -e "${GREEN}Then open: http://localhost:5173${NC}"
echo ""

uvicorn smart_meter_simulator.app:app --reload --host 0.0.0.0 --port $PORT
