import logging
from typing import Dict, Any, List
import asyncio
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import ASYNCHRONOUS
from .base import TransportLayer

logger = logging.getLogger(__name__)

class InfluxDBTransport(TransportLayer):
    """
    InfluxDB transport for historical time-series storage.
    Useful for Grafana visualizations and trend analysis.
    """
    
    def __init__(self, url: str, token: str, org: str, bucket: str):
        self.url = url
        self.token = token
        self.org = org
        self.bucket = bucket
        self.client = None
        self.write_api = None
        self._connected = False

    async def connect(self) -> bool:
        """Initialize the InfluxDB client."""
        try:
            # influxdb-client-python doesn't have a native 'async' client in the older sense,
            # but write_api supports ASYNCHRONOUS mode which uses a thread pool.
            self.client = InfluxDBClient(url=self.url, token=self.token, org=self.org)
            self.write_api = self.client.write_api(write_options=ASYNCHRONOUS)
            self._connected = True
            logger.info(f"InfluxDB Transport connected to {self.url}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect InfluxDB Transport: {e}")
            self._connected = False
            return False

    async def disconnect(self) -> bool:
        """Shutdown the InfluxDB client."""
        if self.client:
            self.client.close()
            self._connected = False
            logger.info("InfluxDB Transport disconnected")
            return True
        return False

    def _reading_to_point(self, reading: Any) -> Point:
        """Convert a reading object/dict to an InfluxDB Point."""
        data = reading.dict() if hasattr(reading, "dict") else reading
        
        point = Point("meter_reading") \
            .tag("meter_id", data.get("meter_id", "unknown")) \
            .tag("meter_type", data.get("meter_type", "unknown")) \
            .tag("location", data.get("location", "unknown")) \
            .field("energy_generated", float(data.get("energy_generated", 0.0))) \
            .field("energy_consumed", float(data.get("energy_consumed", 0.0))) \
            .field("battery_level", float(data.get("battery_level", 0.0))) \
            .field("carbon_offset", float(data.get("carbon_offset", 0.0)))
            
        if "timestamp" in data:
            point.time(data["timestamp"])
            
        return point

    async def send_reading(self, reading: Any) -> bool:
        """Send a single reading to InfluxDB."""
        if not self._connected:
            return False
            
        try:
            point = self._reading_to_point(reading)
            # write() in ASYNCHRONOUS mode returns immediately
            self.write_api.write(bucket=self.bucket, org=self.org, record=point)
            return True
        except Exception as e:
            logger.error(f"Error sending reading to InfluxDB: {e}")
            return False

    async def send_batch(self, readings: List[Any]) -> bool:
        """Send a batch of readings to InfluxDB."""
        if not self._connected:
            return False
            
        try:
            points = [self._reading_to_point(r) for r in readings]
            self.write_api.write(bucket=self.bucket, org=self.org, record=points)
            return True
        except Exception as e:
            logger.error(f"Error sending batch to InfluxDB: {e}")
            return False

    async def send_grid_status(self, status: Dict[str, Any]) -> bool:
        """Send grid estimation status to InfluxDB."""
        if not self._connected:
            return False
        try:
            point = Point("grid_status") \
                .tag("status", "converged" if status.get("converged") else "failed") \
                .field("mae", float(status.get("mae", 0.0))) \
                .field("total_losses_mw", float(status.get("total_losses_mw", 0.0)))
                
            if "timestamp" in status:
                point.time(status["timestamp"])
                
            self.write_api.write(bucket=self.bucket, org=self.org, record=point)
            return True
        except Exception as e:
            logger.error(f"Error sending grid status to InfluxDB: {e}")
            return False

    def is_connected(self) -> bool:
        return self._connected
