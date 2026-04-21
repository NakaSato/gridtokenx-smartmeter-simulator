import logging
from typing import Any, Dict, List, Optional
from influxdb_client import InfluxDBClient
from influxdb_client.client.write_api import SYNCHRONOUS

from .base import TransportLayer
from .influx_mappers import mappers

logger = logging.getLogger(__name__)

class InfluxDBTransport(TransportLayer):
    """
    InfluxDB transport for complete simulation data storage.
    Delegates point mapping to specialized mapper functions.
    """

    def __init__(self, url: str, token: str, org: str, bucket: str, **kwargs):
        super().__init__(max_retries=kwargs.get('max_retries', 3), retry_backoff=kwargs.get('retry_backoff', 1.0))
        self.url, self.token, self.org, self.bucket = url, token, org, bucket
        self.client, self.write_api = None, None

    async def connect(self) -> bool:
        try:
            self.client = InfluxDBClient(url=self.url, token=self.token, org=self.org, timeout=10_000)
            self.write_api = self.client.write_api(write_options=SYNCHRONOUS)
            self._set_connected(True)
            logger.info(f"✅ InfluxDB Transport connected to {self.url}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect InfluxDB: {e}")
            return False

    async def disconnect(self) -> bool:
        if self.client:
            self.write_api.close()
            self.client.close()
            self.client = self.write_api = None
            self._set_connected(False)
            return True
        return False

    async def send_reading(self, reading: Any) -> bool:
        if not self.connected: return False
        try:
            point = mappers.map_reading(self._convert_reading_to_dict(reading))
            self.write_api.write(bucket=self.bucket, org=self.org, record=point)
            return True
        except Exception as e:
            logger.error(f"Error sending reading: {e}")
            return False

    async def send_batch(self, readings: List[Any]) -> bool:
        if not self.connected: return False
        try:
            points = [mappers.map_reading(self._convert_reading_to_dict(r)) for r in readings]
            self.write_api.write(bucket=self.bucket, org=self.org, record=points)
            return True
        except Exception as e:
            logger.error(f"Error sending batch: {e}")
            return False

    async def send_grid_status(self, status: Dict[str, Any]) -> bool:
        if not self.connected: return False
        try:
            point = mappers.map_grid_status(status)
            self.write_api.write(bucket=self.bucket, org=self.org, record=point)
            return True
        except Exception as e:
            logger.error(f"Error sending grid status: {e}")
            return False

    async def send_vpp_dispatch(self, dispatch_data: Dict[str, Any]) -> bool:
        if not self.connected: return False
        try:
            points = mappers.map_vpp_dispatch(dispatch_data)
            self.write_api.write(bucket=self.bucket, org=self.org, record=points)
            return True
        except Exception as e:
            logger.error(f"Error sending VPP dispatch: {e}")
            return False

    def is_connected(self) -> bool: return self.connected
