import logging
import aiohttp
import asyncio
from typing import Optional
from .base import TransportLayer
from ..models.reading import EnergyReading
from ..config import SimulatorConfig

logger = logging.getLogger(__name__)


class HttpTransport(TransportLayer):
    """
    HTTP implementation of TransportLayer using aiohttp.
    Sends readings to the API Gateway via REST endpoints.
    
    Supports two payload modes:
    - 'monitoring': Optimized for real-time grid monitoring (default)
    - 'full': Complete telemetry for detailed analysis
    """

    def __init__(
        self,
        base_url: str,
        api_key: Optional[str] = None,
        payload_mode: str = 'monitoring',  # 'monitoring' or 'full'
        batch_size: int = 10,  # Batch readings for efficiency
    ):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.payload_mode = payload_mode
        self.batch_size = batch_size
        self.session: Optional[aiohttp.ClientSession] = None
        
        # Statistics
        self.stats = {
            'sent': 0,
            'failed': 0,
            'bytes_sent': 0,
            'batch_sent': 0,
        }

    async def connect(self) -> bool:
        """Initialize aiohttp session."""
        if not self.session:
            headers = {"Content-Type": "application/json"}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            self.session = aiohttp.ClientSession(headers=headers)
            logger.info(f"HTTP Transport connected to {self.base_url}")
        return True

    async def disconnect(self) -> bool:
        """Close aiohttp session."""
        if self.session:
            await self.session.close()
            self.session = None
            logger.info("HTTP Transport disconnected")
        return True

    async def send_reading(self, reading: EnergyReading) -> bool:
        """Send a single reading via POST /api/meters/submit-reading with retries."""
        if not self.session:
            await self.connect()

        max_retries = 3
        retry_delay = 2  # seconds

        # Select payload based on mode
        if self.payload_mode == 'full':
            payload = reading.to_full_telemetry_payload()
        else:
            payload = reading.to_grid_monitoring_payload()
            
        meter_id = payload.get("meter_serial")
        
        if not meter_id:
             logger.error("Missing meter_serial in payload")
             self.stats['failed'] += 1
             return False

        url = f"{self.base_url}/api/v1/meters/{meter_id}/readings"
        kwh_amount = float(payload.get("kwh", 0))
        
        # Skip zero readings in monitoring mode (optimization)
        if kwh_amount == 0 and self.payload_mode == 'monitoring':
            logger.debug(f"Skipping reading with zero net kWh (monitoring mode)")
            return True

        for attempt in range(max_retries):
            try:
                # Calculate payload size for statistics
                import json
                payload_bytes = len(json.dumps(payload).encode('utf-8'))
                
                logger.debug(f"Sending reading for {meter_id} ({self.payload_mode} mode, {payload_bytes} bytes)")
                async with self.session.post(url, json=payload, timeout=60) as response:
                    response_text = await response.text()
                    if response.status in (200, 201):
                        self.stats['sent'] += 1
                        self.stats['bytes_sent'] += payload_bytes
                        logger.info(f"✓ Sent {meter_id} ({payload_bytes}B, {self.payload_mode})")
                        if attempt > 0:
                            logger.info(f"Successfully sent reading after {attempt} retries")
                        return True
                    else:
                        logger.warning(
                            f"Attempt {attempt + 1} failed: {response.status} {response_text}"
                        )
                        if response.status >= 500:
                            # Server error, worth retrying
                            pass
                        else:
                            # Client error (4xx), don't retry
                            self.stats['failed'] += 1
                            return False
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1} error: {e}")
            
            if attempt < max_retries - 1:
                await asyncio.sleep(retry_delay * (2 ** attempt)) # Exponential backoff

        logger.error(f"Failed to send reading for {meter_id} after {max_retries} attempts")
        self.stats['failed'] += 1
        return False
    
    def get_transfer_stats(self) -> dict:
        """Get transfer statistics for monitoring."""
        return {
            'sent': self.stats['sent'],
            'failed': self.stats['failed'],
            'success_rate': f"{(self.stats['sent'] / max(1, self.stats['sent'] + self.stats['failed']) * 100):.1f}%",
            'total_bytes': self.stats['bytes_sent'],
            'avg_bytes_per_reading': self.stats['bytes_sent'] / max(1, self.stats['sent']),
            'payload_mode': self.payload_mode,
        }

    async def send_batch(self, readings: list[EnergyReading]) -> bool:
        """
        Send a batch of readings via POST /api/v1/meters/batch/readings.
        Falls back to sending individually if batch endpoint fails.
        """
        if not self.session:
            await self.connect()
        
        if not readings:
            return True

        # Try batch endpoint first - use public endpoint (no auth)
        batch_url = f"{self.base_url}/api/v1/public/meters/batch/readings"
        max_retries = 3
        retry_delay = 2
        
        payload = {
            "readings": [reading.to_submission_payload() for reading in readings]
        }
        
        for attempt in range(max_retries):
            try:
                # Longer timeout for batch operations
                async with self.session.post(batch_url, json=payload, timeout=120) as response:
                    response_text = await response.text()
                    
                    if response.status in (200, 201):
                        logger.info(f"Batch of {len(readings)} readings sent successfully")
                        return True
                    elif response.status == 404:
                        # Batch endpoint doesn't exist, fall back to individual sends
                        logger.warning("Batch endpoint not found, falling back to individual sends")
                        return await self._send_batch_individually(readings)
                    elif response.status >= 500:
                        logger.warning(f"Batch attempt {attempt+1} server error: {response.status}")
                    else:
                        # 4xx client error - don't retry
                        logger.warning(f"Batch failed with client error: {response.status} {response_text}")
                        return await self._send_batch_individually(readings)
                        
            except asyncio.TimeoutError:
                logger.warning(f"Batch attempt {attempt+1} timed out")
            except Exception as e:
                logger.warning(f"Batch attempt {attempt+1} error: {e}")
            
            if attempt < max_retries - 1:
                await asyncio.sleep(retry_delay * (2 ** attempt))
        
        # All retries failed, try individual sends as last resort
        logger.warning("Batch retries exhausted, falling back to individual sends")
        return await self._send_batch_individually(readings)
    
    async def _send_batch_individually(self, readings: list[EnergyReading]) -> bool:
        """Fallback: send batch readings individually with concurrency limit."""
        import asyncio
        
        semaphore = asyncio.Semaphore(10)  # Limit concurrent individual requests
        success_count = 0
        
        async def send_one(reading):
            nonlocal success_count
            async with semaphore:
                result = await self.send_reading(reading)
                if result:
                    success_count += 1
                return result
        
        await asyncio.gather(*[send_one(r) for r in readings], return_exceptions=True)
        
        # Consider success if majority succeeded
        success_rate = success_count / len(readings) if readings else 1.0
        logger.info(f"Individual fallback: {success_count}/{len(readings)} readings sent ({success_rate:.1%})")
        return success_rate > 0.5

