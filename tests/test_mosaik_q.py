import pytest
from unittest.mock import MagicMock
import sys

# Mock mosaik_api before importing the adapter
mock_mosaik_api = MagicMock()
class DummySimulator:
    def __init__(self, meta):
        self.meta = meta
mock_mosaik_api.Simulator = DummySimulator
sys.modules["mosaik_api"] = mock_mosaik_api

from smart_meter_simulator.adapters.mosaik_adapter import MosaikAdapter

def test_mosaik_q_calculation():
    """Verify that reactive power is correctly calculated in MosaikAdapter."""
    adapter = MosaikAdapter()
    
    # Create a mock engine and meter
    mock_engine = MagicMock()
    mock_meter = MagicMock()
    mock_meter.meter_id = "M_001"
    mock_meter.energy_consumed = 1.0  # 1 kWh
    mock_meter.energy_generated = 0.0
    mock_meter.last_reading = MagicMock()
    mock_meter.last_reading.reactive_power_kvar = None
    mock_meter.last_reading.interval_seconds = 3600 # 1 hour -> 1 kW
    mock_meter.config = {'power_factor': 0.8} # Q = P * tan(acos(0.8)) = P * 0.75
    
    mock_engine.meters = [mock_meter]
    adapter.engine = mock_engine
    
    # Setup adapter entities
    adapter.entities = {"Meter_M_001": "M_001"}
    
    # Get data
    outputs = {"Meter_M_001": ["p_kw", "q_kvar", "power_factor"]}
    data = adapter.get_data(outputs)
    
    # Verify values
    vals = data["Meter_M_001"]
    assert vals["p_kw"] == 1.0
    assert vals["power_factor"] == 0.8
    # Q should be P * 0.75 = 0.75
    assert abs(vals["q_kvar"] - 0.75) < 0.001
    
    print("Mosaik Q Calculation Test Passed!")

if __name__ == "__main__":
    test_mosaik_q_calculation()
