"""
Kafka transport layer for high-throughput meter event streaming.
Uses kafka-python for producing meter readings to Kafka topics.
"""

import json
import logging
import asyncio
from typing import Optional
from kafka import KafkaProducer
from kafka.errors import KafkaError, NoBrokersAvailable

from .base import TransportLayer
from ..models.reading import EnergyReading
from ..config.constants import SimulatorConfig

logger = logging.getLogger(__name__)


class KafkaTransport(TransportLayer):
    """
    Kafka implementation of TransportLayer using kafka-python.
    Publishes meter readings to a Kafka topic for high-throughput streaming.
    """

    def __init__(
        self,
        bootstrap_servers: str = None,
        topic: str = None,
        client_id: str = "smartmeter-simulator",
        acks: str = "all",  # 'all' for durability, 1 for latency
        batch_size: int = 16384,  # 16KB batch size
        linger_ms: int = 10,  # Wait up to 10ms for batching
        compression_type: str = "gzip",  # Compress for efficiency
    ):
        self.bootstrap_servers = bootstrap_servers or SimulatorConfig.KAFKA_SERVERS
        self.topic = topic or getattr(SimulatorConfig, "KAFKA_TOPIC", "meter-readings")
        self.client_id = client_id
        self.acks = acks
        self.batch_size = batch_size
        self.linger_ms = linger_ms
        self.compression_type = compression_type
        
        self.producer: Optional[KafkaProducer] = None
        self._connected = False
        
        # Statistics
        self.stats = {
            "sent": 0,
            "failed": 0,
            "bytes_sent": 0,
        }

    async def connect(self) -> bool:
        """Initialize Kafka producer connection."""
        if self._connected and self.producer:
            return True
        
        try:
            # Run producer initialization in thread pool (kafka-python is sync)
            loop = asyncio.get_event_loop()
            self.producer = await loop.run_in_executor(
                None,
                self._create_producer
            )
            self._connected = True
            logger.info(
                f"✅ Kafka Transport connected to {self.bootstrap_servers}, "
                f"topic: {self.topic}"
            )
            return True
        except NoBrokersAvailable as e:
            logger.error(f"❌ Kafka brokers unavailable: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Failed to connect to Kafka: {e}")
            return False

    def _create_producer(self) -> KafkaProducer:
        """Create Kafka producer (sync, run in thread pool)."""
        return KafkaProducer(
            bootstrap_servers=self.bootstrap_servers.split(","),
            client_id=self.client_id,
            acks=self.acks,
            batch_size=self.batch_size,
            linger_ms=self.linger_ms,
            compression_type=self.compression_type,
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
            key_serializer=lambda k: k.encode("utf-8") if k else None,
            retries=3,
            retry_backoff_ms=100,
        )

    async def disconnect(self) -> bool:
        """Close Kafka producer connection."""
        if self.producer:
            try:
                loop = asyncio.get_event_loop()
                # Flush and close producer
                await loop.run_in_executor(None, self.producer.flush)
                await loop.run_in_executor(None, self.producer.close)
                self.producer = None
                self._connected = False
                logger.info("🔌 Kafka Transport disconnected")
                return True
            except Exception as e:
                logger.error(f"Error closing Kafka producer: {e}")
                return False
        return True

    async def send_reading(self, reading: EnergyReading) -> bool:
        """Send a single meter reading to Kafka topic."""
        if not self._connected or not self.producer:
            connected = await self.connect()
            if not connected:
                self.stats["failed"] += 1
                return False

        try:
            # Convert reading to payload
            payload = reading.to_grid_monitoring_payload()
            meter_id = payload.get("meter_serial", "unknown")
            
            # Serialize payload to measure size
            payload_bytes = len(json.dumps(payload).encode("utf-8"))
            
            # Send to Kafka (async via callback)
            loop = asyncio.get_event_loop()
            future = await loop.run_in_executor(
                None,
                lambda: self.producer.send(
                    self.topic,
                    key=meter_id,
                    value=payload,
                )
            )
            
            # Wait for send to complete
            await loop.run_in_executor(None, future.get, 10)  # 10s timeout
            
            self.stats["sent"] += 1
            self.stats["bytes_sent"] += payload_bytes
            logger.debug(f"📤 Sent {meter_id} to Kafka ({payload_bytes}B)")
            return True
            
        except KafkaError as e:
            logger.error(f"❌ Kafka send error: {e}")
            self.stats["failed"] += 1
            return False
        except Exception as e:
            logger.error(f"❌ Failed to send reading to Kafka: {e}")
            self.stats["failed"] += 1
            return False

    async def send_batch(self, readings: list[EnergyReading]) -> bool:
        """Send a batch of readings to Kafka topic (optimized for throughput)."""
        if not readings:
            return True
            
        if not self._connected or not self.producer:
            connected = await self.connect()
            if not connected:
                self.stats["failed"] += len(readings)
                return False

        try:
            loop = asyncio.get_event_loop()
            futures = []
            total_bytes = 0
            
            for reading in readings:
                payload = reading.to_grid_monitoring_payload()
                meter_id = payload.get("meter_serial", "unknown")
                payload_bytes = len(json.dumps(payload).encode("utf-8"))
                total_bytes += payload_bytes
                
                # Send async
                future = await loop.run_in_executor(
                    None,
                    lambda p=payload, k=meter_id: self.producer.send(
                        self.topic,
                        key=k,
                        value=p,
                    )
                )
                futures.append(future)
            
            # Flush to ensure all messages are sent
            await loop.run_in_executor(None, self.producer.flush)
            
            # Wait for all futures
            success_count = 0
            for future in futures:
                try:
                    await loop.run_in_executor(None, future.get, 10)
                    success_count += 1
                except Exception as e:
                    logger.warning(f"Batch item failed: {e}")
            
            self.stats["sent"] += success_count
            self.stats["failed"] += len(readings) - success_count
            self.stats["bytes_sent"] += total_bytes
            
            logger.info(
                f"📤 Kafka batch: {success_count}/{len(readings)} sent, "
                f"{total_bytes}B total"
            )
            return success_count > len(readings) / 2  # Success if majority sent
            
        except Exception as e:
            logger.error(f"❌ Kafka batch error: {e}")
            self.stats["failed"] += len(readings)
            return False

    def get_stats(self) -> dict:
        """Get transport statistics."""
        total = self.stats["sent"] + self.stats["failed"]
        return {
            "sent": self.stats["sent"],
            "failed": self.stats["failed"],
            "success_rate": f"{(self.stats['sent'] / max(1, total)) * 100:.1f}%",
            "bytes_sent": self.stats["bytes_sent"],
            "topic": self.topic,
            "bootstrap_servers": self.bootstrap_servers,
        }
