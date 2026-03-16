from typing import Any, Dict, List
from fastapi import APIRouter, Depends, HTTPException, Request
from .dependencies import get_engine

router = APIRouter(prefix="/api/meters", tags=["Meters"])

@router.get("")
async def list_meters(engine=Depends(get_engine)):
    """Get list of all meters with their serial numbers"""
    meters_list = []
    for meter in engine.meters:
        meters_list.append({
            "meter_id": meter.meter_id,
            "serial_number": meter.meter_id,
            "meter_type": meter.config.get('meter_type', 'unknown'),
            "location": meter.config.get('location', 'Unknown'),
            "status": "active"
        })
    
    return {
        "meters": meters_list,
        "count": len(meters_list)
    }

@router.get("/{meter_id}")
async def get_meter(meter_id: str, engine=Depends(get_engine)):
    """Get details of a specific meter by serial number"""
    meter = next((m for m in engine.meters if m.meter_id == meter_id), None)
    if not meter:
        raise HTTPException(status_code=404, detail=f"Meter {meter_id} not found")
    
    return {
        "meter_id": meter.meter_id,
        "serial_number": meter.meter_id,
        "meter_type": meter.config.get('meter_type', 'unknown'),
        "location_name": meter.config.get('location_name', meter.config.get('location', 'Unknown')),
        "location": meter.config.get('location', 'Unknown'),
        "latitude": meter.config.get('latitude'),
        "longitude": meter.config.get('longitude'),
        "phase": meter.config.get('phase'),
        "solar_capacity": meter.config.get('solar_capacity', 0),
        "has_battery": meter.config.get('has_battery', False),
        "has_solar": meter.config.get('has_solar', False),
        "wallet_address": meter.config.get('wallet_address'),
        "status": "active"
    }

from pydantic import BaseModel
from typing import Optional

class MeterCreateRequest(BaseModel):
    meter_type: str
    location: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    solar_capacity: Optional[float] = 0.0
    trading_preference: Optional[str] = "moderate"
    custom_id: Optional[str] = None
    wallet_address: Optional[str] = None

@router.post("")
async def create_meter(meter_data: MeterCreateRequest, engine=Depends(get_engine)):
    """Dynamically add a new meter to the simulation."""
    try:
        from ..core.meter import SmartMeter
        meter_id = meter_data.custom_id or f"METER-{len(engine.meters) + 1:04d}"
        
        config = {
            "meter_id": meter_id,
            "meter_type": meter_data.meter_type,
            "location": meter_data.location,
            "latitude": meter_data.latitude,
            "longitude": meter_data.longitude,
            "solar_capacity": meter_data.solar_capacity,
            "wallet_address": meter_data.wallet_address,
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
        raise HTTPException(status_code=500, detail=str(e))

class MeterOverrideRequest(BaseModel):
    gen: Optional[float] = None
    cons: Optional[float] = None

@router.post("/{meter_id}/override")
async def override_meter(meter_id: str, data: MeterOverrideRequest, engine=Depends(get_engine)):
    """Manually override generation and consumption for a meter."""
    meter = next((m for m in engine.meters if m.meter_id == meter_id), None)
    if not meter:
        raise HTTPException(status_code=404, detail=f"Meter {meter_id} not found")
    
    if data.gen is not None:
        meter.manual_override_gen = data.gen
    if data.cons is not None:
        meter.manual_override_cons = data.cons
        
    return {
        "success": True,
        "message": f"Overrides applied to {meter_id}",
        "overrides": {
            "gen": getattr(meter, 'manual_override_gen', None),
            "cons": getattr(meter, 'manual_override_cons', None)
        }
    }
