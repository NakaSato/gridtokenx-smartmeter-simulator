"""
gRPC Transport Layer using betterproto and grpclib.
Sends readings to the Oracle Bridge via Industrial ConnectRPC / gRPC.
"""

import logging
import uuid
from typing import Any, Dict, List, Optional

from grpclib.client import Channel

from ..config import get_config
from ..models.reading import EnergyReading
from .base import TransportLayer
from .proto.gridtokenx.oracle.v1 import (
    OracleServiceStub,
    TelemetryRequest,
    TelemetryBatchRequest,
)

logger = logging.getLogger(__name__)


class GrpcTransport(TransportLayer):
    """
    gRPC implementation of TransportLayer using betterproto/grpclib.
    Aligns with the industrial DLMS/COSEM (IEC 62056) ingestion standard.
    """

    def __init__(
        self, 
        host: Optional[str] = None, 
        port: Optional[int] = None, 
        max_retries: int = 3,
        retry_backoff: float = 1.0
    ):
        super().__init__(max_retries=max_retries, retry_backoff=retry_backoff)
        self._config = get_config()
        
        # Parse host/port. Default to the same host as api_gateway but on GRPC_PORT (50051)
        if host:
            self.host = host
        else:
            # Extract host from api_gateway_url (e.g., http://localhost:4000 -> localhost)
            clean_url = self._config.api_gateway_url.split("//")[-1]
            self.host = clean_url.split(":")[0]
            
        self.port = port or self._config.grpc_gateway_port
        self.channel: Optional[Channel] = None
        self.stub: Optional[OracleServiceStub] = None

    async def connect(self) -> bool:
        """Initialize grpclib channel and stub."""
        if not self.channel:
            try:
                self.channel = Channel(self.host, self.port)
                self.stub = OracleServiceStub(self.channel)
                logger.info(f"gRPC Transport connected to {self.host}:{self.port}")
                self._set_connected(True)
            except Exception as e:
                logger.error(f"Failed to initialize gRPC channel: {e}")
                return False
        return True

    async def disconnect(self) -> bool:
        """Close grpclib channel."""
        if self.channel:
            self.channel.close()
            self.channel = None
            self.stub = None
            self._set_connected(False)
            logger.info("gRPC Transport disconnected")
        return True

    def _map_reading(self, reading: EnergyReading) -> TelemetryRequest:
        """Map EnergyReading model to TelemetryRequest protobuf message."""
        # Extract zone_id from location string if possible (e.g. "Zone_1")
        zone_id = None
        if "Zone_" in reading.location:
             try:
                 zone_id = int(reading.location.split("_")[1])
             except (IndexError, ValueError):
                 pass
        
        return TelemetryRequest(
            reading_id=str(uuid.uuid4()),
            meter_id=reading.meter_id,
            meter_serial=reading.meter_id, # Using ID as serial for simplicity
            zone_id=zone_id,
            kwh=str(round(max(0.0, reading.surplus_energy), 6)),
            energy_generated=str(round(reading.energy_generated, 6)),
            energy_consumed=str(round(reading.energy_consumed, 6)),
            voltage=str(round(reading.voltage, 2)) if reading.voltage is not None else None,
            current=str(round(reading.current, 3)) if reading.current is not None else None,
            battery_level=str(round(reading.battery_level, 1)),
            temperature=str(round(reading.temperature, 1)) if reading.temperature is not None else None,
            timestamp=int(reading.timestamp.timestamp()),
            raw_payload=reading.generate_dlms_payload() if self._config.enable_dlms_binary else b"",
            signature=reading.meter_signature
        )

    async def send_reading(self, reading: EnergyReading) -> bool:
        """Send a single reading via OracleService.SubmitTelemetry with retry."""
        if not self.stub:
            await self.connect()

        # Skip sending if kwh is zero or negative (aligned with HTTP behavior)
        if reading.surplus_energy <= 0:
            logger.debug(f"Skipping gRPC reading with zero/negative kWh: {reading.surplus_energy}")
            return True

        request = self._map_reading(reading)

        async def _send():
            try:
                response = await self.stub.submit_telemetry(request)
                logger.debug(
                    f"gRPC Reading sent: meter={request.meter_id} "
                    f"receipt={response.receipt_id} status={response.status}"
                )
                return True
            except Exception as e:
                logger.warning(f"gRPC submit_telemetry failed: {e}")
                return False

        return await self._retry_operation(_send, operation_name="Sending gRPC reading")

    async def send_batch(self, readings: List[EnergyReading]) -> bool:
        """Send a batch of readings via OracleService.SubmitTelemetryBatch."""
        if not self.stub:
            await self.connect()

        requests = [self._map_reading(r) for r in readings if r.surplus_energy > 0]
        if not requests:
            return True

        batch_request = TelemetryBatchRequest(readings=requests)

        async def _send():
            try:
                response = await self.stub.submit_telemetry_batch(batch_request)
                logger.info(
                    f"gRPC Batch sent: accepted={response.accepted_count} "
                    f"rejected={response.rejected_count} status={response.status}"
                )
                return True
            except Exception as e:
                logger.warning(f"gRPC submit_telemetry_batch failed: {e}")
                return False

        return await self._retry_operation(_send, operation_name="Sending gRPC batch")

    async def send_grid_status(self, results: dict) -> bool:
        """Send grid status (Currently no-op, fits the base class)."""
        return True


    async def send_alert(self, alert: Dict[str, Any]) -> bool:
        """Send an alert (Currently no-op)."""
        return True

    def is_connected(self) -> bool:
        return self._connected
