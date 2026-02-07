import argparse
import asyncio
import logging
import os
import uvicorn

from smart_meter_simulator.core.engine import SimulationEngine
from smart_meter_simulator.core.meter import SmartMeter
from smart_meter_simulator.transport.http import HttpTransport
from smart_meter_simulator.meter_generator import MeterGenerator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def run_standalone(num_meters: int, api_url: str, api_key: str):
    """Run simulator in standalone mode (no API server)."""
    transport = HttpTransport(base_url=api_url, api_key=api_key)
    generator = MeterGenerator(num_meters)
    meter_configs = generator.generate_meters()
    meters = [SmartMeter(config) for config in meter_configs]
    
    engine = SimulationEngine(meters, transport)
    
    try:
        await engine.start()
    except KeyboardInterrupt:
        await engine.stop()

def main():
    parser = argparse.ArgumentParser(description="Smart Meter Simulator CLI")
    parser.add_argument("--mode", choices=["server", "standalone"], default="server", help="Run mode")
    parser.add_argument("--meters", type=int, default=20, help="Number of meters")
    parser.add_argument("--api-url", default="http://localhost:3000", help="API Gateway URL")
    parser.add_argument("--api-key", default="sim-secret-key", help="API Key")
    parser.add_argument("--port", type=int, default=8000, help="Server port")
    
    args = parser.parse_args()
    
    if args.mode == "server":
        # Set env vars for app.py
        os.environ["NUM_METERS"] = str(args.meters)
        os.environ["API_GATEWAY_URL"] = args.api_url
        os.environ["API_KEY"] = args.api_key
        os.environ["PORT"] = str(args.port)
        
        uvicorn.run("smart_meter_simulator.app:app", host="0.0.0.0", port=args.port, reload=False)
        
    else:
        asyncio.run(run_standalone(args.meters, args.api_url, args.api_key))

if __name__ == "__main__":
    main()
