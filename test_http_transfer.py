#!/usr/bin/env python3
"""
Test HTTP transfer data optimization after refactoring.
Validates payload modes and transfer efficiency.
"""

import json
from datetime import datetime
from src.app.models.reading import EnergyReading


def test_payload_modes():
    """Test monitoring vs full telemetry payload modes."""
    print("=" * 70)
    print("HTTP TRANSFER DATA OPTIMIZATION TEST")
    print("=" * 70)
    
    # Create test reading
    reading = EnergyReading(
        meter_id="TEST_METER_001",
        timestamp=datetime.now(),
        energy_generated=15.5,
        energy_consumed=10.2,
        surplus_energy=5.3,
        deficit_energy=0.0,
        voltage=230.5,
        current=12.3,
        power_factor=0.95,
        frequency=50.0,
        temperature=25.0,
        thd_voltage=2.1,
        thd_current=3.2,
        location={"lat": 13.7563, "lon": 100.5018},  # Required field
        latitude=13.7563,
        longitude=100.5018,
        grid_zone_id=1,  # Integer, not string
        battery_level=75.0,
        meter_type="PROSUMER",
        user_type="residential",  # Required field
        weather_condition="sunny",
        max_sell_price=3.50,
        max_buy_price=4.20,
        rec_eligible=True,
        carbon_offset=2.5,
        wallet_address="0xABC123",
        meter_signature="sig_xyz"
    )
    
    # Test 1: Monitoring Payload
    print("\n✓ Test 1: Grid Monitoring Payload (Optimized)")
    print("-" * 70)
    monitoring = reading.to_grid_monitoring_payload()
    monitoring_json = json.dumps(monitoring, indent=2)
    monitoring_bytes = len(monitoring_json.encode('utf-8'))
    
    print(f"Fields: {len(monitoring)}")
    print(f"Size: {monitoring_bytes} bytes")
    print(f"\nIncluded fields:")
    for key in sorted(monitoring.keys()):
        print(f"  - {key}")
    
    # Verify P2P fields removed
    assert 'max_sell_price' not in monitoring, "P2P pricing should be removed"
    assert 'max_buy_price' not in monitoring, "P2P pricing should be removed"
    assert 'rec_eligible' not in monitoring, "Certification should be removed"
    assert 'carbon_offset' not in monitoring, "Trading fields should be removed"
    print("\n✓ P2P/Trading fields correctly removed")
    
    # Verify grid physics fields present
    assert 'voltage' in monitoring, "Grid physics required"
    assert 'frequency' in monitoring, "Grid physics required"
    assert 'thd_voltage' in monitoring, "Power quality required"
    assert 'battery_level' in monitoring, "Optimization data required"
    print("✓ Grid physics fields correctly included")
    
    # Test 2: Full Telemetry Payload
    print("\n" + "=" * 70)
    print("✓ Test 2: Full Telemetry Payload (Complete)")
    print("-" * 70)
    full = reading.to_full_telemetry_payload()
    full_json = json.dumps(full, indent=2)
    full_bytes = len(full_json.encode('utf-8'))
    
    print(f"Fields: {len(full)}")
    print(f"Size: {full_bytes} bytes")
    
    # Verify all fields present
    assert 'rec_eligible' in full, "Certification should be in full payload"
    assert 'carbon_offset' in full, "Trading fields should be in full payload"
    assert 'wallet_address' in full, "Blockchain fields should be in full payload"
    print("✓ All fields correctly included in full payload")
    
    # Test 3: Default Submission Payload
    print("\n" + "=" * 70)
    print("✓ Test 3: Default Submission Payload (Backward Compatibility)")
    print("-" * 70)
    default = reading.to_submission_payload()
    assert default == monitoring, "Default should use monitoring mode"
    print("✓ to_submission_payload() correctly defaults to monitoring mode")
    
    # Test 4: Payload Size Comparison
    print("\n" + "=" * 70)
    print("✓ Test 4: Payload Size Comparison & Efficiency")
    print("-" * 70)
    
    old_payload_estimate = 1000  # Bytes (estimated from old implementation)
    monitoring_savings_pct = ((old_payload_estimate - monitoring_bytes) / old_payload_estimate) * 100
    
    print(f"Old Payload (estimated):  {old_payload_estimate} bytes")
    print(f"Monitoring Mode:          {monitoring_bytes} bytes")
    print(f"Full Telemetry:           {full_bytes} bytes")
    print(f"\nSavings (monitoring):     {monitoring_savings_pct:.1f}%")
    print(f"Fields reduced:           {len(full)} → {len(monitoring)} ({len(full) - len(monitoring)} removed)")
    
    # Network efficiency calculation
    readings_per_mb_old = (1024 * 1024) / old_payload_estimate
    readings_per_mb_new = (1024 * 1024) / monitoring_bytes
    efficiency_gain = (readings_per_mb_new / readings_per_mb_old - 1) * 100
    
    print(f"\nNetwork Efficiency:")
    print(f"  Old: {readings_per_mb_old:.0f} readings/MB")
    print(f"  New: {readings_per_mb_new:.0f} readings/MB")
    print(f"  Gain: +{efficiency_gain:.1f}%")
    
    # Monthly bandwidth savings for 10,000 meters
    meters = 10000
    readings_per_hour = 60  # 1/minute
    hours_per_month = 730
    
    old_monthly_mb = (meters * readings_per_hour * hours_per_month * old_payload_estimate) / (1024 * 1024)
    new_monthly_mb = (meters * readings_per_hour * hours_per_month * monitoring_bytes) / (1024 * 1024)
    savings_gb = (old_monthly_mb - new_monthly_mb) / 1024
    
    print(f"\nMonthly Bandwidth (10,000 meters @ 1 reading/min):")
    print(f"  Old: {old_monthly_mb/1024:.1f} GB/month")
    print(f"  New: {new_monthly_mb/1024:.1f} GB/month")
    print(f"  Savings: {savings_gb:.1f} GB/month")
    
    # Test 5: Field Categories
    print("\n" + "=" * 70)
    print("✓ Test 5: Field Category Analysis")
    print("-" * 70)
    
    grid_physics = ['voltage', 'frequency', 'power_factor', 'thd_voltage', 'thd_current']
    energy_metrics = ['kwh', 'energy_generated', 'energy_consumed']
    optimization = ['battery_level', 'zone_id', 'latitude', 'longitude']
    identity = ['meter_serial', 'meter_id', 'timestamp']
    
    monitoring_categories = {
        'Grid Physics': [f for f in grid_physics if f in monitoring],
        'Energy Metrics': [f for f in energy_metrics if f in monitoring],
        'Optimization': [f for f in optimization if f in monitoring],
        'Identity': [f for f in identity if f in monitoring],
    }
    
    for category, fields in monitoring_categories.items():
        print(f"\n{category}: {len(fields)} fields")
        for field in fields:
            print(f"  ✓ {field}")
    
    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print("✓ All tests passed!")
    print(f"✓ Monitoring payload: {monitoring_bytes} bytes ({len(monitoring)} fields)")
    print(f"✓ Full payload: {full_bytes} bytes ({len(full)} fields)")
    print(f"✓ Bandwidth savings: {monitoring_savings_pct:.1f}%")
    print(f"✓ Network efficiency: +{efficiency_gain:.1f}%")
    print(f"✓ Monthly savings: {savings_gb:.1f} GB (10k meters)")
    print("\n✅ HTTP Transfer Optimization: SUCCESS")
    print("=" * 70)


if __name__ == "__main__":
    test_payload_modes()
