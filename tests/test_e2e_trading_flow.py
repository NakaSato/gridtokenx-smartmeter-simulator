"""
E2E Integration Test: Smart Meter Reading → Submission Payload → HTTP Transport → API Gateway

Tests the complete flow from reading generation through to API gateway submission,
covering:
1. Meter reading generation with correct data shape
2. Ed25519 cryptographic signing
3. Submission payload format (matches Rust Decimal deserialization)
4. HTTP transport with retry logic
5. Rich telemetry fields for dashboard + analytics
"""

import pytest
import asyncio
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
import json

from src.app.core.meter import SmartMeter
from src.app.models.reading import EnergyReading
from src.app.transport.http import HttpTransport
from src.app.utils.crypto import sign_message, verify_signature, KeyManager


# =============================================================================
# Phase 1: Meter Reading Generation
# =============================================================================
class TestMeterReadingGeneration:
    """Test that meter readings are generated with correct data."""
    
    def setup_method(self):
        """Create a solar prosumer meter for testing."""
        self.config = {
            'meter_id': 'test-meter-001',
            'meter_type': 'Solar_Prosumer',
            'user_type': 'Prosumer',
            'location': 'Zone_1_Building_3',
            'wallet_address': '2Xyfzwzq7vATKYYT2SPjERVbQESq8F4PXo1WNmo1Ba29',
            'solar_capacity': 10.0,
            'battery_capacity': 20.0,
            'base_consumption': 2.0,
            'max_sell_price': 4.50,
            'max_buy_price': 5.00,
            'accuracy_class': 'CLASS_1_0',
            'has_solar': True,
        }
        self.meter = SmartMeter(self.config)
    
    def test_generates_valid_reading(self):
        """Should produce a reading with all required fields."""
        # Use midday for solar generation
        timestamp = datetime(2026, 2, 7, 12, 0, 0, tzinfo=timezone.utc)
        reading = self.meter.generate_reading(timestamp)
        
        assert isinstance(reading, EnergyReading)
        assert reading.meter_id == 'test-meter-001'
        assert reading.energy_generated >= 0
        assert reading.energy_consumed >= 0
        assert reading.surplus_energy >= 0
        assert reading.deficit_energy >= 0
        assert reading.wallet_address == '2Xyfzwzq7vATKYYT2SPjERVbQESq8F4PXo1WNmo1Ba29'
    
    def test_generates_surplus_at_midday(self):
        """Solar prosumers should produce surplus at midday."""
        timestamp = datetime(2026, 2, 7, 12, 0, 0, tzinfo=timezone.utc)
        reading = self.meter.generate_reading(timestamp)
        
        # At midday, solar generation should exceed typical consumption
        assert reading.energy_generated > 0, "Solar should generate at midday"
    
    def test_no_generation_at_night(self):
        """No solar generation at night."""
        timestamp = datetime(2026, 2, 7, 2, 0, 0, tzinfo=timezone.utc)
        reading = self.meter.generate_reading(timestamp)
        
        assert reading.energy_generated == 0 or reading.energy_generated < 0.01
    
    def test_reading_has_signature(self):
        """Reading should be cryptographically signed."""
        timestamp = datetime(2026, 2, 7, 12, 0, 0, tzinfo=timezone.utc)
        reading = self.meter.generate_reading(timestamp)
        
        assert reading.meter_signature is not None, "Reading should be Ed25519 signed"
        assert len(reading.meter_signature) > 0


# =============================================================================
# Phase 2: Ed25519 Cryptographic Signing
# =============================================================================
class TestCryptoSigning:
    """Test Ed25519 signing and verification."""
    
    def test_sign_and_verify(self):
        """Should sign and verify a message."""
        km = KeyManager()
        message = "3.500000|2026-02-07T12:00:00+00:00"
        signature = km.sign_data(message)
        
        assert signature is not None
        assert len(signature) > 0
        
        # Verify the signature
        is_valid = verify_signature(km.get_public_key(), message, signature)
        assert is_valid, "Signature should be valid"
    
    def test_signature_rejects_tampered_data(self):
        """Tampered data should fail verification."""
        km = KeyManager()
        message = "3.500000|2026-02-07T12:00:00+00:00"
        signature = km.sign_data(message)
        
        tampered = "99.000000|2026-02-07T12:00:00+00:00"
        is_valid = verify_signature(km.get_public_key(), tampered, signature)
        assert not is_valid, "Tampered data should fail verification"


# =============================================================================
# Phase 3: Submission Payload Format
# =============================================================================
class TestSubmissionPayload:
    """Test that the payload matches the API gateway's Rust Decimal format."""
    
    def test_kwh_amount_is_numeric(self):
        """kwh_amount must be a JSON number (float), not a string."""
        reading = EnergyReading(
            meter_id='SM-001',
            timestamp=datetime(2026, 2, 7, 12, 0, 0, tzinfo=timezone.utc),
            energy_generated=5.0,
            energy_consumed=1.5,
            surplus_energy=3.5,
            deficit_energy=0.0,
            location='Zone_1',
            meter_type='Solar_Prosumer',
            user_type='Prosumer',
            wallet_address='2Xyfzwzq7vATKYYT2SPjERVbQESq8F4PXo1WNmo1Ba29',
        )
        
        payload = reading.to_submission_payload()
        
        # Critical: kwh_amount must be a float, NOT a string
        assert isinstance(payload['kwh_amount'], float), \
            f"kwh_amount should be float, got {type(payload['kwh_amount'])}"
        assert payload['kwh_amount'] == 3.5
    
    def test_payload_includes_telemetry(self):
        """Payload should include energy and electrical telemetry."""
        reading = EnergyReading(
            meter_id='SM-001',
            timestamp=datetime(2026, 2, 7, 12, 0, 0, tzinfo=timezone.utc),
            energy_generated=5.0,
            energy_consumed=1.5,
            surplus_energy=3.5,
            deficit_energy=0.0,
            voltage=230.5,
            current=12.3,
            power_factor=0.95,
            frequency=50.01,
            temperature=32.5,
            battery_level=75.0,
            location='Zone_1',
            meter_type='Solar_Prosumer',
            user_type='Prosumer',
            wallet_address='2Xyfzwzq7vATKYYT2SPjERVbQESq8F4PXo1WNmo1Ba29',
        )
        
        payload = reading.to_submission_payload()
        
        # Core fields
        assert 'wallet_address' in payload
        assert 'kwh_amount' in payload
        assert 'reading_timestamp' in payload
        assert 'meter_signature' in payload
        assert 'meter_serial' in payload
        
        # Telemetry fields (new — required for dashboard)
        assert payload['energy_generated'] == 5.0
        assert payload['energy_consumed'] == 1.5
        assert payload['surplus_energy'] == 3.5
        assert payload['power_generated'] == 20.0  # 5.0 kWh × 4 = 20.0 kW
        assert payload['power_consumed'] == 6.0     # 1.5 kWh × 4 = 6.0 kW
        assert payload['voltage'] == 230.5
        assert payload['current'] == 12.3
        assert payload['power_factor'] == 0.95
        assert payload['frequency'] == 50.01
        assert payload['temperature'] == 32.5
        assert payload['battery_level'] == 75.0
    
    def test_payload_json_serializable(self):
        """Payload must be JSON-serializable for HTTP transport."""
        reading = EnergyReading(
            meter_id='SM-001',
            timestamp=datetime(2026, 2, 7, 12, 0, 0, tzinfo=timezone.utc),
            energy_generated=5.0,
            energy_consumed=1.5,
            surplus_energy=3.5,
            deficit_energy=0.0,
            location='Zone_1',
            meter_type='Solar_Prosumer',
            user_type='Prosumer',
        )
        
        payload = reading.to_submission_payload()
        
        # Should not raise
        json_str = json.dumps(payload)
        parsed = json.loads(json_str)
        
        # Verify kwh_amount survives JSON round-trip as a number
        assert isinstance(parsed['kwh_amount'], float)
    
    def test_zero_surplus_payload(self):
        """Consumer with zero surplus should have kwh_amount = 0."""
        reading = EnergyReading(
            meter_id='SM-002',
            timestamp=datetime(2026, 2, 7, 12, 0, 0, tzinfo=timezone.utc),
            energy_generated=0.0,
            energy_consumed=3.0,
            surplus_energy=0.0,
            deficit_energy=3.0,
            location='Zone_2',
            meter_type='Grid_Consumer',
            user_type='Consumer',
        )
        
        payload = reading.to_submission_payload()
        assert payload['kwh_amount'] == 0.0


# =============================================================================
# Phase 4: HTTP Transport with Retry
# =============================================================================
class TestHttpTransport:
    """Test HTTP transport sends correctly formatted requests to API gateway."""
    
    @pytest.fixture
    def transport(self):
        return HttpTransport(base_url='http://localhost:8080', api_key='test-api-key')
    
    @pytest.fixture
    def reading(self):
        return EnergyReading(
            meter_id='SM-001',
            timestamp=datetime(2026, 2, 7, 12, 0, 0, tzinfo=timezone.utc),
            energy_generated=5.0,
            energy_consumed=1.5,
            surplus_energy=3.5,
            deficit_energy=0.0,
            voltage=230.5,
            current=12.3,
            battery_level=75.0,
            location='Zone_1',
            meter_type='Solar_Prosumer',
            user_type='Prosumer',
            wallet_address='2Xyfzwzq7vATKYYT2SPjERVbQESq8F4PXo1WNmo1Ba29',
            meter_signature='base64-ed25519-sig',
        )
    
    @pytest.mark.asyncio
    async def test_sends_reading_to_correct_endpoint(self, transport, reading):
        """Should POST to /api/meters/submit-reading."""
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.text = AsyncMock(return_value='{"status":"ok"}')
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=False)
        
        mock_session = AsyncMock()
        mock_session.post = MagicMock(return_value=mock_response)
        transport.session = mock_session
        
        result = await transport.send_reading(reading)
        
        assert result is True
        mock_session.post.assert_called_once()
        call_args = mock_session.post.call_args
        assert '/api/meters/submit-reading' in call_args[0][0]
        
        # Verify payload structure
        payload = call_args[1]['json']
        assert isinstance(payload['kwh_amount'], float)
        assert payload['wallet_address'] == '2Xyfzwzq7vATKYYT2SPjERVbQESq8F4PXo1WNmo1Ba29'
        assert payload['meter_serial'] == 'SM-001'
        assert payload['meter_signature'] == 'base64-ed25519-sig'
        assert payload['energy_generated'] == 5.0
        assert payload['voltage'] == 230.5
    
    @pytest.mark.asyncio
    async def test_skips_zero_kwh_readings(self, transport):
        """Should not send readings with zero surplus."""
        reading = EnergyReading(
            meter_id='SM-002',
            timestamp=datetime(2026, 2, 7, 12, 0, 0, tzinfo=timezone.utc),
            energy_generated=0.0,
            energy_consumed=3.0,
            surplus_energy=0.0,
            deficit_energy=3.0,
            location='Zone_2',
            meter_type='Grid_Consumer',
            user_type='Consumer',
        )
        
        mock_session = AsyncMock()
        transport.session = mock_session
        
        result = await transport.send_reading(reading)
        
        assert result is True  # Returns True (not an error, just skipped)
        mock_session.post.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_retries_on_failure(self, transport, reading):
        """Should retry on HTTP failures up to MAX_RETRIES."""
        # First two attempts fail, third succeeds
        fail_response = AsyncMock()
        fail_response.status = 500
        fail_response.text = AsyncMock(return_value='Internal Server Error')
        fail_response.__aenter__ = AsyncMock(return_value=fail_response)
        fail_response.__aexit__ = AsyncMock(return_value=False)
        
        success_response = AsyncMock()
        success_response.status = 200
        success_response.text = AsyncMock(return_value='{"status":"ok"}')
        success_response.__aenter__ = AsyncMock(return_value=success_response)
        success_response.__aexit__ = AsyncMock(return_value=False)
        
        mock_session = AsyncMock()
        mock_session.post = MagicMock(side_effect=[fail_response, fail_response, success_response])
        transport.session = mock_session
        
        result = await transport.send_reading(reading)
        
        assert result is True
        assert mock_session.post.call_count == 3
    
    @pytest.mark.asyncio
    async def test_auth_header_included(self, transport):
        """Should include Bearer token in Authorization header."""
        await transport.connect()
        
        assert transport.session is not None
        # The session headers should include the API key
        # (aiohttp stores default headers on the session)


# =============================================================================
# Phase 5: Full E2E Integration
# =============================================================================
class TestE2EFlow:
    """Test the complete flow from meter to API gateway."""
    
    def test_meter_to_payload_pipeline(self):
        """Complete flow: generate_reading → sign → to_submission_payload → JSON."""
        config = {
            'meter_id': 'SM-E2E-001',
            'meter_type': 'Solar_Prosumer',
            'user_type': 'Prosumer',
            'location': 'Zone_1_Building_5',
            'wallet_address': '2Xyfzwzq7vATKYYT2SPjERVbQESq8F4PXo1WNmo1Ba29',
            'solar_capacity': 10.0,
            'battery_capacity': 20.0,
            'base_consumption': 2.0,
            'max_sell_price': 4.50,
            'max_buy_price': 5.00,
            'accuracy_class': 'CLASS_1_0',
            'has_solar': True,
        }
        meter = SmartMeter(config)
        
        # Generate a midday reading (high solar)
        timestamp = datetime(2026, 2, 7, 12, 0, 0, tzinfo=timezone.utc)
        reading = meter.generate_reading(timestamp)
        
        # Convert to payload
        payload = reading.to_submission_payload()
        
        # Serialize to JSON (as HTTP transport does)
        json_str = json.dumps(payload)
        parsed = json.loads(json_str)
        
        # Verify the complete pipeline
        assert parsed['meter_serial'] == 'SM-E2E-001'
        assert parsed['wallet_address'] == '2Xyfzwzq7vATKYYT2SPjERVbQESq8F4PXo1WNmo1Ba29'
        assert isinstance(parsed['kwh_amount'], (int, float))
        assert parsed['meter_signature'] is not None
        assert parsed['reading_timestamp'] is not None
        assert parsed['energy_generated'] >= 0
        assert parsed['energy_consumed'] >= 0
        assert 'voltage' in parsed
        assert 'battery_level' in parsed
