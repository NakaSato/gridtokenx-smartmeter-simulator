import logging
import aiohttp
import asyncio
from typing import Any, Dict, Optional
from .base import TransportLayer
from ..models.reading import EnergyReading
from ..config import SimulatorConfig

logger = logging.getLogger(__name__)

class HttpTransport(TransportLayer):
    """
    HTTP implementation of TransportLayer using aiohttp.
    Sends readings to the API Gateway via REST endpoints.
    """
    
    MAX_RETRIES = 3
    RETRY_BACKOFF = 1.0  # seconds
    REQUEST_TIMEOUT = 10  # seconds

    def __init__(self, base_url: str = SimulatorConfig.API_GATEWAY_URL, api_key: Optional[str] = None):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.session: Optional[aiohttp.ClientSession] = None
        
    async def connect(self) -> bool:
        """Initialize aiohttp session with timeout."""
        if not self.session:
            timeout = aiohttp.ClientTimeout(total=self.REQUEST_TIMEOUT)
            headers = {"Content-Type": "application/json"}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            self.session = aiohttp.ClientSession(headers=headers, timeout=timeout)
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
        """Send a single reading via POST /api/meters/submit-reading with retry."""
        if not self.session:
            await self.connect()
            
        url = f"{self.base_url}{SimulatorConfig.SUBMIT_READING_ENDPOINT}"
        payload = reading.to_submission_payload()
        
        # Skip sending if kwh_amount is zero or negative
        kwh_amount = float(payload.get('kwh_amount', 0))
        if kwh_amount <= 0:
            logger.debug(f"Skipping reading with zero/negative kWh: {kwh_amount}")
            return True
        
        for attempt in range(1, self.MAX_RETRIES + 1):
            try:
                async with self.session.post(url, json=payload) as response:
                    if response.status in (200, 201):
                        logger.debug(
                            f"Reading sent: meter={payload['meter_serial']} "
                            f"kwh={kwh_amount} wallet={payload.get('wallet_address', 'N/A')[:8]}..."
                        )
                        return True
                    else:
                        body = await response.text()
                        # Don't retry on client errors (except 408 Timeout or 429 Too Many Requests)
                        if 400 <= response.status < 500 and response.status not in (408, 429):
                            logger.error(
                                f"Permanent failure sending reading: {response.status} {body[:200]}"
                            )
                            return False
                            
                        logger.warning(
                            f"Failed to send reading (attempt {attempt}/{self.MAX_RETRIES}): "
                            f"{response.status} {body[:200]}"
                        )
            except asyncio.TimeoutError:
                logger.warning(f"Timeout sending reading (attempt {attempt}/{self.MAX_RETRIES})")
            except aiohttp.ClientError as e:
                logger.warning(f"Connection error (attempt {attempt}/{self.MAX_RETRIES}): {e}")
            except Exception as e:
                logger.error(f"Unexpected error sending reading: {e}")
                return False
            
            if attempt < self.MAX_RETRIES:
                await asyncio.sleep(self.RETRY_BACKOFF * attempt)
        
        logger.error(f"Failed to send reading after {self.MAX_RETRIES} attempts: meter={payload['meter_serial']}")
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

    async def send_grid_status(self, results: dict) -> bool:
        """Send grid status (Currently no-op for HTTP, but could be sent to a monitoring endpoint)."""
        return True

    async def send_auction_bid(self, bid_payload: Dict[str, Any], batch_id: str) -> bool:
        """Send an encrypted auction bid via POST /api/v1/trading/auction/bid."""
        if not self.session:
            await self.connect()
            
        url = f"{self.base_url}{SimulatorConfig.AUCTION_BID_ENDPOINT}"
        try:
            payload = {
                "batch_id": batch_id,
                "encrypted_price": bid_payload["encrypted_price"],
                "encrypted_amount": bid_payload["encrypted_amount"],
                "is_bid": bid_payload["is_bid"],
                "session_token": None # Optional
            }
            async with self.session.post(url, json=payload) as response:
                if response.status in (202, 201, 200):
                    logger.info(f"Encrypted bid for meter {bid_payload['meter_id']} sent successfully")
                    return True
                else:
                    logger.warning(f"Failed to send encrypted bid: {response.status} {await response.text()}")
                    return False
        except Exception as e:
            logger.error(f"Error sending encrypted bid: {e}")
            return False

    def is_connected(self) -> bool:
        return self.session is not None
