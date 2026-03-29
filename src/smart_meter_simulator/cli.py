import argparse
import asyncio
import logging
import os
import uvicorn

from smart_meter_simulator.core.engine import SimulationEngine
from smart_meter_simulator.core.meter import SmartMeter
from smart_meter_simulator.transport.http import HttpTransport
from smart_meter_simulator.meter_generator import MeterGenerator
from smart_meter_simulator.utils.zk_worker import zk_pool

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def run_standalone(num_meters: int, api_url: str, api_key: str):
    """Run simulator in standalone mode (no API server)."""
    logger.info(f"Starting standalone simulation: {num_meters} meters, API={api_url}")
    transport = HttpTransport(base_url=api_url, api_key=api_key)
    generator = MeterGenerator(num_meters)
    meter_configs = generator.generate_meters()
    meters = [SmartMeter(config) for config in meter_configs]
    
    engine = SimulationEngine(meters, transport)
    
    try:
        await engine.start()
        # Keep alive while running
        while engine.running:
            await asyncio.sleep(1)
    except (KeyboardInterrupt, asyncio.CancelledError):
        logger.info("Simulation interrupted...")
        await engine.stop()
    finally:
        zk_pool.shutdown()
        logger.info("Standalone simulation terminated.")

def main():
    parser = argparse.ArgumentParser(description="Smart Meter Simulator CLI")
    parser.add_argument("--mode", choices=["server", "standalone"], default="server", help="Run mode")
    parser.add_argument("--meters", type=int, default=20, help="Number of meters")
    parser.add_argument("--api-url", default="http://localhost:3000", help="API Gateway URL")
    parser.add_argument("--api-key", default="sim-secret-key", help="API Key")
    parser.add_argument("--port", type=int, default=8082, help="Server port")
    
    # New arguments based on user request "count price energy interval meter change"
    parser.add_argument("--interval", type=int, help="Simulation interval in seconds (e.g. 900 for 15m)")
    
    # Price parameters
    parser.add_argument("--purchase-rate", type=float, help="Grid purchase rate (Baht/kWh)")
    parser.add_argument("--feed-in-rate", type=float, help="Grid feed-in rate (Baht/kWh)")
    
    # Energy parameters
    parser.add_argument("--base-gen-min", type=float, help="Minimum base generation (kW)")
    parser.add_argument("--base-gen-max", type=float, help="Maximum base generation (kW)")
    parser.add_argument("--base-cons-min", type=float, help="Minimum base consumption (kW)")
    parser.add_argument("--base-cons-max", type=float, help="Maximum base consumption (kW)")
    
    # Meter distribution ratios
    parser.add_argument("--solar-ratio", type=float, help="Ratio of solar prosumer meters")
    parser.add_argument("--consumer-ratio", type=float, help="Ratio of grid consumer meters")
    parser.add_argument("--hybrid-ratio", type=float, help="Ratio of hybrid prosumer meters")
    parser.add_argument("--battery-ratio", type=float, help="Ratio of battery storage meters")
    parser.add_argument("--ev-ratio", type=float, help="Ratio of EV charger meters")
    
    args = parser.parse_args()
    
    # Map arguments to environment variables for SimulatorConfig
    os.environ["NUM_METERS"] = str(args.meters)
    os.environ["API_GATEWAY_URL"] = args.api_url
    os.environ["API_KEY"] = args.api_key
    os.environ["PORT"] = str(args.port)
    
    if args.interval: os.environ["SIMULATION_INTERVAL"] = str(args.interval)
    if args.purchase_rate: os.environ["GRID_PURCHASE_RATE"] = str(args.purchase_rate)
    if args.feed_in_rate: os.environ["GRID_FEED_IN_RATE"] = str(args.feed_in_rate)
    
    if args.base_gen_min: os.environ["BASE_GENERATION_MIN"] = str(args.base_gen_min)
    if args.base_gen_max: os.environ["BASE_GENERATION_MAX"] = str(args.base_gen_max)
    if args.base_cons_min: os.environ["BASE_CONSUMPTION_MIN"] = str(args.base_cons_min)
    if args.base_cons_max: os.environ["BASE_CONSUMPTION_MAX"] = str(args.base_cons_max)
    
    if args.solar_ratio: os.environ["SOLAR_PROSUMER_RATIO"] = str(args.solar_ratio)
    if args.consumer_ratio: os.environ["GRID_CONSUMER_RATIO"] = str(args.consumer_ratio)
    if args.hybrid_ratio: os.environ["HYBRID_PROSUMER_RATIO"] = str(args.hybrid_ratio)
    if args.battery_ratio: os.environ["BATTERY_STORAGE_RATIO"] = str(args.battery_ratio)
    if args.ev_ratio: os.environ["EV_CHARGER_RATIO"] = str(args.ev_ratio)
    
    if args.mode == "server":
        uvicorn.run("smart_meter_simulator.app:app", host="0.0.0.0", port=args.port, reload=False)
    else:
        asyncio.run(run_standalone(args.meters, args.api_url, args.api_key))

if __name__ == "__main__":
    main()
