"""
Early Warning System (EWS) for Grid Incidents

Detects anomalies, capacity drops, and stability risks using a hybrid 
AI-first approach (Autoencoders + Rule-Based Expert System).
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from smart_meter_simulator.services.anomaly_detector import GridAnomalyAutoencoder, GridRecommendationEngine

logger = logging.getLogger(__name__)

class EarlyWarningSystem:
    """
    Automated monitoring and AI anomaly detection engine for the Island Hub.
    Designed to satisfy Hackathon requirements for high-security grid monitoring.
    """
    
    def __init__(self):
        self.last_capacity_mw: Optional[float] = None
        self.incident_active = False
        self.alert_history: List[Dict[str, Any]] = []
        self.autoencoder = GridAnomalyAutoencoder(input_dim=12) # 3-hour window
        self.recommendations = GridRecommendationEngine()

    def analyze_telemetry_ai(self, telemetry: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        AI-First detection: Uses an Autoencoder reconstruction error.
        Spots anomalies that rule-based systems might miss.
        """
        result = self.autoencoder.predict_incident(telemetry)
        
        if result["is_anomaly"]:
            self.incident_active = True
            error = result["reconstruction_error"]
            
            # Actionable Recommendation mapping
            a_type = "VOLTAGE_SAG" if telemetry.get("voltage_v", 230) < 210 else "OVERLOAD"
            
            alert = {
                "type": "AI_ANOMALY_DETECTED",
                "severity": "CRITICAL" if error > 50.0 else "HIGH",
                "reconstruction_error": error,
                "confidence_pct": result["confidence_pct"],
                "incident": f"AI-Reconstruction Anomaly: {a_type}",
                "timestamp": datetime.now().isoformat(),
                "actionable_recommendation": self.recommendations.get_recommendation(a_type, "HIGH")
            }
            
            logger.critical(f"🤖 AI ALERT: {alert['incident']}! Error: {error} - Recommendation: {alert['actionable_recommendation']}")
            self.alert_history.append(alert)
            return alert
            
        return None

    def monitor_line_health(
        self, 
        line_id: str, 
        current_capacity_mw: float, 
        current_loading_pct: float
    ) -> Optional[Dict[str, Any]]:
        """
        Rule-Based detection: Sudden drops in line capacity or severe overloads.
        """
        alert = None
        
        if self.last_capacity_mw is not None:
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
                    "actionable_recommendation": self.recommendations.get_recommendation("CAPACITY_DROP", "CRITICAL")
                }
                logger.critical(f"🚨 EWS ALERT: {alert['incident']} detected on {line_id}! Recommendation: {alert['actionable_recommendation']}")
                self.alert_history.append(alert)
            
            elif current_loading_pct > 105.0:
                alert = {
                    "type": "EWS_OVERLOAD_WARNING",
                    "severity": "HIGH",
                    "line_id": line_id,
                    "loading_pct": round(current_loading_pct, 1),
                    "timestamp": datetime.now().isoformat(),
                    "actionable_recommendation": self.recommendations.get_recommendation("OVERLOAD", "HIGH")
                }
                logger.warning(f"⚠️ EWS WARNING: Severe overload on {line_id}. Recommendation: {alert['actionable_recommendation']}")
                self.alert_history.append(alert)

        self.last_capacity_mw = current_capacity_mw
        return alert

    def reset_incident(self):
        self.incident_active = False
        logger.info("EWS: Incident status reset.")
