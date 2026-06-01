import pytest
import os
from datetime import datetime
from smart_meter_simulator.models.reading import EnergyReading
from smart_meter_simulator.core.protocol_v4 import ProtocolV4Encoder, ProtocolV4Decoder


def test_protocol_v4_encode_decode():
    # 1. Setup test data
    reading = EnergyReading(
        meter_id="TEST-METER-001",
        timestamp=datetime(2026, 6, 1, 12, 0, 0),
        sequence_number=42,
        energy_generated=10.5,
        energy_consumed=5.2,
        surplus_energy=5.3,
        deficit_energy=0.0,
        battery_level=85.5,
        voltage=230.1,
        current=12.5,
        location="Bangkok",
        meter_type="Residential",
        user_type="Prosumer",
        manufacturer_id="GXT",
        logical_device_name="LDN-001"
    )
    
    # Generate a random 32-byte key
    device_key = os.urandom(32)
    
    # 2. Encode
    frame = ProtocolV4Encoder.encode(reading, device_key)
    
    assert len(frame) > 40
    assert frame[0] == 0x04 # Version
    assert frame[1] == len(frame) # Total Length
    
    # 3. Decode
    decoded = ProtocolV4Decoder.decode(frame, device_key)
    
    # 4. Verify
    assert decoded["manufacturer_id"] == "GXT"
    assert decoded["logical_device_name"] == "LDN-001"
    assert decoded["timestamp"].timestamp() == reading.timestamp.timestamp()
    assert decoded["energy_consumed"] == pytest.approx(5.2)
    assert decoded["energy_generated"] == pytest.approx(10.5)
    assert decoded["voltage"] == pytest.approx(230.1)
    assert decoded["current"] == pytest.approx(12.5)
    assert decoded["battery_level"] == pytest.approx(85.5)


def test_protocol_v4_invalid_key():
    reading = EnergyReading(
        meter_id="TEST-METER-001",
        timestamp=datetime.now(),
        energy_generated=1.0,
        energy_consumed=1.0,
        surplus_energy=0.0,
        deficit_energy=0.0,
        battery_level=50.0,
        location="Bangkok",
        meter_type="Residential",
        user_type="Prosumer"
    )
    
    device_key = os.urandom(32)
    wrong_key = os.urandom(32)
    
    frame = ProtocolV4Encoder.encode(reading, device_key)
    
    with pytest.raises(ValueError, match="Decryption failed"):
        ProtocolV4Decoder.decode(frame, wrong_key)


def test_protocol_v4_crc_mismatch():
    reading = EnergyReading(
        meter_id="TEST-METER-001",
        timestamp=datetime.now(),
        energy_generated=1.0,
        energy_consumed=1.0,
        surplus_energy=0.0,
        deficit_energy=0.0,
        battery_level=50.0,
        location="Bangkok",
        meter_type="Residential",
        user_type="Prosumer"
    )
    
    device_key = os.urandom(32)
    frame = bytearray(ProtocolV4Encoder.encode(reading, device_key))
    
    # Corrupt the frame (not the CRC)
    frame[10] ^= 0xFF
    
    with pytest.raises(ValueError, match="CRC-32 mismatch"):
        ProtocolV4Decoder.decode(bytes(frame), device_key)

def test_v4_signature_canonical_string():
    reading = EnergyReading(
        meter_id="TEST-METER-001",
        timestamp=datetime(2026, 6, 1, 12, 0, 0),
        sequence_number=123,
        energy_generated=10.5,
        energy_consumed=5.2,
        surplus_energy=5.3,
        deficit_energy=0.0,
        battery_level=85.5,
        location="Bangkok",
        meter_type="Residential",
        user_type="Prosumer"
    )
    
    ts_ms = int(reading.timestamp.timestamp() * 1000)
    expected = f"TEST-METER-001:5.300000:{ts_ms}:123"
    assert reading.get_v4_signature_canonical_string() == expected
