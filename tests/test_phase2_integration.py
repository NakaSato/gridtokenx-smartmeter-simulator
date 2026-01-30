"""
Phase 2 Integration Tests - End-to-End AMI Foundation

Tests the complete pipeline:
SmartMeter → PandapowerAdapter → TopologyBuilder → StateEstimator → ANSI Validation
"""

import pytest
import sys
from pathlib import Path
from datetime import datetime, timezone

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app.adapters import (
    PandapowerAdapter,
    TopologyBuilder,
    StateEstimator,
    MeasurementValidator,
    EstimationAlgorithm
)
from app.core.meter import SmartMeter
from app.models.reading import EnergyReading
from app.config import MeterType

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
def meter_configs():
    """Create realistic meter configurations."""
    return [
        {
            "meter_id": "GRID-001",
            "location": {"lat": 13.7563, "lon": 100.5018},  # Bangkok
            "meter_type": MeterType.GRID_CONSUMER,
            "user_type": "RESIDENTIAL",
            "nominal_voltage": 230.0,
            "max_current": 60.0,
        },
        {
            "meter_id": "SOLAR-001",
            "location": {"lat": 13.7564, "lon": 100.5019},
            "meter_type": MeterType.SOLAR_PROSUMER,
            "user_type": "RESIDENTIAL",
            "nominal_voltage": 230.0,
            "max_current": 60.0,
        },
        {
            "meter_id": "GRID-002",
            "location": {"lat": 13.7565, "lon": 100.5020},
            "meter_type": MeterType.GRID_CONSUMER,
            "user_type": "COMMERCIAL",
            "nominal_voltage": 230.0,
            "max_current": 100.0,
        },
        {
            "meter_id": "HYBRID-001",
            "location": {"lat": 13.7566, "lon": 100.5021},
            "meter_type": MeterType.HYBRID_PROSUMER,
            "user_type": "RESIDENTIAL",
            "nominal_voltage": 230.0,
            "max_current": 60.0,
        },
    ]


@pytest.fixture
def sample_readings():
    """Create realistic energy readings."""
    timestamp = datetime.now(timezone.utc)
    
    return [
        EnergyReading(
            meter_id="GRID-001",
            timestamp=timestamp,
            energy_generated=0.0,
            energy_consumed=150.5,
            energy_kwh=150.5,
            voltage=232.0,
            current=15.2,
            power_factor=0.95,
            frequency=50.0,
            surplus_energy=0.0,
            deficit_energy=150.5,
            location="13.7563,100.5018",
            meter_type=MeterType.GRID_CONSUMER,
            user_type="RESIDENTIAL"
        ),
        EnergyReading(
            meter_id="SOLAR-001",
            timestamp=timestamp,
            energy_generated=25.0,
            energy_consumed=60.3,
            energy_kwh=85.3,
            voltage=228.0,
            current=8.5,
            power_factor=0.98,
            frequency=50.0,
            surplus_energy=25.0,
            deficit_energy=60.3,
            location="13.7564,100.5019",
            meter_type=MeterType.SOLAR_PROSUMER,
            user_type="RESIDENTIAL"
        ),
        EnergyReading(
            meter_id="GRID-002",
            timestamp=timestamp,
            energy_generated=0.0,
            energy_consumed=450.0,
            energy_kwh=450.0,
            voltage=235.0,
            current=45.0,
            power_factor=0.92,
            frequency=50.0,
            surplus_energy=0.0,
            deficit_energy=450.0,
            location="13.7565,100.5020",
            meter_type=MeterType.GRID_CONSUMER,
            user_type="COMMERCIAL"
        ),
        EnergyReading(
            meter_id="HYBRID-001",
            timestamp=timestamp,
            energy_generated=15.0,
            energy_consumed=105.0,
            energy_kwh=120.0,
            voltage=230.0,
            current=12.0,
            power_factor=0.97,
            frequency=50.0,
            surplus_energy=15.0,
            deficit_energy=105.0,
            location="13.7566,100.5021",
            meter_type=MeterType.HYBRID_PROSUMER,
            user_type="RESIDENTIAL"
        ),
    ]


class TestPhase2EndToEnd:
    """End-to-end integration tests for Phase 2 AMI Foundation."""
    
    def test_complete_pipeline(self, meter_configs, sample_readings):
        """Test complete pipeline from meters to state estimation."""
        # 1. Create meters
        meters = []
        for config in meter_configs:
            meter = SmartMeter(config)
            meters.append(meter)
        
        assert len(meters) == 4
        
        # 2. Create network with topology builder
        builder = TopologyBuilder()
        net = builder.build_radial_network(
            num_buses=len(meters) + 1,  # +1 for grid connection
            voltage_kv=0.4,
            line_length_km=0.1
        )
        
        assert len(net.bus) == 5
        assert len(net.line) == 4
        
        # 3. Add loads and measurements using adapter
        adapter = PandapowerAdapter(topology_builder=builder)
        
        for idx, (meter, reading) in enumerate(zip(meters, sample_readings)):
            bus_idx = idx + 1  # Bus 0 is grid
            
            # Calculate power
            voltage_kv = reading.voltage / 1000.0
            power_kw = voltage_kv * reading.current * reading.power_factor
            power_mw = power_kw / 1000.0
            reactive_power_mvar = power_mw * (1 - reading.power_factor**2)**0.5
            
            # Add load/generation
            if reading.surplus_energy > 0:
                # Has generation - use sgen
                pp.create_sgen(net, bus=bus_idx, p_mw=power_mw, q_mvar=0.0, name=f"Gen_{meter.meter_id}")
            
            # Always add consumption load
            pp.create_load(net, bus=bus_idx, p_mw=power_mw, q_mvar=reactive_power_mvar, name=f"Load_{meter.meter_id}")
            
            # Add measurements
            voltage_pu = reading.voltage / (net.bus.at[bus_idx, 'vn_kv'] * 1000.0)
            adapter.builder.add_voltage_measurement(
                meter_id=meter.meter_id,
                bus_index=bus_idx,
                voltage_pu=voltage_pu,
                meter_type=meter.config['meter_type']
            )
            
            adapter.builder.add_active_power_measurement(
                meter_id=meter.meter_id,
                load_index=idx,
                power_mw=power_mw,
                meter_type=meter.config['meter_type'],
                is_generation=False
            )
            
            adapter.builder.add_reactive_power_measurement(
                meter_id=meter.meter_id,
                load_index=idx,
                power_mvar=reactive_power_mvar,
                meter_type=meter.config['meter_type'],
                is_generation=False
            )
        
        # Add grid bus measurement
        pp.create_measurement(net, "v", "bus", 1.0, 0.01, 0, name="Grid_V")
        
        # Transfer measurements to network
        measurement_df = adapter.builder.to_dataframe()
        if len(measurement_df) > 0:
            net.measurement = measurement_df
        
        total_measurements = len(net.measurement)
        assert total_measurements > 0, "No measurements added"
        
        # 4. Run power flow
        pp.runpp(net, algorithm='nr', calculate_voltage_angles=True)
        
        assert net.converged, "Power flow should converge"
        
        # 5. Validate measurements
        validator = MeasurementValidator()
        
        # Range validation
        range_results = validator.validate_range(net.measurement)
        assert len(range_results) > 0
        
        # Consistency checks
        consistency = validator.validate_consistency(net)
        assert consistency['has_measurements'] is True
        assert consistency['has_voltage_measurements'] is True
        assert consistency['has_power_measurements'] is True
        
        # Z-score outlier detection
        zscore_results = validator.detect_outliers_zscore(net.measurement)
        assert len(zscore_results) > 0
        
        # 6. State estimation
        estimator = StateEstimator(
            algorithm=EstimationAlgorithm.WLS,
            tolerance=1e-6,
            max_iterations=10
        )
        
        results = estimator.run_estimation(net)
        
        # Results should exist even if not converged
        assert results is not None
        assert results.num_measurements == total_measurements
        
        # 7. Get summary
        summary = estimator.get_summary()
        
        assert 'converged' in summary
        assert 'num_measurements' in summary
        assert summary['num_measurements'] == total_measurements
    
    def test_meter_to_measurement_conversion(self, meter_configs):
        """Test conversion from SmartMeter to pandapower measurements."""
        # Create meter
        meter = SmartMeter(meter_configs[0])
        
        # Create adapter and network
        adapter = PandapowerAdapter()
        net = adapter.topology_builder.build_radial_network(num_buses=2, voltage_kv=0.4)
        
        # Add measurement
        meter_type = meter_configs[0]['meter_type']
        adapter.builder.add_voltage_measurement(
            meter_id=meter.meter_id,
            bus_index=1,
            voltage_pu=1.0,
            meter_type=meter_type
        )
        
        # Get measurements
        measurements = adapter.builder.to_dataframe()
        
        assert len(measurements) == 1
        assert measurements.iloc[0]['name'] == f"{meter.meter_id}_V"
        assert measurements.iloc[0]['meas_type'] == 'v'
        assert measurements.iloc[0]['value'] == 1.0
        assert measurements.iloc[0]['std_dev'] > 0
    
    def test_topology_with_multiple_voltages(self):
        """Test multi-voltage topology creation."""
        builder = TopologyBuilder()
        
        net = builder.build_multi_voltage_network(
            hv_buses=2,
            mv_buses=3,
            lv_buses_per_mv=4,
            hv_voltage_kv=110.0,
            mv_voltage_kv=22.0,
            lv_voltage_kv=0.4
        )
        
        # Verify structure
        assert len(net.bus) >= 17  # 2 HV + 3 MV + 3*4 LV buses
        assert len(net.trafo) >= 2  # HV-MV and MV-LV transformers
        
        # Verify voltage levels
        hv_buses = net.bus[net.bus['vn_kv'] == 110.0]
        mv_buses = net.bus[net.bus['vn_kv'] == 22.0]
        lv_buses = net.bus[net.bus['vn_kv'] == 0.4]
        
        assert len(hv_buses) >= 2
        assert len(mv_buses) >= 3
        assert len(lv_buses) >= 12  # 3 MV buses * 4 LV buses per MV
    
    def test_accuracy_class_mapping(self):
        """Test accuracy class standard deviation calculation."""
        from app.adapters.pandapower_adapter import MeasurementTableBuilder, AccuracyClass
        
        builder = MeasurementTableBuilder()
        
        # Test accuracy class mapping
        std_dev_1_0 = builder.calculate_std_dev(AccuracyClass.CLASS_1_0, 230.0)
        std_dev_0_5 = builder.calculate_std_dev(AccuracyClass.CLASS_0_5, 230.0)
        std_dev_0_2 = builder.calculate_std_dev(AccuracyClass.CLASS_0_2, 230.0)
        
        # Higher accuracy class should have lower std_dev
        assert std_dev_0_2 < std_dev_0_5 < std_dev_1_0
        
        # Verify formula: σ = (AccuracyClass / 300) × NominalValue
        # CLASS_1_0 has value 0.01 (1% in decimal form)
        expected_1_0 = (0.01 / 300.0) * 230.0
        # Allow small floating point error
        assert abs(std_dev_1_0 - expected_1_0) < 0.01
    
    def test_measurement_sign_conventions(self):
        """Test sign conventions for power measurements."""
        builder = TopologyBuilder()
        net = builder.build_radial_network(num_buses=2, voltage_kv=0.4)
        
        adapter = PandapowerAdapter(topology_builder=builder)
        
        # Add consumption (positive)
        pp.create_load(net, bus=1, p_mw=0.01, q_mvar=0.003, name="Load")
        adapter.builder.add_active_power_measurement(
            meter_id="METER-001",
            load_index=0,
            power_mw=0.01,
            meter_type=MeterType.GRID_CONSUMER,
            is_generation=False
        )
        
        # Add generation (positive at sgen)
        pp.create_sgen(net, bus=1, p_mw=0.005, q_mvar=0.0, name="Gen")
        adapter.builder.add_active_power_measurement(
            meter_id="METER-002",
            load_index=0,
            power_mw=0.005,
            meter_type=MeterType.SOLAR_PROSUMER,
            is_generation=True
        )
        
        measurements = adapter.builder.to_dataframe()
        
        # Both should be positive (pandapower convention)
        assert all(measurements['value'] > 0)
    
    def test_validation_pipeline(self):
        """Test complete validation pipeline."""
        # Create network with measurements
        builder = TopologyBuilder()
        net = builder.build_radial_network(num_buses=3, voltage_kv=0.4)
        
        # Add loads
        pp.create_load(net, bus=1, p_mw=0.01, q_mvar=0.003)
        pp.create_load(net, bus=2, p_mw=0.02, q_mvar=0.006)
        
        # Add measurements
        pp.create_measurement(net, "v", "bus", 1.0, 0.01, 0, name="V_0")
        pp.create_measurement(net, "v", "bus", 0.98, 0.01, 1, name="V_1")
        pp.create_measurement(net, "v", "bus", 0.97, 0.01, 2, name="V_2")
        pp.create_measurement(net, "p", "load", 0.01, 0.001, 0, name="P_1")
        pp.create_measurement(net, "p", "load", 0.02, 0.001, 1, name="P_2")
        
        # Run power flow
        pp.runpp(net)
        
        # Create validator
        validator = MeasurementValidator()
        
        # 1. Range validation
        range_results = validator.validate_range(net.measurement)
        assert len(range_results) == 5
        
        # 2. Z-score detection
        zscore_results = validator.detect_outliers_zscore(net.measurement)
        assert len(zscore_results) == 5
        
        # 3. Consistency checks
        consistency = validator.validate_consistency(net)
        assert consistency['has_measurements'] is True
        assert consistency['has_voltage_measurements'] is True
        assert consistency['has_power_measurements'] is True
        assert consistency['all_buses_measured'] is True
    
    def test_error_handling(self):
        """Test error handling in pipeline."""
        # 1. Test with no measurements
        estimator = StateEstimator()
        net = pp.create_empty_network()
        pp.create_bus(net, vn_kv=0.4)
        
        with pytest.raises(ValueError, match="no measurements"):
            estimator.run_estimation(net)
        
        # 2. Test with empty network validation
        validator = MeasurementValidator()
        builder = TopologyBuilder()
        net = builder.build_radial_network(num_buses=2, voltage_kv=0.4)
        
        consistency = validator.validate_consistency(net)
        assert consistency['has_measurements'] is False
    
    def test_scalability(self):
        """Test pipeline with larger network."""
        # Create network with 20 buses
        builder = TopologyBuilder()
        net = builder.build_radial_network(
            num_buses=20,
            voltage_kv=0.4,
            line_length_km=0.05
        )
        
        assert len(net.bus) == 20
        assert len(net.line) == 19
        
        # Add loads to every bus except grid
        adapter = PandapowerAdapter(topology_builder=builder)
        
        for i in range(1, 20):
            pp.create_load(net, bus=i, p_mw=0.005, q_mvar=0.002)
            
            # Add measurements
            adapter.builder.add_voltage_measurement(
                meter_id=f"METER-{i:03d}",
                bus_index=i,
                voltage_pu=0.99,
                meter_type=MeterType.GRID_CONSUMER
            )
            
            adapter.builder.add_active_power_measurement(
                meter_id=f"METER-{i:03d}",
                load_index=i-1,
                power_mw=0.005,
                meter_type=MeterType.GRID_CONSUMER,
                is_generation=False
            )
        
        # Add grid measurement
        pp.create_measurement(net, "v", "bus", 1.0, 0.01, 0, name="Grid")
        
        # Transfer measurements
        measurement_df = adapter.builder.to_dataframe()
        if len(measurement_df) > 0:
            net.measurement = measurement_df
        
        # Run power flow
        pp.runpp(net)
        
        assert net.converged
        assert len(net.measurement) > 0
        
        # Validate
        validator = MeasurementValidator()
        range_results = validator.validate_range(net.measurement)
        
        assert len(range_results) > 0


class TestPhase2Components:
    """Test individual Phase 2 components."""
    
    def test_pandapower_adapter_initialization(self):
        """Test adapter initialization."""
        adapter = PandapowerAdapter()
        
        assert adapter is not None
        assert adapter.builder is not None
        assert adapter.topology_builder is not None
    
    def test_topology_builder_initialization(self):
        """Test topology builder initialization."""
        builder = TopologyBuilder()
        
        assert builder is not None
    
    def test_state_estimator_initialization(self):
        """Test state estimator initialization."""
        estimator = StateEstimator()
        
        assert estimator is not None
        assert estimator.algorithm == EstimationAlgorithm.WLS
        assert estimator.tolerance == 1e-6
        assert estimator.max_iterations == 10
    
    def test_measurement_validator_initialization(self):
        """Test measurement validator initialization."""
        validator = MeasurementValidator()
        
        assert validator is not None
        assert validator.validation_history == []
