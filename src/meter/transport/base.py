from abc import ABC, abstractmethod
from typing import Any, Dict
from ..models.reading import EnergyReading

class TransportLayer(ABC):
    """
    Abstract base class for transport layers (HTTP, WebSocket, MQTT).
    """
    
    @abstractmethod
    async def connect(self) -> bool:
        """Establish connection to the server."""
        pass
        
    @abstractmethod
    async def disconnect(self) -> bool:
        """Close connection to the server."""
        pass
        
    @abstractmethod
    async def send_reading(self, reading: EnergyReading) -> bool:
        """Send a single meter reading."""
        pass
        
    @abstractmethod
    async def send_batch(self, readings: list[EnergyReading]) -> bool:
        """Send a batch of meter readings."""
        pass

    @abstractmethod
    async def send_grid_status(self, status: Dict[str, Any]) -> bool:
        """Send grid estimation status."""
        pass

    @abstractmethod
    async def send_auction_bid(self, bid_payload: Dict[str, Any], batch_id: str) -> bool:
        """Send an encrypted auction bid."""
        pass

    @abstractmethod
    def is_connected(self) -> bool:
        """Check if the transport is currently connected."""
        pass
