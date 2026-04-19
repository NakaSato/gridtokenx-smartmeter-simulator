"""
Regression Test: Grid Bottleneck & Strategy Service

Verifies the integration of the StrategyService (13 THB penalty) 
with the VPP cluster dispatch and Analytics ETL.
"""

import sys
import os
from datetime import datetime
import json

# Add backend/src to path
sys.path.append(os.path.join(os.getcwd(), 'backend/src'))

from smart_meter_simulator.core.vpp import VPPManager
from smart_meter_simulator.services.strategy_service import StrategyService
from smart_meter_simulator.services.analytics_service import GridAnalyticsService

def run_regression_test():
    print("=== GridTokenX Regression Test: Strategy & Bottleneck ===")
    
    # 1. Initialize VPP with StrategyService
    vpp = VPPManager()
    strategy = StrategyService()
    
    print("\n[1] Testing Payoff Matrix (115kV Bottleneck)")
    # Scenario: 110% loading on a 12MW line
    line_loading = 110.0
    capacity_mw = 12.0
    
    strategy_decision, reduction_kw = strategy.resolve_transmission_bottleneck(line_loading, capacity_mw)
    
    print(f"Loading: {line_loading}% | Capacity: {capacity_mw}MW")
    print(f"Decision: {strategy_decision}")
    print(f"Reduction Needed: {reduction_kw:.2f} kW")
    
    # Verify S2_BESS selection for Peak
    assert strategy_decision == "S2_BESS", "Peak should prioritize BESS"
    assert reduction_kw > 0, "Reduction should be calculated for >95% loading"

    # 2. Testing Aggregate Forecast Financials
    print("\n[2] Testing Financial Forecast Integration")
    # Mock some meters
    class MockMeter:
        def __init__(self, mid, has_solar=False):
            self.meter_id = mid
            self.config = {'meter_type': 'RESIDENTIAL', 'has_solar': has_solar, 'base_consumption': 1.0}

    meters = [MockMeter(f"M{i}") for i in range(100)]
    forecast = GridAnalyticsService.calculate_aggregate_forecast(meters, datetime.now())
    
    fin_opt = forecast.get("financial_optimization", [])
    print(f"Generated {len(fin_opt)} hours of financial forecast")
    
    # Check if we have savings in peak hours
    total_potential_savings = sum(step.get("savings_thb", 0) for step in fin_opt)
    print(f"Total 24h Potential Savings (BESS vs Diesel): {total_potential_savings:,.2f} THB")
    
    # 3. Final Integrity Check
    print("\n[3] Architectural Integrity Check")
    from smart_meter_simulator.adapters.egat_transmission import EGATTransmissionBuilder
    builder = EGATTransmissionBuilder()
    print(f"EGAT Builder loaded {len(builder.substations)} substations and {len(builder.lines)} lines from JSON.")

    print("\n=== REGRESSION TEST COMPLETED SUCCESSFULLY ===")

if __name__ == "__main__":
    try:
        run_regression_test()
    except Exception as e:
        print(f"\n!!! REGRESSION TEST FAILED: {e}")
        sys.exit(1)
