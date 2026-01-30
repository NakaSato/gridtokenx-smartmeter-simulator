import pytest
import aiohttp
from unittest.mock import AsyncMock, patch, MagicMock
from app.transport.http import HttpTransport
from app.models.reading import EnergyReading
from datetime import datetime

@pytest.mark.asyncio
async def test_http_transport_connect():
    transport = HttpTransport("http://localhost:8080/submit")
    with patch('aiohttp.ClientSession.get') as mock_get:
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_get.return_value.__aenter__.return_value = mock_response
        connected = await transport.connect()
        assert connected is True

@pytest.mark.asyncio
async def test_http_transport_send_reading():
    transport = HttpTransport("http://localhost:8080/submit")
    reading = EnergyReading(
        meter_id="M1",
        timestamp=datetime.now(),
        energy_generated=1.0,
        energy_consumed=0.5,
        surplus_energy=0.5,
        deficit_energy=0.0,
        location="L1",
        meter_type="Solar_Prosumer",
        user_type="Prosumer"
    )
    
    with patch('aiohttp.ClientSession.post') as mock_post:
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_post.return_value.__aenter__.return_value = mock_response
        success = await transport.send_reading(reading)
        assert success is True

@pytest.mark.asyncio
async def test_http_transport_send_batch():
    transport = HttpTransport("http://localhost:8080/submit")
    reading = EnergyReading(
        meter_id="M1",
        timestamp=datetime.now(),
        energy_generated=1.0,
        energy_consumed=0.5,
        surplus_energy=0.5,
        deficit_energy=0.0,
        location="L1",
        meter_type="Solar_Prosumer",
        user_type="Prosumer"
    )
    
    with patch('aiohttp.ClientSession.post') as mock_post:
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_post.return_value.__aenter__.return_value = mock_response
        success = await transport.send_batch([reading])
        assert success is True
