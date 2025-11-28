"""
Simulation service for managing smart meter simulation.
"""

import logging
from typing import List, Dict, Any, Optional

from ..core.engine import SimulationEngine
from ..core.database import DatabaseManager
from ..exceptions import SimulationError

logger = logging.getLogger(__name__)


class SimulationService:
    """Service for managing simulation operations."""
    
    def __init__(self, engine: SimulationEngine, db_manager: DatabaseManager):
        """Initialize simulation service."""
        self.engine = engine
        self.db_manager = db_manager
        logger.info("SimulationService initialized")
    
    def start_simulation(self) -> Dict[str, Any]:
        """Start simulation."""
        try:
            if self.is_running():
                return {
                    "success": False,
                    "message": "Simulation is already running",
                    "running": True,
                }
            
            # Just set running flag for now
            self.engine.running = True
            
            logger.info("Simulation started")
            
            return {
                "success": True,
                "message": "Simulation started successfully",
                "running": True,
                "meters_count": len(self.engine.meters),
            }
            
        except Exception as e:
            logger.error(f"Error starting simulation: {e}")
            raise SimulationError(f"Failed to start simulation: {str(e)}")
    
    def stop_simulation(self) -> Dict[str, Any]:
        """Stop simulation."""
        try:
            if not self.is_running():
                return {
                    "success": False,
                    "message": "Simulation is not running",
                    "running": False,
                }
            
            # Stop the simulation
            self.engine.running = False
            
            logger.info("Simulation stopped")
            
            return {
                "success": True,
                "message": "Simulation stopped successfully",
                "running": False,
            }
            
        except Exception as e:
            logger.error(f"Error stopping simulation: {e}")
            raise SimulationError(f"Failed to stop simulation: {str(e)}")
    
    def pause_simulation(self) -> Dict[str, Any]:
        """Pause simulation."""
        try:
            if not self.is_running():
                return {
                    "success": False,
                    "message": "Simulation is not running",
                    "running": False,
                }
            
            # Pause the simulation
            self.engine.paused = True
            
            logger.info("Simulation paused")
            
            return {
                "success": True,
                "message": "Simulation paused successfully",
                "running": True,
                "paused": True,
            }
            
        except Exception as e:
            logger.error(f"Error pausing simulation: {e}")
            raise SimulationError(f"Failed to pause simulation: {str(e)}")
    
    def resume_simulation(self) -> Dict[str, Any]:
        """Resume simulation."""
        try:
            if not self.is_paused():
                return {
                    "success": False,
                    "message": "Simulation is not paused",
                    "running": self.is_running(),
                }
            
            # Resume the simulation
            self.engine.paused = False
            
            logger.info("Simulation resumed")
            
            return {
                "success": True,
                "message": "Simulation resumed successfully",
                "running": True,
                "paused": False,
            }
            
        except Exception as e:
            logger.error(f"Error resuming simulation: {e}")
            raise SimulationError(f"Failed to resume simulation: {str(e)}")
    
    def get_simulation_status(self) -> Dict[str, Any]:
        """Get current simulation status."""
        try:
            # Count connected meters
            connected_count = sum(
                1 for meter in self.engine.meters 
                if getattr(meter, "is_connected", False)
            )
            
            return {
                "status": "running" if self.engine.running else "stopped",
                "running": self.engine.running,
                "paused": getattr(self.engine, "paused", False),
                "meters_count": len(self.engine.meters),
                "connected_meters": connected_count,
                "disconnected_meters": len(self.engine.meters) - connected_count,
                "mode": "Simulation",
            }
            
        except Exception as e:
            logger.error(f"Error getting simulation status: {e}")
            raise SimulationError(f"Failed to get simulation status: {str(e)}")
    
    def get_simulation_stats(self) -> Dict[str, Any]:
        """Get detailed simulation statistics."""
        try:
            # Basic stats
            stats = {
                "meters_count": len(self.engine.meters),
                "running": self.is_running(),
                "paused": self.is_paused(),
            }
            
            # Meter type distribution
            meter_types = {}
            for meter in self.engine.meters:
                meter_type = meter.config.get("meter_type", "Unknown")
                meter_types[meter_type] = meter_types.get(meter_type, 0) + 1
            stats["meter_types"] = meter_types
            
            # Connection status
            connected = sum(1 for meter in self.engine.meters 
                         if getattr(meter, 'is_connected', False))
            stats["connected_meters"] = connected
            stats["disconnected_meters"] = len(self.engine.meters) - connected
            
            # Energy statistics (if available)
            total_generated = 0
            total_consumed = 0
            total_battery = 0
            
            for meter in self.engine.meters:
                if hasattr(meter, 'battery_level'):
                    total_battery += meter.battery_level
                
                if hasattr(meter, 'last_reading') and meter.last_reading:
                    if hasattr(meter.last_reading, 'energy_generated'):
                        total_generated += meter.last_reading.energy_generated
                    if hasattr(meter.last_reading, 'energy_consumed'):
                        total_consumed += meter.last_reading.energy_consumed
            
            stats["energy"] = {
                "total_generated": round(total_generated, 4),
                "total_consumed": round(total_consumed, 4),
                "net_energy": round(total_generated - total_consumed, 4),
                "average_battery_level": round(total_battery / len(self.engine.meters), 2) if self.engine.meters else 0,
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting simulation stats: {e}")
            raise SimulationError(f"Failed to get simulation stats: {str(e)}")
    
    def is_running(self) -> bool:
        """Check if simulation is running."""
        return getattr(self.engine, 'running', False)
    
    def is_paused(self) -> bool:
        """Check if simulation is paused."""
        return getattr(self.engine, 'paused', False)
