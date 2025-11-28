"""
Meter management API routes.
"""

import logging
import random
import uuid
from typing import Dict, Any, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ..exceptions import MeterError, ValidationError
from ..services.meter_service import MeterService
from ..container import get_container

logger = logging.getLogger(__name__)
router = APIRouter(tags=["meters"])


class MeterRequest(BaseModel):
    """Request model for creating a new meter."""
    meter_type: str = Field(..., description="Type of meter")
    location: str = Field(default="", description="Location of the meter")
    solar_capacity: float = Field(default=10.0, ge=0, description="Solar capacity in kW")
    battery_capacity: float = Field(default=10.0, ge=0, description="Battery capacity in kWh")
    trading_preference: str = Field(default="Moderate", description="Trading preference")
    latitude: Optional[float] = Field(default=None, description="Latitude coordinate")
    longitude: Optional[float] = Field(default=None, description="Longitude coordinate")


class MeterOverrideRequest(BaseModel):
    """Request model for meter override."""
    energy_generated: float = Field(default=0.0, ge=0, le=100, description="Energy generation in kWh")
    energy_consumed: float = Field(default=0.0, ge=0, le=100, description="Energy consumption in kWh")
    battery_level: float = Field(default=50.0, ge=0, le=100, description="Battery level percentage")
    voltage: float = Field(default=240.0, ge=0, description="Voltage in V")
    current: float = Field(default=0.0, ge=0, description="Current in A")
    frequency: float = Field(default=50.0, ge=0, description="Frequency in Hz")
    temperature: float = Field(default=25.0, description="Temperature in Celsius")
    power_factor: float = Field(default=1.0, ge=0, le=1, description="Power factor")
    max_sell_price: Optional[float] = Field(default=None, ge=0, description="Maximum sell price")
    max_buy_price: Optional[float] = Field(default=None, ge=0, description="Maximum buy price")


# Global storage for meter overrides (temporary - will be moved to service layer)
meter_overrides: Dict[str, Dict[str, Any]] = {}


# This will be injected from the main application
_simulation_engine = None
_db_manager = None


def set_dependencies(engine, db_manager):
    """Set dependencies from main application."""
    global _simulation_engine, _db_manager
    _simulation_engine = engine
    _db_manager = db_manager


@router.get("/")
async def list_meters():
    """List all meters."""
    try:
        container = get_container()
        meter_service = container.get(MeterService)
        meters_status = meter_service.get_all_meters()
        return {
            "meters": meters_status,
            "total_meters": len(meters_status),
        }
    except Exception as e:
        logger.error(f"Error listing meters: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/add")
async def add_meter(request: MeterRequest):
    """Add a new meter to the simulation."""
    try:
        container = get_container()
        meter_service = container.get(MeterService)
        
        # Validate meter type
        valid_types = [
            "Solar_Prosumer",
            "Grid_Consumer", 
            "Hybrid_Prosumer",
            "Battery_Storage",
        ]
        if request.meter_type not in valid_types:
            raise ValidationError(f"Invalid meter type. Must be one of: {', '.join(valid_types)}")

        # Validate trading preference
        valid_preferences = ["Aggressive", "Moderate", "Conservative"]
        if request.trading_preference not in valid_preferences:
            raise ValidationError(f"Invalid trading preference. Must be one of: {', '.join(valid_preferences)}")

        # Create meter configuration
        meter_config = {
            "meter_id": str(uuid.uuid4()),
            "meter_type": request.meter_type,
            "location": request.location or f"Zone_{random.randint(1, 5)}_Building_{random.randint(1, 10)}",
            "user_type": "Prosumer" if request.meter_type in ["Solar_Prosumer", "Hybrid_Prosumer"] else "Consumer",
            "base_generation": random.uniform(0.5, 3.0),
            "base_consumption": random.uniform(0.5, 2.5),
            "battery_capacity": request.battery_capacity,
            "solar_efficiency": random.uniform(0.15, 0.22),
            "battery_efficiency": random.uniform(0.85, 0.95),
            "trading_preference": request.trading_preference,
            "has_solar": request.meter_type in ["Solar_Prosumer", "Hybrid_Prosumer"],
            "solar_capacity": request.solar_capacity if request.meter_type in ["Solar_Prosumer", "Hybrid_Prosumer"] else 0.0,
            "panel_efficiency": random.uniform(0.15, 0.22) if request.meter_type in ["Solar_Prosumer", "Hybrid_Prosumer"] else 0.0,
            "has_battery": request.meter_type in ["Hybrid_Prosumer", "Battery_Storage"],
            "current_battery_level": random.uniform(20.0, 80.0) if request.meter_type in ["Hybrid_Prosumer", "Battery_Storage"] else 0.0,
            "max_sell_price": random.uniform(0.08, 0.15),
            "max_buy_price": random.uniform(0.10, 0.20),
            "latitude": request.latitude,
            "longitude": request.longitude,
        }

        # Add meter using service
        result = meter_service.add_meter(meter_config)

        return {
            "success": True,
            "message": f"Successfully added {request.meter_type} meter",
            "meter": {
                "meter_id": result["meter_id"],
                "meter_type": request.meter_type,
                "location": meter_config["location"],
                "solar_capacity": request.solar_capacity,
                "battery_capacity": request.battery_capacity,
                "trading_preference": request.trading_preference,
            },
            "total_meters": result["total_meters"],
        }
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error adding meter: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{meter_id}")
async def delete_meter(meter_id: str):
    """Remove a meter from the simulation."""
    if not _simulation_engine:
        raise HTTPException(status_code=503, detail="Simulator not initialized")

    try:
        # Find and remove meter
        target_meter = None
        for i, m in enumerate(_simulation_engine.meters):
            if m.meter_id == meter_id:
                target_meter = m
                _simulation_engine.meters.pop(i)
                break

        if not target_meter:
            raise HTTPException(status_code=404, detail=f"Meter {meter_id} not found")

        # Clean up any overrides
        if meter_id in meter_overrides:
            del meter_overrides[meter_id]

        # Remove from DB
        if _db_manager:
            _db_manager.delete_meter(meter_id)

        logger.info(f"Removed meter: {meter_id}")

        return {
            "success": True,
            "message": f"Successfully removed meter {meter_id}",
            "total_meters": len(_simulation_engine.meters),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing meter: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{meter_id}/status")
async def get_meter_status(meter_id: str):
    """Get detailed status for a specific meter."""
    if not _simulation_engine:
        raise HTTPException(status_code=503, detail="Simulator not initialized")

    try:
        # Find the meter
        target_meter = None
        for meter in _simulation_engine.meters:
            if meter.meter_id == meter_id:
                target_meter = meter
                break

        if not target_meter:
            raise HTTPException(status_code=404, detail=f"Meter {meter_id} not found")

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
            # Connection status
            "is_connected": getattr(target_meter, "is_connected", False),
            "connection_status": "✅ ONLINE" if getattr(target_meter, "is_connected", False) else "❌ OFFLINE",
            # Configuration
            "config": {
                "has_solar": target_meter.config.get("has_solar", False),
                "solar_capacity": target_meter.config.get("solar_capacity", 0),
                "has_battery": target_meter.config.get("has_battery", False),
                "battery_capacity": target_meter.config.get("battery_capacity", 0),
                "trading_preference": target_meter.config.get("trading_preference", "Unknown"),
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
                "timestamp": latest_reading.timestamp.isoformat() if latest_reading else None,
                "energy_generated": round(latest_reading.energy_generated, 4) if latest_reading else 0,
                "energy_consumed": round(latest_reading.energy_consumed, 4) if latest_reading else 0,
                "surplus_energy": round(latest_reading.surplus_energy, 4) if latest_reading else 0,
                "deficit_energy": round(latest_reading.deficit_energy, 4) if latest_reading else 0,
                "battery_level": round(latest_reading.battery_level, 2) if latest_reading else 0,
                "voltage": round(latest_reading.voltage, 2) if latest_reading else 0,
                "current": round(latest_reading.current, 3) if latest_reading else 0,
                "temperature": round(latest_reading.temperature, 1) if latest_reading else 0,
                "net_emission": round(latest_reading.net_emission, 4) if latest_reading else 0,
                "rec_eligible": latest_reading.rec_eligible if latest_reading else False,
            } if latest_reading else None,
            # GPS coordinates
            "coordinates": {
                "latitude": target_meter.latitude,
                "longitude": target_meter.longitude,
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting meter status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{meter_id}/override")
async def set_meter_override(meter_id: str, request: MeterOverrideRequest):
    """Set manual override values for a specific meter."""
    if not _simulation_engine:
        raise HTTPException(status_code=503, detail="Simulator not initialized")

    try:
        # Validate meter exists
        target_meter = None
        for m in _simulation_engine.meters:
            if m.meter_id == meter_id:
                target_meter = m
                break

        if not target_meter:
            raise HTTPException(status_code=404, detail=f"Meter {meter_id} not found")

        # Create override data
        override = {
            "mode": "manual",
            "energy_generated": request.energy_generated,
            "energy_consumed": request.energy_consumed,
            "battery_level": request.battery_level,
            "voltage": request.voltage,
            "current": request.current,
            "frequency": request.frequency,
            "temperature": request.temperature,
            "power_factor": request.power_factor,
            "max_sell_price": request.max_sell_price or target_meter.current_sell_price,
            "max_buy_price": request.max_buy_price or target_meter.current_buy_price,
        }

        # Store in global overrides (for persistence/API checks)
        meter_overrides[meter_id] = override

        # Inject directly into meter instance
        target_meter.static_data = override

        logger.info(f"Set manual override for {meter_id}: {override}")

        return {
            "success": True,
            "message": f"Manual override set for {meter_id}",
            "override": override,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error setting meter override: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{meter_id}/override")
async def delete_meter_override(meter_id: str):
    """Remove manual override for a specific meter (return to auto mode)."""
    try:
        if meter_id in meter_overrides:
            del meter_overrides[meter_id]

            # Remove from meter instance
            if _simulation_engine:
                for m in _simulation_engine.meters:
                    if m.meter_id == meter_id:
                        if hasattr(m, "static_data"):
                            delattr(m, "static_data")
                        break

            logger.info(f"Removed manual override for {meter_id}")
            return {"success": True, "message": f"Meter {meter_id} returned to auto mode"}
        else:
            raise HTTPException(status_code=404, detail=f"No override found for {meter_id}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing meter override: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/overrides")
async def get_meter_overrides():
    """Get all current meter overrides."""
    return {"success": True, "overrides": meter_overrides}
