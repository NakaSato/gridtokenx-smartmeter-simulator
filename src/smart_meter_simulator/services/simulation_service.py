"""
Simulation service for managing smart meter simulation.
"""

import asyncio
import logging
from typing import Dict, Any, Optional

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
        self._task: Optional[asyncio.Task] = None
        logger.info("SimulationService initialized")

    def start_simulation(self) -> Dict[str, Any]:
        """Start simulation."""
        try:
            if self.is_running():
                # Already running - return success (idempotent)
                return {
                    "success": True,
                    "message": "Simulation is already running",
                    "running": True,
                    "meters_count": len(self.engine.meters),
                }

            # Start the engine in a background task
            self._task = asyncio.create_task(self.engine.start())

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

            # Stop the simulation engine (it will break its loop)
            # We need to call stop() on the engine which sets running=False
            # But since engine.start() is running in a loop checking self.running,
            # we can just set the flag or call a stop method if exposed.
            # The engine has a stop() method which is async.

            # We can't await engine.stop() easily here if we want to be synchronous-ish
            # or we can create a task to stop it.
            # Ideally we should await it. Since this method is not async in the interface shown (it lacks async def in my view but likely called from async context),
            # wait, the file content shows `def stop_simulation(self)` not `async def`.
            # However, the router calls it with `await`? No, the router is async but calls this synchronously?
            # Let's check api/simulation.py again.
            # It calls `return sim_service.stop_simulation()`. It doesn't await it.
            # But `engine.stop()` is `async def`.
            # So `SimulationService` methods should probably be `async` or manage tasks.
            # Given the existing code structure, `engine.running = False` is what was there.
            # `engine.stop()` sets running=False and disconnects transport.

            # Let's use a fire-and-forget task to call engine.stop() properly
            asyncio.create_task(self.engine.stop())

            if self._task:
                self._task.cancel()
                self._task = None

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
                1
                for meter in self.engine.meters
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
            connected = sum(
                1
                for meter in self.engine.meters
                if getattr(meter, "is_connected", False)
            )
            stats["connected_meters"] = connected
            stats["disconnected_meters"] = len(self.engine.meters) - connected

            # Energy statistics (if available)
            total_generated = 0
            total_consumed = 0
            total_battery = 0

            for meter in self.engine.meters:
                if hasattr(meter, "battery_level"):
                    total_battery += meter.battery_level

                if hasattr(meter, "last_reading") and meter.last_reading:
                    if hasattr(meter.last_reading, "energy_generated"):
                        total_generated += meter.last_reading.energy_generated
                    if hasattr(meter.last_reading, "energy_consumed"):
                        total_consumed += meter.last_reading.energy_consumed

            stats["energy"] = {
                "total_generated": round(total_generated, 4),
                "total_consumed": round(total_consumed, 4),
                "net_energy": round(total_generated - total_consumed, 4),
                "average_battery_level": round(
                    total_battery / len(self.engine.meters), 2
                )
                if self.engine.meters
                else 0,
            }

            return stats

        except Exception as e:
            logger.error(f"Error getting simulation stats: {e}")
            raise SimulationError(f"Failed to get simulation stats: {str(e)}")

    def is_running(self) -> bool:
        """Check if simulation is running."""
        return getattr(self.engine, "running", False)

    def is_paused(self) -> bool:
        """Check if simulation is paused."""
        return getattr(self.engine, "paused", False)
