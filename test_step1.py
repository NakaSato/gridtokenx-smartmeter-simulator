#!/usr/bin/env python3
"""
Test script to demonstrate Step 1: Smart Meter Reading Generation
"""
import json
from datetime import datetime, timezone
from src.smart_meter_simulator.core.meter import SmartMeter
from src.smart_meter_simulator.utils.crypto import verify_signature

def test_step1_reading_generation():
    """Demonstrate Step 1: Reading Generation with Signing"""
    
    print("=" * 80)
    print("STEP 1: SMART METER READING GENERATION - DEMONSTRATION")
    print("=" * 80)
    print()
    
    # Configure a sample meter
    meter_config = {
        'meter_id': 'MTR-DEMO-001',
        'location': 'Zone_1_Building_A',
        'meter_type': 'Solar_Prosumer',
        'user_type': 'Prosumer',
        'has_solar': True,
        'solar_capacity': 5.0,  # kW
        'panel_efficiency': 0.18,
        'base_consumption': 2.0,  # kW
        'has_battery': True,
        'battery_capacity': 10.0,  # kWh
        'current_battery_level': 5.0  # kWh
    }
    
    print("📊 Meter Configuration:")
    print(f"   Meter ID: {meter_config['meter_id']}")
    print(f"   Type: {meter_config['meter_type']}")
    print(f"   Location: {meter_config['location']}")
    print(f"   Solar Capacity: {meter_config['solar_capacity']} kW")
    print(f"   Battery: {meter_config['battery_capacity']} kWh")
    print()
    
    # Create meter instance
    meter = SmartMeter(meter_config)
    
    print("🔐 Cryptographic Keys Generated:")
    print(f"   Public Key: {meter.key_manager.get_public_key()[:32]}...")
    print(f"   Private Key: [SECURED]")
    print()
    
    # Generate readings at different times of day
    test_times = [
        datetime(2025, 11, 26, 7, 0, 0, tzinfo=timezone.utc),   # Morning
        datetime(2025, 11, 26, 12, 0, 0, tzinfo=timezone.utc),  # Noon (peak solar)
        datetime(2025, 11, 26, 19, 0, 0, tzinfo=timezone.utc),  # Evening
        datetime(2025, 11, 26, 22, 0, 0, tzinfo=timezone.utc),  # Night
    ]
    
    print("⚡ Generating Readings at Different Times:")
    print()
    
    for i, timestamp in enumerate(test_times, 1):
        # Update weather (simulate sunny day)
        meter.update_weather("Sunny")
        
        # Generate reading
        reading = meter.generate_reading(timestamp)
        
        print(f"Reading #{i} - {timestamp.strftime('%H:%M %p')}")
        print("-" * 80)
        
        # Display key metrics
        print(f"   Production:    {reading.energy_generated:>8.4f} kWh")
        print(f"   Consumption:   {reading.energy_consumed:>8.4f} kWh")
        print(f"   Net Energy:    {reading.energy_generated - reading.energy_consumed:>8.4f} kWh")
        print(f"   Surplus:       {reading.surplus_energy:>8.4f} kWh")
        print(f"   Deficit:       {reading.deficit_energy:>8.4f} kWh")
        print(f"   Battery Level: {reading.battery_level:>8.1f} %")
        print()
        
        # Display electrical parameters
        print(f"   Voltage:       {reading.voltage:>8.2f} V")
        print(f"   Current:       {reading.current:>8.3f} mA")
        print(f"   Frequency:     {reading.frequency:>8.2f} Hz")
        print()
        
        # Display signature
        print(f"   Signature:     {reading.meter_signature[:40]}...")
        print()
        
        # Verify signature
        kwh_str = f"{reading.energy_generated:.6f}"
        timestamp_str = reading.timestamp.isoformat()
        payload = f"{kwh_str}|{timestamp_str}"
        
        is_valid = verify_signature(
            meter.key_manager.get_public_key(),
            payload,
            reading.meter_signature
        )
        
        print(f"   ✅ Signature Valid: {is_valid}")
        print()
        
        # Show API submission format
        if i == 2:  # Show detailed format for noon reading
            print("   📤 API Submission Payload:")
            submission = reading.to_submission_payload()
            print(f"   {json.dumps(submission, indent=6)}")
            print()
        
        print()
    
    # Summary
    print("=" * 80)
    print("✅ STEP 1 DEMONSTRATION COMPLETE")
    print("=" * 80)
    print()
    print("Key Features Demonstrated:")
    print("  ✅ Realistic solar generation (time-of-day variation)")
    print("  ✅ Consumption patterns (morning/evening peaks)")
    print("  ✅ Net surplus calculation")
    print("  ✅ Battery state tracking")
    print("  ✅ Ed25519 cryptographic signing")
    print("  ✅ Signature verification")
    print("  ✅ API-ready payload format")
    print()
    print("Next Step: Step 3 - API Gateway Submission")
    print("  (Step 2 - Cryptographic Signing is already integrated)")
    print()

if __name__ == "__main__":
    test_step1_reading_generation()
