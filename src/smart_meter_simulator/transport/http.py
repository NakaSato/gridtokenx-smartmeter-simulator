"""
HTTP Transport Layer using aiohttp
Sends readings to the API Gateway via REST endpoints.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional

import aiohttp

from ..config import get_config
from ..models.reading import EnergyReading
from .base import TransportLayer

logger = logging.getLogger(__name__)


class HttpTransport(TransportLayer):
    """
    HTTP implementation of TransportLayer using aiohttp.
    Sends readings to the API Gateway via REST endpoints.
    """

    REQUEST_TIMEOUT = 10  # seconds

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        max_retries: int = 3,
        retry_backoff: float = 1.0
    ):
        super().__init__(max_retries=max_retries, retry_backoff=retry_backoff)
        self._config = get_config()
        self.base_url = (base_url or self._config.api_gateway_url).rstrip('/')
        self.api_key = api_key or self._config.api_key
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
            self._set_connected(True)
        return True

    async def disconnect(self) -> bool:
        """Close aiohttp session."""
        if self.session:
            await self.session.close()
            self.session = None
            self._set_connected(False)
            logger.info("HTTP Transport disconnected")
        return True

    async def send_reading(self, reading: EnergyReading) -> bool:
        """Send a single reading via POST /api/meters/submit-reading with retry."""
        if not self.session:
            await self.connect()

        url = f"{self.base_url}{self._config.submit_reading_endpoint}"
        payload = reading.to_submission_payload()

        # Skip sending if kwh is zero or negative
        kwh_amount = float(payload.get('kwh', 0))
        if kwh_amount <= 0:
            logger.debug(f"Skipping reading with zero/negative kWh: {kwh_amount}")
            return True

        async def _send():
            async with self.session.post(url, json=payload) as response:
                if response.status in (200, 201):
                    logger.debug(
                        f"Reading sent: meter={payload['meter_serial']} "
                        f"kwh={kwh_amount}"
                    )
                    return True

                try:
                    error_data = await response.json()
                    detail = error_data.get('detail', '')
                    suggestion = error_data.get('suggestion', '')
                    error_msg = f"{detail} {f'Suggestion: {suggestion}' if suggestion else ''}".strip()
                    if not error_msg:
                        error_msg = await response.text()
                except Exception:
                    error_msg = await response.text()

                # Don't retry on client errors (except 408 Timeout or 429 Too Many Requests)
                if 400 <= response.status < 500 and response.status not in (408, 429):
                    logger.error(
                        f"Permanent failure sending reading: {response.status} {error_msg[:200]}"
                    )
                    return False

                logger.warning(
                    f"Failed to send reading: {response.status} {error_msg[:200]}"
                )
                return False  # Trigger retry

        return await self._retry_operation(_send, operation_name="Sending reading")

    async def send_batch(self, readings: List[EnergyReading]) -> bool:
        """Send a batch of readings via POST /api/meters/submit-batch."""
        if not self.session:
            await self.connect()

        url = f"{self.base_url}{self._config.submit_batch_endpoint}"
        try:
            payload = {
                "readings": [reading.to_submission_payload() for reading in readings]
            }
            async with self.session.post(url, json=payload) as response:
                if response.status in (200, 201, 202):
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

    async def register_meters(self, meters) -> int:
        """Register meters with the API Gateway via POST /api/v1/simulator/meters/register."""
        if not self.session:
            await self.connect()

        url = f"{self.base_url}{self._config.register_meter_endpoint}"
        registered = 0
        connection_error = None

        for meter in meters:
            payload = {
                "meter_id": meter.meter_id,
                "meter_type": meter.config.get('meter_type', 'solar'),
                "location": meter.config.get('location', 'Simulator'),
                "zone_id": int(meter.config.get('location', 'Zone_1').split('_')[1]) if 'Zone_' in meter.config.get('location', '') else 1,
            }
            try:
                async with self.session.post(url, json=payload) as response:
                    if response.status in (200, 201):
                        registered += 1
                    else:
                        body = await response.text()
                        logger.warning(f"Failed to register meter {meter.meter_id}: {response.status} {body[:200]}")
            except aiohttp.ClientConnectorError as e:
                connection_error = e
                break
            except Exception as e:
                logger.warning(f"Error registering meter {meter.meter_id}: {e}")

        if connection_error:
            logger.warning(f"Could not connect to API Gateway at {self.base_url} for meter registration. Skipping batch. Error: {connection_error}")
        elif registered < len(meters):
            logger.warning(f"Only registered {registered}/{len(meters)} meters. Some readings may be rejected by API Gateway.")

        return registered


    async def send_alert(self, alert: Dict[str, Any]) -> bool:
        """Send an alert (Currently no-op for HTTP, but could be sent to a monitoring endpoint)."""
        return True

    def is_connected(self) -> bool:
        return self.session is not None
