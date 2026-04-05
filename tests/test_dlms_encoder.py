import pytest
from datetime import datetime, timezone
from smart_meter_simulator.models.reading import EnergyReading
from smart_meter_simulator.core.dlms import DlmsEncoder, ObisCode

def test_dlms_encoding():
    # Create a mock reading
    reading = EnergyReading(
        meter_id="TEST_001",
        timestamp=datetime.now(timezone.utc),
        energy_generated=10.5,
        energy_consumed=20.2,
        surplus_energy=0.0,
        deficit_energy=9.7,
        location="Zone_1",
        meter_type="Residential",
        user_type="Consumer",
        voltage=230.5,
        current=5.2,
        battery_level=85.0,
        manufacturer_id="KMP",
        logical_device_name="LDN-00000001"
    )
    
    # Encode to binary
    binary_payload = DlmsEncoder.encode_reading(reading)
    assert isinstance(binary_payload, bytes)
    assert len(binary_payload) > 20
    
    # Check system title (Header: 3-byte Manu + 8-byte LDN)
    assert binary_payload.startswith(b"KMPLDN-0000")
    
    # Convert to hex
    hex_payload = DlmsEncoder.to_hex(binary_payload)
    assert isinstance(hex_payload, str)
    assert len(hex_payload) == len(binary_payload) * 2
    
    print(f"Encoded Hex Payload: {hex_payload}")

if __name__ == "__main__":
    test_dlms_encoding()
