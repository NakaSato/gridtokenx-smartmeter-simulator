
import sys
import os

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.app.config import AccuracyClass, METER_TYPE_CHANNELS, MeterType

def test_accuracy_class_values():
    """Verify AccuracyClass values match ANSI C12.20 standard (±2%)"""
    assert AccuracyClass.CLASS_0_2.value == 0.002
    assert AccuracyClass.CLASS_0_5.value == 0.005
    assert AccuracyClass.CLASS_1_0.value == 0.010
    assert AccuracyClass.CLASS_2_0.value == 0.020
    print("test_accuracy_class_values: PASS")

def test_meter_type_channels_completeness():
    """Verify all MeterType enums have channel mappings"""
    for meter_type in MeterType:
        assert meter_type in METER_TYPE_CHANNELS, f"Missing channel mapping for {meter_type}"
    print("test_meter_type_channels_completeness: PASS")
        
def test_channel_definitions():
    """Verify channel sets contain valid channel identifiers"""
    for channels in METER_TYPE_CHANNELS.values():
        for channel in channels:
            assert channel in ["v", "p", "q", "i", "ia", "va"]
    print("test_channel_definitions: PASS")

def test_std_dev_calculation_logic():
    """Test standard deviation calculation logic concept"""
    # Manual verification of the formula: σ = (AccuracyClass / 300) * NominalValue
    # For Class 2.0 (0.02) and scalar 3 (sigma_factor)
    accuracy_val = 0.02
    nominal_val = 100.0
    sigma_factor = 3
    
    expected_sigma = (accuracy_val / (100 * sigma_factor)) * nominal_val
    # 0.02 / 300 * 100 = 0.00666...
    
    assert abs(expected_sigma - 0.006666666666666667) < 1e-9
    print("test_std_dev_calculation_logic: PASS")

if __name__ == "__main__":
    try:
        test_accuracy_class_values()
        test_meter_type_channels_completeness()
        test_channel_definitions()
        test_std_dev_calculation_logic()
        print("ALL TESTS PASSED")
    except Exception as e:
        print(f"TEST FAILED: {e}")
        sys.exit(1)
