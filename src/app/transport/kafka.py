import json
import logging
from typing import Dict, Any, List
import asyncio
from aiokafka import AIOKafkaProducer
from .base import Transport

logger = logging.getLogger(__name__)

class KafkaTransport(Transport):
    """
    Kafka transport for real-time meter reading streaming.
    Uses aiokafka for asynchronous production.
    """
    
    def __init__(self, bootstrap_servers: str, topic: str = "meter_readings"):
        self.bootstrap_servers = bootstrap_servers
        self.topic = topic
        self.producer = None
        self._connected = False
        self._loop = None

    async def connect(self) -> bool:
        """Initialize the Kafka producer."""
        try:
            self._loop = asyncio.get_event_loop()
            self.producer = AIOKafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                loop=self._loop,
                value_serializer=lambda v: json.dumps(v).encode('utf-8')
            )
            await self.producer.start()
            self._connected = True
            logger.info(f"Kafka Transport connected to {self.bootstrap_servers}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect Kafka Transport: {e}")
            self._connected = False
            return False

    async def disconnect(self) -> bool:
        """Shutdown the Kafka producer."""
        if self.producer:
            await self.producer.stop()
            self._connected = False
            logger.info("Kafka Transport disconnected")
            return True
        return False

    async def send_reading(self, reading: Any) -> bool:
        """Send a single meter reading to Kafka."""
        if not self._connected:
            return False
            
        try:
            # Convert to dict if it's a Pydantic model
            payload = reading.dict() if hasattr(reading, "dict") else reading
            await self.producer.send_and_wait(self.topic, payload)
            return True
        except Exception as e:
            logger.error(f"Error sending reading to Kafka: {e}")
            return False

    async def send_batch(self, readings: List[Any]) -> bool:
        """Send a batch of readings to Kafka."""
        if not self._connected:
            return False
            
        try:
            # We can use the producer's internal buffering or send individually
            # For simplicity and immediate durability, we send_and_wait in a gathering
            tasks = []
            for reading in readings:
                payload = reading.dict() if hasattr(reading, "dict") else reading
                tasks.append(self.producer.send(self.topic, payload))
            
            await asyncio.gather(*tasks)
            return True
        except Exception as e:
            logger.error(f"Error sending batch to Kafka: {e}")
            return False

    def is_connected(self) -> bool:
        return self._connected
