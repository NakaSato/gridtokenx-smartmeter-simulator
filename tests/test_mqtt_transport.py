import asyncio
import json
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from smart_meter_simulator.core.dlms import DlmsEncoder
from smart_meter_simulator.models.reading import EnergyReading
from smart_meter_simulator.transport.mqtt import MqttTransport


@pytest.mark.asyncio
async def test_mqtt_transport_send_reading():
    # Arrange
    reading = EnergyReading(
        meter_id="TEST_002",
        timestamp=datetime.now(timezone.utc),
        energy_generated=15.0,
        energy_consumed=25.0,
        surplus_energy=0.0,
        deficit_energy=10.0,
        battery_level=90.0,
        location="Zone_2",
        meter_type="Residential",
        user_type="Consumer",
        voltage=230.0,
        current=10.0,
        manufacturer_id="GXT",
        logical_device_name="LDN-TEST00"
    )

    transport = MqttTransport(
        broker_url="broker.hivemq.com",
        port=1883,
        base_topic="test/gridtokenx/ami"
    )

    # Mock the MQTT Client
    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.publish = AsyncMock()

    transport.client = mock_client
    transport._set_connected(True)

    # Act
    result = await transport.send_reading(reading)

    # Assert
    assert result is True
    assert mock_client.publish.call_count == 2  # One for JSON, one for RAW DLMS

    # Verify JSON publish
    json_call = mock_client.publish.call_args_list[0]
    topic, payload = json_call[0][0], json_call[0][1]
    
    assert topic == "test/gridtokenx/ami/TEST_002"
    payload_dict = json.loads(payload)
    assert payload_dict["meter_serial"] == "TEST_002"
    assert "dlms_hex" in payload_dict

    # Verify RAW DLMS publish
    raw_call = mock_client.publish.call_args_list[1]
    raw_topic, raw_payload = raw_call[0][0], raw_call[0][1]
    
    assert raw_topic == "test/gridtokenx/ami/TEST_002/raw"
    assert raw_payload == DlmsEncoder.encode_reading(reading)

@pytest.mark.asyncio
async def test_mqtt_transport_send_batch():
    # Arrange
    readings = [
        EnergyReading(
            meter_id=f"TEST_{i}",
            timestamp=datetime.now(timezone.utc),
            energy_generated=5.0,
            energy_consumed=10.0,
            surplus_energy=0.0,
            deficit_energy=5.0,
            battery_level=50.0,
            location="Zone_1",
            meter_type="Residential",
            user_type="Consumer"
        ) for i in range(3)
    ]

    transport = MqttTransport(broker_url="broker.hivemq.com")
    transport.client = AsyncMock()
    transport._set_connected(True)
    
    # Act
    result = await transport.send_batch(readings)

    # Assert
    assert result is True
    # 3 readings * 2 publishes (json + raw) = 6 calls
    assert transport.client.publish.call_count == 6
