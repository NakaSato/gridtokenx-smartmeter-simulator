"""
WebSocket implementation of TransportLayer for real-time data streaming.
Handles broadcasting meter readings to connected WebSocket clients.
"""

import asyncio
import json
import logging
from typing import Set, List, Dict, Any
from fastapi import WebSocket
from .base import TransportLayer
from ..models.reading import EnergyReading

logger = logging.getLogger(__name__)


class WebSocketManager:
    """Manages WebSocket connections and broadcasting."""

    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket):
        """Accept a new WebSocket connection."""
        await websocket.accept()
        async with self._lock:
            self.active_connections.add(websocket)
        logger.info(
            f"WebSocket connected. Total connections: {len(self.active_connections)}"
        )

    async def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection."""
        async with self._lock:
            self.active_connections.discard(websocket)
        logger.info(
            f"WebSocket disconnected. Total connections: {len(self.active_connections)}"
        )

    async def broadcast(self, message: dict):
        """Broadcast a message to all connected clients."""
        if not self.active_connections:
            return

        disconnected = []
        # Use jsonable_encoder to handle numpy types and NaN/Inf before serialization
        from fastapi.encoders import jsonable_encoder

        json_data = jsonable_encoder(message)
        message_str = json.dumps(json_data)

        async with self._lock:
            for connection in self.active_connections.copy():
                try:
                    await connection.send_text(message_str)
                except Exception as e:
                    logger.warning(f"Failed to send to WebSocket: {e}")
                    disconnected.append(connection)

        # Clean up disconnected connections
        for conn in disconnected:
            await self.disconnect(conn)

    async def broadcast_readings(self, readings: List[EnergyReading]):
        """Broadcast meter readings to all connected clients."""
        if not readings:
            return

        message = {
            "type": "meter_readings",
            "timestamp": readings[0].timestamp.isoformat() if readings else None,
            "readings": [reading.dict() for reading in readings],
        }

        await self.broadcast(message)

    def get_connection_count(self) -> int:
        """Get the number of active connections."""
        return len(self.active_connections)


class WebSocketTransport(TransportLayer):
    """
    WebSocket implementation of TransportLayer.
    Broadcasts readings to connected WebSocket clients.
    """

    def __init__(self, manager: WebSocketManager):
        self.manager = manager
        self._connected = False

    async def connect(self) -> bool:
        """Initialize WebSocket transport."""
        self._connected = True
        logger.info("WebSocket Transport initialized")
        return True

    async def disconnect(self) -> bool:
        """Disconnect WebSocket transport."""
        self._connected = False
        logger.info("WebSocket Transport disconnected")
        return True

    async def send_reading(self, reading: EnergyReading) -> bool:
        """Send a single reading via WebSocket broadcast."""
        if not self._connected:
            return False

        try:
            message = {
                "type": "meter_reading",
                "timestamp": reading.timestamp.isoformat(),
                "reading": reading.dict(),
            }
            await self.manager.broadcast(message)
            return True
        except Exception as e:
            logger.error(f"Error sending reading via WebSocket: {e}")
            return False

    async def send_batch(self, readings: List[EnergyReading]) -> bool:
        """Send a batch of readings via WebSocket broadcast."""
        if not self._connected:
            return False

        try:
            await self.manager.broadcast_readings(readings)
            return True
        except Exception as e:
            logger.error(f"Error sending batch via WebSocket: {e}")
            return False

    async def send_grid_status(self, results: dict) -> bool:
        """Send grid estimation results via WebSocket broadcast."""
        if not self._connected:
            return False

        try:
            message = {
                "type": "grid_status",
                "timestamp": results.get("timestamp", None),
                "data": results,
            }
            await self.manager.broadcast(message)
            return True
        except Exception as e:
            logger.error(f"Error sending grid status via WebSocket: {e}")
            return False

    async def send_alert(self, alert: Dict[str, Any]) -> bool:
        """Send an alert via WebSocket broadcast."""
        if not self._connected:
            return False

        try:
            message = {
                "type": "alert",
                "timestamp": alert.get("timestamp", None),
                "data": alert,
            }
            await self.manager.broadcast(message)
            return True
        except Exception as e:
            logger.error(f"Error sending alert via WebSocket: {e}")
            return False

    def is_connected(self) -> bool:
        return self._connected
