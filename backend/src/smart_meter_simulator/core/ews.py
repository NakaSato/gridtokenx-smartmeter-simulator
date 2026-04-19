"""
Early Warning System (EWS) for Grid Incidents

Detects anomalies, capacity drops, and stability risks to trigger 
automated emergency responses (e.g. BESS discharge, load shedding).
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)

class EarlyWarningSystem:
    """
    Automated monitoring and anomaly detection engine for the Island Hub.
    Designed to satisfy Hackathon requirements for incident simulation.
    """
    
    def __init__(self):
        self.last_capacity_mw: Optional[float] = None
        self.incident_active = False
        self.alert_history: List[Dict[str, Any]] = []

    def monitor_line_health(
        self, 
        line_id: str, 
        current_capacity_mw: float, 
        current_loading_pct: float
    ) -> Optional[Dict[str, Any]]:
        """
        Detect sudden drops in line capacity (Submarine cable fault scenario).
        """
        alert = None
        
        if self.last_capacity_mw is not None:
            # 1. Detection: Sudden Drop (>20%)
            drop_ratio = (self.last_capacity_mw - current_capacity_mw) / self.last_capacity_mw
            
            if drop_ratio > 0.20:
                self.incident_active = True
                alert = {
                    "type": "EWS_CAPACITY_DROP",
                    "severity": "CRITICAL",
                    "line_id": line_id,
                    "incident": "Submarine Cable Fault / Thermal Violation",
                    "drop_pct": round(drop_ratio * 100, 1),
                    "current_capacity_mw": round(current_capacity_mw, 2),
                    "timestamp": datetime.now().isoformat(),
                    "recommended_action": "TRIGGER_EMERGENCY_BESS"
                }
                logger.critical(f"🚨 EWS ALERT: {alert['incident']} detected on {line_id}! Capacity dropped {alert['drop_pct']}%")
                self.alert_history.append(alert)
            
            # 2. Detection: Overload Trend
            elif current_loading_pct > 105.0:
                alert = {
                    "type": "EWS_OVERLOAD_WARNING",
                    "severity": "HIGH",
                    "line_id": line_id,
                    "loading_pct": round(current_loading_pct, 1),
                    "timestamp": datetime.now().isoformat(),
                    "recommended_action": "PREEMPTIVE_PEAK_SHAVING"
                }
                logger.warning(f"⚠️ EWS WARNING: Severe overload on {line_id} ({alert['loading_pct']}%)")
                self.alert_history.append(alert)

        self.last_capacity_mw = current_capacity_mw
        return alert

    def reset_incident(self):
        self.incident_active = False
        logger.info("EWS: Incident status reset.")
