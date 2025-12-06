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
    solar_capacity: float = Field(
        default=10.0, ge=0, description="Solar capacity in kW"
    )
    battery_capacity: float = Field(
        default=10.0, ge=0, description="Battery capacity in kWh"
    )
    trading_preference: str = Field(
        default="Moderate", description="Trading preference"
    )
    latitude: Optional[float] = Field(default=None, description="Latitude coordinate")
    longitude: Optional[float] = Field(default=None, description="Longitude coordinate")
    wallet_address: Optional[str] = Field(
        default=None, description="Wallet address of the owner"
    )


class MeterOverrideRequest(BaseModel):
    """Request model for meter override."""

    energy_generated: float = Field(
        default=0.0, ge=0, le=100, description="Energy generation in kWh"
    )
    energy_consumed: float = Field(
        default=0.0, ge=0, le=100, description="Energy consumption in kWh"
    )
    battery_level: float = Field(
        default=50.0, ge=0, le=100, description="Battery level percentage"
    )
    voltage: float = Field(default=240.0, ge=0, description="Voltage in V")
    current: float = Field(default=0.0, ge=0, description="Current in A")
    frequency: float = Field(default=50.0, ge=0, description="Frequency in Hz")
    temperature: float = Field(default=25.0, description="Temperature in Celsius")
    power_factor: float = Field(default=1.0, ge=0, le=1, description="Power factor")
    max_sell_price: Optional[float] = Field(
        default=None, ge=0, description="Maximum sell price"
    )
    max_buy_price: Optional[float] = Field(
        default=None, ge=0, description="Maximum buy price"
    )


def get_meter_service() -> MeterService:
    """Helper to get MeterService from container."""
    container = get_container()
    if not container.has(MeterService):
        raise HTTPException(status_code=503, detail="Meter service not available")
    return container.get(MeterService)


@router.get("/")
async def list_meters():
    """List all meters."""
    try:
        meter_service = get_meter_service()
        meters_status = meter_service.get_all_meters()
        return {
            "meters": meters_status,
            "total_meters": len(meters_status),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing meters: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/add")
async def add_meter(request: MeterRequest):
    """Add a new meter to the simulation."""
    try:
        meter_service = get_meter_service()

        # Create meter configuration
        meter_config = {
            "meter_id": str(uuid.uuid4()),
            "meter_type": request.meter_type,
            "location": request.location
            or f"Zone_{random.randint(1, 5)}_Building_{random.randint(1, 10)}",
            "user_type": "Prosumer"
            if request.meter_type in ["Solar_Prosumer", "Hybrid_Prosumer"]
            else "Consumer",
            "base_generation": random.uniform(0.5, 3.0),
            "base_consumption": random.uniform(0.5, 2.5),
            "battery_capacity": request.battery_capacity,
            "solar_efficiency": random.uniform(0.15, 0.22),
            "battery_efficiency": random.uniform(0.85, 0.95),
            "trading_preference": request.trading_preference,
            "has_solar": request.meter_type in ["Solar_Prosumer", "Hybrid_Prosumer"],
            "solar_capacity": request.solar_capacity
            if request.meter_type in ["Solar_Prosumer", "Hybrid_Prosumer"]
            else 0.0,
            "panel_efficiency": random.uniform(0.15, 0.22)
            if request.meter_type in ["Solar_Prosumer", "Hybrid_Prosumer"]
            else 0.0,
            "has_battery": request.meter_type in ["Hybrid_Prosumer", "Battery_Storage"],
            "current_battery_level": random.uniform(20.0, 80.0)
            if request.meter_type in ["Hybrid_Prosumer", "Battery_Storage"]
            else 0.0,
            "max_buy_price": random.uniform(0.10, 0.20),
            "latitude": request.latitude,
            "longitude": request.longitude,
            "wallet_address": request.wallet_address,
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
                "meter_public_key": result["meter_public_key"],
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
    try:
        meter_service = get_meter_service()
        result = meter_service.remove_meter(meter_id)

        return {
            "success": True,
            "message": f"Successfully removed meter {meter_id}",
            "total_meters": result["total_meters"],
        }
    except ValidationError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing meter: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{meter_id}/status")
async def get_meter_status(meter_id: str):
    """Get detailed status for a specific meter."""
    try:
        meter_service = get_meter_service()
        return meter_service.get_meter_status(meter_id)
    except ValidationError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting meter status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{meter_id}/override")
async def set_meter_override(meter_id: str, request: MeterOverrideRequest):
    """Set manual override values for a specific meter."""
    try:
        meter_service = get_meter_service()

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
            "max_sell_price": request.max_sell_price,
            "max_buy_price": request.max_buy_price,
        }

        result = meter_service.set_meter_override(meter_id, override)

        return {
            "success": True,
            "message": f"Manual override set for {meter_id}",
            "override": result["override"],
        }
    except ValidationError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error setting meter override: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{meter_id}/override")
async def delete_meter_override(meter_id: str):
    """Remove manual override for a specific meter (return to auto mode)."""
    try:
        meter_service = get_meter_service()
        result = meter_service.remove_meter_override(meter_id)
        return {"success": True, "message": result["message"]}
    except ValidationError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing meter override: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/overrides")
async def get_meter_overrides():
    """Get all current meter overrides."""
    try:
        meter_service = get_meter_service()
        overrides = meter_service.get_meter_overrides()
        return {"success": True, "overrides": overrides}
    except Exception as e:
        logger.error(f"Error getting overrides: {e}")
        raise HTTPException(status_code=500, detail=str(e))
