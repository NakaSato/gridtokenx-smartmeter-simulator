"""
Enhanced Transport Layer Base Class
Provides common functionality for all transport implementations.
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from ..models.reading import EnergyReading

logger = logging.getLogger(__name__)


class TransportLayer(ABC):
    """
    Abstract base class for transport layers (HTTP, WebSocket, MQTT, Kafka, InfluxDB).
    Provides common connection management and retry logic.
    """

    # Default retry configuration
    DEFAULT_MAX_RETRIES = 3
    DEFAULT_RETRY_BACKOFF = 1.0  # seconds

    def __init__(
        self,
        max_retries: int = DEFAULT_MAX_RETRIES,
        retry_backoff: float = DEFAULT_RETRY_BACKOFF
    ):
        self._connected = False
        self._max_retries = max_retries
        self._retry_backoff = retry_backoff

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
    async def send_batch(self, readings: List[EnergyReading]) -> bool:
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
    async def send_alert(self, alert: Dict[str, Any]) -> bool:
        """Send a critical alert."""
        pass

    @abstractmethod
    def is_connected(self) -> bool:
        """Check if the transport is currently connected."""
        pass

    def _convert_reading_to_dict(self, reading: Any) -> Dict[str, Any]:
        """Convert reading to dictionary (handles Pydantic models)."""
        if hasattr(reading, 'dict'):
            return reading.dict()
        elif hasattr(reading, 'model_dump'):
            return reading.model_dump()
        return reading

    async def _retry_operation(
        self,
        operation,
        operation_name: str = "operation",
        max_retries: Optional[int] = None,
        backoff: Optional[float] = None
    ) -> bool:
        """
        Retry an async operation with exponential backoff.

        Args:
            operation: Async callable to execute
            operation_name: Name for logging purposes
            max_retries: Override default max retries
            backoff: Override default backoff seconds

        Returns:
            True if operation succeeded, False if all retries failed
        """
        retries = max_retries or self._max_retries
        retry_delay = backoff or self._retry_backoff

        for attempt in range(1, retries + 1):
            try:
                result = await operation()
                if result:
                    return True
            except asyncio.TimeoutError:
                logger.warning(f"{operation_name} timeout (attempt {attempt}/{retries})")
            except Exception as e:
                logger.warning(f"{operation_name} failed (attempt {attempt}/{retries}): {e}")

            if attempt < retries:
                await asyncio.sleep(retry_delay * attempt)

        logger.error(f"{operation_name} failed after {retries} attempts")
        return False

    def _set_connected(self, connected: bool) -> None:
        """Set connection state."""
        self._connected = connected

    @property
    def connected(self) -> bool:
        """Property to check connection state."""
        return self._connected
