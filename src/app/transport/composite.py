"""
Composite transport layer that can send data via multiple transport mechanisms.
Supports both HTTP (to external API) and WebSocket (to dashboard) simultaneously.
"""

import logging
from typing import List
from .base import TransportLayer
from ..models.reading import EnergyReading

logger = logging.getLogger(__name__)

class CompositeTransport(TransportLayer):
    """
    Composite transport that sends data through multiple underlying transports.
    This allows sending data to both an external API via HTTP and to the dashboard via WebSocket.
    """
    
    def __init__(self, transports: List[TransportLayer]):
        self.transports = transports
    
    async def connect(self) -> bool:
        """Connect all underlying transports."""
        success_count = 0
        for i, transport in enumerate(self.transports):
            try:
                result = await transport.connect()
                if result:
                    success_count += 1
                    logger.info(f"Transport {i} connected successfully")
                else:
                    logger.warning(f"Transport {i} failed to connect")
            except Exception as e:
                logger.error(f"Error connecting transport {i}: {e}")
        
        logger.info(f"Connected {success_count}/{len(self.transports)} transports")
        return success_count > 0
    
    async def disconnect(self) -> bool:
        """Disconnect all underlying transports."""
        success_count = 0
        for i, transport in enumerate(self.transports):
            try:
                result = await transport.disconnect()
                if result:
                    success_count += 1
                    logger.info(f"Transport {i} disconnected successfully")
                else:
                    logger.warning(f"Transport {i} failed to disconnect")
            except Exception as e:
                logger.error(f"Error disconnecting transport {i}: {e}")
        
        logger.info(f"Disconnected {success_count}/{len(self.transports)} transports")
        return success_count > 0
    
    async def send_reading(self, reading: EnergyReading) -> bool:
        """Send a reading through all transports."""
        success_count = 0
        for i, transport in enumerate(self.transports):
            try:
                result = await transport.send_reading(reading)
                if result:
                    success_count += 1
                else:
                    logger.warning(f"Failed to send reading via transport {i}")
            except Exception as e:
                logger.error(f"Error sending reading via transport {i}: {e}")
        
        # Consider it successful if at least one transport succeeds
        return success_count > 0
    
    async def send_batch(self, readings: List[EnergyReading]) -> bool:
        """Send a batch of readings through all transports."""
        success_count = 0
        for i, transport in enumerate(self.transports):
            try:
                result = await transport.send_batch(readings)
                if result:
                    success_count += 1
                else:
                    logger.warning(f"Failed to send batch via transport {i}")
            except Exception as e:
                logger.error(f"Error sending batch via transport {i}: {e}")
        
        # Consider it successful if at least one transport succeeds
        return success_count > 0
