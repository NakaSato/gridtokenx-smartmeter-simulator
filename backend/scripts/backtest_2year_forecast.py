#!/usr/bin/env python
"""
2-Year Backtest for PEA Forecasting Model

Tests forecast accuracy across multiple seasons and conditions.
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import sys
sys.path.insert(0, 'src')

from smart_meter_simulator.core.forecaster import EdgeForecastingEngine

print("=" * 70)
print("PEA FORECASTING MODEL — 2-YEAR BACKTEST")
print("=" * 70)

# Generate 2 years of synthetic data (730 days)
print("\n📊 Generating 2 years of synthetic island load data...")
start_date = datetime(2024, 4, 1)
end_date = datetime(2026, 4, 1)
dates = pd.date_range(start=start_date, end=end_date, freq='1h')

# Realistic Koh Tao load pattern with seasonal variation
base_profile = [
    0.6, 0.5, 0.45, 0.4, 0.45, 0.6,   # 00-05: Night
    0.8, 1.2, 1.5, 1.8, 2.0, 2.1,     # 06-11: Morning ramp
    2.0, 1.9, 1.8, 1.7, 1.9, 2.3,     # 12-17: Afternoon
    2.5, 2.4, 2.2, 1.8, 1.2, 0.8      # 18-23: Evening peak
]

# Generate actual load with seasonal and random variation
actual_loads = []
for dt in dates:
    hour = dt.hour
    month = dt.month
    
    # Base load
    load = base_profile[hour] * 15.0  # Scale to ~15 MW average
    
    # Seasonal factor (hot season = higher AC load)
    if month in [3, 4, 5]:  # Hot season
        load *= 1.3
    elif month in [11, 12, 1, 2]:  # Cool season
        load *= 0.8
    
    # Weekend boost (tourism)
    if dt.weekday() >= 5:
        load *= 1.15
    
    # Random noise
    load *= (1 + np.random.normal(0, 0.08))
    
    actual_loads.append(max(0, load))

actual_loads = np.array(actual_loads)

print(f"✅ Generated {len(actual_loads):,} hourly data points")
print(f"   Date range: {start_date.date()} to {end_date.date()}")
print(f"   Average load: {actual_loads.mean():.1f} MW")
print(f"   Peak load: {actual_loads.max():.1f} MW")
print(f"   Min load: {actual_loads.min():.1f} MW")

# Walk-forward backtest: predict each day based on previous data
print("\n🔄 Running walk-forward backtest...")
print("   Strategy: Predict next 24h using current conditions")

forecaster = EdgeForecastingEngine("SAMUI-HUB-01")
mape_scores = []
predictions = []
actuals_test = []

# Test every 7 days (104 weeks = 2 years)
test_points = range(24, len(actual_loads) - 24, 24 * 7)

for i, start_idx in enumerate(test_points):
    # Current conditions
    current_load = actual_loads[start_idx]
    current_date = dates[start_idx]
    
    # Temperature proxy (higher in hot months)
    temp_c = 35.0 if current_date.month in [3, 4, 5] else 30.0
    
    # Generate 24h forecast
    forecast = forecaster.generate_24h_forecast(
        current_load, 
        {"temp_c": temp_c, "cloud_cover": 10.0},
        timestamp=current_date
    )
    
    # Get actual next 24h
    actual_24h = actual_loads[start_idx:start_idx + 24]
    
    # Calculate MAPE for this forecast
    mape = np.mean(np.abs((actual_24h - forecast) / np.where(actual_24h == 0, 1e-6, actual_24h))) * 100
    mape_scores.append(mape)
    
    predictions.extend(forecast)
    actuals_test.extend(actual_24h)
    
    if (i + 1) % 13 == 0:  # Progress every quarter
        print(f"   Quarter {(i+1)//13}: MAPE = {np.mean(mape_scores[-13:]):.2f}%")

# Overall statistics
mape_scores = np.array(mape_scores)
predictions = np.array(predictions)
actuals_test = np.array(actuals_test)

print("\n" + "=" * 70)
print("BACKTEST RESULTS")
print("=" * 70)

print(f"\n📈 Forecast Performance:")
print(f"   Test periods: {len(mape_scores)} weeks")
print(f"   Total forecasts: {len(predictions):,} hours")
print(f"   Mean MAPE: {mape_scores.mean():.2f}%")
print(f"   Median MAPE: {np.median(mape_scores):.2f}%")
print(f"   Std Dev: {mape_scores.std():.2f}%")
print(f"   Min MAPE: {mape_scores.min():.2f}%")
print(f"   Max MAPE: {mape_scores.max():.2f}%")

# PEA mandate check
passing_weeks = (mape_scores < 10.0).sum()
pass_rate = (passing_weeks / len(mape_scores)) * 100

print(f"\n✅ PEA Mandate (<10% MAPE):")
print(f"   Passing weeks: {passing_weeks}/{len(mape_scores)} ({pass_rate:.1f}%)")
print(f"   Status: {'PASS ✅' if pass_rate >= 95 else 'FAIL ❌'}")

# Seasonal breakdown
print(f"\n📅 Seasonal Performance:")
seasonal_mapes = {}
for i, start_idx in enumerate(test_points):
    month = dates[start_idx].month
    season = "Hot" if month in [3,4,5] else "Rainy" if month in [6,7,8,9,10] else "Cool"
    if season not in seasonal_mapes:
        seasonal_mapes[season] = []
    seasonal_mapes[season].append(mape_scores[i])

for season, mapes in sorted(seasonal_mapes.items()):
    print(f"   {season:6s}: {np.mean(mapes):.2f}% MAPE ({len(mapes)} weeks)")

# Error distribution
print(f"\n📊 Error Distribution:")
errors = np.abs(predictions - actuals_test)
print(f"   Mean Absolute Error: {errors.mean():.2f} MW")
print(f"   95th percentile: {np.percentile(errors, 95):.2f} MW")
print(f"   99th percentile: {np.percentile(errors, 99):.2f} MW")

# Final verdict
print("\n" + "=" * 70)
if mape_scores.mean() < 10.0 and pass_rate >= 95:
    print("🎉 MODEL VALIDATED — READY FOR PRODUCTION")
    print(f"   Average MAPE: {mape_scores.mean():.2f}% (Target: <10%)")
    print(f"   Pass rate: {pass_rate:.1f}% (Target: >95%)")
else:
    print("⚠️  MODEL NEEDS TUNING")
    print(f"   Average MAPE: {mape_scores.mean():.2f}% (Target: <10%)")
    print(f"   Pass rate: {pass_rate:.1f}% (Target: >95%)")
print("=" * 70)
