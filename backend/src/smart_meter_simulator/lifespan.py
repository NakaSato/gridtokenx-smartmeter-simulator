import asyncio
import logging
import redis
from contextlib import asynccontextmanager
from fastapi import FastAPI

from smart_meter_simulator.config import get_config
from smart_meter_simulator.core import app_state
from smart_meter_simulator.core.db import DatabaseManager
from smart_meter_simulator.core.engine import SimulationEngine
from smart_meter_simulator.devices.ami import SmartMeter
from smart_meter_simulator.meter_generator import MeterGenerator
from smart_meter_simulator.transport.composite import CompositeTransport
from smart_meter_simulator.transport.http import HttpTransport
from smart_meter_simulator.transport.grpc import GrpcTransport
from smart_meter_simulator.transport.influxdb import InfluxDBTransport
from smart_meter_simulator.transport.kafka import KafkaTransport
from smart_meter_simulator.transport.mqtt import MqttTransport
from smart_meter_simulator.transport.websocket import WebSocketTransport

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Initializing Smart Meter Simulator...")

    simulation_task = None
    config = get_config()

    # 1. Initialize Persistence (PostgreSQL)
    db_manager = None
    try:
        db_manager = DatabaseManager(config.database_url)
        await db_manager.init_db()
        logger.info("Database connection established")
    except Exception as e:
        logger.warning(f"Database initialization failed: {e}")

    # 2. Initialize Transports
    http_transport = HttpTransport(
        base_url=config.api_gateway_url, api_key=config.api_key
    )
    websocket_transport = WebSocketTransport(app_state.websocket_manager)

    # Choose primary ingestion transport based on config
    if config.transport_type == "grpc":
        primary_transport = GrpcTransport(
            host=config.grpc_gateway_host, port=config.grpc_gateway_port
        )
        logger.info("Using Industrial gRPC Transport (DLMS/COSEM) for telemetry")
    elif config.transport_type == "mqtt":
        primary_transport = MqttTransport(
            broker_url=config.mqtt_broker_url,
            port=config.mqtt_port,
            username=config.mqtt_username,
            password=config.mqtt_password,
            base_topic=config.mqtt_topic,
        )
        logger.info(
            f"Using Industrial MQTT Transport (DLMS/COSEM) for telemetry at {config.mqtt_broker_url}"
        )
    else:
        primary_transport = http_transport
        logger.info("Using legacy REST Transport for telemetry")

    transports = [primary_transport, websocket_transport]

    if config.kafka_servers:
        transports.append(KafkaTransport(config.kafka_servers, config.kafka_topic))

    if config.influxdb_url:
        influx_transport = InfluxDBTransport(
            url=config.influxdb_url,
            token=config.influxdb_token,
            org=config.influxdb_org,
            bucket=config.influxdb_bucket,
        )
        transports.append(influx_transport)
        logger.info(
            f"InfluxDB Transport initialized for complete storage at {config.influxdb_url}"
        )

    # 3. Engine Setup
    generator = MeterGenerator(config.num_meters)
    meters = [SmartMeter(c) for c in generator.generate_meters()]

    # Auto-register keys in Redis (Essential for Oracle Bridge signature verification)
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

    # Register meters
    try:
        # API Gateway (Oracle Bridge) handles registration internally or via different means now
        # await http_transport.register_meters(meters)
        pass
    except Exception as e:
        logger.warning(f"Meter registration failed: {e}")

    # 4. Initialize Engine with Grid Adapter and DB Manager
    app_state.engine = SimulationEngine(
        meters, CompositeTransport(transports), adapter=None, db_manager=db_manager
    )

    # 5. Start Engine
    if not config.autostart_simulation:
        logger.info(
            "AUTOSTART_SIMULATION is false, starting simulator in paused state..."
        )
        app_state.engine.paused = True

    simulation_task = asyncio.create_task(app_state.engine.start())

    yield

    # Shutdown
    logger.info("Shutting down simulator...")
    if app_state.engine:
        await app_state.engine.stop()
    if simulation_task:
        simulation_task.cancel()
        try:
            await simulation_task
        except asyncio.CancelledError:
            pass

    logger.info("Simulator shutdown complete")
