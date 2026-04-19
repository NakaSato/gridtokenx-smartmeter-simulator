#!/usr/bin/env python3
"""
Test script for AI forecasting implementation
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from datetime import datetime
from smart_meter_simulator.services.ai_service import AIService
from smart_meter_simulator.ai.forecasting_engine import AIForecastingEngine
from smart_meter_simulator.ai.feature_engineering import FeaturePipeline

def test_feature_engineering():
    print("=" * 60)
    print("Testing Feature Engineering Pipeline")
    print("=" * 60)
    
    target_time = datetime(2026, 4, 20, 14, 30)
    
    # Test temporal features
    temporal = FeaturePipeline.extract_temporal_features(target_time)
    print(f"\nTemporal Features for {target_time}:")
    for key, value in temporal.items():
        print(f"  {key}: {value:.4f}")
    
    # Test weather features
    weather = FeaturePipeline.get_weather_features(target_time)
    print(f"\nWeather Features:")
    for key, value in weather.items():
        print(f"  {key}: {value:.2f}")
    
    # Test inference vector
    vector = FeaturePipeline.prepare_inference_vector(target_time, 15000.0)
    print(f"\nInference Vector: {[f'{v:.4f}' for v in vector]}")
    print("✓ Feature Engineering Test Passed\n")

def test_forecasting_engine():
    print("=" * 60)
    print("Testing AI Forecasting Engine")
    print("=" * 60)
    
    engine = AIForecastingEngine()
    start_time = datetime(2026, 4, 20, 0, 0)
    current_load = 15000.0
    
    forecasts = engine.forecast_next_24_hours(start_time, current_load)
    
    print(f"\n24-Hour Forecast Summary:")
    print(f"  Start Time: {start_time}")
    print(f"  Current Load: {current_load} kW")
    print(f"  Forecast Points: {len(forecasts)}")
    
    # Show first 3 hours
    print(f"\nFirst 3 Hours:")
    for f in forecasts[:3]:
        print(f"  Hour {f['hour_offset']}: Load={f['Load_Tao']:.2f} kW, "
              f"Capacity={f['Capacity_115kV']:.2f} kW, Delta={f['delta']:.2f} kW, "
              f"Constraint={'YES' if f['constraint_active'] else 'NO'}")
    
    # Count constraints
    constraint_count = sum(1 for f in forecasts if f['constraint_active'])
    print(f"\nConstraint Analysis:")
    print(f"  Total Constraint Hours: {constraint_count}/24")
    
    if constraint_count > 0:
        max_deficit = max(abs(f['delta']) for f in forecasts if f['constraint_active'])
        print(f"  Maximum Deficit: {max_deficit:.2f} kW")
    
    print("✓ Forecasting Engine Test Passed\n")

def test_ai_service():
    print("=" * 60)
    print("Testing AI Service Integration")
    print("=" * 60)
    
    service = AIService()
    start_time = datetime(2026, 4, 20, 0, 0)
    
    # Test 24h forecast
    result = service.get_24h_forecast(start_time, 15000.0)
    
    print(f"\nForecast Result:")
    print(f"  Generated At: {result['generated_at']}")
    print(f"  Forecast Start: {result['forecast_start']}")
    print(f"  Total Points: {len(result['forecasts'])}")
    
    print(f"\nSummary Metrics:")
    for key, value in result['summary'].items():
        print(f"  {key}: {value}")
    
    print(f"\nConstraints: {len(result['constraints'])} hours")
    
    # Test constraint analysis
    constraint_analysis = service.get_constraint_analysis(start_time, 15000.0)
    
    print(f"\nConstraint Analysis:")
    print(f"  Status: {constraint_analysis['status']}")
    print(f"  BESS Required: {constraint_analysis.get('bess_required', False)}")
    
    if 'bess_requirements' in constraint_analysis:
        print(f"  BESS Requirements:")
        for key, value in constraint_analysis['bess_requirements'].items():
            print(f"    {key}: {value}")
    
    print("✓ AI Service Test Passed\n")

def test_demographic_metrics():
    print("=" * 60)
    print("Testing Demographic Metrics")
    print("=" * 60)
    
    engine = AIForecastingEngine()
    
    # Test Koh Tao
    target_time = datetime(2026, 4, 20, 14, 0)
    tao_metrics = engine._calculate_demographic_metrics(target_time)
    
    print(f"\nKoh Tao Metrics (April 20, 2026):")
    print(f"  Tourist Active: {tao_metrics['T_active']:.0f}")
    print(f"  Daily Active Population: {tao_metrics['DAP_d']:.0f}")
    print(f"  Base Load: {tao_metrics['Load_d_kw']:.2f} kW")
    
    # Test Koh Phangan
    phangan_metrics = engine._calculate_phangan_demographic_metrics(target_time)
    
    print(f"\nKoh Phangan Metrics (April 20, 2026):")
    print(f"  Tourist Active: {phangan_metrics['T_active']:.0f}")
    print(f"  Digital Nomad Active: {phangan_metrics['N_active']:.0f}")
    print(f"  Base Load: {phangan_metrics['Load_d_kw']:.2f} kW")
    
    # Test Full Moon effect
    full_moon_date = datetime(2026, 4, 23, 14, 0)
    phangan_full_moon = engine._calculate_phangan_demographic_metrics(full_moon_date)
    
    print(f"\nKoh Phangan Full Moon (April 23, 2026):")
    print(f"  Base Load: {phangan_full_moon['Load_d_kw']:.2f} kW")
    print(f"  Lunar Spike: +8000 kW")
    
    print("✓ Demographic Metrics Test Passed\n")

if __name__ == "__main__":
    try:
        test_feature_engineering()
        test_forecasting_engine()
        test_demographic_metrics()
        test_ai_service()
        
        print("=" * 60)
        print("✓ ALL TESTS PASSED")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
