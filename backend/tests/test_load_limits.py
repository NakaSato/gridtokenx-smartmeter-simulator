import pytest
from datetime import datetime
from smart_meter_simulator.core.meter_logic import profiles

def test_consumption_clamping():
    """Verify that consumption is clamped between min and max load limits."""
    # Test case 1: Normal range
    config = {
        "meter_type": "Residential",
        "base_consumption": 1.0,
        "min_load_kw": 0.5,
        "max_load_kw": 2.0
    }
    timestamp = datetime(2026, 5, 27, 12, 0)
    
    # Run multiple times to account for noise
    for _ in range(100):
        val, _ = profiles.calculate_consumption(timestamp, config, "test-meter", 0.0)
        assert val >= 0.5
        assert val <= 2.0

    # Test case 2: Force high consumption
    config_high = {
        "meter_type": "Residential",
        "base_consumption": 100.0,
        "min_load_kw": 0.1,
        "max_load_kw": 10.0
    }
    val_clamped, _ = profiles.calculate_consumption(timestamp, config_high, "test-meter", 0.0)
    assert val_clamped == 10.0

    # Test case 3: Force low consumption
    config_low = {
        "meter_type": "Residential",
        "base_consumption": 0.001,
        "min_load_kw": 1.5,
        "max_load_kw": 500.0
    }
    val_clamped_low, _ = profiles.calculate_consumption(timestamp, config_low, "test-meter", 0.0)
    assert val_clamped_low == 1.5
