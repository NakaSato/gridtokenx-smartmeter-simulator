"""
Unit tests for SmartMeter class.

Tests cover:
- Reading generation edge cases
- Battery charge/discharge logic
- Signature generation and verification
- Weather impact on solar generation
- Time-of-day solar curves
"""

import pytest
from datetime import datetime, timezone
from app.core.meter import SmartMeter
from app.config import MeterType
from app.utils.crypto import verify_signature


class TestSmartMeterInitialization:
    """Test SmartMeter initialization and configuration."""
    
    def test_meter_initialization_basic(self):
        """Test basic meter initialization with minimal config."""
        config = {
            'meter_id': 'TEST_METER_001',
            'location': 'Test Location',
            'meter_type': MeterType.GRID_CONSUMER,
            'user_type': 'RESIDENTIAL',
        }
        meter = SmartMeter(config)
        
        assert meter.meter_id == 'TEST_METER_001'
        assert meter.battery_level == 0.0
        assert meter.current_weather == "Sunny"
        assert meter.key_manager is not None
        
    def test_meter_initialization_with_battery(self):
        """Test meter initialization with battery configuration."""
        config = {
            'meter_id': 'TEST_METER_002',
            'location': 'Test Location',
            'meter_type': MeterType.HYBRID_PROSUMER,
            'user_type': 'PROSUMER',
            'has_battery': True,
            'current_battery_level': 50.0,
            'battery_capacity': 10.0,
        }
        meter = SmartMeter(config)
        
        assert meter.battery_level == 50.0
        assert meter.config['has_battery'] is True
        assert meter.config['battery_capacity'] == 10.0


class TestSolarGeneration:
    """Test solar generation calculations."""
    
    @pytest.fixture
    def solar_meter(self):
        """Fixture for a solar prosumer meter."""
        config = {
            'meter_id': 'SOLAR_001',
            'location': 'Test Location',
            'meter_type': MeterType.SOLAR_PROSUMER,
            'user_type': 'PROSUMER',
            'has_solar': True,
            'solar_capacity': 5.0,  # 5 kW system
            'panel_efficiency': 0.18,
        }
        return SmartMeter(config)
    
    def test_solar_generation_night_time_is_zero(self, solar_meter):
        """Test that solar generation is zero during night time (0-5 AM)."""
        timestamp = datetime(2024, 6, 15, 2, 0, 0, tzinfo=timezone.utc)  # 2 AM
        reading = solar_meter.generate_reading(timestamp)
        
        assert reading.energy_generated == 0.0
        
    def test_solar_generation_early_morning_is_zero(self, solar_meter):
        """Test that solar generation is zero before 6 AM."""
        timestamp = datetime(2024, 6, 15, 5, 30, 0, tzinfo=timezone.utc)  # 5:30 AM
        reading = solar_meter.generate_reading(timestamp)
        
        assert reading.energy_generated == 0.0
        
    def test_solar_generation_evening_is_zero(self, solar_meter):
        """Test that solar generation is zero after 6 PM."""
        timestamp = datetime(2024, 6, 15, 19, 0, 0, tzinfo=timezone.utc)  # 7 PM
        reading = solar_meter.generate_reading(timestamp)
        
        assert reading.energy_generated == 0.0
        
    def test_solar_generation_noon_is_maximum(self, solar_meter):
        """Test that solar generation is maximum around noon."""
        timestamp_noon = datetime(2024, 6, 15, 12, 0, 0, tzinfo=timezone.utc)
        reading_noon = solar_meter.generate_reading(timestamp_noon)
        
        # Noon should have higher generation than morning/evening
        timestamp_morning = datetime(2024, 6, 15, 8, 0, 0, tzinfo=timezone.utc)
        reading_morning = solar_meter.generate_reading(timestamp_morning)
        
        assert reading_noon.energy_generated > reading_morning.energy_generated
        assert reading_noon.energy_generated > 0
        
    def test_solar_generation_weather_impact(self, solar_meter):
        """Test that weather affects solar generation."""
        timestamp = datetime(2024, 6, 15, 12, 0, 0, tzinfo=timezone.utc)
        
        # Sunny weather
        solar_meter.update_weather("Sunny")
        reading_sunny = solar_meter.generate_reading(timestamp)
        
        # Cloudy weather
        solar_meter.update_weather("Cloudy")
        reading_cloudy = solar_meter.generate_reading(timestamp)
        
        # Rainy weather
        solar_meter.update_weather("Rainy")
        reading_rainy = solar_meter.generate_reading(timestamp)
        
        # Verify weather impact hierarchy
        assert reading_sunny.energy_generated > reading_cloudy.energy_generated
        assert reading_cloudy.energy_generated > reading_rainy.energy_generated


class TestBatteryManagement:
    """Test battery charge/discharge logic."""
    
    @pytest.fixture
    def battery_meter(self):
        """Fixture for a meter with battery storage."""
        config = {
            'meter_id': 'BATTERY_001',
            'location': 'Test Location',
            'meter_type': MeterType.BATTERY_STORAGE,
            'user_type': 'PROSUMER',
            'has_battery': True,
            'has_solar': True,
            'battery_capacity': 10.0,  # 10 kWh
            'current_battery_level': 5.0,  # Start at 50%
            'solar_capacity': 5.0,
        }
        return SmartMeter(config)
    
    def test_battery_charges_with_surplus(self, battery_meter):
        """Test battery charges when there's surplus energy."""
        # Set low consumption to create surplus
        battery_meter.config['base_consumption'] = 0.1
        
        initial_level = battery_meter.battery_level
        timestamp = datetime(2024, 6, 15, 12, 0, 0, tzinfo=timezone.utc)  # Noon - high solar
        
        reading = battery_meter.generate_reading(timestamp)
        
        # Battery should charge if there's surplus
        if reading.surplus_energy > 0:
            assert battery_meter.battery_level >= initial_level
            
    def test_battery_discharges_with_deficit(self, battery_meter):
        """Test battery discharges when there's energy deficit."""
        # Set high consumption to create deficit
        battery_meter.config['base_consumption'] = 10.0
        battery_meter.battery_level = 80.0  # High charge level
        
        initial_level = battery_meter.battery_level
        timestamp = datetime(2024, 6, 15, 20, 0, 0, tzinfo=timezone.utc)  # 8 PM - no solar
        
        reading = battery_meter.generate_reading(timestamp)
        
        # Battery should discharge if there's deficit
        if reading.deficit_energy > 0 and initial_level > 0:
            assert battery_meter.battery_level <= initial_level
            
        # Try to charge beyond 100% capacity
        battery_meter.battery_level = battery_meter.config['battery_capacity'] - 0.5
        battery_meter.config['base_consumption'] = 0.0  # No consumption
        
        timestamp = datetime(2024, 6, 15, 12, 0, 0, tzinfo=timezone.utc)
        battery_meter.generate_reading(timestamp)
        
        assert 0.0 <= battery_meter.battery_level <= 100.0
        
        # Try to discharge below 0%
        battery_meter.battery_level = 5.0
        battery_meter.config['base_consumption'] = 20.0  # High consumption
        battery_meter.config['has_solar'] = False
        
        timestamp_night = datetime(2024, 6, 15, 22, 0, 0, tzinfo=timezone.utc)
        battery_meter.generate_reading(timestamp_night)
        
        assert 0.0 <= battery_meter.battery_level <= 100.0


class TestSignatureGeneration:
    """Test cryptographic signature generation and verification."""
    
    @pytest.fixture
    def test_meter(self):
        """Fixture for basic test meter."""
        config = {
            'meter_id': 'SIG_TEST_001',
            'location': 'Test Location',
            'meter_type': MeterType.GRID_CONSUMER,
            'user_type': 'RESIDENTIAL',
        }
        return SmartMeter(config)
    
    def test_reading_has_signature(self, test_meter):
        """Test that generated reading contains a signature."""
        timestamp = datetime(2024, 6, 15, 12, 0, 0, tzinfo=timezone.utc)
        reading = test_meter.generate_reading(timestamp)
        
        assert reading.meter_signature is not None
        assert isinstance(reading.meter_signature, str)
        assert len(reading.meter_signature) > 0
        
    def test_signature_is_valid(self, test_meter):
        """Test that generated signature can be verified."""
        timestamp = datetime(2024, 6, 15, 12, 0, 0, tzinfo=timezone.utc)
        reading = test_meter.generate_reading(timestamp)
        
        # Reconstruct payload
        kwh_str = f"{reading.energy_generated:.6f}"
        timestamp_str = reading.timestamp.isoformat()
        payload = f"{kwh_str}|{timestamp_str}"
        
        # Verify signature
        is_valid = verify_signature(
            test_meter.key_manager.get_public_key(),
            payload,
            reading.meter_signature
        )
        
        assert is_valid is True
        
    def test_signature_changes_with_different_readings(self, test_meter):
        """Test that different readings produce different signatures."""
        timestamp1 = datetime(2024, 6, 15, 12, 0, 0, tzinfo=timezone.utc)
        reading1 = test_meter.generate_reading(timestamp1)
        
        timestamp2 = datetime(2024, 6, 15, 13, 0, 0, tzinfo=timezone.utc)
        reading2 = test_meter.generate_reading(timestamp2)
        
        # Signatures should differ (different timestamps)
        assert reading1.meter_signature != reading2.meter_signature


class TestRECandCarbonOffset:
    """Test REC eligibility and carbon offset calculations."""
    
    def test_rec_eligible_with_solar_generation(self):
        """Test REC eligibility when solar is generating."""
        config = {
            'meter_id': 'REC_001',
            'location': 'Test Location',
            'meter_type': MeterType.SOLAR_PROSUMER,
            'user_type': 'PROSUMER',
            'has_solar': True,
            'solar_capacity': 5.0,
        }
        meter = SmartMeter(config)
        
        timestamp = datetime(2024, 6, 15, 12, 0, 0, tzinfo=timezone.utc)  # Noon
        reading = meter.generate_reading(timestamp)
        
        if reading.energy_generated > 0:
            assert reading.rec_eligible is True
            assert reading.carbon_offset > 0
            
    def test_rec_not_eligible_without_solar(self):
        """Test REC not eligible for non-solar meters."""
        config = {
            'meter_id': 'REC_002',
            'location': 'Test Location',
            'meter_type': MeterType.GRID_CONSUMER,
            'user_type': 'RESIDENTIAL',
            'has_solar': False,
        }
        meter = SmartMeter(config)
        
        timestamp = datetime(2024, 6, 15, 12, 0, 0, tzinfo=timezone.utc)
        reading = meter.generate_reading(timestamp)
        
        assert reading.rec_eligible is False
        assert reading.carbon_offset == 0.0
        
    def test_rec_not_eligible_at_night(self):
        """Test REC not eligible when no solar generation (night)."""
        config = {
            'meter_id': 'REC_003',
            'location': 'Test Location',
            'meter_type': MeterType.SOLAR_PROSUMER,
            'user_type': 'PROSUMER',
            'has_solar': True,
            'solar_capacity': 5.0,
        }
        meter = SmartMeter(config)
        
        timestamp = datetime(2024, 6, 15, 2, 0, 0, tzinfo=timezone.utc)  # 2 AM
        reading = meter.generate_reading(timestamp)
        
        assert reading.rec_eligible is False
        assert reading.carbon_offset == 0.0


class TestEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_zero_solar_capacity(self):
        """Test meter with zero solar capacity."""
        config = {
            'meter_id': 'EDGE_001',
            'location': 'Test Location',
            'meter_type': MeterType.SOLAR_PROSUMER,
            'user_type': 'PROSUMER',
            'has_solar': True,
            'solar_capacity': 0.0,  # Zero capacity
        }
        meter = SmartMeter(config)
        
        timestamp = datetime(2024, 6, 15, 12, 0, 0, tzinfo=timezone.utc)
        reading = meter.generate_reading(timestamp)
        
        assert reading.energy_generated == 0.0
        
    def test_negative_grid_consumption(self):
        """Test handling of surplus energy (negative grid consumption)."""
        config = {
            'meter_id': 'EDGE_002',
            'location': 'Test Location',
            'meter_type': MeterType.SOLAR_PROSUMER,
            'user_type': 'PROSUMER',
            'has_solar': True,
            'solar_capacity': 10.0,  # High capacity
            'base_consumption': 0.5,  # Low consumption
        }
        meter = SmartMeter(config)
        
        timestamp = datetime(2024, 6, 15, 12, 0, 0, tzinfo=timezone.utc)
        reading = meter.generate_reading(timestamp)
        
        # Should have surplus when generation > consumption
        if reading.energy_generated > reading.energy_consumed:
            assert reading.surplus_energy > 0
            assert reading.deficit_energy == 0
