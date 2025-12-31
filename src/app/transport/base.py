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
