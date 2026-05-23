import logging
from typing import Any, Dict
from ..transport.base import TransportLayer

logger = logging.getLogger(__name__)


class EventManager:
    """
    Monitors grid events, health, and dispatches alerts via transport layers.
    """

    def __init__(self, transport: TransportLayer, ews: Any = None):
        self.transport = transport
        self.ews = ews

    async def monitor_grid_health(self, net: Any, timestamp: str):
        """Monitor grid lines for congestion and health anomalies (Simplified)."""
        # Grid health monitoring disabled (EWS/Pandapower removed)
        return

    async def send_vpp_dispatch_alerts(
        self, dispatches: Dict[str, float], line: str, loading: float, trigger: str
    ):
        """Send alerts for proactive or reactive VPP dispatches."""
        for m_id, kw in dispatches.items():
            await self.transport.send_alert(
                {
                    "type": f"{trigger}_RESOLUTION",
                    "line": line,
                    "loading": f"{loading:.1f}%",
                    "asset": m_id,
                    "dispatch_kw": kw,
                    "trigger": trigger,
                }
            )

    async def broadcast_islanding_event(
        self, subtype: str, message: str, timestamp: str
    ):
        """Broadcast grid islanding or reconnection events."""
        # Send structured islanding event
        await self.transport.send_islanding_event(
            {
                "status": "islanded" if subtype == "ISLANDING" else "connected",
                "island_id": "microgrid_alpha",
                "timestamp": timestamp,
                "meters_count": 50,  # Mock count for now
            }
        )

        # Also keep the legacy alert for backward compatibility
        await self.transport.send_alert(
            {
                "type": "GRID_EVENT",
                "subtype": subtype,
                "timestamp": timestamp,
                "message": message,
            }
        )
