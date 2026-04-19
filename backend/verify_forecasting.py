import sys
import os
from datetime import datetime

# Add src to python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

from smart_meter_simulator.ai.forecasting_engine import AIForecastingEngine
from smart_meter_simulator.core.vpp import VPPManager

def main():
    engine = AIForecastingEngine()
    start_time = datetime(2026, 4, 19, 12, 0)
    current_load = 12000.0 # 12 MW
    
    forecasts = engine.forecast_next_24_hours(start_time, current_load)
    
    print(f"Generated {len(forecasts)} hourly forecasts.")
    
    # Show first 5
    for f in forecasts[:5]:
        print(f"Time: {f['timestamp']}, Load_Tao: {f['Load_Tao']} kW, Cap_115kV: {f['Capacity_115kV']} kW, Delta: {f['delta']} kW, Active: {f['constraint_active']}")

    # Test VPP dispatch
    vpp = VPPManager()
    # Mocking cluster
    vpp.register_meter("SAMUI-BESS-01", {"has_battery": True, "battery_capacity": 5000.0, "max_power_kw": 2000.0, "feeder_id": "SAMUI-FEEDER"}, {"battery_level": 4000.0})
    
    dispatches = vpp.proactive_bess_dispatch_from_forecast(forecasts)
    print("VPP Dispatches:", dispatches)

if __name__ == "__main__":
    main()
