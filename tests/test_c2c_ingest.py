import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock, patch

from smart_meter_simulator.app import app, InfluxDBTransport
from smart_meter_simulator.config import SimulatorConfig
from smart_meter_simulator.core.meter import SmartMeter

client = TestClient(app)

@pytest.fixture
def mock_engine_transports():
    # Setup mock InfluxDBTransport
    mock_influx = MagicMock(spec=InfluxDBTransport)
    mock_influx._connected = True
    mock_influx.send_reading = AsyncMock()
    
    # Setup mock meter
    mock_meter = MagicMock(spec=SmartMeter)
    mock_meter.meter_id = "METER-1234"
    mock_meter.config = {
        "meter_id": "METER-1234",
        "meter_type": "solar_prosumer",
        "bus_id": 1,
        "location": {"lat": 13.0, "lon": 100.0}
    }
    
    mock_engine = MagicMock()
    mock_engine.meters = [mock_meter]
    mock_engine.transport.transports = [mock_influx]
    mock_engine.current_sim_time = "2024-01-01T12:00:00Z"
    
    with patch('smart_meter_simulator.app.engine', mock_engine):
        yield mock_influx

def test_ingest_c2c_data_unauthorized():
    response = client.post(
        "/api/c2c/ingest",
        json={"node_id": "METER-1234", "power_kw": 5.0}
    )
    assert response.status_code == 401

def test_ingest_c2c_data_invalid_api_key():
    response = client.post(
        "/api/c2c/ingest",
        headers={"X-API-Key": "wrong_key"},
        json={"node_id": "METER-1234", "power_kw": 5.0}
    )
    assert response.status_code == 401

def test_ingest_c2c_data_valid(mock_engine_transports):
    # Retrieve the configured API key
    api_key = getattr(SimulatorConfig, "C2C_API_KEY", "gridtokenx_c2c_live_feed")
    
    response = client.post(
        "/api/c2c/ingest",
        headers={"X-API-Key": api_key},
        json={"node_id": "METER-1234", "power_kw": 12.5, "status": "CHARGING"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["message"] == "Ingested Live Feed for METER-1234"
    
    # Verify the influxdb transport was called
    mock_engine_transports.send_reading.assert_called_once()
    
    # Verify the payload structure that was sent
    call_args = mock_engine_transports.send_reading.call_args[0][0]
    assert call_args["meter_id"] == "METER-1234"
    assert call_args["meter_type"] == "solar_prosumer"
    assert call_args["energy_generated"] == 12.5
    assert call_args["energy_consumed"] == 0.0

def test_ingest_c2c_data_unknown_meter():
    api_key = getattr(SimulatorConfig, "C2C_API_KEY", "gridtokenx_c2c_live_feed")
    
    # We still need the engine so it doesn't fail on None, let's mock it for this test too
    mock_engine = MagicMock()
    mock_engine.meters = []
    
    with patch('smart_meter_simulator.app.engine', mock_engine):
        response = client.post(
            "/api/c2c/ingest",
            headers={"X-API-Key": api_key},
            json={"node_id": "UNKNOWN-0000", "power_kw": 5.0}
        )
    # The current implementation returns 200 even for unknown meters,
    # mapping them to 'unknown' in the dict, but we can assert on the success
    assert response.status_code == 200
