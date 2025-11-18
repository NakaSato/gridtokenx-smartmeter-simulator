#!/usr/bin/env python3
"""
FastAPI Application for Smart Meter Simulator
Provides REST API endpoints and WebSocket support with HTML rendering
"""

import asyncio
import json
import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import asdict

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from smart_meter_simulator.simulator import SmartMeterSimulator, get_global_simulator, set_global_simulator
from smart_meter_simulator.utils import EnergyReading

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global simulator instance
simulator: Optional[SmartMeterSimulator] = None
simulation_task: Optional[asyncio.Task] = None
readings_history: List[Dict] = []
max_history = 1000
connected_websockets = set()


async def run_simulator():
    """Run the simulator in background"""
    global simulator, readings_history
    
    while True:
        try:
            if simulator:
                simulator.simulate_readings()
                
                # Broadcast to connected WebSocket clients
                if connected_websockets:
                    for ws in list(connected_websockets):
                        try:
                            # Get latest readings
                            latest_readings = [asdict(simulator.generate_enhanced_reading(meter)) 
                                             for meter in simulator.meters[:5]]  # Send 5 latest
                            await ws.send_json(latest_readings)
                        except Exception as e:
                            logger.debug(f"Error broadcasting to WebSocket: {e}")
                            connected_websockets.discard(ws)
                
                await asyncio.sleep(simulator.simulation_interval)
            else:
                await asyncio.sleep(1)
        except Exception as e:
            logger.error(f"Error in simulator loop: {e}")
            await asyncio.sleep(1)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for FastAPI"""
    global simulator, simulation_task
    
    # Startup
    logger.info("Initializing Smart Meter Simulator...")
    simulator = SmartMeterSimulator()
    set_global_simulator(simulator)
    
    # Start simulator
    simulator.start()
    
    # Start background simulation task
    simulation_task = asyncio.create_task(run_simulator())
    logger.info("Simulator started in background")
    
    yield
    
    # Shutdown
    logger.info("Shutting down simulator...")
    if simulation_task:
        simulation_task.cancel()
        try:
            await simulation_task
        except asyncio.CancelledError:
            pass
    
    if simulator:
        simulator.stop()
        simulator.print_statistics()
        if simulator.ws_server:
            simulator.ws_server.stop()
        
        # Close connections
        if simulator.producer:
            simulator.producer.close()
        if simulator.db_conn:
            simulator.db_conn.close()
        if simulator.influxdb_client:
            simulator.influxdb_client.close()
    
    logger.info("Simulator shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="Smart Meter Simulator",
    description="P2P Energy Trading Meter Simulator with FastAPI",
    version="1.0.0",
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

try:
    app.mount("/static", StaticFiles(directory="static"), name="static")
except Exception as e:
    logger.warning(f"Could not mount static files: {e}")


# Routes
@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Main dashboard page"""
    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "title": "Smart Meter Simulator Dashboard",
        }
    )


@app.get("/api/status")
async def get_status():
    """Get simulator status"""
    if not simulator:
        return {"error": "Simulator not initialized"}
    
    return {
        "running": getattr(simulator, 'running', False),
        "paused": getattr(simulator, 'paused', False),
        "num_meters": len(simulator.meters),
        "simulation_interval": simulator.simulation_interval,
        "current_weather": simulator.current_weather.value,
        "total_readings": simulator.stats['total_readings'],
        "kafka_available": simulator.producer is not None,
        "database_available": simulator.db_conn is not None,
        "influxdb_available": simulator.influxdb_client is not None,
        "connected_clients": len(connected_websockets),
        "mode": "Standalone" if simulator.standalone_mode else "Integrated"
    }


@app.get("/api/stats")
async def get_stats():
    """Get aggregated statistics"""
    if not simulator:
        return {"error": "Simulator not initialized"}
    
    # Calculate stats from recent readings
    recent_readings = [simulator.generate_enhanced_reading(meter) 
                      for meter in simulator.meters]
    
    total_generation = sum(r.energy_generated for r in recent_readings)
    total_consumption = sum(r.energy_consumed for r in recent_readings)
    total_surplus = sum(r.surplus_energy for r in recent_readings)
    total_deficit = sum(r.deficit_energy for r in recent_readings)
    avg_battery = sum(r.battery_level for r in recent_readings) / len(recent_readings) if recent_readings else 0
    active_traders = sum(1 for r in recent_readings if r.surplus_energy > 0 or r.deficit_energy > 0)
    rec_eligible = sum(1 for r in recent_readings if r.rec_eligible)
    
    return {
        "total_generation": round(total_generation, 2),
        "total_consumption": round(total_consumption, 2),
        "total_surplus": round(total_surplus, 2),
        "total_deficit": round(total_deficit, 2),
        "average_battery_level": round(avg_battery, 2),
        "active_traders": active_traders,
        "rec_eligible_count": rec_eligible
    }


@app.get("/api/readings")
async def get_readings(limit: int = 10):
    """Get recent readings"""
    if not simulator:
        return {"error": "Simulator not initialized"}
    
    readings = [asdict(simulator.generate_enhanced_reading(meter)) 
                for meter in simulator.meters[:limit]]
    
    return {
        "count": len(readings),
        "readings": readings
    }


@app.get("/api/meters")
async def get_meters():
    """Get list of all meters"""
    if not simulator:
        return {"error": "Simulator not initialized"}
    
    meters_info = []
    for meter in simulator.meters:
        meters_info.append({
                "meter_id": meter['meter_id'],
                "meter_type": meter['meter_type'],
                "location": meter['location'],
                "user_type": meter['user_type'],
                "has_solar": meter.get('has_solar', False),
                "has_battery": meter.get('has_battery', False),
                "trading_strategy": meter.get('trading_strategy', 'N/A'),
                "static_key": meter.get('static_key', ''),
                "blockchain_registered": meter.get('blockchain_registered', False)
            })
    
    return {
        "count": len(meters_info),
        "meters": meters_info
    }


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time data streaming"""
    await websocket.accept()
    connected_websockets.add(websocket)
    logger.info(f"WebSocket client connected. Total: {len(connected_websockets)}")
    
    try:
        # Send initial data
        if simulator:
            initial_readings = [asdict(simulator.generate_enhanced_reading(meter)) 
                              for meter in simulator.meters[:10]]
            await websocket.send_json(initial_readings)
        
        # Keep connection alive and handle incoming messages
        while True:
            try:
                data = await websocket.receive_text()
                # Echo back or handle commands if needed
                logger.debug(f"Received from client: {data}")
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
                break
                
    except Exception as e:
        logger.error(f"WebSocket connection error: {e}")
    finally:
        connected_websockets.discard(websocket)
        logger.info(f"WebSocket client disconnected. Total: {len(connected_websockets)}")


# Control endpoints
@app.post("/api/control/start")
async def start_simulation():
    """Start the simulation"""
    if not simulator:
        return {"error": "Simulator not initialized"}
    
    success = simulator.start()
    return {
        "success": success,
        "message": "Simulation started" if success else "Failed to start simulation",
        "status": simulator.get_status()
    }

@app.post("/api/control/stop")
async def stop_simulation():
    """Stop the simulation"""
    if not simulator:
        return {"error": "Simulator not initialized"}
    
    success = simulator.stop()
    return {
        "success": success,
        "message": "Simulation stopped" if success else "Failed to stop simulation",
        "status": simulator.get_status()
    }

@app.post("/api/control/pause")
async def pause_simulation():
    """Pause the simulation"""
    if not simulator:
        return {"error": "Simulator not initialized"}
    
    success = simulator.pause()
    return {
        "success": success,
        "message": "Simulation paused" if success else "Failed to pause simulation",
        "status": simulator.get_status()
    }

@app.post("/api/control/resume")
async def resume_simulation():
    """Resume the simulation"""
    if not simulator:
        return {"error": "Simulator not initialized"}
    
    success = simulator.resume()
    return {
        "success": success,
        "message": "Simulation resumed" if success else "Failed to resume simulation",
        "status": simulator.get_status()
    }

@app.post("/api/control/restart")
async def restart_simulation():
    """Restart the simulation"""
    if not simulator:
        return {"error": "Simulator not initialized"}
    
    success = simulator.restart()
    return {
        "success": success,
        "message": "Simulation restarted" if success else "Failed to restart simulation",
        "status": simulator.get_status()
    }

@app.post("/api/control/meters")
async def update_meter_count(request: Request):
    """Update number of meters"""
    if not simulator:
        return {"error": "Simulator not initialized"}
    
    try:
        body = await request.json()
        new_count = int(body.get('num_meters', body.get('meter_count', simulator.num_meters)))
        
        if not new_count or new_count < 1 or new_count > 1000:
            return {"error": "Invalid meter count. Must be between 1 and 1000"}
        
        success = simulator.update_meter_count(new_count)
        
        return {
            "success": success,
            "message": f"Meter count updated to {new_count}" if success else "Failed to update meter count",
            "old_count": len(simulator.meters),
            "new_count": new_count if success else len(simulator.meters),
            "status": simulator.get_status()
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Error updating meter count: {e}",
            "status": simulator.get_status() if simulator else {}
        }


@app.get("/api/control/status")
async def get_control_status():
    """Get control status"""
    if not simulator:
        return {"error": "Simulator not initialized"}
    
    return simulator.get_status()

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "simulator_running": simulator is not None,
        "timestamp": datetime.utcnow().isoformat()
    }


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
