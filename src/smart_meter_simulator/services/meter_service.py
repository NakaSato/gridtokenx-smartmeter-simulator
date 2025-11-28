"""
Meter service for managing smart meters in the simulation.
"""

import logging
import random
import uuid
from typing import List, Dict, Any, Optional

from ..core.engine import SimulationEngine
from ..core.database import DatabaseManager
from ..core.meter import SmartMeter
from ..exceptions import MeterError, ValidationError

logger = logging.getLogger(__name__)


class MeterService:
    """Service for managing smart meters."""
    
    def __init__(self, engine: SimulationEngine, db_manager: DatabaseManager):
        """Initialize the meter service."""
        self.engine = engine
        self.db_manager = db_manager
        self._meter_overrides: Dict[str, Dict[str, Any]] = {}
        logger.info("MeterService initialized")
    
    def add_meter(self, meter_config: Dict[str, Any]) -> Dict[str, Any]:
        """Add a new meter to the simulation."""
        try:
            # Validate meter configuration
            self._validate_meter_config(meter_config)
            
            # Create new meter
            new_meter = SmartMeter(meter_config)
            
            # Add to engine
            self.engine.meters.append(new_meter)
            
            # Save to database
            if self.db_manager:
                self.db_manager.save_meter(meter_config)
            
            logger.info(f"Added new meter: {new_meter.meter_id}")
            
            return {
                "meter_id": new_meter.meter_id,
                "meter_type": meter_config["meter_type"],
                "location": meter_config.get("location", "Unknown"),
                "total_meters": len(self.engine.meters),
            }
            
        except ValidationError as e:
            raise
        except Exception as e:
            logger.error(f"Error adding meter: {e}")
            raise MeterError(f"Failed to add meter: {str(e)}")
    
    def remove_meter(self, meter_id: str) -> Dict[str, Any]:
        """Remove a meter from the simulation."""
        try:
            # Find and remove meter
            target_meter = None
            for i, meter in enumerate(self.engine.meters):
                if meter.meter_id == meter_id:
                    target_meter = meter
                    self.engine.meters.pop(i)
                    break
            
            if not target_meter:
                raise ValidationError(f"Meter {meter_id} not found")
            
            # Clean up overrides
            if meter_id in self._meter_overrides:
                del self._meter_overrides[meter_id]
            
            # Remove from database
            if self.db_manager:
                self.db_manager.delete_meter(meter_id)
            
            logger.info(f"Removed meter: {meter_id}")
            
            return {
                "meter_id": meter_id,
                "total_meters": len(self.engine.meters),
            }
            
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error removing meter: {e}")
            raise MeterError(f"Failed to remove meter: {str(e)}")
    
    def get_meter_status(self, meter_id: str) -> Dict[str, Any]:
        """Get detailed status for a specific meter."""
        try:
            # Find the meter
            target_meter = None
            for meter in self.engine.meters:
                if meter.meter_id == meter_id:
                    target_meter = meter
                    break
            
            if not target_meter:
                raise ValidationError(f"Meter {meter_id} not found")
            
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
                "is_connected": getattr(target_meter, "is_connected", False),
                "connection_status": "✅ ONLINE" if getattr(target_meter, "is_connected", False) else "❌ OFFLINE",
                "config": {
                    "has_solar": target_meter.config.get("has_solar", False),
                    "solar_capacity": target_meter.config.get("solar_capacity", 0),
                    "has_battery": target_meter.config.get("has_battery", False),
                    "battery_capacity": target_meter.config.get("battery_capacity", 0),
                    "trading_preference": target_meter.config.get("trading_preference", "Unknown"),
                },
                "current_state": {
                    "battery_level": round(target_meter.battery_level, 2),
                    "current_weather": target_meter.current_weather,
                    "current_sell_price": round(target_meter.current_sell_price, 4),
                    "current_buy_price": round(target_meter.current_buy_price, 4),
                },
                "latest_reading": self._format_reading(latest_reading) if latest_reading else None,
                "coordinates": {
                    "latitude": target_meter.latitude,
                    "longitude": target_meter.longitude,
                },
            }
            
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error getting meter status: {e}")
            raise MeterError(f"Failed to get meter status: {str(e)}")
    
    def set_meter_override(self, meter_id: str, override_data: Dict[str, Any]) -> Dict[str, Any]:
        """Set manual override values for a specific meter."""
        try:
            # Find the meter
            target_meter = None
            for meter in self.engine.meters:
                if meter.meter_id == meter_id:
                    target_meter = meter
                    break
            
            if not target_meter:
                raise ValidationError(f"Meter {meter_id} not found")
            
            # Store override
            self._meter_overrides[meter_id] = override_data
            
            # Apply to meter using setattr for dynamic attribute
            setattr(target_meter, "static_data", override_data)
            
            logger.info(f"Set manual override for {meter_id}")
            
            return {
                "meter_id": meter_id,
                "override": override_data,
            }
            
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error setting meter override: {e}")
            raise MeterError(f"Failed to set meter override: {str(e)}")
    
    def remove_meter_override(self, meter_id: str) -> Dict[str, Any]:
        """Remove manual override for a specific meter."""
        try:
            if meter_id in self._meter_overrides:
                del self._meter_overrides[meter_id]
                
                # Remove from meter instance
                for meter in self.engine.meters:
                    if meter.meter_id == meter_id:
                        if hasattr(meter, "static_data"):
                            delattr(meter, "static_data")
                        break
                
                logger.info(f"Removed manual override for {meter_id}")
                return {"meter_id": meter_id, "message": "Override removed"}
            else:
                raise ValidationError(f"No override found for {meter_id}")
                
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error removing meter override: {e}")
            raise MeterError(f"Failed to remove meter override: {str(e)}")
    
    def get_all_meters(self) -> List[Dict[str, Any]]:
        """Get status for all meters."""
        try:
            meters_status = []
            for meter in self.engine.meters:
                try:
                    status = self.get_meter_status(meter.meter_id)
                    meters_status.append(status)
                except Exception as e:
                    logger.warning(f"Error getting status for meter {meter.meter_id}: {e}")
                    # Add basic status even if detailed status fails
                    meters_status.append({
                        "meter_id": meter.meter_id,
                        "meter_type": meter.config.get("meter_type", "Unknown"),
                        "error": str(e)
                    })
            
            return meters_status
            
        except Exception as e:
            logger.error(f"Error getting all meters: {e}")
            raise MeterError(f"Failed to get all meters: {str(e)}")
    
    def get_meter_overrides(self) -> Dict[str, Dict[str, Any]]:
        """Get all current meter overrides."""
        return self._meter_overrides.copy()
    
    def _validate_meter_config(self, config: Dict[str, Any]) -> None:
        """Validate meter configuration."""
        required_fields = ["meter_type"]
        for field in required_fields:
            if field not in config:
                raise ValidationError(f"Missing required field: {field}")
        
        # Validate meter type
        valid_types = [
            "Solar_Prosumer",
            "Grid_Consumer", 
            "Hybrid_Prosumer",
            "Battery_Storage",
        ]
        if config["meter_type"] not in valid_types:
            raise ValidationError(f"Invalid meter type. Must be one of: {', '.join(valid_types)}")
        
        # Validate trading preference if provided
        if "trading_preference" in config:
            valid_preferences = ["Aggressive", "Moderate", "Conservative"]
            if config["trading_preference"] not in valid_preferences:
                raise ValidationError(f"Invalid trading preference. Must be one of: {', '.join(valid_preferences)}")
    
    def _format_reading(self, reading) -> Dict[str, Any]:
        """Format a meter reading for API response."""
        return {
            "timestamp": reading.timestamp.isoformat() if reading else None,
            "energy_generated": round(reading.energy_generated, 4) if reading else 0,
            "energy_consumed": round(reading.energy_consumed, 4) if reading else 0,
            "surplus_energy": round(reading.surplus_energy, 4) if reading else 0,
            "deficit_energy": round(reading.deficit_energy, 4) if reading else 0,
            "battery_level": round(reading.battery_level, 2) if reading else 0,
            "voltage": round(reading.voltage, 2) if reading else 0,
            "current": round(reading.current, 3) if reading else 0,
            "temperature": round(reading.temperature, 1) if reading else 0,
            "net_emission": round(reading.net_emission, 4) if reading else 0,
            "rec_eligible": reading.rec_eligible if reading else False,
        }
