"""
MQTT Transport Layer for real-world AMI ingestion.
Uses aiomqtt for high-performance asynchronous delivery.
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

import aiomqtt
from ..config import get_config
from ..models.reading import EnergyReading
from .base import TransportLayer

logger = logging.getLogger(__name__)

class MqttTransport(TransportLayer):
    """
    MQTT implementation of TransportLayer.
    Standard for industrial IoT and AMI Head-End Systems.
    """

    def __init__(
        self,
        broker_url: Optional[str] = None,
        port: int = 1883,
        username: Optional[str] = None,
        password: Optional[str] = None,
        base_topic: str = "gridtokenx/ami/telemetry",
        max_retries: int = 3,
        retry_backoff: float = 1.0
    ):
        super().__init__(max_retries=max_retries, retry_backoff=retry_backoff)
        self._config = get_config()
        
        # Use config if not provided
        self.broker_url = broker_url or getattr(self._config, 'mqtt_broker_url', 'localhost')
        self.port = port or getattr(self._config, 'mqtt_port', 1883)
        self.username = username or getattr(self._config, 'mqtt_username', None)
        self.password = password or getattr(self._config, 'mqtt_password', None)
        self.base_topic = base_topic
        
        self.client: Optional[aiomqtt.Client] = None
        self._loop_task: Optional[asyncio.Task] = None
        self._connected_event = asyncio.Event()

    async def connect(self) -> bool:
        """Initialize MQTT client and wait for connection."""
        if self._connected:
            return True
            
        try:
            if not self.client:
                self.client = aiomqtt.Client(
                    hostname=self.broker_url,
                    port=self.port,
                    username=self.username,
                    password=self.password
                )
            
            # Start the background loop if not already running
            if not self._loop_task or self._loop_task.done():
                self._connected_event.clear()
                self._loop_task = asyncio.create_task(self._mqtt_loop())
            
            # Wait for the handshake to complete (timeout after 10s)
            try:
                await asyncio.wait_for(self._connected_event.wait(), timeout=10.0)
                logger.info(f"MQTT Transport successfully connected to {self.broker_url}:{self.port}")
                return True
            except asyncio.TimeoutError:
                logger.error("Timeout waiting for MQTT connection handshake")
                return False
                
        except Exception as e:
            logger.error(f"Failed to connect MQTT Transport: {e}")
            return False

    async def _mqtt_loop(self):
        """Background task to keep the MQTT connection alive."""
        while True:
            try:
                async with self.client:
                    self._set_connected(True)
                    self._connected_event.set()
                    # Keep loop alive while the client context is active
                    while self._connected:
                        await asyncio.sleep(0.5)
            except (aiomqtt.MqttError, Exception) as e:
                logger.warning(f"MQTT Connection lost or failed: {e}. Retrying in 5s...")
                self._set_connected(False)
                self._connected_event.clear()
                await asyncio.sleep(5)
            except asyncio.CancelledError:
                break

    async def disconnect(self) -> bool:
        """Close MQTT client and stop background loop."""
        self._set_connected(False)
        self._connected_event.clear()
        if self._loop_task:
            self._loop_task.cancel()
            try:
                await self._loop_task
            except asyncio.CancelledError:
                pass
            self._loop_task = None
        self.client = None
        logger.info("MQTT Transport disconnected")
        return True

    async def send_reading(self, reading: EnergyReading) -> bool:
        """
        Send a single reading via MQTT.
        Sends both a JSON version and the 'Real World' DLMS binary hex.
        """
        if not self.client:
            await self.connect()

        topic = f"{self.base_topic}/{reading.meter_id}"
        
        # 1. Prepare JSON payload
        payload_data = reading.to_submission_payload()
        
        # 2. Add 'Real World' DLMS Hex
        dlms_bin = reading.generate_dlms_payload()
        from ..core.dlms import DlmsEncoder
        payload_data["dlms_hex"] = DlmsEncoder.to_hex(dlms_bin)
        
        payload_json = json.dumps(payload_data)

        async def _publish():
            try:
                # Publish JSON to main topic
                await self.client.publish(topic, payload_json, qos=1)
                
                # Also publish RAW binary to industrial sub-topic for authentic ingestion
                binary_topic = f"{topic}/raw"
                await self.client.publish(binary_topic, dlms_bin, qos=1)
                
                logger.debug(f"MQTT Reading published to {topic}")
                return True
            except Exception as e:
                logger.warning(f"MQTT publish failed: {e}")
                return False

        return await self._retry_operation(_publish, operation_name=f"MQTT publish to {topic}")

    async def send_batch(self, readings: List[EnergyReading]) -> bool:
        """Send a batch of readings (Iterative publish for MQTT)."""
        tasks = [self.send_reading(r) for r in readings]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return all(r is True for r in results)

    async def send_grid_status(self, status: Dict[str, Any]) -> bool:
        """Send grid status to monitoring topic."""
        if not self.client: return True
        topic = "gridtokenx/ami/grid/status"
        try:
            await self.client.publish(topic, json.dumps(status), qos=1)
            return True
        except: return False

    async def send_alert(self, alert: Dict[str, Any]) -> bool:
        """Send alert to critical topic."""
        if not self.client: return True
        topic = "gridtokenx/ami/alerts"
        try:
            await self.client.publish(topic, json.dumps(alert), qos=2)
            return True
        except: return False

    def is_connected(self) -> bool:
        return self._connected
