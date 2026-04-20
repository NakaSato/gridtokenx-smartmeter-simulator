import sys
import os
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from smart_meter_simulator.core.ews import EarlyWarningSystem
import logging

logging.basicConfig(level=logging.INFO)

def test_ai_ews():
    ews = EarlyWarningSystem()
    
    print("============================================================")
    print("PEA SECURITY LAYER: AI ANOMALY DETECTION TEST")
    print("============================================================")
    
    # 1. Healthy Telemetry
    healthy = {"power_kw": 500.0, "voltage_v": 230.5}
    alert = ews.analyze_telemetry_ai(healthy)
    print(f"🟢 [Healthy Data] AI Prediction: {'ANOMALY 🚨' if alert else 'NORMAL ✅'}")
    if alert:
        print(f"   Error: {alert['reconstruction_error']} | Recommendation: {alert['actionable_recommendation']}")
    
    # 2. Voltage Sag Incident (The Anomaly)
    sag = {"power_kw": 500.0, "voltage_v": 195.0}
    alert = ews.analyze_telemetry_ai(sag)
    print(f"\n🔴 [Voltage Sag] AI Prediction: {'ANOMALY 🚨' if alert else 'NORMAL ✅'}")
    if alert:
        print(f"   Error: {alert['reconstruction_error']} | Confidence: {alert['confidence_pct']}%")
        print(f"   Actionable Recommendation: {alert['actionable_recommendation']}")
        
    # 3. Rule-Based Secondary Check (Capacity Drop)
    print("\n------------------------------------------------------------")
    print("SECONDARY CHECK: RULE-BASED EXPERT SYSTEM")
    print("------------------------------------------------------------")
    ews.last_capacity_mw = 25.0
    rule_alert = ews.monitor_line_health("115kV_CABLE_01", 15.0, 95.0) # 40% drop
    if rule_alert:
        print(f"⚠️  Rule Alert: {rule_alert['incident']}")
        print(f"   Actionable Recommendation: {rule_alert['actionable_recommendation']}")

if __name__ == "__main__":
    test_ai_ews()
