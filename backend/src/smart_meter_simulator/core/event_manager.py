import logging
from typing import Any, Dict, List
from .ews import EarlyWarningSystem
from ..transport.base import TransportLayer

logger = logging.getLogger(__name__)

class EventManager:
    """
    Monitors grid events, health, and dispatches alerts via transport layers.
    """
    def __init__(self, transport: TransportLayer, ews: EarlyWarningSystem):
        self.transport = transport
        self.ews = ews

    async def monitor_grid_health(self, net: Any, timestamp: str):
        """Monitor grid lines for congestion and health anomalies."""
        if not net or not hasattr(net, 'res_line'):
            return

        # Simplified bottleneck monitoring for known lines
        bottleneck_line = net.line[net.line.name == "115kV KMB (Circuit 3) Bottleneck"]
        if not bottleneck_line.empty:
            import numpy as np
            line_idx = bottleneck_line.index[0]
            loading = net.res_line.loading_percent.at[line_idx]
            capacity = (net.line.at[line_idx, 'max_i_ka'] * 
                        net.bus.vn_kv.at[net.line.at[line_idx, 'from_bus']] * 
                        np.sqrt(3))
            
            ews_alert = self.ews.monitor_line_health("115kV KMB (Circuit 3)", capacity, loading)
            if ews_alert:
                await self.transport.send_alert(ews_alert)

    async def send_vpp_dispatch_alerts(self, dispatches: Dict[str, float], line: str, loading: float, trigger: str):
        """Send alerts for proactive or reactive VPP dispatches."""
        for m_id, kw in dispatches.items():
            await self.transport.send_alert({
                "type": f"{trigger}_RESOLUTION",
                "line": line,
                "loading": f"{loading:.1f}%",
                "asset": m_id,
                "dispatch_kw": kw,
                "trigger": trigger
            })

    async def broadcast_islanding_event(self, subtype: str, message: str, timestamp: str):
        """Broadcast grid islanding or reconnection events."""
        await self.transport.send_alert({
            "type": "GRID_EVENT",
            "subtype": subtype,
            "timestamp": timestamp,
            "message": message
        })
