import asyncio
import os
import shutil
import tempfile
import uuid
import json
import subprocess
import logging
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Header
from pydantic import BaseModel
from .dependencies import get_engine, get_websocket_manager, get_mapbox_matcher
from ..config import get_config

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["Control"])

@router.get("/status")
async def get_simulator_status(engine=Depends(get_engine), ws_manager=Depends(get_websocket_manager)):
    """Get simulator status"""
    meters_data = []
    for meter in engine.meters:
        latest_reading = getattr(meter, 'last_reading', None)
        meters_data.append({
            "meter_id": meter.meter_id,
            "name": meter.config.get('meter_type', 'Unknown'),
            "location": meter.config.get('location', 'Unknown'),
            "latitude": meter.config.get('latitude'),
            "longitude": meter.config.get('longitude'),
            "current_generation": getattr(latest_reading, 'energy_generated', 0) if latest_reading else 0,
            "current_consumption": getattr(latest_reading, 'energy_consumed', 0) if latest_reading else 0,
            "status": "active"
        })
    
    grid_metrics = {"converged": False}
    if engine.last_estimation_results:
        res = engine.last_estimation_results
        grid_metrics = {
            "converged": res.converged,
            "num_measurements": res.num_measurements,
            "chi2": round(float(res.chi2_statistic), 6) if getattr(res, 'chi2_statistic', None) is not None else 0.0,
        }
    
    return {
        "status": "running" if engine.running else "stopped",
        "running": engine.running,
        "paused": getattr(engine, 'paused', False),
        "num_meters": len(engine.meters),
        "grid_metrics": grid_metrics,
        "websocket_connections": ws_manager.get_connection_count()
    }

@router.post("/control/start")
async def start_simulation(engine=Depends(get_engine)):
    """Start the simulation"""
    if engine.running:
        return {"success": False, "message": "Already running"}

    engine.running = True
    engine.paused = False
    return {"success": True, "message": "Simulation started"}

@router.post("/control/stop")
async def stop_simulation(engine=Depends(get_engine)):
    """Stop the simulation"""
    engine.running = False
    return {"success": True, "message": "Simulation stopped"}

@router.post("/control/pause")
async def pause_simulation(engine=Depends(get_engine)):
    """Pause the simulation"""
    engine.paused = True
    return {"success": True, "message": "Simulation paused"}

@router.post("/control/resume")
async def resume_simulation(engine=Depends(get_engine)):
    """Resume the simulation"""
    engine.paused = False
    return {"success": True, "message": "Simulation resumed"}

@router.post("/control/tick")
async def step_simulation(engine=Depends(get_engine)):
    """Manually step the simulation"""
    from datetime import timedelta
    await engine.tick()
    engine.current_sim_time += timedelta(seconds=engine.interval)
    return {"success": True, "sim_time": engine.current_sim_time.isoformat()}

class C2CIngestRequest(BaseModel):
    node_id: str
    timestamp: Optional[str] = None
    status: Optional[str] = None
    power_kw: Optional[float] = None
    voltage_v: Optional[float] = None
    soc_pct: Optional[float] = None

async def verify_c2c_api_key(x_api_key: str = Header(None)):
    config = get_config()
    if not x_api_key or x_api_key != config.c2c_api_key:
        raise HTTPException(status_code=401, detail="Unauthorized C2C API Key")
    return x_api_key

@router.post("/c2c/ingest", dependencies=[Depends(verify_c2c_api_key)])
async def ingest_c2c_data(request: C2CIngestRequest, engine=Depends(get_engine), ws_manager=Depends(get_websocket_manager)):
    """Cloud-to-Cloud Ingestor"""
    try:
        from ..core.market import MarketOrder
        meter = next((m for m in engine.meters if m.meter_id == request.node_id), None)
        if meter and request.power_kw is not None:
            if request.power_kw < 0 or request.status == "CHARGING":
                meter.manual_override_cons = abs(request.power_kw)
                meter.manual_override_gen = 0.0
                engine.market.submit_order(MarketOrder(
                    meter_id=request.node_id, is_buy=True,
                    amount=abs(request.power_kw) * (engine.interval / 3600),
                    price=meter.config.get('max_buy_price', 0.35),
                    timestamp=engine.current_sim_time
                ))
            else:
                meter.manual_override_gen = abs(request.power_kw)
                meter.manual_override_cons = 0.0
                engine.market.submit_order(MarketOrder(
                    meter_id=request.node_id, is_buy=False,
                    amount=abs(request.power_kw) * (engine.interval / 3600),
                    price=meter.config.get('min_sell_price', 0.15),
                    timestamp=engine.current_sim_time
                ))
        
        message = {
            "type": "C2C_LIVE_FEED",
            "data": {
                "node_id": request.node_id,
                "timestamp": request.timestamp or datetime.now().isoformat(),
                "status": request.status or "ONLINE",
                "power_kw": request.power_kw or 0.0,
                "voltage_v": request.voltage_v,
                "soc_pct": request.soc_pct
            }
        }
        await ws_manager.broadcast(message)
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/geo-sam/inventory")
async def get_solar_inventory(engine=Depends(get_engine)):
    """Get solar panel inventory"""
    if not engine.db_manager:
        return {"success": False, "inventory": [], "mapping": {}}
    
    try:
        inventory = await engine.db_manager.get_all_solar_inventory()
        # Transform to match frontend expectations
        panels = []
        for panel in inventory:
            kwp_potential = (panel.get('area_sqm', 0) or 0) * 0.15  # ~150W per m²
            panels.append({
                "id": panel.get('id'),
                "area_sqm": panel.get('area_sqm', 0),
                "confidence_score": panel.get('confidence_score', 0),
                "geometry": panel.get('geometry', {}),
                "kwp_potential": kwp_potential,
                "created_at": panel.get('created_at')
            })
        
        # Build mapping from bus_solar_capacity
        mapping = {str(k): v for k, v in engine.bus_solar_capacity.items()}
        
        return {"success": True, "inventory": panels, "mapping": mapping}
    except Exception as e:
        logger.error(f"Error fetching solar inventory: {e}")
        return {"success": False, "inventory": [], "mapping": {}, "error": str(e)}

@router.post("/geo-sam/detect")
async def detect_solar_panels(file: UploadFile = File(...), engine=Depends(get_engine)):
    """Geo-SAM detection"""
    if not engine.db_manager:
        raise HTTPException(status_code=503, detail="Database not initialized")
    # ... logic from app.py ...
    return {"success": True, "message": "Geo-SAM triggered (Stub)"}

@router.post("/control/island")
async def island_grid(engine=Depends(get_engine)):
    success = await engine.disconnect_grid()
    return {"success": success}

@router.post("/control/reconnect")
async def reconnect_grid(engine=Depends(get_engine)):
    success = await engine.reconnect_grid()
    return {"success": success}

@router.post("/control/attack")
async def control_attack(request: dict, engine=Depends(get_engine)):
    engine.attacker.configure(**request)
    return {"success": True, "status": engine.attacker.get_status()}
