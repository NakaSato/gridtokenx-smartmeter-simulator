"""
Null transport implementation for testing and fallback.
"""

import logging
from typing import List, Dict, Any, Optional

from .base import TransportLayer
from ..models.reading import EnergyReading

logger = logging.getLogger(__name__)


class NullTransport(TransportLayer):
    """Null transport that does nothing - useful for testing."""
    
    def __init__(self):
        """Initialize null transport."""
        self.connected = False
    
    async def start(self) -> bool:
        """Start transport (no-op for null transport)."""
        logger.debug("Null transport started")
        self.connected = True
        return True
    
    async def stop(self) -> bool:
        """Stop transport (no-op for null transport)."""
        logger.debug("Null transport stopped")
        self.connected = False
        return True
    
    async def connect(self) -> bool:
        """Connect transport (no-op for null transport)."""
        logger.debug("Null transport connected")
        self.connected = True
        return True
    
    async def disconnect(self) -> bool:
        """Disconnect transport (no-op for null transport)."""
        logger.debug("Null transport disconnected")
        self.connected = False
        return True
    
    async def send_readings(self, readings: List[Dict[str, Any]]) -> bool:
        """Send readings (no-op for null transport)."""
        logger.debug(f"Null transport: {len(readings)} readings discarded")
        return True
    
    async def send_status(self, status: Dict[str, Any]) -> bool:
        """Send status (no-op for null transport)."""
        logger.debug("Null transport: status discarded")
        return True
    
    async def send_reading(self, reading: EnergyReading) -> bool:
        """Send single reading (no-op for null transport)."""
        logger.debug("Null transport: reading discarded")
        return True
    
    async def send_batch(self, readings: list[EnergyReading]) -> bool:
        """Send batch of readings (no-op for null transport)."""
        logger.debug(f"Null transport: {len(readings)} readings discarded")
        return True
    
    def is_connected(self) -> bool:
        """Check if transport is connected."""
        return self.connected
    
    def get_status(self) -> Dict[str, Any]:
        """Get transport status."""
        return {
            "type": "null",
            "connected": self.connected,
            "description": "Null transport - discards all data"
        }
