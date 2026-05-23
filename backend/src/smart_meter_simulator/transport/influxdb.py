import logging
from typing import Any, Dict, List
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
        super().__init__(
            max_retries=kwargs.get("max_retries", 3),
            retry_backoff=kwargs.get("retry_backoff", 1.0),
        )
        self.url, self.token, self.org, self.bucket = url, token, org, bucket
        self.client, self.write_api = None, None

    async def connect(self) -> bool:
        try:
            self.client = InfluxDBClient(
                url=self.url, token=self.token, org=self.org, timeout=10_000
            )

            # Verify connection and authorization by checking health
            health = self.client.health()
            if health.status != "pass":
                # Check for 401 in health message or try a simple authenticated call
                try:
                    self.client.organizations_api().find_organizations()
                except Exception as auth_e:
                    if "401" in str(auth_e) or "unauthorized" in str(auth_e).lower():
                        logger.error(
                            f"❌ InfluxDB Authorization Failed (401) at {self.url}. Check your INFLUXDB_TOKEN."
                        )
                        return False

                logger.error(
                    f"Failed to connect InfluxDB at {self.url}: Health check status is {health.status}. Message: {health.message}"
                )
                return False

            self.write_api = self.client.write_api(write_options=SYNCHRONOUS)
            self._set_connected(True)
            logger.info(
                f"✅ InfluxDB Transport connected to {self.url} (Bucket: {self.bucket})"
            )
            return True
        except Exception as e:
            if "401" in str(e) or "unauthorized" in str(e).lower():
                logger.error(
                    f"❌ InfluxDB Authorization Failed (401) at {self.url}. Check your INFLUXDB_TOKEN."
                )
            else:
                logger.error(f"Failed to connect InfluxDB at {self.url}: {e}")
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
        if not self.connected:
            return False
        try:
            point = mappers.map_reading(self._convert_reading_to_dict(reading))
            self.write_api.write(bucket=self.bucket, org=self.org, record=point)
            return True
        except Exception as e:
            logger.error(f"Error sending reading: {e}")
            return False

    async def send_batch(self, readings: List[Any]) -> bool:
        if not self.connected:
            return False
        try:
            points = [
                mappers.map_reading(self._convert_reading_to_dict(r)) for r in readings
            ]
            self.write_api.write(bucket=self.bucket, org=self.org, record=points)
            return True
        except Exception as e:
            logger.error(f"Error sending batch: {e}")
            return False

    async def send_grid_status(self, status: Dict[str, Any]) -> bool:
        if not self.connected:
            return False
        try:
            point = mappers.map_grid_status(status)
            self.write_api.write(bucket=self.bucket, org=self.org, record=point)
            return True
        except Exception as e:
            logger.error(f"Error sending grid status: {e}")
            return False

    async def send_vpp_dispatch(self, dispatch_data: Dict[str, Any]) -> bool:
        if not self.connected:
            return False
        try:
            points = mappers.map_vpp_dispatch(dispatch_data)
            self.write_api.write(bucket=self.bucket, org=self.org, record=points)
            return True
        except Exception as e:
            logger.error(f"Error sending VPP dispatch: {e}")
            return False

    async def send_frequency_event(self, freq_data: Dict[str, Any]) -> bool:
        if not self.connected:
            return False
        try:
            point = mappers.map_frequency_event(freq_data)
            self.write_api.write(bucket=self.bucket, org=self.org, record=point)
            return True
        except Exception as e:
            logger.error(f"Error sending frequency event: {e}")
            return False

    async def send_islanding_event(self, island_data: Dict[str, Any]) -> bool:
        if not self.connected:
            return False
        try:
            point = mappers.map_islanding_event(island_data)
            self.write_api.write(bucket=self.bucket, org=self.org, record=point)
            return True
        except Exception as e:
            logger.error(f"Error sending islanding event: {e}")
            return False

    async def send_demand_response(self, dr_data: Dict[str, Any]) -> bool:
        if not self.connected:
            return False
        try:
            point = mappers.map_demand_response(dr_data)
            self.write_api.write(bucket=self.bucket, org=self.org, record=point)
            return True
        except Exception as e:
            logger.error(f"Error sending demand response: {e}")
            return False

    async def send_carbon_intensity(self, carbon_data: Dict[str, Any]) -> bool:
        if not self.connected:
            return False
        try:
            point = mappers.map_carbon_intensity(carbon_data)
            self.write_api.write(bucket=self.bucket, org=self.org, record=point)
            return True
        except Exception as e:
            logger.error(f"Error sending carbon intensity: {e}")
            return False

    async def send_weather(self, weather_data: Dict[str, Any]) -> bool:
        if not self.connected:
            return False
        try:
            point = mappers.map_weather(weather_data)
            self.write_api.write(bucket=self.bucket, org=self.org, record=point)
            return True
        except Exception as e:
            logger.error(f"Error sending weather: {e}")
            return False

    async def send_simulation_step(self, step_data: Dict[str, Any]) -> bool:
        if not self.connected:
            return False
        try:
            point = mappers.map_simulation_step(step_data)
            self.write_api.write(bucket=self.bucket, org=self.org, record=point)
            return True
        except Exception as e:
            logger.error(f"Error sending simulation step: {e}")
            return False

    async def send_alert(self, alert: Dict[str, Any]) -> bool:
        if not self.connected:
            return False
        try:
            # Map alert to InfluxDB point if needed, or just log for now
            # For now, we'll use a generic mapper if it exists or just skip
            logger.debug(f"Alert received for InfluxDB: {alert}")
            return True
        except Exception as e:
            logger.error(f"Error sending alert: {e}")
            return False

    def is_connected(self) -> bool:
        return self.connected
