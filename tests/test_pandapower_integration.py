
import sys
import os
import pandas as pd
from datetime import datetime

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.app.core.meter import SmartMeter, MeterType
from src.app.adapters.pandapower_adapter import PandapowerAdapter, MeasurementTableBuilder
from src.app.config import AccuracyClass

def test_pandapower_adapter_accuracy_mapping():
    """Test that adapter maps meter types to correct accuracy classes"""
    builder = MeasurementTableBuilder()
    
    assert builder.accuracy_map[MeterType.RESIDENTIAL] == AccuracyClass.CLASS_2_0
    assert builder.accuracy_map[MeterType.SUBSTATION] == AccuracyClass.CLASS_0_2
    print("test_pandapower_adapter_accuracy_mapping: PASS")
    
def test_measurement_generation_integration():
    """Test end-to-end measurement table generation"""
    # Create a meter
    config = {
        'meter_id': 'METER_001',
        'meter_type': MeterType.RESIDENTIAL.value,
        'location': 'Test Loc',
        'user_type': 'Consumer',
        'base_consumption': 5.0
    }
    meter = SmartMeter(config)
    reading = meter.generate_reading(datetime.now())
    
    # Use Adapter
    adapter = PandapowerAdapter()
    net = adapter.create_simple_network(num_buses=2)
    
    # connections
    indices = adapter.add_meter_to_network(net, meter, reading, bus_index=1)
    
    df = adapter.get_measurement_table()
    
    assert not df.empty
    assert 'std_dev' in df.columns
    assert 'meas_type' in df.columns
    
    # Verify we have v, p, q measurements
    meas_types = df['meas_type'].unique()
    assert 'v' in meas_types
    assert 'p' in meas_types
    assert 'q' in meas_types
    
    # Check std_dev is non-zero
    assert (df['std_dev'] > 0).all()
    print("test_measurement_generation_integration: PASS")

if __name__ == "__main__":
    try:
        test_pandapower_adapter_accuracy_mapping()
        test_measurement_generation_integration()
        print("ALL TESTS PASSED")
    except Exception as e:
        print(f"TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
