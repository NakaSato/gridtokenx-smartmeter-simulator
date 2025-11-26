import pytest
import asyncio
from datetime import datetime
from smart_meter_simulator.core.meter import SmartMeter
from smart_meter_simulator.core.engine import SimulationEngine
from smart_meter_simulator.transport.base import TransportLayer
from smart_meter_simulator.models.reading import EnergyReading

class MockTransport(TransportLayer):
    def __init__(self):
        self.connected = False
        self.sent_readings = []
        
    async def connect(self):
        self.connected = True
        return True
        
    async def disconnect(self):
        self.connected = False
        return True
        
    async def send_reading(self, reading: EnergyReading):
        self.sent_readings.append(reading)
        return True
        
    async def send_batch(self, readings: list[EnergyReading]):
        self.sent_readings.extend(readings)
        return True

def test_smart_meter_generation():
    config = {
        'meter_id': 'TEST_001',
        'location': 'Test Lab',
        'meter_type': 'Solar_Prosumer',
        'user_type': 'Prosumer',
        'has_solar': True,
        'has_battery': True,
        'solar_capacity': 5.0,
        'battery_capacity': 10.0,
        'current_battery_level': 5.0
    }
    
    meter = SmartMeter(config)
    timestamp = datetime.now()
    reading = meter.generate_reading(timestamp)
    
    assert reading.meter_id == 'TEST_001'
    assert reading.meter_signature is not None
    assert reading.energy_generated >= 0
    assert reading.energy_consumed >= 0
    assert reading.battery_level >= 0

async def _test_simulation_engine_async():
    config = {
        'meter_id': 'TEST_001',
        'location': 'Test Lab',
        'meter_type': 'Consumer',
        'user_type': 'Consumer',
        'has_solar': False,
        'has_battery': False
    }
    
    meter = SmartMeter(config)
    transport = MockTransport()
    engine = SimulationEngine([meter], transport)
    
    # Run one tick
    engine.running = True
    await transport.connect()
    await engine.tick()
    
    assert len(transport.sent_readings) == 1
    assert transport.sent_readings[0].meter_id == 'TEST_001'

def test_simulation_engine():
    asyncio.run(_test_simulation_engine_async())
