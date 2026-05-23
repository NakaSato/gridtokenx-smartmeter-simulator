"""
Composite transport layer that can send data via multiple transport mechanisms.
Supports both HTTP (to external API) and WebSocket (to dashboard) simultaneously.
"""

import logging
from typing import List, Dict, Any
from .base import TransportLayer
from ..models.reading import EnergyReading

logger = logging.getLogger(__name__)


class CompositeTransport(TransportLayer):
    """
    Composite transport that sends data through multiple underlying transports.
    This allows sending data to both an external API via HTTP and to the dashboard via WebSocket.
    """

    def __init__(self, transports: List[TransportLayer]):
        self.transports = transports

    async def connect(self) -> bool:
        """Connect all underlying transports."""
        success_count = 0
        for i, transport in enumerate(self.transports):
            try:
                result = await transport.connect()
                if result:
                    success_count += 1
                    logger.info(f"Transport {i} connected successfully")
                else:
                    logger.warning(f"Transport {i} failed to connect")
            except Exception as e:
                logger.error(f"Error connecting transport {i}: {e}")

        logger.info(f"Connected {success_count}/{len(self.transports)} transports")
        return success_count > 0

    async def disconnect(self) -> bool:
        """Disconnect all underlying transports."""
        success_count = 0
        for i, transport in enumerate(self.transports):
            try:
                result = await transport.disconnect()
                if result:
                    success_count += 1
                    logger.info(f"Transport {i} disconnected successfully")
                else:
                    logger.warning(f"Transport {i} failed to disconnect")
            except Exception as e:
                logger.error(f"Error disconnecting transport {i}: {e}")

        logger.info(f"Disconnected {success_count}/{len(self.transports)} transports")
        return success_count > 0

    async def send_reading(self, reading: EnergyReading) -> bool:
        """Send a reading through all transports."""
        success_count = 0
        for i, transport in enumerate(self.transports):
            try:
                result = await transport.send_reading(reading)
                if result:
                    success_count += 1
                else:
                    logger.warning(f"Failed to send reading via transport {i}")
            except Exception as e:
                logger.error(f"Error sending reading via transport {i}: {e}")

        # Consider it successful if at least one transport succeeds
        return success_count > 0

    async def send_batch(self, readings: List[EnergyReading]) -> bool:
        """Send a batch of readings through all transports."""
        success_count = 0
        for i, transport in enumerate(self.transports):
            try:
                result = await transport.send_batch(readings)
                if result:
                    success_count += 1
                else:
                    logger.warning(f"Failed to send batch via transport {i}")
            except Exception as e:
                logger.error(f"Error sending batch via transport {i}: {e}")

        # Consider it successful if at least one transport succeeds
        return success_count > 0

    async def send_grid_status(self, results: dict) -> bool:
        """Send grid status through all transports."""
        success_count = 0
        for i, transport in enumerate(self.transports):
            try:
                result = await transport.send_grid_status(results)
                if result:
                    success_count += 1
            except Exception as e:
                logger.error(f"Error sending grid status via transport {i}: {e}")

        return success_count > 0

    async def send_alert(self, alert: Dict[str, Any]) -> bool:
        """Send an alert through all transports."""
        success_count = 0
        for i, transport in enumerate(self.transports):
            try:
                # Check if transport has send_alert method
                if hasattr(transport, "send_alert"):
                    result = await transport.send_alert(alert)
                    if result:
                        success_count += 1
            except Exception as e:
                logger.error(f"Error sending alert via transport {i}: {e}")

        return success_count > 0

    async def send_vpp_dispatch(self, dispatch_data: Dict[str, Any]) -> bool:
        """Send VPP dispatch through all transports."""
        success_count = 0
        for i, transport in enumerate(self.transports):
            try:
                if hasattr(transport, "send_vpp_dispatch"):
                    result = await transport.send_vpp_dispatch(dispatch_data)
                    if result:
                        success_count += 1
            except Exception as e:
                logger.error(f"Error sending VPP dispatch via transport {i}: {e}")
        return success_count > 0

    async def send_frequency_event(self, freq_data: Dict[str, Any]) -> bool:
        """Send frequency event through all transports."""
        success_count = 0
        for i, transport in enumerate(self.transports):
            try:
                if hasattr(transport, "send_frequency_event"):
                    result = await transport.send_frequency_event(freq_data)
                    if result:
                        success_count += 1
            except Exception as e:
                logger.error(f"Error sending frequency event via transport {i}: {e}")
        return success_count > 0

    async def send_islanding_event(self, island_data: Dict[str, Any]) -> bool:
        """Send islanding event through all transports."""
        success_count = 0
        for i, transport in enumerate(self.transports):
            try:
                if hasattr(transport, "send_islanding_event"):
                    result = await transport.send_islanding_event(island_data)
                    if result:
                        success_count += 1
            except Exception as e:
                logger.error(f"Error sending islanding event via transport {i}: {e}")
        return success_count > 0

    async def send_demand_response(self, dr_data: Dict[str, Any]) -> bool:
        """Send demand response through all transports."""
        success_count = 0
        for i, transport in enumerate(self.transports):
            try:
                if hasattr(transport, "send_demand_response"):
                    result = await transport.send_demand_response(dr_data)
                    if result:
                        success_count += 1
            except Exception as e:
                logger.error(f"Error sending demand response via transport {i}: {e}")
        return success_count > 0

    async def send_carbon_intensity(self, carbon_data: Dict[str, Any]) -> bool:
        """Send carbon intensity through all transports."""
        success_count = 0
        for i, transport in enumerate(self.transports):
            try:
                if hasattr(transport, "send_carbon_intensity"):
                    result = await transport.send_carbon_intensity(carbon_data)
                    if result:
                        success_count += 1
            except Exception as e:
                logger.error(f"Error sending carbon intensity via transport {i}: {e}")
        return success_count > 0

    async def send_weather(self, weather_data: Dict[str, Any]) -> bool:
        """Send weather through all transports."""
        success_count = 0
        for i, transport in enumerate(self.transports):
            try:
                if hasattr(transport, "send_weather"):
                    result = await transport.send_weather(weather_data)
                    if result:
                        success_count += 1
            except Exception as e:
                logger.error(f"Error sending weather via transport {i}: {e}")
        return success_count > 0

    async def send_simulation_step(self, step_data: Dict[str, Any]) -> bool:
        """Send simulation step through all transports."""
        success_count = 0
        for i, transport in enumerate(self.transports):
            try:
                if hasattr(transport, "send_simulation_step"):
                    result = await transport.send_simulation_step(step_data)
                    if result:
                        success_count += 1
            except Exception as e:
                logger.error(f"Error sending simulation step via transport {i}: {e}")
        return success_count > 0

    def is_connected(self) -> bool:
        """Check if at least one transport is connected."""
        for transport in self.transports:
            if transport.is_connected():
                return True
        return False
