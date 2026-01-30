import pytest
from unittest.mock import AsyncMock
from app.transport.composite import CompositeTransport
from app.models.reading import EnergyReading
from datetime import datetime

@pytest.mark.asyncio
async def test_composite_transport_connect():
    t1 = AsyncMock()
    t1.connect.return_value = True
    t2 = AsyncMock()
    t2.connect.return_value = True
    
    composite = CompositeTransport([t1, t2])
    success = await composite.connect()
    assert success is True
    assert t1.connect.called
    assert t2.connect.called

@pytest.mark.asyncio
async def test_composite_transport_send_reading():
    t1 = AsyncMock()
    t1.send_reading.return_value = True
    t2 = AsyncMock()
    t2.send_reading.return_value = True
    
    composite = CompositeTransport([t1, t2])
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
    
    success = await composite.send_reading(reading)
    assert success is True
    assert t1.send_reading.called
    assert t2.send_reading.called
