#!/usr/bin/env python3
"""
FastAPI Application for Smart Meter Simulator
Provides REST API endpoints and WebSocket support with HTML rendering
"""

import asyncio
import logging
import os
from pathlib import Path
import random
import uuid
from contextlib import asynccontextmanager
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

# Get the project root directory (where templates and static folders are)
# app.py is in src/smart_meter_simulator/app.py
# So: parent -> smart_meter_simulator/, parent -> src/, parent -> project root
PROJECT_ROOT = Path(__file__).parent.parent.parent
# Templates and static are in src/ directory
TEMPLATES_DIR = PROJECT_ROOT / "src" / "templates"
STATIC_DIR = PROJECT_ROOT / "src" / "static"

from smart_meter_simulator.core.engine import SimulationEngine
# Use PhysicsSimulationEngine for P2P features
from smart_meter_simulator.simulation.engine import PhysicsSimulationEngine
from smart_meter_simulator.core.meter import SmartMeter
from smart_meter_simulator.transport.http import HttpTransport
from smart_meter_simulator.transport.websocket import (
    WebSocketManager,
    WebSocketTransport,
)
from smart_meter_simulator.transport.composite import CompositeTransport
from smart_meter_simulator.meter_generator import MeterGenerator

# Configure logging
# Configure logging
log_level = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

from smart_meter_simulator.core.database import DatabaseManager

# Global state
engine: Optional[SimulationEngine] = None
simulation_task: Optional[asyncio.Task] = None
websocket_manager = WebSocketManager()
db_manager: Optional[DatabaseManager] = None

# Simulation parameters (user-controlled)
simulation_params = {
    "weather": "Auto",  # Auto, Sunny, Partly_Cloudy, Cloudy, Rainy
    "solar_multiplier": 1.0,  # 0.0 - 1.0
    "consumption_multiplier": 1.0,  # 0.0 - 2.0
    "grid_buy_price": 0.28,  # USD per kWh
    "grid_sell_price": 0.12,  # USD per kWh
}

# Per-meter manual overrides
meter_overrides = {}  # {meter_id: {mode, energy_generated, energy_consumed, battery_level}}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for FastAPI"""
    global engine, simulation_task, db_manager

    # Startup
    logger.info("Initializing Smart Meter Simulator...")

    # Configuration
    api_url = os.getenv("API_GATEWAY_URL", "http://localhost:4000")
    api_key = os.getenv("API_KEY", "sim-secret-key")
    num_meters = int(os.getenv("NUM_METERS", "20"))

    # 0. Initialize Database
    db_manager = DatabaseManager()

    # 1. Initialize Transports
    http_transport = HttpTransport(base_url=api_url, api_key=api_key)
    websocket_transport = WebSocketTransport(websocket_manager)

    # 2. Create Composite Transport
    composite_transport = CompositeTransport([http_transport, websocket_transport])

    # 3. Load Meters from DB
    loaded_configs = db_manager.load_meters()
    meters = [SmartMeter(config) for config in loaded_configs]

    # 4. Initialize Engine (Physics Engine for P2P support)
    engine = PhysicsSimulationEngine(meters, composite_transport, db_manager)
    
    # Store engine in app state for API access
    app.state.engine = engine

    # 4. Start Engine
    simulation_task = asyncio.create_task(engine.start())
    logger.info(f"Simulator started with {len(meters)} meters")

    yield

    # Shutdown
    logger.info("Shutting down simulator...")
    if engine:
        await engine.stop()

    if simulation_task:
        simulation_task.cancel()
        try:
            await simulation_task
        except asyncio.CancelledError:
            pass

    logger.info("Simulator shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="Smart Meter Simulator",
    description="P2P Energy Trading Meter Simulator (Renewed)",
    version="2.0.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure directories exist
STATIC_DIR.mkdir(parents=True, exist_ok=True)
TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)

# Mount static files
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Setup templates
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

logger.info(f"Templates directory: {TEMPLATES_DIR}")
logger.info(f"Static directory: {STATIC_DIR}")

logger.info(f"Static directory: {STATIC_DIR}")

# Import Routers
from smart_meter_simulator.api.p2p import router as p2p_router

# Include Routers
app.include_router(p2p_router)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok"}


@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Main dashboard page"""
    # Detect development mode (Vite dev server running)
    dev_mode = os.getenv("DEV_MODE", "false").lower() == "true"

    manifest = {}
    if not dev_mode:
        try:
            manifest_path = STATIC_DIR / ".vite" / "manifest.json"
            if manifest_path.exists():
                import json

                with open(manifest_path, "r") as f:
                    manifest_data = json.load(f)
                    # Map original filenames to hashed filenames
                    # We need main.js and main.css (which is imported by main.js)
                    if "js/dashboard.js" in manifest_data:
                        entry = manifest_data["js/dashboard.js"]
                        manifest["main.js"] = entry["file"]
                        if "css" in entry and entry["css"]:
                            manifest["main.css"] = entry["css"][0]
            else:
                logger.warning(f"Manifest file not found at {manifest_path}")
        except Exception as e:
            logger.error(f"Error loading manifest: {e}")

    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "title": "Smart Meter Simulator Dashboard",
            "status": "Running" if engine and engine.running else "Stopped",
            "meter_count": len(engine.meters) if engine else 0,
            "dev_mode": dev_mode,
            "manifest": manifest,
        },
    )


@app.get("/how-it-works", response_class=HTMLResponse)
async def how_it_works(request: Request):
    """Animated explanation page"""
    return templates.TemplateResponse(
        "how_it_works.html",
        {"request": request, "title": "How It Works - Smart Meter Simulator"},
    )


@app.get("/maps", response_class=HTMLResponse)
async def maps_page(request: Request):
    """Interactive map view of smart meters"""
    return templates.TemplateResponse(
        "maps.html",
        {"request": request, "title": "Smart Meter Map - GridTokenX"},
    )

@app.get("/thailand-demo", response_class=HTMLResponse)
async def thailand_demo_page(request: Request):
    """Thailand GIS Data Demo Page"""
    return templates.TemplateResponse(
        "thailand_demo.html",
        {"request": request, "title": "Thailand Smart Grid Demo (Phaya Thai)"},
    )

@app.get("/api/thailand/data")
async def get_thailand_data():
    """Get static structure of Thailand grid (Transformers/Zones and Meters)"""
    if not engine:
         return {"error": "Simulator not initialized"}
    
    # Reuse /api/zones logic but exposed specifically for this demo to ensure clarity
    # Getting zone summary from zoning service which is now initialized with Thailand data
    try:
        zone_summary = engine.zoning_service.get_zone_summary()
        zones = {}
        for zone_id, info in zone_summary.items():
            zones[zone_id] = {
                "zone_id": int(info.zone_id),
                "centroid_lat": float(info.centroid_lat),
                "centroid_lon": float(info.centroid_lon),
                "meter_count": int(info.meter_count),
                "transformer_name": f"TR-{info.zone_id}", # Custom naming
            }
            
        meters = []
        for meter in engine.meters:
            if meter.latitude is not None and meter.longitude is not None:
                zid = getattr(meter, "grid_zone_id", None)
                meters.append({
                    "meter_id": str(meter.meter_id),
                    "latitude": float(meter.latitude),
                    "longitude": float(meter.longitude),
                    "zone_id": int(zid) if zid is not None else None,
                    "meter_type": str(meter.config.get("meter_type", "Unknown")),
                    "contract_capacity": meter.config.get("contract_capacity_kw", 0),
                    "building_area": meter.config.get("building_area_sqm", 0)
                })
        
        return {
            "region": "Phaya Thai, Bangkok",
            "stats": {
                "total_meters": len(meters),
                "total_transformers": len(zones)
            },
            "zones": zones,
            "meters": meters
        }
    except Exception as e:
        import traceback
        return {"error": str(e), "traceback": traceback.format_exc()}

@app.get("/api/zones")
async def get_zones():
    """Get K-Means zone data including centroids and meter assignments"""
    if not engine:
        return {"error": "Simulator not initialized"}

    try:
        # Get zone summary from zoning service
        zone_summary = engine.zoning_service.get_zone_summary()
        
        # Build zones dict with explicit type casting for JSON serialization
        zones = {}
        for zone_id, info in zone_summary.items():
            zones[zone_id] = {
                "zone_id": int(info.zone_id),
                "centroid_lat": float(info.centroid_lat),
                "centroid_lon": float(info.centroid_lon),
                "meter_count": int(info.meter_count),
                "transformer_name": str(info.transformer_name),
            }
        
        # Build meters list with zone assignments
        meters = []
        for meter in engine.meters:
            if meter.latitude is not None and meter.longitude is not None:
                zid = getattr(meter, "grid_zone_id", None)
                meters.append({
                    "meter_id": str(meter.meter_id),
                    "latitude": float(meter.latitude),
                    "longitude": float(meter.longitude),
                    "zone_id": int(zid) if zid is not None else None,
                    "meter_type": str(meter.config.get("meter_type", "Unknown")),
                })
        
        return {
            "zones": zones,
            "meters": meters,
            "wheeling_charges": engine.zoning_service.get_wheeling_charge_matrix(),
            "loss_factors": engine.zoning_service.get_loss_factor_matrix(),
        }
    except Exception as e:
        import traceback
        return {"error": str(e), "traceback": traceback.format_exc()}


@app.get("/api/status")
async def get_status():
    """Get simulator status"""
    if not engine:
        return {"error": "Simulator not initialized"}

    # Create meter data for dashboard
    meters_data = []
    for meter in engine.meters:
        # Get latest reading from meter if available
        latest_reading = None
        if hasattr(meter, "last_reading") and meter.last_reading:
            latest_reading = meter.last_reading

        meters_data.append(
            {
                "meter_id": meter.meter_id,
                "name": meter.config.get("meter_type", "Unknown"),
                "location": meter.config.get("location", "Unknown"),
                "capacity": meter.config.get("solar_capacity", 0),
                "current_generation": getattr(latest_reading, "energy_generated", 0)
                if latest_reading
                else 0,
                "current_consumption": getattr(latest_reading, "energy_consumed", 0)
                if latest_reading
                else 0,
                "energy_type": meter.config.get("meter_type", "solar"),
                "status": "active",
                "latitude": meter.latitude,
                "longitude": meter.longitude,
                "net_emission": getattr(latest_reading, "net_emission", 0.0)
                if latest_reading
                else 0.0,
                "is_connected": getattr(meter, "is_connected", False),
            }
        )

    # Get API gateway URL from transport
    api_gateway = "Unknown"
    api_gateway_connected = False
    if (
        isinstance(engine.transport, CompositeTransport)
        and len(engine.transport.transports) > 0
    ):
        http_transport = engine.transport.transports[0]
        if isinstance(http_transport, HttpTransport):
            api_gateway = http_transport.base_url
            # Check if at least one meter is connected
            api_gateway_connected = any(
                getattr(m, "is_connected", False) for m in engine.meters
            )

    # Count connected meters
    connected_count = sum(1 for m in engine.meters if getattr(m, "is_connected", False))

    return {
        "status": "running" if engine.running else "stopped",
        "running": engine.running,
        "paused": getattr(engine, "paused", False),
        "meters": meters_data,
        "num_meters": len(engine.meters),
        "connected_meters": connected_count,
        "disconnected_meters": len(engine.meters) - connected_count,
        "mode": "Simulation",
        "api_gateway": api_gateway,
        "api_gateway_connected": api_gateway_connected,
        "websocket_clients": websocket_manager.get_connection_count(),
        "websocket_connections": websocket_manager.get_connection_count(),
    }


@app.get("/api/meters/{meter_id}/status")
async def get_meter_status(meter_id: str):
    """Get detailed status for a specific meter"""
    if not engine:
        return {"error": "Simulator not initialized"}

    # Find the meter
    target_meter = None
    for meter in engine.meters:
        if meter.meter_id == meter_id:
            target_meter = meter
            break

    if not target_meter:
        return {
            "error": "Meter not found",
            "meter_id": meter_id,
            "available_meters": [m.meter_id for m in engine.meters],
        }

    # Get latest reading
    latest_reading = None
    if hasattr(target_meter, "last_reading") and target_meter.last_reading:
        latest_reading = target_meter.last_reading

    # Build detailed status
    return {
        "meter_id": target_meter.meter_id,
        "meter_type": target_meter.config.get("meter_type", "Unknown"),
        "location": target_meter.config.get("location", "Unknown"),
        "user_type": target_meter.config.get("user_type", "Unknown"),
        "wallet_address": target_meter.wallet_address,
        # Connection status
        "is_connected": getattr(target_meter, "is_connected", False),
        "connection_status": "✅ ONLINE"
        if getattr(target_meter, "is_connected", False)
        else "❌ OFFLINE",
        # Configuration
        "config": {
            "has_solar": target_meter.config.get("has_solar", False),
            "solar_capacity": target_meter.config.get("solar_capacity", 0),
            "has_battery": target_meter.config.get("has_battery", False),
            "battery_capacity": target_meter.config.get("battery_capacity", 0),
            "trading_preference": target_meter.config.get(
                "trading_preference", "Unknown"
            ),
        },
        # Current state
        "current_state": {
            "battery_level": round(target_meter.battery_level, 2),
            "current_weather": target_meter.current_weather,
            "current_sell_price": round(target_meter.current_sell_price, 4),
            "current_buy_price": round(target_meter.current_buy_price, 4),
        },
        # Latest reading (if available)
        "latest_reading": {
            "timestamp": latest_reading.timestamp.isoformat()
            if latest_reading
            else None,
            "energy_generated": round(latest_reading.energy_generated, 4)
            if latest_reading
            else 0,
            "energy_consumed": round(latest_reading.energy_consumed, 4)
            if latest_reading
            else 0,
            "surplus_energy": round(latest_reading.surplus_energy, 4)
            if latest_reading
            else 0,
            "deficit_energy": round(latest_reading.deficit_energy, 4)
            if latest_reading
            else 0,
            "battery_level": round(latest_reading.battery_level, 2)
            if latest_reading
            else 0,
            "voltage": round(latest_reading.voltage, 2) if latest_reading else 0,
            "current": round(latest_reading.current, 3) if latest_reading else 0,
            "temperature": round(latest_reading.temperature, 1)
            if latest_reading
            else 0,
            "net_emission": round(latest_reading.net_emission, 4)
            if latest_reading
            else 0,
            "rec_eligible": latest_reading.rec_eligible if latest_reading else False,
            "wallet_address": latest_reading.wallet_address if latest_reading else None,
        }
        if latest_reading
        else None,
        # GPS coordinates
        "coordinates": {
            "latitude": target_meter.latitude,
            "longitude": target_meter.longitude,
        },
    }


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time meter readings"""
    await websocket_manager.connect(websocket)
    try:
        while True:
            # Keep connection alive and handle any incoming messages
            await websocket.receive_text()
    except WebSocketDisconnect:
        await websocket_manager.disconnect(websocket)


@app.post("/api/control/start")
async def start_simulation():
    """Start the simulation"""
    global simulation_task

    if not engine:
        return {"success": False, "message": "Simulator not initialized"}

    if engine.running:
        return {"success": False, "message": "Simulation already running"}

    try:
        engine.running = True
        simulation_task = asyncio.create_task(engine.start())
        return {
            "success": True,
            "message": "Simulation started",
            "status": {
                "running": True,
                "paused": getattr(engine, "paused", False),
                "num_meters": len(engine.meters),
            },
        }
    except Exception as e:
        return {"success": False, "message": str(e)}


@app.post("/api/control/stop")
async def stop_simulation():
    """Stop the simulation"""
    global simulation_task

    if not engine:
        return {"success": False, "message": "Simulator not initialized"}

    try:
        engine.running = False
        if simulation_task is not None:
            simulation_task.cancel()
            try:
                await simulation_task
            except asyncio.CancelledError:
                pass

        return {
            "success": True,
            "message": "Simulation stopped",
            "status": {
                "running": False,
                "paused": getattr(engine, "paused", False),
                "num_meters": len(engine.meters),
            },
        }
    except Exception as e:
        return {"success": False, "message": str(e)}


@app.post("/api/control/pause")
async def pause_simulation():
    """Pause the simulation"""
    if not engine:
        return {"success": False, "message": "Simulator not initialized"}

    try:
        engine.paused = True
        return {
            "success": True,
            "message": "Simulation paused",
            "status": {
                "running": engine.running,
                "paused": True,
                "num_meters": len(engine.meters),
            },
        }
    except Exception as e:
        return {"success": False, "message": str(e)}


@app.post("/api/control/resume")
async def resume_simulation():
    """Resume the simulation"""
    if not engine:
        return {"success": False, "message": "Simulator not initialized"}

    try:
        engine.paused = False
        return {
            "success": True,
            "message": "Simulation resumed",
            "status": {
                "running": engine.running,
                "paused": False,
                "num_meters": len(engine.meters),
            },
        }
    except Exception as e:
        return {"success": False, "message": str(e)}


@app.post("/api/control/restart")
async def restart_simulation():
    """Restart the simulation"""
    global simulation_task

    if not engine:
        return {"success": False, "message": "Simulator not initialized"}

    try:
        # Stop current simulation
        engine.running = False
        if simulation_task is not None:
            simulation_task.cancel()
            try:
                await simulation_task
            except asyncio.CancelledError:
                pass

        # Restart simulation
        await asyncio.sleep(1)  # Brief pause
        engine.running = True
        engine.paused = False
        simulation_task = asyncio.create_task(engine.start())

        return {
            "success": True,
            "message": "Simulation restarted",
            "status": {
                "running": True,
                "paused": False,
                "num_meters": len(engine.meters),
            },
        }
    except Exception as e:
        return {"success": False, "message": str(e)}


@app.post("/api/control/meters")
async def update_meter_count(request: dict):
    """Update the number of meters"""
    if not engine:
        return {"success": False, "message": "Simulator not initialized"}

    try:
        return {
            "success": False,
            "message": "Automatic meter generation is disabled. Please add meters manually.",
        }
    except Exception as e:
        return {"success": False, "message": str(e)}


@app.post("/api/meters/add")
async def add_meter(request: dict):
    """Add a new meter to the simulation"""
    if not engine:
        return {"success": False, "message": "Simulator not initialized"}

    try:
        # Extract meter configuration from request
        meter_type = request.get("meter_type", "Solar_Prosumer")
        location = request.get(
            "location", f"Zone_{random.randint(1, 5)}_Building_{random.randint(1, 10)}"
        )
        solar_capacity = float(request.get("solar_capacity", 10.0))
        battery_capacity = float(request.get("battery_capacity", 10.0))
        trading_preference = request.get("trading_preference", "Moderate")

        # Optional GPS coordinates
        latitude = request.get("latitude")
        longitude = request.get("longitude")
        if latitude is not None:
            latitude = float(latitude)
        if longitude is not None:
            longitude = float(longitude)

        # Validate meter type
        valid_types = [
            "Solar_Prosumer",
            "Grid_Consumer",
            "Hybrid_Prosumer",
            "Battery_Storage",
        ]
        if meter_type not in valid_types:
            return {
                "success": False,
                "message": f"Invalid meter type. Must be one of: {', '.join(valid_types)}",
            }

        # Validate trading preference
        valid_preferences = ["Aggressive", "Moderate", "Conservative"]
        if trading_preference not in valid_preferences:
            return {
                "success": False,
                "message": f"Invalid trading preference. Must be one of: {', '.join(valid_preferences)}",
            }

        # Custom Identity
        meter_id = request.get("meter_id")
        wallet_address = request.get("wallet_address")

        # Create meter configuration
        meter_config = {
            "meter_id": meter_id or str(uuid.uuid4()),
            "meter_type": meter_type,
            "location": location,
            "user_type": "Prosumer"
            if meter_type in ["Solar_Prosumer", "Hybrid_Prosumer"]
            else "Consumer",
            "base_generation": random.uniform(0.5, 3.0),
            "base_consumption": random.uniform(0.5, 2.5),
            "battery_capacity": battery_capacity,
            "solar_efficiency": random.uniform(0.15, 0.22),
            "battery_efficiency": random.uniform(0.85, 0.95),
            "trading_preference": trading_preference,
            "has_solar": meter_type in ["Solar_Prosumer", "Hybrid_Prosumer"],
            "solar_capacity": solar_capacity
            if meter_type in ["Solar_Prosumer", "Hybrid_Prosumer"]
            else 0.0,
            "panel_efficiency": random.uniform(0.15, 0.22)
            if meter_type in ["Solar_Prosumer", "Hybrid_Prosumer"]
            else 0.0,
            "has_battery": meter_type in ["Hybrid_Prosumer", "Battery_Storage"],
            "current_battery_level": random.uniform(20.0, 80.0)
            if meter_type in ["Hybrid_Prosumer", "Battery_Storage"]
            else 0.0,
            "max_sell_price": random.uniform(0.08, 0.15),
            "max_buy_price": random.uniform(0.10, 0.20),
            "latitude": latitude,
            "longitude": longitude,
            "wallet_address": wallet_address,
        }

        # Create new meter
        new_meter = SmartMeter(meter_config)

        # Add meter to engine
        engine.meters.append(new_meter)

        # Save to DB
        if db_manager:
            db_manager.save_meter(meter_config)

        logger.info(
            f"Added new meter: {new_meter.meter_id} ({meter_type}) at {location}"
        )

        return {
            "success": True,
            "message": f"Successfully added {meter_type} meter",
            "meter": {
                "meter_id": new_meter.meter_id,
                "meter_type": meter_type,
                "location": location,
                "solar_capacity": solar_capacity,
                "battery_capacity": battery_capacity,
                "trading_preference": trading_preference,
                "meter_public_key": new_meter.key_manager.get_public_key(),
            },
            "total_meters": len(engine.meters),
        }
    except Exception as e:
        logger.error(f"Error adding meter: {e}")
        return {"success": False, "message": str(e)}


@app.delete("/api/meters/{meter_id}")
async def delete_meter(meter_id: str):
    """Remove a meter from the simulation"""
    if not engine:
        return {"success": False, "message": "Simulator not initialized"}

    try:
        # Find and remove meter
        target_meter = None
        for i, m in enumerate(engine.meters):
            if m.meter_id == meter_id:
                target_meter = m
                engine.meters.pop(i)
                break

        if not target_meter:
            return {"success": False, "message": f"Meter {meter_id} not found"}

        # Clean up any overrides
        if meter_id in meter_overrides:
            del meter_overrides[meter_id]

        # Remove from DB
        if db_manager:
            db_manager.delete_meter(meter_id)

        logger.info(f"Removed meter: {meter_id}")

        return {
            "success": True,
            "message": f"Successfully removed meter {meter_id}",
            "total_meters": len(engine.meters),
        }
    except Exception as e:
        logger.error(f"Error removing meter: {e}")
        return {"success": False, "message": str(e)}


@app.get("/api/simulation/parameters")
async def get_simulation_parameters():
    """Get current simulation parameters"""
    return {"success": True, "parameters": simulation_params}


@app.post("/api/simulation/parameters")
async def update_simulation_parameters(request: dict):
    """Update simulation parameters"""
    global simulation_params

    try:
        # Update parameters with validation
        if "weather" in request:
            valid_weather = ["Auto", "Sunny", "Partly_Cloudy", "Cloudy", "Rainy"]
            if request["weather"] in valid_weather:
                simulation_params["weather"] = request["weather"]

        if "solar_multiplier" in request:
            value = float(request["solar_multiplier"])
            if 0.0 <= value <= 1.0:
                simulation_params["solar_multiplier"] = value

        if "consumption_multiplier" in request:
            value = float(request["consumption_multiplier"])
            if 0.0 <= value <= 2.0:
                simulation_params["consumption_multiplier"] = value

        if "grid_buy_price" in request:
            value = float(request["grid_buy_price"])
            if 0.10 <= value <= 0.50:
                simulation_params["grid_buy_price"] = value

        if "grid_sell_price" in request:
            value = float(request["grid_sell_price"])
            if 0.05 <= value <= 0.35:
                simulation_params["grid_sell_price"] = value

        logger.info(f"Updated simulation parameters: {simulation_params}")

        return {
            "success": True,
            "message": "Simulation parameters updated",
            "parameters": simulation_params,
        }
    except Exception as e:
        logger.error(f"Error updating simulation parameters: {e}")
        return {"success": False, "message": str(e)}


@app.post("/api/simulation/preset/{preset_name}")
async def apply_preset(preset_name: str):
    """Apply a preset scenario"""
    global simulation_params

    presets = {
        "sunny_day": {
            "weather": "Sunny",
            "solar_multiplier": 1.0,
            "consumption_multiplier": 0.7,
            "grid_buy_price": 0.28,
            "grid_sell_price": 0.12,
        },
        "cloudy_day": {
            "weather": "Cloudy",
            "solar_multiplier": 0.3,
            "consumption_multiplier": 1.0,
            "grid_buy_price": 0.32,
            "grid_sell_price": 0.10,
        },
        "night_time": {
            "weather": "Auto",
            "solar_multiplier": 0.0,
            "consumption_multiplier": 1.2,
            "grid_buy_price": 0.35,
            "grid_sell_price": 0.08,
        },
        "peak_demand": {
            "weather": "Auto",
            "solar_multiplier": 0.6,
            "consumption_multiplier": 1.8,
            "grid_buy_price": 0.45,
            "grid_sell_price": 0.15,
        },
        "battery_test": {
            "weather": "Partly_Cloudy",
            "solar_multiplier": 0.7,
            "consumption_multiplier": 0.5,
            "grid_buy_price": 0.28,
            "grid_sell_price": 0.12,
        },
        "auto": {
            "weather": "Auto",
            "solar_multiplier": 1.0,
            "consumption_multiplier": 1.0,
            "grid_buy_price": 0.28,
            "grid_sell_price": 0.12,
        },
    }

    if preset_name not in presets:
        return {
            "success": False,
            "message": f"Unknown preset: {preset_name}",
            "available_presets": list(presets.keys()),
        }

    simulation_params.update(presets[preset_name])
    logger.info(f"Applied preset '{preset_name}': {simulation_params}")

    return {
        "success": True,
        "message": f"Applied preset: {preset_name}",
        "parameters": simulation_params,
    }


@app.post("/api/meters/{meter_id}/override")
async def set_meter_override(meter_id: str, request: dict):
    """Set manual override values for a specific meter"""
    global meter_overrides

    try:
        # Validate meter exists
        target_meter = None
        if engine:
            for m in engine.meters:
                if m.meter_id == meter_id:
                    target_meter = m
                    break

        if not target_meter:
            return {"success": False, "message": f"Meter {meter_id} not found"}

        # Extract and validate values
        # Support both legacy simple override and new full static data
        override = {
            "mode": "manual",
            # Core energy values
            "energy_generated": float(request.get("energy_generated", 0.0)),
            "energy_consumed": float(request.get("energy_consumed", 0.0)),
            "battery_level": float(request.get("battery_level", 50.0)),
            # Advanced electrical values (optional, defaults handled in meter)
            "voltage": float(request.get("voltage", 240.0)),
            "current": float(request.get("current", 0.0)),
            "frequency": float(request.get("frequency", 50.0)),
            "temperature": float(request.get("temperature", 25.0)),
            "power_factor": float(request.get("power_factor", 1.0)),
            # Pricing overrides
            "max_sell_price": float(
                request.get("max_sell_price", target_meter.current_sell_price)
            ),
            "max_buy_price": float(
                request.get("max_buy_price", target_meter.current_buy_price)
            ),
        }

        # Validate ranges
        if not (0.0 <= override["energy_generated"] <= 100.0):
            return {
                "success": False,
                "message": "energy_generated must be between 0 and 100",
            }
        if not (0.0 <= override["energy_consumed"] <= 100.0):
            return {
                "success": False,
                "message": "energy_consumed must be between 0 and 100",
            }
        if not (0.0 <= override["battery_level"] <= 100.0):
            return {
                "success": False,
                "message": "battery_level must be between 0 and 100",
            }

        # Store in global overrides (for persistence/API checks)
        meter_overrides[meter_id] = override

        # Inject directly into meter instance
        setattr(target_meter, "static_data", override)

        logger.info(f"Set manual override for {meter_id}: {override}")

        return {
            "success": True,
            "message": f"Manual override set for {meter_id}",
            "override": override,
        }
    except Exception as e:
        logger.error(f"Error setting meter override: {e}")
        return {"success": False, "message": str(e)}


@app.delete("/api/meters/{meter_id}/override")
async def delete_meter_override(meter_id: str):
    """Remove manual override for a specific meter (return to auto mode)"""
    global meter_overrides

    if meter_id in meter_overrides:
        del meter_overrides[meter_id]

        # Remove from meter instance
        if engine:
            for m in engine.meters:
                if m.meter_id == meter_id:
                    if hasattr(m, "static_data"):
                        delattr(m, "static_data")
                    break

        logger.info(f"Removed manual override for {meter_id}")
        return {"success": True, "message": f"Meter {meter_id} returned to auto mode"}
    else:
        return {"success": False, "message": f"No override found for {meter_id}"}


@app.get("/api/meters/overrides")
async def get_meter_overrides():
    """Get all current meter overrides"""
    return {"success": True, "overrides": meter_overrides}


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", "8000"))
    host = os.getenv("HOST", "0.0.0.0")

    uvicorn.run("app:app", host=host, port=port, reload=True, log_level="info")
