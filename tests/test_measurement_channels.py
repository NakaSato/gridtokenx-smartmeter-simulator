
import sys
import os
from datetime import datetime

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.app.core.meter import SmartMeter, MeterType
from src.app.models.reading import MeasurementChannel
from src.app.config import METER_TYPE_CHANNELS

def test_measurement_channel_enum():
    """Verify MeasurementChannel enum values"""
    assert MeasurementChannel.VOLTAGE == "v"
    assert MeasurementChannel.ACTIVE_POWER == "p"
    assert MeasurementChannel.REACTIVE_POWER == "q"
    print("test_measurement_channel_enum: PASS")

def test_smart_meter_channel_assignment():
    """Test that SmartMeter is assigned correct channels based on type"""
    
    # Test Residential (should have v, p, q)
    config_res = {
        'meter_id': 'RES_TEST',
        'meter_type': MeterType.RESIDENTIAL.value,
        'location': 'Test Loc',
        'user_type': 'Consumer'
    }
    meter_res = SmartMeter(config_res)
    assert "v" in meter_res.channels
    assert "p" in meter_res.channels
    assert "q" in meter_res.channels
    assert "i" not in meter_res.channels # Default residential doesn't have current
    
    # Test Commercial (should have i)
    config_com = {
        'meter_id': 'COM_TEST',
        'meter_type': MeterType.COMMERCIAL.value,
        'location': 'Test Loc',
        'user_type': 'Prosumer'
    }
    meter_com = SmartMeter(config_com)
    assert "i" in meter_com.channels
    print("test_smart_meter_channel_assignment: PASS")

def test_reading_generation_filtering():
    """Test that generated readings respect channel filtering (implicitly via None values for electrical params)"""
    config_res = {
        'meter_id': 'RES_TEST_2',
        'meter_type': MeterType.RESIDENTIAL.value,
        'location': 'Test Loc',
        'user_type': 'Consumer',
        'base_consumption': 1.0
    }
    meter = SmartMeter(config_res)
    
    # Residential has NO current channel in our config
    reading = meter.generate_reading(datetime.now())
    
    assert reading.voltage is not None
    assert reading.current is None # Should be None as 'i' is not in channels
    assert reading.power_factor is not None # Derived from p/q presence
    assert reading.frequency is not None # Derived from v presence
    print("test_reading_generation_filtering: PASS")

if __name__ == "__main__":
    try:
        test_measurement_channel_enum()
        test_smart_meter_channel_assignment()
        test_reading_generation_filtering()
        print("ALL TESTS PASSED")
    except Exception as e:
        print(f"TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
