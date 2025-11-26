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
    """
    
    def __init__(self, base_url: str = SimulatorConfig.API_GATEWAY_URL, api_key: Optional[str] = None):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.session: Optional[aiohttp.ClientSession] = None
        
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
        """Send a single reading via POST /api/meters/submit-reading."""
        if not self.session:
            await self.connect()
            
        url = f"{self.base_url}{SimulatorConfig.SUBMIT_READING_ENDPOINT}"
        try:
            payload = reading.to_submission_payload()
            async with self.session.post(url, json=payload) as response:
                if response.status in (200, 201):
                    logger.debug(f"Reading sent successfully: {payload['reading_timestamp']}")
                    return True
                else:
                    logger.warning(f"Failed to send reading: {response.status} {await response.text()}")
                    return False
        except Exception as e:
            logger.error(f"Error sending reading: {e}")
            return False
            
    async def send_batch(self, readings: list[EnergyReading]) -> bool:
        """Send a batch of readings via POST /api/meters/submit-batch."""
        if not self.session:
            await self.connect()
            
        url = f"{self.base_url}{SimulatorConfig.SUBMIT_BATCH_ENDPOINT}"
        try:
            payload = {
                "readings": [reading.to_submission_payload() for reading in readings]
            }
            async with self.session.post(url, json=payload) as response:
                if response.status in (200, 201):
                    logger.info(f"Batch of {len(readings)} readings sent successfully")
                    return True
                else:
                    logger.warning(f"Failed to send batch: {response.status} {await response.text()}")
                    return False
        except Exception as e:
            logger.error(f"Error sending batch: {e}")
            return False
