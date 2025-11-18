"""
WebSocket Server Module
Handles real-time broadcasting of meter readings to connected clients
"""

import asyncio
import json
import logging
import threading
from typing import Set

import websockets
from websockets.server import WebSocketServerProtocol

logger = logging.getLogger(__name__)


class WebSocketServer:
    """WebSocket server for broadcasting simulation data"""

    def __init__(self, host: str = 'localhost', port: int = 8765):
        self.host = host
        self.port = port
        self.clients: Set[WebSocketServerProtocol] = set()
        self.server = None
        self.loop = None
        self.thread = None

    async def register_client(self, websocket: WebSocketServerProtocol):
        """Register new client connection"""
        self.clients.add(websocket)
        logger.info(
            f"Client connected. Total clients: {len(self.clients)}"
        )

        try:
            await websocket.wait_closed()
        finally:
            self.clients.discard(websocket)
            logger.info(
                f"Client disconnected. Total clients: {len(self.clients)}"
            )

    async def broadcast_reading(self, reading: dict):
        """Broadcast single reading to all clients"""
        if not self.clients:
            return

        message = json.dumps(reading, default=str)
        disconnected = set()

        for client in self.clients:
            try:
                await client.send(message)
            except Exception as e:
                logger.debug(f"Error sending to client: {e}")
                disconnected.add(client)

        for client in disconnected:
            self.clients.discard(client)

    async def broadcast_batch(self, readings: list):
        """Broadcast batch of readings to all clients"""
        if not self.clients or not readings:
            return

        message = json.dumps(readings, default=str)
        disconnected = set()

        for client in self.clients:
            try:
                await client.send(message)
            except Exception as e:
                logger.debug(f"Error sending batch to client: {e}")
                disconnected.add(client)

        for client in disconnected:
            self.clients.discard(client)

    async def handler(self, websocket: WebSocketServerProtocol):
        """Handle incoming WebSocket connections"""
        await self.register_client(websocket)

    async def start_server(self):
        """Start the WebSocket server"""
        self.server = await websockets.serve(
            self.handler,
            self.host,
            self.port,
            ping_interval=20,
            ping_timeout=10,
        )
        logger.info(
            f"WebSocket server started on ws://{self.host}:{self.port}"
        )

    def run_server(self):
        """Run server in event loop"""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

        try:
            self.loop.run_until_complete(self.start_server())
            self.loop.run_forever()
        except Exception as e:
            logger.error(f"WebSocket server error: {e}")
        finally:
            self.loop.close()

    def start(self):
        """Start server in background thread"""
        self.thread = threading.Thread(
            target=self.run_server,
            daemon=True
        )
        self.thread.start()
        logger.info("WebSocket server thread started")

    def broadcast_reading_sync(self, reading: dict):
        """Thread-safe broadcast of single reading"""
        if not self.loop or not self.clients:
            return

        asyncio.run_coroutine_threadsafe(
            self.broadcast_reading(reading),
            self.loop
        )

    def broadcast_batch_sync(self, readings: list):
        """Thread-safe broadcast of batch readings"""
        if not self.loop or not self.clients or not readings:
            return

        asyncio.run_coroutine_threadsafe(
            self.broadcast_batch(readings),
            self.loop
        )

    def stop(self):
        """Stop the WebSocket server"""
        if self.loop:
            self.loop.call_soon_threadsafe(self.loop.stop)
        if self.thread:
            self.thread.join(timeout=5)
        logger.info("WebSocket server stopped")
