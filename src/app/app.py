#!/usr/bin/env python3
"""
FastAPI Application for Smart Meter Simulator
Provides REST API endpoints and WebSocket support with HTML rendering
"""

import asyncio
import logging
import os
from contextlib import asynccontextmanager
from typing import Dict, List, Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from app.core.engine import SimulationEngine
from app.core.meter import SmartMeter
from app.transport.http import HttpTransport
from app.transport.websocket import WebSocketManager, WebSocketTransport
from app.transport.composite import CompositeTransport
from app.meter_generator import MeterGenerator

# Configure logging
# Configure logging
log_level = os.getenv("LOG_LEVEL", "INFO").upper()
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
    logger.info("Initializing Smart Meter Simulator...")
    
    # Configuration
    api_url = os.getenv("API_GATEWAY_URL", "http://localhost:3000")
    api_key = os.getenv("API_KEY", "sim-secret-key")
    num_meters = int(os.getenv("NUM_METERS", "20"))
    
    # 1. Initialize Transports
    http_transport = HttpTransport(base_url=api_url, api_key=api_key)
    websocket_transport = WebSocketTransport(websocket_manager)
    
    # 2. Create Composite Transport
    composite_transport = CompositeTransport([http_transport, websocket_transport])
    
    # 3. Generate Meters
    generator = MeterGenerator(num_meters)
    meter_configs = generator.generate_meters()
    meters = [SmartMeter(config) for config in meter_configs]
    
    # 4. Initialize Engine
    engine = SimulationEngine(meters, composite_transport)
    
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

# Setup templates and static files
templates = Jinja2Templates(directory="templates")

# UI directory
UI_DIST_DIR = os.path.join(os.getcwd(), "ui", "dist")

try:
    if os.path.exists(UI_DIST_DIR):
        app.mount("/assets", StaticFiles(directory=os.path.join(UI_DIST_DIR, "assets")), name="ui-assets")
        logger.info(f"Mounted UI assets from {UI_DIST_DIR}")
    else:
        app.mount("/static", StaticFiles(directory="static"), name="static")
        logger.warning(f"UI build not found at {UI_DIST_DIR}. Serving legacy static files.")
except Exception as e:
    logger.warning(f"Could not mount static files: {e}")


# Routes
@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Main dashboard page"""
    index_path = os.path.join(UI_DIST_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    
    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "title": "Smart Meter Simulator Dashboard",
            "status": "Running" if engine and engine.running else "Stopped",
            "meter_count": len(engine.meters) if engine else 0
        }
    )

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
        "websocket_clients": websocket_manager.get_connection_count(),
        "websocket_connections": websocket_manager.get_connection_count()
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
                "paused": getattr(engine, 'paused', False),
                "num_meters": len(engine.meters)
            }
        }
    except Exception as e:
        return {"success": False, "message": str(e)}

@app.post("/api/control/stop")
async def stop_simulation():
    """Stop the simulation"""
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

if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", "8000"))
    host = os.getenv("HOST", "0.0.0.0")
    
    uvicorn.run(
        "app:app",
        host=host,
        port=port,
        reload=True,
        log_level="info"
    )
