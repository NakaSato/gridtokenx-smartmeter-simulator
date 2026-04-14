"""
EV Charger and DC Fast Charger Test Suite

Tests for:
- EV Level 2 AC charger behavior (V2G, driving drain, charging)
- DC Fast Charger behavior (high power, no V2G, multi-port)
- Charging station multi-port load balancing
- SoC tracking accuracy
- Rust engine EV parity
"""

import pytest
import random
from datetime import datetime
from unittest.mock import patch

from smart_meter_simulator.config.enums import MeterType, AccuracyClass
from smart_meter_simulator.core.meter import SmartMeter
from smart_meter_simulator.core.charging_station import ChargingStation, EVPort


class TestEVChargerBasic:
    """Test EV Level 2 AC charger basic functionality"""
    
    def test_ev_charger_enum_exists(self):
        """Verify EV_Charger meter type enum exists"""
        assert MeterType.EV_CHARGER.value == "EV_Charger"
    
    def test_ev_charger_accuracy_class(self):
        """EV chargers use CLASS_1_0 accuracy"""
        meter = SmartMeter({
            'meter_id': 'ev_test_001',
            'meter_type': 'EV_Charger',
        })
        assert meter.accuracy_class == AccuracyClass.CLASS_1_0
    
    def test_ev_charger_has_soc_channel(self):
        """EV charger includes SoC channel"""
        meter = SmartMeter({
            'meter_id': 'ev_test_002',
            'meter_type': 'EV_Charger',
        })
        assert 'soc' in meter.channels


class TestEVChargerBehavior:
    """Test EV charging behavior patterns"""
    
    def test_v2g_discharge_during_peak(self):
        """V2G discharges during peak hours (18-21) when SoC > threshold"""
        config = {
            'meter_id': 'ev_v2g_test',
            'meter_type': 'EV_Charger',
            'has_battery': False,  # EV manages its own battery
            'current_battery_level': 60.0,  # 60% SoC
            'ev_battery_capacity': 60.0,
            'ev_charge_rate_kw': 7.4,
            'ev_v2g_discharge_rate_kw': 5.0,
            'ev_v2g_threshold_soc': 0.4,
        }
        meter = SmartMeter(config)
        
        # Peak hour: 19:00
        timestamp = datetime(2024, 1, 1, 19, 0, 0)
        initial_soc = meter.battery_level
        
        reading = meter.generate_reading(
            timestamp=timestamp,
            interval_seconds=900,
        )
        
        # Should discharge (energy_generated > 0)
        assert reading.energy_generated > 0, "V2G should generate during peak"
        assert meter.battery_level < initial_soc, "SoC should decrease during V2G"
    
    def test_ev_charging_when_low_soc(self):
        """EV charges when SoC < 90%"""
        config = {
            'meter_id': 'ev_charge_test',
            'meter_type': 'EV_Charger',
            'has_battery': False,  # EV manages its own battery
            'current_battery_level': 30.0,  # 30% SoC
            'ev_battery_capacity': 60.0,
            'ev_charge_rate_kw': 7.4,
            'ev_v2g_discharge_rate_kw': 5.0,
            'ev_v2g_threshold_soc': 0.4,
        }
        meter = SmartMeter(config)
        
        # Off-peak hour: 2:00 AM (not V2G time)
        timestamp = datetime(2024, 1, 1, 2, 0, 0)
        initial_soc = meter.battery_level
        
        reading = meter.generate_reading(
            timestamp=timestamp,
            interval_seconds=900,
        )
        
        # Should charge (energy_consumed > 0)
        assert reading.energy_consumed > 0, "EV should charge when SoC < 90%"
        assert meter.battery_level > initial_soc, "SoC should increase during charging"
    
    def test_ev_driving_drain_during_day(self):
        """EV loses SoC during driving hours (8-18)"""
        config = {
            'meter_id': 'ev_driving_test',
            'meter_type': 'EV_Charger',
            'has_battery': False,  # EV manages its own battery
            'current_battery_level': 50.0,
            'ev_battery_capacity': 60.0,
            'ev_charge_rate_kw': 7.4,
            'ev_v2g_discharge_rate_kw': 5.0,
            'ev_v2g_threshold_soc': 0.4,
        }
        meter = SmartMeter(config)
        
        # Driving hour: 12:00 PM
        timestamp = datetime(2024, 1, 1, 12, 0, 0)
        initial_soc = meter.battery_level
        
        meter.generate_reading(
            timestamp=timestamp,
            interval_seconds=900,
        )
        
        # SoC should decrease due to driving
        assert meter.battery_level < initial_soc, "SoC should decrease during driving hours"
        assert meter.battery_level >= 20.0, "SoC should not drop below 20%"


class TestDCFastCharger:
    """Test DC Fast Charger functionality"""
    
    def test_dc_fast_charger_enum_exists(self):
        """Verify DC_Fast_Charger meter type enum exists"""
        assert MeterType.DC_FAST_CHARGER.value == "DC_Fast_Charger"
    
    def test_dc_fast_charger_accuracy_class(self):
        """DC fast chargers use CLASS_0_5 accuracy (higher precision)"""
        meter = SmartMeter({
            'meter_id': 'dc_test_001',
            'meter_type': 'DC_Fast_Charger',
        })
        assert meter.accuracy_class == AccuracyClass.CLASS_0_5
    
    def test_dc_fast_charger_has_extra_channels(self):
        """DC fast charger has connector_count and port_status channels"""
        meter = SmartMeter({
            'meter_id': 'dc_test_002',
            'meter_type': 'DC_Fast_Charger',
        })
        assert 'soc' in meter.channels
        assert 'connector_count' in meter.channels
        assert 'port_status' in meter.channels
    
    def test_dc_fast_charger_no_v2g(self):
        """DC fast chargers don't support V2G (no discharge)"""
        config = {
            'meter_id': 'dc_no_v2g_test',
            'meter_type': 'DC_Fast_Charger',
            'has_battery': False,
            'current_battery_level': 60.0,
            'ev_battery_capacity': 60.0,
            'ev_charge_rate_kw': 150.0,
            'ev_v2g_discharge_rate_kw': 0.0,  # DC doesn't V2G
            'ev_v2g_threshold_soc': 0.0,
            'connector_count': 4,
            'max_station_capacity_kw': 600.0,
        }
        meter = SmartMeter(config)
        
        # Peak hour
        timestamp = datetime(2024, 1, 1, 19, 0, 0)
        
        reading = meter.generate_reading(
            timestamp=timestamp,
            interval_seconds=900,
        )
        
        # DC fast charger should never generate (no V2G)
        assert reading.energy_generated == 0.0, "DC fast charger should not V2G"
        assert reading.energy_consumed > 0.0, "DC fast charger should consume power"
    
    def test_dc_fast_charger_high_power(self):
        """DC fast charger consumes much more power than AC charger"""
        dc_config = {
            'meter_id': 'dc_high_power_test',
            'meter_type': 'DC_Fast_Charger',
            'has_battery': False,
            'current_battery_level': 30.0,
            'ev_battery_capacity': 60.0,
            'ev_charge_rate_kw': 150.0,
            'ev_v2g_discharge_rate_kw': 0.0,
            'ev_v2g_threshold_soc': 0.0,
            'connector_count': 4,
            'max_station_capacity_kw': 600.0,
        }
        dc_meter = SmartMeter(dc_config)
        
        ac_config = {
            'meter_id': 'ac_comparison_test',
            'meter_type': 'EV_Charger',
            'has_battery': False,
            'current_battery_level': 30.0,
            'ev_battery_capacity': 60.0,
            'ev_charge_rate_kw': 7.4,
            'ev_v2g_discharge_rate_kw': 5.0,
            'ev_v2g_threshold_soc': 0.4,
        }
        ac_meter = SmartMeter(ac_config)
        
        # Same time (off-peak to avoid V2G)
        timestamp = datetime(2024, 1, 1, 2, 0, 0)
        
        dc_reading = dc_meter.generate_reading(
            timestamp=timestamp,
            interval_seconds=900,
        )
        ac_reading = ac_meter.generate_reading(
            timestamp=timestamp,
            interval_seconds=900,
        )
        
        # DC should consume much more power
        assert dc_reading.energy_consumed > ac_reading.energy_consumed, \
            "DC fast charger should consume more power than AC charger"


class TestChargingStation:
    """Test multi-port charging station functionality"""
    
    def test_station_initialization(self):
        """Station initializes with correct number of ports"""
        station = ChargingStation(
            station_id='STATION_001',
            meter_id='METER_001',
            num_ports=4,
            max_station_capacity_kw=600.0,
        )
        assert len(station.ports) == 4
        assert station.num_ports == 4
        assert station.max_station_capacity_kw == 600.0
        assert station.get_utilization() == 0.0
    
    def test_port_occupation(self):
        """Port can be occupied and released"""
        station = ChargingStation(
            station_id='STATION_002',
            meter_id='METER_002',
            num_ports=2,
        )
        
        port = station.get_available_port()
        assert port is not None
        assert not port.occupied
        
        station.occupy_port(port, initial_soc=30.0, capacity_kwh=60.0)
        assert port.occupied
        assert port.vehicle_soc == 30.0
        
        session = station.release_port(port)
        assert not port.occupied
        assert 'energy_delivered_kwh' in session
    
    def test_load_balancing(self):
        """Load balancing caps total power at station capacity"""
        station = ChargingStation(
            station_id='STATION_003',
            meter_id='METER_003',
            num_ports=4,
            max_station_capacity_kw=600.0,
            base_charge_rate_kw=150.0,
        )
        
        # Occupy all ports
        for port in station.ports:
            station.occupy_port(port, initial_soc=30.0, capacity_kwh=60.0)
        
        power_dist = station.calculate_power_distribution()
        total_power = sum(power_dist.values())
        
        # Should not exceed station capacity
        assert total_power <= 600.0, "Total power should not exceed station capacity"
    
    def test_charging_simulation(self):
        """Charging simulation updates SoC correctly"""
        station = ChargingStation(
            station_id='STATION_004',
            meter_id='METER_004',
            num_ports=2,
            max_station_capacity_kw=300.0,
        )
        
        # Occupy one port
        port = station.get_available_port()
        station.occupy_port(port, initial_soc=20.0, capacity_kwh=60.0)
        initial_soc = port.vehicle_soc
        
        energy = station.simulate_charging(interval_hours=0.25)
        
        assert port.vehicle_soc > initial_soc, "SoC should increase after charging"
        assert port.port_id in energy, "Should return energy for active port"
        assert energy[port.port_id] > 0, "Energy delivered should be positive"
    
    def test_cc_cv_charging_curve(self):
        """CC-CV curve: charging rate drops at high SoC"""
        station = ChargingStation(
            station_id='STATION_005',
            meter_id='METER_005',
            num_ports=1,
            max_station_capacity_kw=200.0,
        )
        
        # Test at low SoC (CC phase)
        port_low = station.ports[0]
        station.occupy_port(port_low, initial_soc=30.0, capacity_kwh=60.0)
        power_low = station.calculate_power_distribution()[port_low.port_id]
        station.release_port(port_low)
        
        # Test at high SoC (CV phase)
        port_high = station.ports[0]
        station.occupy_port(port_high, initial_soc=90.0, capacity_kwh=60.0)
        power_high = station.calculate_power_distribution()[port_high.port_id]
        station.release_port(port_high)
        
        assert power_high < power_low, "Power should drop at high SoC (CV phase)"
    
    def test_station_utilization(self):
        """Utilization calculation is correct"""
        station = ChargingStation(
            station_id='STATION_006',
            meter_id='METER_006',
            num_ports=4,
        )
        
        assert station.get_utilization() == 0.0
        
        # Occupy 2 ports
        for i in range(2):
            port = station.get_available_port()
            station.occupy_port(port)
        
        assert station.get_utilization() == 0.5
    
    def test_full_station_rejects_arrival(self):
        """Full station returns False for new arrival"""
        station = ChargingStation(
            station_id='STATION_007',
            meter_id='METER_007',
            num_ports=2,
        )
        
        # Fill all ports
        for _ in range(2):
            port = station.get_available_port()
            station.occupy_port(port)
        
        assert station.get_available_port() is None
        assert not station.random_vehicle_arrival()


class TestRustEngineEVParity:
    """Test Rust engine EV field passing"""
    
    def test_rust_engine_config_conversion(self):
        """EV fields are correctly passed to Rust config"""
        try:
            from smart_meter_simulator.core.rust_engine import (
                RustAcceleratedMeter,
                USE_RUST_ENGINE,
            )
            
            if not USE_RUST_ENGINE:
                pytest.skip("Rust engine not available")
            
            config = {
                'meter_id': 'rust_ev_test',
                'meter_type': 'EV_Charger',
                'has_solar': False,
                'has_battery': True,
                'solar_capacity': 0.0,
                'battery_capacity': 10.0,
                'base_consumption': 1.0,
                'panel_efficiency': 0.0,
                'current_battery_level': 50.0,
                'price_elasticity': 0.15,
                'accuracy_class': 1.0,
                'ev_battery_capacity': 60.0,
                'ev_charge_rate_kw': 7.4,
                'ev_v2g_discharge_rate_kw': 5.0,
                'ev_v2g_threshold_soc': 0.4,
                'connector_count': 4,
                'max_station_capacity_kw': 600.0,
            }
            
            rust_config = RustAcceleratedMeter.convert_meter_to_rust_config(config)
            
            assert rust_config.ev_battery_capacity_kwh == 60.0
            assert rust_config.ev_charge_rate_kw == 7.4
            assert rust_config.ev_v2g_discharge_rate_kw == 5.0
            assert rust_config.ev_v2g_threshold_soc == 0.4
            assert rust_config.is_dc_fast_charger is False
            
        except ImportError:
            pytest.skip("Rust engine not available")
    
    def test_dc_fast_charger_config_conversion(self):
        """DC fast charger fields are correctly passed to Rust config"""
        try:
            from smart_meter_simulator.core.rust_engine import (
                RustAcceleratedMeter,
                USE_RUST_ENGINE,
            )
            
            if not USE_RUST_ENGINE:
                pytest.skip("Rust engine not available")
            
            config = {
                'meter_id': 'rust_dc_test',
                'meter_type': 'DC_Fast_Charger',
                'has_solar': False,
                'has_battery': True,
                'solar_capacity': 0.0,
                'battery_capacity': 10.0,
                'base_consumption': 1.0,
                'panel_efficiency': 0.0,
                'current_battery_level': 30.0,
                'price_elasticity': 0.15,
                'accuracy_class': 0.5,
                'ev_battery_capacity': 60.0,
                'ev_charge_rate_kw': 150.0,
                'ev_v2g_discharge_rate_kw': 0.0,
                'ev_v2g_threshold_soc': 0.0,
                'connector_count': 4,
                'max_station_capacity_kw': 600.0,
            }
            
            rust_config = RustAcceleratedMeter.convert_meter_to_rust_config(config)
            
            assert rust_config.is_dc_fast_charger is True
            assert rust_config.ev_charge_rate_kw == 150.0
            assert rust_config.ev_v2g_discharge_rate_kw == 0.0
            assert rust_config.connector_count == 4
            
        except ImportError:
            pytest.skip("Rust engine not available")


class TestMeterGeneratorEVConfig:
    """Test meter generator creates correct EV/DC configs"""
    
    def test_ev_charger_config_has_ev_fields(self):
        """EV charger config includes EV-specific fields"""
        from smart_meter_simulator.meter_generator import MeterGenerator
        from smart_meter_simulator.config import get_config
        
        gen = MeterGenerator(num_meters=10)
        
        # Force create an EV charger
        ev_config = gen._create_meter_config(1, MeterType.EV_CHARGER)
        
        assert 'ev_battery_capacity' in ev_config
        assert 'ev_charge_rate_kw' in ev_config
        assert 'ev_v2g_discharge_rate_kw' in ev_config
        assert 'ev_v2g_threshold_soc' in ev_config
        assert ev_config['ev_v2g_discharge_rate_kw'] > 0
    
    def test_dc_fast_charger_config_has_high_power(self):
        """DC fast charger config has high charge rate"""
        from smart_meter_simulator.meter_generator import MeterGenerator
        
        gen = MeterGenerator(num_meters=10)
        
        dc_config = gen._create_meter_config(1, MeterType.DC_FAST_CHARGER)
        
        assert dc_config['ev_charge_rate_kw'] in [50, 150, 350]
        assert dc_config['ev_v2g_discharge_rate_kw'] == 0.0
        assert 'connector_count' in dc_config
        assert 'max_station_capacity_kw' in dc_config
        assert dc_config['priority'] == 2


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
