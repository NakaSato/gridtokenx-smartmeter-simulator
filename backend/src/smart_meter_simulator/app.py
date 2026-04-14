#!/usr/bin/env python3
"""
FastAPI Application for Smart Meter Simulator
Provides REST API endpoints and WebSocket support with HTML rendering
"""

import asyncio
import logging
import os
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

from smart_meter_simulator.adapters.pandapower_adapter import PandapowerAdapter
from smart_meter_simulator.config import get_config
from smart_meter_simulator.core.db import DatabaseManager
from smart_meter_simulator.core.engine import SimulationEngine
from smart_meter_simulator.core.meter import SmartMeter
from smart_meter_simulator.meter_generator import MeterGenerator
from smart_meter_simulator.transport.composite import CompositeTransport
from smart_meter_simulator.transport.http import HttpTransport
from smart_meter_simulator.transport.grpc import GrpcTransport
from smart_meter_simulator.transport.influxdb import InfluxDBTransport
from smart_meter_simulator.transport.kafka import KafkaTransport
from smart_meter_simulator.transport.mqtt import MqttTransport
from smart_meter_simulator.transport.websocket import WebSocketTransport
from smart_meter_simulator.routers.api_v1 import router as api_v1_router
from smart_meter_simulator.routers.power_plants_v1 import router as power_plants_router

# OpenTelemetry Implementation
from opentelemetry import trace, metrics
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor

def setup_otel(service_name: str, endpoint: str):
    # Resource attributes
    resource = Resource.create({
        "service.name": service_name,
        "deployment.environment": os.getenv("ENVIRONMENT", "development"),
    })

    # Tracing
    tracer_provider = TracerProvider(resource=resource)
    span_exporter = OTLPSpanExporter(endpoint=endpoint, insecure=True)
    tracer_provider.add_span_processor(BatchSpanProcessor(span_exporter))
    trace.set_tracer_provider(tracer_provider)

    # Metrics
    metric_exporter = OTLPMetricExporter(endpoint=endpoint, insecure=True)
    reader = PeriodicExportingMetricReader(metric_exporter)
    meter_provider = MeterProvider(resource=resource, metric_readers=[reader])
    metrics.set_meter_provider(meter_provider)
    
    # Logging
    LoggingInstrumentor().instrument(set_logging_format=True)

# Initialize OTEL if enabled
otel_enabled = os.getenv("OTEL_ENABLED", "true").lower() == "true"
if otel_enabled:
    otel_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://otel-collector:4317")
    setup_otel("gridtokenx-smartmeter-simulator", otel_endpoint)

# Configure logging
log_level = os.getenv("LOG_LEVEL", "ERROR").upper()
logging.basicConfig(
    level=getattr(logging, log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

from smart_meter_simulator.core import app_state
from smart_meter_simulator.routers.api_v1 import router as api_v1_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Initializing Smart Meter Simulator...")

    global simulation_task
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
    http_transport = HttpTransport(base_url=config.api_gateway_url, api_key=config.api_key)
    websocket_transport = WebSocketTransport(app_state.websocket_manager)
    
    # Choose primary ingestion transport based on config
    if config.transport_type == "grpc":
        primary_transport = GrpcTransport(host=config.grpc_gateway_host, port=config.grpc_gateway_port)
        logger.info("Using Industrial gRPC Transport (DLMS/COSEM) for telemetry")
    elif config.transport_type == "mqtt":
        primary_transport = MqttTransport(
            broker_url=config.mqtt_broker_url,
            port=config.mqtt_port,
            username=config.mqtt_username,
            password=config.mqtt_password,
            base_topic=config.mqtt_topic
        )
        logger.info(f"Using Industrial MQTT Transport (DLMS/COSEM) for telemetry at {config.mqtt_broker_url}")
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
            bucket=config.influxdb_bucket
        )
        transports.append(influx_transport)
        logger.info(f"InfluxDB Transport initialized for complete storage at {config.influxdb_url}")


    # 3. Engine Setup
    generator = MeterGenerator(config.num_meters)
    meters = [SmartMeter(c) for c in generator.generate_meters()]
    
    # Register meters
    try: await http_transport.register_meters(meters)
    except Exception as e: logger.warning(f"Meter registration failed: {e}")
    # 6. Initialize Engine with Grid Adapter and DB Manager
    adapter = PandapowerAdapter()
    app_state.engine = SimulationEngine(meters, CompositeTransport(transports), adapter=adapter, db_manager=db_manager)
    # 7. Start Engine
    if not config.autostart_simulation:
        logger.info("AUTOSTART_SIMULATION is false, starting simulator in paused state...")
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

def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="Smart Meter Simulator",
        description="P2P Energy Trading Meter Simulator (Modular)",
        version="3.0.0",
        lifespan=lifespan
    )

    if otel_enabled:
        FastAPIInstrumentor().instrument_app(app)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Static and Templates
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    PROJECT_ROOT = os.path.dirname(os.path.dirname(BASE_DIR))
    UI_DIST_DIR = os.path.join(PROJECT_ROOT, "ui", "dist")

    if os.path.exists(UI_DIST_DIR):
        app.mount("/assets", StaticFiles(directory=os.path.join(UI_DIST_DIR, "assets")), name="ui-assets")

    # Routers
    app.include_router(api_v1_router)
    app.include_router(power_plants_router)

    return app

app = create_app()

# Exception Handlers
@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException):
    """Handle 404 errors"""
    if request.url.path.startswith("/api"):
        return JSONResponse(content={"detail": "Not Found", "path": request.url.path}, status_code=404)

    index_path = os.path.join(UI_DIST_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path, status_code=404)
    return HTMLResponse(content="<h1>404 - Not Found</h1>", status_code=404)

@app.exception_handler(500)
async def server_error_handler(request: Request, exc: HTTPException):
    """Handle 500 errors"""
    if request.url.path.startswith("/api"):
        return JSONResponse(content={"detail": "Internal Server Error"}, status_code=500)
    index_path = os.path.join(UI_DIST_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path, status_code=500)
    return HTMLResponse(content="<h1>500 - Server Error</h1>", status_code=500)

@app.get("/health")
async def health_check():
    from datetime import datetime
    return {"status": "ok", "timestamp": datetime.now().isoformat()}

async def serve_ui():
    index_path = os.path.join(UI_DIST_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return HTMLResponse(content="<h1>UI Build not found.</h1>")

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await app_state.websocket_manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        await app_state.websocket_manager.disconnect(websocket)




@app.get("/metrics")
async def get_metrics():
    from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
    from fastapi import Response
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.get("/{full_path:path}", response_class=HTMLResponse)
async def catch_all(full_path: str, request: Request):
    # Don't catch /api routes
    if request.url.path.startswith("/api"):
        return JSONResponse(content={"detail": "Not Found", "path": request.url.path}, status_code=404)
    # Serve UI for SPA routing
    index_path = os.path.join(UI_DIST_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return HTMLResponse(content="<h1>Not Found</h1>", status_code=404)

def main():
    port = int(os.getenv("PORT", 8082))
    uvicorn.run("smart_meter_simulator.app:app", host="0.0.0.0", port=port, reload=False)

if __name__ == "__main__":
    main()
