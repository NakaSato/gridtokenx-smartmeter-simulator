#!/usr/bin/env python3
"""
FastAPI Application for Smart Meter Simulator
Provides REST API endpoints and WebSocket support with HTML rendering
"""

import asyncio
import logging
import os
import random
from contextlib import asynccontextmanager
from typing import Dict, List, Optional
from pydantic import BaseModel
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.encoders import jsonable_encoder
import uvicorn

from smart_meter_simulator.core.engine import SimulationEngine, SimulationMode
from smart_meter_simulator.core.meter import SmartMeter
from smart_meter_simulator.transport.http import HttpTransport
from smart_meter_simulator.transport.websocket import WebSocketManager, WebSocketTransport
from smart_meter_simulator.transport.composite import CompositeTransport
from smart_meter_simulator.transport.kafka import KafkaTransport
from smart_meter_simulator.transport.influxdb import InfluxDBTransport
from smart_meter_simulator.meter_generator import MeterGenerator
from smart_meter_simulator.core.meter import SmartMeter, MeterType
from smart_meter_simulator.transport.base import TransportLayer
from smart_meter_simulator.adapters.pandapower_adapter import PandapowerAdapter
from smart_meter_simulator.core.db import DatabaseManager
from smart_meter_simulator.config import SimulatorConfig

# Configure logging
# Configure logging
log_level = os.getenv("LOG_LEVEL", "ERROR").upper()
logging.basicConfig(
    level=getattr(logging, log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global state
engine: Optional[SimulationEngine] = None
simulation_task: Optional[asyncio.Task] = None
websocket_manager = WebSocketManager()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for FastAPI"""
    global engine, simulation_task
    
    # Startup
    logger.info("Initializing Smart Meter Simulator with Cloud Persistence...")
    
    config = SimulatorConfig()
    
    # 1. Initialize Persistence (PostgreSQL)
    db_manager = DatabaseManager(config.DATABASE_URL)
    await db_manager.init_db()
    
    # 2. Initialize Transports
    http_transport = HttpTransport(base_url=config.API_GATEWAY_URL, api_key=config.API_KEY)
    websocket_transport = WebSocketTransport(websocket_manager)
    
    transports = [http_transport, websocket_transport]
    
    # Add Kafka if configured
    if config.KAFKA_SERVERS:
        kafka_transport = KafkaTransport(config.KAFKA_SERVERS, config.KAFKA_TOPIC)
        transports.append(kafka_transport)
        
    # Add InfluxDB if configured
    if config.INFLUXDB_TOKEN:
        influx_transport = InfluxDBTransport(
            config.INFLUXDB_URL, config.INFLUXDB_TOKEN, config.INFLUXDB_ORG, config.INFLUXDB_BUCKET
        )
        transports.append(influx_transport)
        
    # 3. Create Composite Transport
    composite_transport = CompositeTransport(transports)
    
    # 4. Generate Meters
    generator = MeterGenerator(config.NUM_METERS)
    meter_configs = generator.generate_meters()
    meters = [SmartMeter(config_dict) for config_dict in meter_configs]
    
    # 5. Initialize Engine with Grid Adapter and DB Manager
    adapter = PandapowerAdapter()
    engine = SimulationEngine(meters, composite_transport, adapter=adapter, db_manager=db_manager)
    
    # 6. Start Engine
    simulation_task = asyncio.create_task(engine.start())
    logger.info(f"Simulator started with {len(meters)} meters and {len(transports)} transports")
    
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
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create directories
os.makedirs("static", exist_ok=True)
os.makedirs("templates", exist_ok=True)

# Robust Path Resolution
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(BASE_DIR))

# Setup templates and static files
# Search both in package and in project root for flexibility
template_dirs = [
    os.path.join(BASE_DIR, "templates"),
    os.path.join(PROJECT_ROOT, "templates"),
    os.path.join(PROJECT_ROOT, "src", "templates")
]
templates = Jinja2Templates(directory=[d for d in template_dirs if os.path.exists(d)] or "templates")

# UI directory
UI_DIST_DIR = os.path.join(PROJECT_ROOT, "ui", "dist")

try:
    if os.path.exists(UI_DIST_DIR):
        app.mount("/assets", StaticFiles(directory=os.path.join(UI_DIST_DIR, "assets")), name="ui-assets")
        logger.info(f"Mounted UI assets from {UI_DIST_DIR}")
    else:
        static_dir = os.path.join(PROJECT_ROOT, "static")
        if os.path.exists(static_dir):
            app.mount("/static", StaticFiles(directory=static_dir), name="static")
            logger.warning(f"UI build not found at {UI_DIST_DIR}. Serving legacy static files.")
        else:
            logger.warning("No static or UI assets found.")
except Exception as e:
    logger.warning(f"Could not mount static files: {e}")


# Routes
@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Main dashboard page"""
    index_path = os.path.join(UI_DIST_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    
    try:
        return templates.TemplateResponse(
            "dashboard.html",
            {
                "request": request,
                "title": "Smart Meter Simulator Dashboard",
                "status": "Running" if engine and engine.running else "Stopped",
                "meter_count": len(engine.meters) if engine else 0
            }
        )
    except Exception:
        return HTMLResponse(content="<h1>Smart Meter Simulator</h1><p>UI Build not found and dashboard template missing. API is running at /api/status</p>", status_code=200)

@app.get("/how-it-works", response_class=HTMLResponse)
async def how_it_works(request: Request):
    """Animated explanation page"""
    index_path = os.path.join(UI_DIST_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)

    return templates.TemplateResponse(
        "how_it_works.html",
        {
            "request": request,
            "title": "How It Works - Smart Meter Simulator"
        }
    )

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
        if hasattr(meter, 'last_reading') and meter.last_reading:
            latest_reading = meter.last_reading
        
        meters_data.append({
            "meter_id": meter.meter_id,
            "name": meter.config.get('meter_type', 'Unknown'),
            "location": meter.config.get('location', 'Unknown'),
            "capacity": meter.config.get('solar_capacity', 0),
            "current_generation": getattr(latest_reading, 'energy_generated', 0) if latest_reading else 0,
            "current_consumption": getattr(latest_reading, 'energy_consumed', 0) if latest_reading else 0,
            "energy_type": meter.config.get('meter_type', 'solar'),
            "status": "active"
        })
    
    # Grid estimation metrics
    grid_metrics = {
        "converged": False,
        "num_measurements": 0,
        "chi2": 0.0
    }
    if engine and engine.last_estimation_results:
        res = engine.last_estimation_results
        grid_metrics = {
            "converged": res.converged,
            "num_measurements": res.num_measurements,
            "chi2": round(float(res.chi2_statistic), 6) if getattr(res, 'chi2_statistic', None) is not None else 0.0,
            "v_deviation_avg": round(float(res.v_deviation_avg), 4) if getattr(res, 'v_deviation_avg', None) is not None else 0.0
        }
    
    # Get API gateway URL from transport
    api_gateway = "Unknown"
    if hasattr(engine.transport, 'transports') and len(engine.transport.transports) > 0:
        http_transport = engine.transport.transports[0]
        if hasattr(http_transport, 'base_url'):
            api_gateway = http_transport.base_url
    
    return {
        "status": "running" if engine.running else "stopped",
        "running": engine.running,
        "paused": getattr(engine, 'paused', False),
        "meters": meters_data,
        "num_meters": len(engine.meters),
        "mode": "Simulation",
        "api_gateway": api_gateway,
        "grid_metrics": grid_metrics,
        "websocket_clients": websocket_manager.get_connection_count(),
        "websocket_connections": websocket_manager.get_connection_count()
    }

@app.get("/api/grid/status")
async def get_grid_status():
    """Get summarized grid topology status"""
    if not engine or not engine.net:
        return {"error": "Grid model not initialized"}
    
    net = engine.net
    return {
        "num_buses": len(net.bus),
        "num_lines": len(net.line),
        "num_loads": len(net.load),
        "num_sgens": len(net.sgen),
        "has_external_grid": len(net.ext_grid) > 0,
        "voltage_levels": net.bus.vn_kv.unique().tolist()
    }

@app.get("/api/grid/legacy-topology")
async def get_legacy_topology():
    """Get topology in legacy format for frontend compatibility (zones/meters)"""
    if not engine:
         return {"zones": {}, "meters": []}
    
    zones = {}
    meters_list = []
    
    # Mock some central coordinates for Bangkok
    base_lat = 13.736717
    base_lon = 100.523186
    
    for meter in engine.meters:
        # Parse zone from location string "Zone_X_Building_Y"
        zone_id = 1
        parts = meter.config.get('location', '').split('_')
        if len(parts) >= 2 and parts[0] == "Zone":
             try:
                 zone_id = int(parts[1])
             except:
                 pass
        
        # Add zone if not exists
        if zone_id not in zones:
             # Spread zones out slightly
             offset_lat = (zone_id - 1) * 0.005
             offset_lon = (zone_id - 1) * 0.005
             
             zones[zone_id] = {
                 "zone_id": zone_id,
                 "transformer_name": f"Transformer Zone {zone_id}",
                 "centroid_lat": base_lat + offset_lat,
                 "centroid_lon": base_lon + offset_lon,
                 "radius_km": 0.5
             }
        
        meters_list.append({
            "meter_id": meter.meter_id,
            "meter_serial": meter.meter_id, # Use ID as serial for Simulator
            "zone_id": zone_id,
            "type": meter.config.get('meter_type', 'unknown'),
            "location": meter.config.get('location', 'Unknown'),
            # Place meters around the zone centroid
            "latitude": zones[zone_id]["centroid_lat"] + random.uniform(-0.002, 0.002),
            "longitude": zones[zone_id]["centroid_lon"] + random.uniform(-0.002, 0.002),
            "status": "active"
        })
        
    return {
        "zones": zones,
        "meters": meters_list
    }

@app.get("/api/grid/estimation")
async def get_estimation_results():
    """Get latest state estimation results"""
    if not engine or not engine.last_estimation_results:
        return {"error": "No estimation results available"}
    
    res = engine.last_estimation_results
    return {
        "converged": res.converged,
        "iterations": res.iterations,
        "num_measurements": res.num_measurements,
        "chi2": res.chi2_statistic, # Corrected field name
        "mean_absolute_error": round(float(res.mean_absolute_error), 6) if res.mean_absolute_error is not None else 0.0,
        "max_residual": round(float(res.max_residual), 6) if res.max_residual is not None else 0.0,
        "v_deviation_avg": round(float(res.v_deviation_avg), 6) if res.v_deviation_avg is not None else 0.0,
        "total_losses_mw": round(float(res.total_losses_mw), 6) if hasattr(res, 'total_losses_mw') and res.total_losses_mw is not None else 0.0,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/grid/measurements")
async def get_grid_measurements():
    """Get current measurements used for estimation"""
    if not engine or not engine.net or engine.net.measurement.empty:
        return {"measurements": []}
    
    meas = engine.net.measurement
    return {
        "measurements": meas.to_dict(orient='records')
    }

@app.get("/api/grid/topology")
async def get_grid_topology():
    """Get detailed grid topology"""
    if not engine or not engine.net:
        return {"error": "No grid model available"}
    
    net = engine.net
    
    # Extract buses
    buses = net.bus[['name', 'vn_kv', 'type']].to_dict(orient='index')
    # Add coordinates if available
    if 'bus_geocoord' in net and not net.bus_geocoord.empty:
        for idx, coord in net.bus_geocoord.iterrows():
            if idx in buses:
                buses[idx]['lat'] = coord.y
                buses[idx]['lng'] = coord.x
    
    # Extract lines
    lines = net.line[['name', 'from_bus', 'to_bus', 'length_km', 'max_i_ka']].to_dict(orient='records')
    
    return {
        "buses": buses,
        "lines": lines
    }

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time meter readings"""
    logger.info("New WebSocket connection attempt")
    await websocket_manager.connect(websocket)
    try:
        logger.info("WebSocket connection established and managed")
        while True:
            # Keep connection alive and handle any incoming messages
            # We use receive_text as it's the standard way to detect disconnections in FastAPI
            try:
                data = await websocket.receive_text()
                logger.debug(f"Received WebSocket message: {data}")
            except asyncio.CancelledError:
                logger.info("WebSocket task cancelled")
                break
    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected normally (WebSocketDisconnect)")
    except Exception as e:
        logger.error(f"WebSocket unexpected error: {e}", exc_info=True)
    finally:
        await websocket_manager.disconnect(websocket)
        logger.info("WebSocket connection cleanup complete")

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
                "paused": getattr(engine, 'paused', False),
                "num_meters": len(engine.meters)
            }
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
        if simulation_task:
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
                "paused": getattr(engine, 'paused', False),
                "num_meters": len(engine.meters)
            }
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
                "num_meters": len(engine.meters)
            }
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
                "num_meters": len(engine.meters)
            }
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
        if simulation_task:
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
                "num_meters": len(engine.meters)
            }
        }
    except Exception as e:
        return {"success": False, "message": str(e)}

@app.post("/api/control/meters")
async def update_meter_count(request: dict):
    """Update the number of meters"""
    global simulation_task
    if not engine:
        return {"success": False, "message": "Simulator not initialized"}
    
    try:
        num_meters = request.get('num_meters', 20)
        if num_meters < 1 or num_meters > 1000:
            return {"success": False, "message": "Number of meters must be between 1 and 1000"}
        
        # Stop current simulation
        engine.running = False
        if simulation_task:
            simulation_task.cancel()
            try:
                await simulation_task
            except asyncio.CancelledError:
                pass
        
        # Generate new meters
        generator = MeterGenerator(num_meters)
        meter_configs = generator.generate_meters()
        new_meters = [SmartMeter(config) for config in meter_configs]
        
        # Update engine with new meters
        engine.meters = new_meters
        
        # Restart simulation
        await asyncio.sleep(1)
        engine.running = True
        engine.paused = False
        simulation_task = asyncio.create_task(engine.start())
        
        return {
            "success": True, 
            "message": f"Updated to {num_meters} meters and restarted",
            "status": {
                "running": True,
                "paused": False,
                "num_meters": len(engine.meters)
            }
        }
    except Exception as e:
        return {"success": False, "message": str(e)}

class MeterCreateRequest(BaseModel):
    meter_type: str
    location: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    solar_capacity: Optional[float] = 0.0
    trading_preference: Optional[str] = "moderate"
    custom_id: Optional[str] = None
    wallet_address: Optional[str] = None

@app.post("/api/meters")
async def create_meter(meter_data: MeterCreateRequest):
    """Dynamically add a new meter to the simulation."""
    if not engine:
        raise HTTPException(status_code=400, detail="Simulation not running")
        
    try:
        # Generate ID if not provided
        meter_id = meter_data.custom_id or f"METER-{len(engine.meters) + 1:04d}"
        
        config = {
            "meter_id": meter_id,
            "meter_type": meter_data.meter_type,
            "location": meter_data.location,
            "latitude": meter_data.latitude,
            "longitude": meter_data.longitude,
            "solar_capacity": meter_data.solar_capacity,
            "wallet_address": meter_data.wallet_address,
            # "trading_strategy": meter_data.trading_preference # Not fully implemented in core yet
        }
        
        new_meter = SmartMeter(config)
        await engine.add_meter(new_meter)
        
        return {
            "success": True, 
            "message": f"Meter {meter_id} added successfully",
            "meter": {
                "meter_id": new_meter.meter_id,
                "type": new_meter.config['meter_type']
            }
        }
    except Exception as e:
        logger.error(f"Failed to add meter: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/profiles")
async def list_profiles():
    """List available historical profiles"""
    if not engine:
        return {"profiles": []}
    return {"profiles": engine.data_source.list_profiles()}

@app.post("/api/control/mode")
async def set_simulation_mode(request: dict):
    """Set simulation mode (random/playback) and profile"""
    if not engine:
        return {"success": False, "message": "Simulator not initialized"}
    
    mode_str = request.get('mode', 'random').lower()
    profile = request.get('profile')
    
    if mode_str == 'playback':
        if not profile:
            return {"success": False, "message": "Profile name is required for playback mode"}
        engine.mode = SimulationMode.PLAYBACK
        engine.playback_profile = profile
    else:
        engine.mode = SimulationMode.RANDOM
        engine.playback_profile = None
        
    return {
        "success": True, 
        "mode": engine.mode.value,
        "profile": engine.playback_profile
    }

@app.post("/api/profiles/upload")
async def upload_profile(request: dict):
    """Upload or save a profile dataset"""
    if not engine:
        return {"success": False, "message": "Simulator not initialized"}
    
    name = request.get('name')
    data = request.get('data')
    format = request.get('format', 'csv')
    
    if not name or not data:
        return {"success": False, "message": "Name and data are required"}
        
    try:
        path = engine.data_source.save_profile(name, data, format)
        return {"success": True, "message": f"Profile saved to {path}"}
    except Exception as e:
        return {"success": False, "message": str(e)}

@app.post("/api/profiles/generate")
async def generate_profile(request: dict):
    """Generate a synthetic profile based on SLP (H0/G0)"""
    if not engine:
        return {"success": False, "message": "Simulator not initialized"}
    
    name = request.get('name')
    profile_type = request.get('profile_type', 'H0')
    annual_kwh = request.get('annual_kwh', 3500)
    days = request.get('days', 1)
    meter_ids = request.get('meter_ids', ["M1"])
    
    if not name:
        return {"success": False, "message": "Name is required"}
        
    try:
        success = engine.data_source.generate_slp(
            name=name,
            profile_type=profile_type,
            annual_kwh=annual_kwh,
            days=days,
            meter_ids=meter_ids
        )
        return {"success": success, "message": f"Profile {name} generated successfully"}
    except Exception as e:
        return {"success": False, "message": str(e)}

@app.get("/api/grid/export/cim")
async def export_cim():
    """Export current grid state as CIM XML"""
    if not engine:
        return {"success": False, "message": "Simulator not initialized"}
    
    from .adapters.cim_adapter import CIMAdapter
    from fastapi import Response
    adapter = CIMAdapter()
    try:
        xml_content = adapter.export_to_xml(engine.net)
        return Response(content=xml_content, media_type="application/xml")
    except Exception as e:
        return {"success": False, "message": str(e)}

@app.get("/api/analytics/report")
async def get_analytics_report():
    """Get summarized grid health report"""
    if not engine:
        return {"success": False, "message": "Simulator not initialized"}
    return jsonable_encoder(engine.analytics.get_summary())

@app.post("/api/control/attack")
async def control_attack(request: dict):
    """Configure and start/stop an FDI attack"""
    if not engine:
        return {"success": False, "message": "Simulator not initialized"}
    
    active = request.get('active', False)
    targets = request.get('targets', [])
    mode = request.get('mode', 'bias')
    bias = request.get('bias', 0.0)
    scale = request.get('scale', 1.0)
    stealthy = request.get('stealthy', False)
    
    try:
        engine.attacker.configure(
            active=active,
            targets=targets,
            mode=mode,
            bias=bias,
            scale=scale,
            stealthy=stealthy
        )
        return {"success": True, "status": engine.attacker.get_status()}
    except Exception as e:
        return {"success": False, "message": str(e)}

@app.get("/metrics")
async def get_metrics():
    """Prometheus metrics endpoint"""
    from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
    from fastapi import Response
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.get("/health/ready")
async def health_ready():
    """Deep health check verifying connectivity to dependencies"""
    from sqlalchemy import select
    health = {"status": "ready", "dependencies": {}}
    
    # Check Database
    if engine and engine.db_manager:
        try:
            async with engine.db_manager.engine.connect() as conn:
                await conn.execute(select(1))
            health["dependencies"]["database"] = "ok"
        except Exception as e:
            health["dependencies"]["database"] = f"failed: {str(e)}"
            health["status"] = "partially_available"
            
    # Check Transports
    if engine and hasattr(engine.transport, 'transports'):
        for i, t in enumerate(engine.transport.transports):
            name = t.__class__.__name__
            health["dependencies"][name] = "connected" if t.is_connected() else "disconnected"
            if not t.is_connected():
                health["status"] = "partially_available"
                
    return health

def main():
    """Main entry point for the simulator app"""
    port = int(os.getenv("PORT", "8000"))
    host = os.getenv("HOST", "0.0.0.0")
    
    uvicorn.run(
        "smart_meter_simulator.app:app",
        host=host,
        port=port,
        reload=False,
        log_level="info"
    )

if __name__ == "__main__":
    main()
