import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch
from app.transport.kafka import KafkaTransport
from app.transport.influxdb import InfluxDBTransport
from app.core.db import DatabaseManager

@pytest.mark.asyncio
async def test_kafka_transport():
    """Test KafkaTransport connection and sending logic with mocks."""
    with patch("aiokafka.AIOKafkaProducer", autospec=True) as mock_producer_class:
        mock_producer = mock_producer_class.return_value
        mock_producer.start = AsyncMock()
        mock_producer.stop = AsyncMock()
        mock_producer.send_and_wait = AsyncMock()
        
        transport = KafkaTransport("localhost:9092", "test_topic")
        connected = await transport.connect()
        assert connected is True
        assert transport.is_connected() is True
        
        reading = {"meter_id": "M1", "energy_generated": 10.0}
        success = await transport.send_reading(reading)
        assert success is True
        mock_producer.send_and_wait.assert_called_with("test_topic", reading)
        
        await transport.disconnect()
        assert transport.is_connected() is False
        mock_producer.stop.assert_called_once()

@pytest.mark.asyncio
async def test_influxdb_transport():
    """Test InfluxDBTransport logic with mocks."""
    with patch("influxdb_client.InfluxDBClient") as mock_client_class:
        mock_client = mock_client_class.return_value
        mock_write_api = MagicMock()
        mock_client.write_api.return_value = mock_write_api
        
        transport = InfluxDBTransport("http://localhost:8086", "token", "org", "bucket")
        connected = await transport.connect()
        assert connected is True
        
        reading = {"meter_id": "M1", "energy_generated": 10.0, "timestamp": "2024-01-01T00:00:00Z"}
        success = await transport.send_reading(reading)
        assert success is True
        # Check that write was called
        assert mock_write_api.write.called
        
        await transport.disconnect()
        mock_client.close.assert_called_once()

@pytest.mark.asyncio
async def test_database_manager_sqlite():
    """Test DatabaseManager using an in-memory SQLite database."""
    # Use sqlite+aiosqlite for async testing
    db_url = "sqlite+aiosqlite:///:memory:"
    db = DatabaseManager(db_url)
    
    # Initialize schema
    success = await db.init_db()
    assert success is True
    
    # Save meter config
    success = await db.save_meter_config("METER_001", "Solar", "Zone A", "Class 0.5", {"p": 1})
    assert success is True
    
    # Verify retrieval
    meters = await db.get_all_meters()
    assert len(meters) == 1
    assert meters[0]["meter_id"] == "METER_001"
    
    # Create session
    success = await db.create_session("SESS_01", {"n": 10})
    assert success is True
    
    # Close session
    success = await db.close_session("SESS_01")
    assert success is True

def test_metrics_endpoint(client):
    """Test GET /metrics endpoint."""
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "text/plain" in response.headers["content-type"]

def test_health_ready_endpoint(client):
    """Test GET /health/ready endpoint."""
    # This might fail in CI if no real DB/Kafka is reachable, 
    # but we can check the status structure.
    response = client.get("/health/ready")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "dependencies" in data
