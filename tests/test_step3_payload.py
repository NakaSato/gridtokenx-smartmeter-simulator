#!/usr/bin/env python3
"""
Step 3 Test: Payload Format Validation
Verifies that simulator generates correct payload format for API Gateway
"""
import json
from datetime import datetime, timezone
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from app.core.meter import SmartMeter

def test_payload_format():
    """Test that payload format matches API specification"""
    
    print("="*80)
    print("STEP 3 TEST: Payload Format Validation")
    print("="*80)
    print()
    
    # Create test meter
    meter_config = {
        'meter_id': 'TEST-PAYLOAD-001',
        'location': 'Test_Zone',
        'meter_type': 'Solar_Prosumer',
        'user_type': 'Prosumer',
        'has_solar': True,
        'solar_capacity': 5.0,
        'panel_efficiency': 0.18,
        'base_consumption': 2.0,
        'has_battery': False,
    }
    
    print("Creating test meter...")
    meter = SmartMeter(meter_config)
    print(f"✅ Meter created: {meter.meter_id}")
    print(f"   Public Key: {meter.key_manager.get_public_key()[:40]}...")
    print()
    
    # Generate reading
    print("Generating reading...")
    timestamp = datetime.now(timezone.utc)
    reading = meter.generate_reading(timestamp)
    print(f"✅ Reading generated:")
    print(f"   Production: {reading.energy_generated:.4f} kWh")
    print(f"   Consumption: {reading.energy_consumed:.4f} kWh")
    print(f"   Surplus: {reading.surplus_energy:.4f} kWh")
    print()
    
    # Get submission payload
    print("Creating submission payload...")
    payload = reading.to_submission_payload()
    print(f"✅ Payload created:")
    print(json.dumps(payload, indent=2))
    print()
    
    # Validate payload structure
    print("Validating payload structure...")
    errors = []
    
    # Check required fields
    required_fields = ['kwh_amount', 'reading_timestamp', 'meter_signature']
    for field in required_fields:
        if field not in payload:
            errors.append(f"Missing required field: {field}")
        else:
            print(f"✅ Field present: {field}")
    
    print()
    
    # Check field types
    print("Validating field types...")
    if 'kwh_amount' in payload:
        if isinstance(payload['kwh_amount'], str):
            print(f"✅ kwh_amount is string: '{payload['kwh_amount']}'")
            try:
                float(payload['kwh_amount'])
                print(f"✅ kwh_amount is parseable as float")
            except ValueError:
                errors.append("kwh_amount is not a valid number string")
        else:
            errors.append(f"kwh_amount should be string, got {type(payload['kwh_amount'])}")
    
    if 'reading_timestamp' in payload:
        if isinstance(payload['reading_timestamp'], str):
            print(f"✅ reading_timestamp is string: '{payload['reading_timestamp']}'")
            # Verify ISO format
            try:
                datetime.fromisoformat(payload['reading_timestamp'].replace('Z', '+00:00'))
                print(f"✅ reading_timestamp is valid ISO format")
            except ValueError:
                errors.append("reading_timestamp is not valid ISO format")
        else:
            errors.append(f"reading_timestamp should be string, got {type(payload['reading_timestamp'])}")
    
    if 'meter_signature' in payload:
        if isinstance(payload['meter_signature'], str):
            print(f"✅ meter_signature is string (length: {len(payload['meter_signature'])})")
        else:
            errors.append(f"meter_signature should be string, got {type(payload['meter_signature'])}")
    
    print()
    
    # Check API Gateway expectations
    print("Checking API Gateway compatibility...")
    print("📋 API expects:")
    print("   - kwh_amount: BigDecimal (from string)")
    print("   - reading_timestamp: DateTime<Utc>")
    print("   - meter_signature: Option<String>")
    print("   - meter_id: Option<Uuid> (optional)")
    print()
    
    print("📋 Simulator provides:")
    print(f"   - kwh_amount: {payload.get('kwh_amount', 'MISSING')}")
    print(f"   - reading_timestamp: {payload.get('reading_timestamp', 'MISSING')}")
    print(f"   - meter_signature: {'Present' if payload.get('meter_signature') else 'MISSING'}")
    print(f"   - meter_id: {'Not provided' if 'meter_id' not in payload else payload['meter_id']}")
    print()
    
    # Summary
    print("="*80)
    if errors:
        print("❌ VALIDATION FAILED")
        print()
        for error in errors:
            print(f"   ❌ {error}")
        return False
    else:
        print("✅ PAYLOAD FORMAT VALID")
        print()
        print("Summary:")
        print("  ✅ All required fields present")
        print("  ✅ All field types correct")
        print("  ✅ Compatible with API Gateway")
        print()
        print("⚠️  Note: meter_id not included (optional field)")
        print("   This is acceptable for legacy_unverified status")
        return True

if __name__ == "__main__":
    success = test_payload_format()
    sys.exit(0 if success else 1)
