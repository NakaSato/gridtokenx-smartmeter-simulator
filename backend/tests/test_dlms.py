import pytest
from datetime import datetime
from smart_meter_simulator.models.reading import EnergyReading
from smart_meter_simulator.core.dlms import DlmsEncoder, ObisCode

@pytest.fixture
def sample_reading():
    return EnergyReading(
        meter_id="METER-001",
        timestamp=datetime(2026, 5, 23, 10, 0, 0),
        sequence_number=1,
        energy_generated=10.5,
        energy_consumed=5.2,
        surplus_energy=5.3,
        deficit_energy=0.0,
        interval_seconds=900,
        battery_level=85.5,
        voltage=230.5,
        current=10.2,
        reactive_power_kvar=1.5,
        power_factor=0.95,
        frequency=50.01,
        location="Bangkok",
        meter_type="Residential",
        user_type="Household",
        manufacturer_id="GXT",
        logical_device_name="LDN-001",
        meter_signature="SIG-123"
    )

def test_dlms_binary_encoding(sample_reading):
    payload = DlmsEncoder.encode_reading(sample_reading)
    assert isinstance(payload, bytes)
    
    # Header check: Manufacturer ID (3 bytes) + LDN (8 bytes)
    # GXT + LDN-001 (padded with \0)
    expected_header = b"GXT" + b"LDN-001".ljust(8, b"\0")
    assert payload.startswith(expected_header)
    
    # Timestamp check (next 8 bytes)
    ts = int(sample_reading.timestamp.timestamp())
    assert payload[11:19] == ts.to_bytes(8, byteorder="big")

def test_dlms_json_encoding(sample_reading):
    payload = DlmsEncoder.encode_reading_to_obis_json(sample_reading)
    assert isinstance(payload, dict)
    
    # Check key OBIS codes
    assert ObisCode.CLOCK in payload
    assert ObisCode.ACTIVE_ENERGY_IMPORT in payload
    assert ObisCode.ACTIVE_ENERGY_EXPORT in payload
    assert ObisCode.VOLTAGE_L1 in payload
    assert ObisCode.CURRENT_L1 in payload
    assert ObisCode.FREQUENCY in payload
    assert ObisCode.POWER_FACTOR in payload
    assert ObisCode.BATTERY_SOC in payload

    # Check values
    assert payload[ObisCode.ACTIVE_ENERGY_IMPORT]["value"] == 5200  # 5.2 * 1000
    assert payload[ObisCode.ACTIVE_ENERGY_EXPORT]["value"] == 10500 # 10.5 * 1000
    assert payload[ObisCode.VOLTAGE_L1]["value"] == 2305           # 230.5 * 10
    assert payload[ObisCode.FREQUENCY]["value"] == 5001            # 50.01 * 100
    assert payload["signature"] == "SIG-123"

def test_dlms_hex_conversion():
    data = b"\x01\x02\x03"
    hex_str = DlmsEncoder.to_hex(data)
    assert hex_str == "010203"

def test_obis_map():
    obis_map = DlmsEncoder.get_obis_map()
    assert obis_map[1] == ObisCode.ACTIVE_ENERGY_IMPORT
    assert obis_map[3] == ObisCode.VOLTAGE_L1

def test_dlms_negative_reactive_power(sample_reading):
    sample_reading.reactive_power_kvar = -2.5
    
    # Binary encoding
    payload = DlmsEncoder.encode_reading(sample_reading)
    # Map index 9 for negative reactive power
    assert 9 in payload 
    
    # JSON encoding
    payload_json = DlmsEncoder.encode_reading_to_obis_json(sample_reading)
    assert ObisCode.REACTIVE_POWER_EXPORT in payload_json
    assert payload_json[ObisCode.REACTIVE_POWER_EXPORT]["value"] == 2500

def test_interface_classes():
    from smart_meter_simulator.core.dlms import IC1Data, IC7ProfileGeneric
    
    ic1 = IC1Data.encode("1.2.3.4.5.6", 100)
    assert ic1["class_id"] == 1
    assert ic1["value"] == 100
    
    ic7 = IC7ProfileGeneric.encode("0.0.99.1.0.255", [], [], 900)
    assert ic7["class_id"] == 7
    assert ic7["capture_period"] == 900
