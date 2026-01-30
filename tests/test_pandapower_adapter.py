"""
Unit tests for PandapowerAdapter and MeasurementTableBuilder.
"""

import pytest
import pandas as pd
import numpy as np
from app.adapters.pandapower_adapter import (
    PandapowerAdapter,
    MeasurementTableBuilder,
    AccuracyClass
)
from app.config import MeterType
from app.core.meter import SmartMeter

try:
    import pandapower as pp
    PANDAPOWER_AVAILABLE = True
except ImportError:
    PANDAPOWER_AVAILABLE = False

pytestmark = pytest.mark.skipif(
    not PANDAPOWER_AVAILABLE,
    reason="pandapower not installed"
)

@pytest.fixture
def builder():
    return MeasurementTableBuilder(sigma_factor=3)

@pytest.fixture
def adapter():
    return PandapowerAdapter(sigma_factor=3)

class TestMeasurementTableBuilder:
    def test_initialization(self, builder):
        assert builder.sigma_factor == 3
        assert len(builder.measurements) == 0

    def test_calculate_std_dev(self, builder):
        # Formula: σ = (AccuracyClass / 300) × NominalValue (for sigma_factor=3)
        nominal = 230.0
        acc_class = AccuracyClass.CLASS_1_0  # 0.01
        
        expected_std_dev = (0.01 / 300.0) * 230.0
        actual_std_dev = builder.calculate_std_dev(acc_class, nominal)
        
        assert pytest.approx(actual_std_dev) == expected_std_dev

    def test_add_voltage_measurement(self, builder):
        builder.add_voltage_measurement(
            meter_id="M1",
            bus_index=0,
            voltage_pu=1.05,
            meter_type=MeterType.GRID_CONSUMER
        )
        
        assert len(builder.measurements) == 1
        m = builder.measurements[0]
        assert m['name'] == "M1_V"
        assert m['meas_type'] == "v"
        assert m['element_type'] == "bus"
        assert m['element'] == 0
        assert m['value'] == 1.05
        assert m['std_dev'] > 0

    def test_add_active_power_measurement(self, builder):
        builder.add_active_power_measurement(
            meter_id="M1",
            load_index=0,
            power_mw=0.005,
            meter_type=MeterType.SOLAR_PROSUMER,
            is_generation=True
        )
        
        assert len(builder.measurements) == 1
        m = builder.measurements[0]
        assert m['name'] == "M1_P"
        assert m['meas_type'] == "p"
        assert m['element_type'] == "sgen"  # Generation uses sgen by default in some contexts or based on flag
        assert m['element'] == 0
        assert m['value'] == 0.005

    def test_to_dataframe(self, builder):
        builder.add_voltage_measurement("M1", 0, 1.0, MeterType.GRID_CONSUMER)
        df = builder.to_dataframe()
        
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 1
        assert list(df.columns) == ["name", "meas_type", "element_type", "element", "value", "std_dev", "side"]

    def test_clear(self, builder):
        builder.add_voltage_measurement("M1", 0, 1.0, MeterType.GRID_CONSUMER)
        builder.clear()
        assert len(builder.measurements) == 0

class TestPandapowerAdapter:
    def test_initialization(self, adapter):
        assert adapter.builder is not None
        assert adapter.topology_builder is not None

    def test_get_measurement_table(self, adapter):
        adapter.builder.add_voltage_measurement("M1", 0, 1.0, MeterType.GRID_CONSUMER)
        df = adapter.get_measurement_table()
        assert len(df) == 1

    def test_create_simple_network(self, adapter):
        net = adapter.create_simple_network(num_buses=3)
        assert len(net.bus) == 3
        assert len(net.line) == 2
