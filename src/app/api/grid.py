"""
Grid Analysis API for Microgrid Optimization.

This module provides REST endpoints for:
- Grid state analysis (voltage, losses, power quality)
- Zone-level aggregated metrics
- Optimization data export for external algorithms
- Battery dispatch commands

Note: P2P trading matching is handled by the API Gateway and Blockchain.
This API focuses on grid physics and optimization support.
"""

from fastapi import APIRouter, Request, HTTPException, Query
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


# =============================================================================
# Pydantic Models for Grid Analysis
# =============================================================================

class GridStateResponse(BaseModel):
    """Response model for grid state at a specific meter."""
    meter_id: str
    voltage_pu: float
    voltage_v: float
    frequency_hz: float
    power_factor: float
    thd_voltage: float
    thd_current: float
    is_on_peak: bool
    temperature_c: float


class ZoneStateResponse(BaseModel):
    """Response model for zone-level aggregated state."""
    zone_id: int
    avg_voltage_pu: float
    min_voltage_pu: float
    max_voltage_pu: float
    total_load_kw: float
    total_generation_kw: float
    net_power_kw: float
    meter_count: int
    has_voltage_violation: bool
    has_overload: bool = False


class BatteryDispatchRequest(BaseModel):
    """Request model for battery dispatch command."""
    meter_id: str = Field(..., description="Target meter with battery")
    power_kw: float = Field(..., description="Power in kW. Positive = discharge, Negative = charge")


class BatteryDispatchResponse(BaseModel):
    """Response model for battery dispatch result."""
    success: bool
    meter_id: str
    power_kw: float
    new_battery_level: Optional[float]
    message: str

@router.get("/thailand/data")
async def get_thailand_data(request: Request):
    """Get static structure of Thailand grid (Transformers/Zones and Meters)"""
    engine = getattr(request.app.state, "engine", None)
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
        import logging
        logging.error(f"Error in get_thailand_data: {e}")
        return {"error": str(e), "traceback": traceback.format_exc()}

@router.get("/zones")
async def get_zones(request: Request):
    """Get K-Means zone data including centroids and meter assignments"""
    engine = getattr(request.app.state, "engine", None)
    if not engine:
        return {"error": "Simulator not initialized"}

    try:
        # Get zone summary from zoning service
        # Check if zoning_service is available
        if not hasattr(engine, "zoning_service"):
             return {"error": "Zoning service not available on engine"}

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
        import logging
        logging.error(f"Error in get_zones: {e}")
        return {"error": str(e), "traceback": traceback.format_exc()}


@router.get("/grid/status")
async def get_grid_status(request: Request):
    """Get aggregate grid status (Generation, Consumption, Balance)"""
    engine = getattr(request.app.state, "engine", None)
    if not engine:
        return {"error": "Simulator not initialized"}

    try:
        total_generation = 0.0
        total_consumption = 0.0
        active_meters = 0
        
        for meter in engine.meters:
            # Check connection status
            if getattr(meter, "is_connected", False):
                active_meters += 1
                
                # Get latest reading if available
                if hasattr(meter, "last_reading") and meter.last_reading:
                    total_generation += meter.last_reading.energy_generated
                    total_consumption += meter.last_reading.energy_consumed
        
        net_balance = total_generation - total_consumption
        # Simple CO2 calculation (approximate 0.5 kg/kWh for grid offset)
        co2_saved_kg = total_generation * 0.5 

        from datetime import datetime, timezone
        
        return {
            "total_generation": round(total_generation, 4),
            "total_consumption": round(total_consumption, 4),
            "net_balance": round(net_balance, 4),
            "active_meters": active_meters,
            "co2_saved_kg": round(co2_saved_kg, 4),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        import traceback
        import logging
        logging.error(f"Error in get_grid_status: {e}")
        return {"error": str(e), "traceback": traceback.format_exc()}


# =============================================================================
# New Grid Analysis Endpoints for Microgrid Optimization
# =============================================================================

@router.get("/grid/state/{meter_id}", response_model=GridStateResponse)
async def get_meter_grid_state(meter_id: str, request: Request):
    """
    Get current grid state for a specific meter.
    
    Returns voltage, frequency, power factor, THD, and other physical parameters.
    """
    engine = getattr(request.app.state, "engine", None)
    if not engine:
        raise HTTPException(status_code=503, detail="Simulator not initialized")
    
    meter = next((m for m in engine.meters if m.meter_id == meter_id), None)
    if not meter:
        raise HTTPException(status_code=404, detail=f"Meter {meter_id} not found")
    
    grid_state = engine.get_grid_state(meter_id)
    
    return GridStateResponse(
        meter_id=meter_id,
        voltage_pu=grid_state.voltage_pu,
        voltage_v=grid_state.voltage_pu * 230.0,
        frequency_hz=grid_state.frequency_hz,
        power_factor=grid_state.power_factor,
        thd_voltage=grid_state.thd_voltage,
        thd_current=grid_state.thd_current,
        is_on_peak=grid_state.is_on_peak,
        temperature_c=grid_state.temperature_c
    )


@router.get("/grid/zone/{zone_id}/state", response_model=ZoneStateResponse)
async def get_zone_state(zone_id: int, request: Request):
    """
    Get aggregated state for a microgrid zone.
    
    Returns voltage statistics, total load/generation, and violation flags.
    """
    engine = getattr(request.app.state, "engine", None)
    if not engine:
        raise HTTPException(status_code=503, detail="Simulator not initialized")
    
    zone_state = engine.get_zone_state(zone_id)
    
    if zone_state.meter_count == 0:
        raise HTTPException(status_code=404, detail=f"Zone {zone_id} not found or has no meters")
    
    return ZoneStateResponse(**vars(zone_state))


@router.get("/grid/analysis")
async def get_grid_analysis(request: Request):
    """
    Perform comprehensive grid analysis.
    
    Runs power flow calculation and returns:
    - Total load and generation
    - Technical losses
    - Voltage violations
    - Optimization recommendations
    """
    engine = getattr(request.app.state, "engine", None)
    if not engine:
        raise HTTPException(status_code=503, detail="Simulator not initialized")
    
    try:
        analysis = engine.analyze_grid()
        
        return {
            "timestamp": analysis.timestamp.isoformat() if analysis.timestamp else "",
            "power_flow_converged": analysis.power_flow_converged,
            "total_load_mw": analysis.total_load_mw,
            "total_generation_mw": analysis.total_generation_mw,
            "total_loss_mw": analysis.total_loss_mw,
            "loss_percentage": analysis.loss_percentage,
            "zone_count": len(analysis.zone_states),
            "voltage_violations": analysis.voltage_violations,
            "overloaded_elements": analysis.overloaded_elements,
            "recommendations": analysis.recommendations
        }
    except Exception as e:
        logger.error(f"Grid analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/grid/losses")
async def get_loss_analysis(request: Request):
    """
    Get detailed technical loss analysis.
    
    Returns loss breakdown by zone with optimization recommendations.
    """
    engine = getattr(request.app.state, "engine", None)
    if not engine:
        raise HTTPException(status_code=503, detail="Simulator not initialized")
    
    try:
        loss_data = engine.get_loss_analysis()
        return loss_data
    except Exception as e:
        logger.error(f"Loss analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/grid/optimization-data")
async def get_optimization_data(request: Request):
    """
    Get data package for external optimization algorithms.
    
    Returns all necessary information for battery dispatch,
    load scheduling, or DER optimization algorithms.
    """
    engine = getattr(request.app.state, "engine", None)
    if not engine:
        raise HTTPException(status_code=503, detail="Simulator not initialized")
    
    try:
        data = engine.get_optimization_data()
        
        # Add summary stats
        data["summary"] = {
            "total_load_mw": sum(m.get("current_load_kw", 0) for m in data.get("meters", [])) / 1000,
            "total_gen_mw": sum(m.get("current_gen_kw", 0) for m in data.get("meters", [])) / 1000,
            "meters_with_battery": len([m for m in data.get("meters", []) if m.get("has_battery")]),
            "meters_with_solar": len([m for m in data.get("meters", []) if m.get("has_solar")]),
            "available_battery_kwh": sum(
                m.get("battery_capacity", 0) * m.get("battery_level", 0) / 100
                for m in data.get("meters", []) if m.get("has_battery")
            )
        }
        
        return data
    except Exception as e:
        logger.error(f"Failed to get optimization data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/grid/battery/dispatch", response_model=BatteryDispatchResponse)
async def dispatch_battery(request: Request, dispatch: BatteryDispatchRequest):
    """
    Send battery dispatch command to a meter.
    
    Use positive power_kw to discharge (inject to grid),
    negative power_kw to charge (absorb from grid).
    """
    engine = getattr(request.app.state, "engine", None)
    if not engine:
        raise HTTPException(status_code=503, detail="Simulator not initialized")
    
    meter = next((m for m in engine.meters if m.meter_id == dispatch.meter_id), None)
    if not meter:
        raise HTTPException(status_code=404, detail=f"Meter {dispatch.meter_id} not found")
    
    if not meter.config.get("has_battery"):
        raise HTTPException(
            status_code=400, 
            detail=f"Meter {dispatch.meter_id} does not have a battery"
        )
    
    success = engine.apply_battery_dispatch(dispatch.meter_id, dispatch.power_kw)
    
    action = "discharge" if dispatch.power_kw > 0 else "charge"
    
    return BatteryDispatchResponse(
        success=success,
        meter_id=dispatch.meter_id,
        power_kw=dispatch.power_kw,
        new_battery_level=meter.battery_level if success else None,
        message=f"Battery {action} command {'sent' if success else 'failed'}"
    )


@router.get("/grid/events")
async def get_grid_events(
    request: Request,
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    zone_id: Optional[int] = Query(None, description="Filter by zone"),
    limit: int = Query(100, le=1000, description="Maximum events to return")
):
    """
    Get recent grid events (violations, dispatches, milestones).
    """
    engine = getattr(request.app.state, "engine", None)
    if not engine:
        return []
    
    if not hasattr(engine, "ledger"):
        return []
    
    return engine.ledger.get_events(event_type=event_type, zone_id=zone_id, limit=limit)


@router.get("/grid/health")
async def grid_health_check(request: Request):
    """
    Quick grid health check endpoint.
    
    Returns basic health status without full analysis.
    """
    engine = getattr(request.app.state, "engine", None)
    if not engine:
        return {"healthy": False, "error": "Simulator not initialized"}
    
    is_valid = engine.validate_grid_state()
    
    return {
        "healthy": is_valid,
        "meter_count": len(engine.meters),
        "simulation_time": engine.current_sim_time.isoformat() if engine.current_sim_time else None,
        "model_type": engine.model_type
    }
