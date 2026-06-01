import argparse
import asyncio
import logging
import os
import uvicorn
import redis

from smart_meter_simulator.core.engine import SimulationEngine
from smart_meter_simulator.devices.ami import SmartMeter
from smart_meter_simulator.transport.http import HttpTransport
from smart_meter_simulator.transport.grpc import GrpcTransport
from smart_meter_simulator.transport.mqtt import MqttTransport
from smart_meter_simulator.meter_generator import MeterGenerator
from smart_meter_simulator.adapters.pandapower_adapter import PandapowerAdapter
from smart_meter_simulator.config import get_config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def run_standalone(num_meters: int, api_url: str, api_key: str, scenario: str = None, transport_type: str = "http", register_keys: bool = False):
    """Run simulator in standalone mode (no API server)."""
    logger.info(f"Starting standalone simulation: {num_meters} meters, Transport={transport_type}, Scenario={scenario}")
    
    config = get_config()
    if transport_type == "grpc":
        transport = GrpcTransport(host=config.grpc_gateway_host, port=config.grpc_gateway_port)
    elif transport_type == "mqtt":
        transport = MqttTransport(
            broker_url=config.mqtt_broker_url,
            port=config.mqtt_port,
            username=config.mqtt_username,
            password=config.mqtt_password,
            base_topic=config.mqtt_topic,
        )
    else:
        transport = HttpTransport(base_url=api_url, api_key=api_key)
        
    generator = MeterGenerator(num_meters)
    adapter = None

    if scenario == "ieee123":
        adapter = PandapowerAdapter()
        net = adapter.build_ieee_123_node()
        meter_configs = generator.generate_ieee_meters(num_nodes=len(net.bus), target_meters=num_meters)
    elif scenario == "ieee8500":
        adapter = PandapowerAdapter()
        net = adapter.build_ieee_8500_node()
        meter_configs = generator.generate_ieee_meters(num_nodes=len(net.bus), target_meters=num_meters)
    else:
        meter_configs = generator.generate_meters()

    meters = [SmartMeter(config) for config in meter_configs]

    # Auto-register keys in Redis if requested
    if register_keys:
        try:
            r = redis.from_url(config.redis_url)
            registered_count = 0
            for meter in meters:
                key = f"gridtokenx:devices:{meter.meter_id}:pubkey"
                pubkey_hex = meter.key_manager.get_public_key_hex()
                r.set(key, pubkey_hex)
                registered_count += 1
            logger.info(f"Auto-registered {registered_count} meter public keys in Redis")
        except Exception as e:
            logger.warning(f"Auto-registration of keys in Redis failed: {e}")

    engine = SimulationEngine(meters, transport, adapter=adapter)

    try:
        await engine.start()
        # Keep alive while running
        while engine.running:
            await asyncio.sleep(1)
    except (KeyboardInterrupt, asyncio.CancelledError):
        logger.info("Simulation interrupted...")
        await engine.stop()
    finally:
        logger.info("Standalone simulation terminated.")


def main():
    parser = argparse.ArgumentParser(description="Smart Meter Simulator CLI")
    parser.add_argument(
        "--mode", choices=["server", "standalone"], default="server", help="Run mode"
    )
    parser.add_argument("--meters", type=int, default=20, help="Number of meters")
    parser.add_argument(
        "--scenario", choices=["ieee123", "ieee8500"], default=None, help="Feeder scenario topology"
    )
    parser.add_argument(
        "--transport", choices=["http", "grpc", "mqtt"], default="http", help="Telemetry transport type"
    )
    parser.add_argument(
        "--register-keys", action="store_true", help="Auto-register meter public keys in Redis"
    )
    parser.add_argument(
        "--api-url", default="http://localhost:3000", help="API Gateway URL"
    )
    parser.add_argument("--api-key", default="sim-secret-key", help="API Key")
    parser.add_argument("--port", type=int, default=8082, help="Server port")

    # New arguments based on user request "count price energy interval meter change"
    parser.add_argument(
        "--interval", type=int, help="Simulation interval in seconds (e.g. 900 for 15m)"
    )

    # Price parameters
    parser.add_argument(
        "--purchase-rate", type=float, help="Grid purchase rate (Baht/kWh)"
    )
    parser.add_argument(
        "--feed-in-rate", type=float, help="Grid feed-in rate (Baht/kWh)"
    )

    # Energy parameters
    parser.add_argument(
        "--base-gen-min", type=float, help="Minimum base generation (kW)"
    )
    parser.add_argument(
        "--base-gen-max", type=float, help="Maximum base generation (kW)"
    )
    parser.add_argument(
        "--base-cons-min", type=float, help="Minimum base consumption (kW)"
    )
    parser.add_argument(
        "--base-cons-max", type=float, help="Maximum base consumption (kW)"
    )

    # Meter distribution ratios
    parser.add_argument(
        "--solar-ratio", type=float, help="Ratio of solar prosumer meters"
    )
    parser.add_argument(
        "--consumer-ratio", type=float, help="Ratio of grid consumer meters"
    )
    parser.add_argument(
        "--hybrid-ratio", type=float, help="Ratio of hybrid prosumer meters"
    )
    parser.add_argument(
        "--battery-ratio", type=float, help="Ratio of battery storage meters"
    )
    parser.add_argument("--ev-ratio", type=float, help="Ratio of EV charger meters")
    parser.add_argument(
        "--dc-ratio", type=float, help="Ratio of DC fast charger meters"
    )

    args = parser.parse_args()

    # Map arguments to environment variables for SimulatorConfig
    os.environ["NUM_METERS"] = str(args.meters)
    os.environ["TRANSPORT_TYPE"] = args.transport
    os.environ["API_GATEWAY_URL"] = args.api_url
    os.environ["API_KEY"] = args.api_key
    os.environ["PORT"] = str(args.port)

    if args.interval:
        os.environ["SIMULATION_INTERVAL"] = str(args.interval)
    if args.purchase_rate:
        os.environ["GRID_PURCHASE_RATE"] = str(args.purchase_rate)
    if args.feed_in_rate:
        os.environ["GRID_FEED_IN_RATE"] = str(args.feed_in_rate)

    if args.base_gen_min:
        os.environ["BASE_GENERATION_MIN"] = str(args.base_gen_min)
    if args.base_gen_max:
        os.environ["BASE_GENERATION_MAX"] = str(args.base_gen_max)
    if args.base_cons_min:
        os.environ["BASE_CONSUMPTION_MIN"] = str(args.base_cons_min)
    if args.base_cons_max:
        os.environ["BASE_CONSUMPTION_MAX"] = str(args.base_cons_max)

    if args.solar_ratio:
        os.environ["SOLAR_PROSUMER_RATIO"] = str(args.solar_ratio)
    if args.consumer_ratio:
        os.environ["GRID_CONSUMER_RATIO"] = str(args.consumer_ratio)
    if args.hybrid_ratio:
        os.environ["HYBRID_PROSUMER_RATIO"] = str(args.hybrid_ratio)
    if args.battery_ratio:
        os.environ["BATTERY_STORAGE_RATIO"] = str(args.battery_ratio)
    if args.ev_ratio:
        os.environ["EV_CHARGER_RATIO"] = str(args.ev_ratio)
    if args.dc_ratio:
        os.environ["DC_CHARGER_RATIO"] = str(args.dc_ratio)

    if args.mode == "server":
        uvicorn.run(
            "smart_meter_simulator.app:app",
            host="0.0.0.0",
            port=args.port,
            reload=False,
        )
    else:
        asyncio.run(run_standalone(args.meters, args.api_url, args.api_key, args.scenario, args.transport, args.register_keys))


if __name__ == "__main__":
    main()
