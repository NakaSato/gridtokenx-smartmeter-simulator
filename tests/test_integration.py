import pytest
import asyncio
from datetime import datetime
from unittest.mock import MagicMock, AsyncMock, patch

from smart_meter_simulator.core.engine import SimulationEngine
from smart_meter_simulator.core.meter import SmartMeter
from smart_meter_simulator.transport.http import HttpTransport
from smart_meter_simulator.config import MeterType, SimulatorConfig
from smart_meter_simulator.models.reading import EnergyReading

async def _test_simulation_flow_async():
    # 1. Setup Mocks
    mock_transport = MagicMock(spec=HttpTransport)
    mock_transport.connect = AsyncMock(return_value=True)
    mock_transport.disconnect = AsyncMock(return_value=True)
    mock_transport.send_reading = AsyncMock(return_value=True)
    
    # 2. Create Meter Config
    meter_config = {
        'meter_id': 'TEST_METER_001',
        'meter_type': MeterType.SOLAR_PROSUMER.value,
        'location': 'Test Zone',
        'user_type': 'Prosumer',
        'base_generation': 5.0,
        'base_consumption': 2.0,
        'has_solar': True,
        'has_battery': True,
        'battery_capacity': 10.0,
        'solar_capacity': 5.0,
        'panel_efficiency': 0.2
    }
    
    # 3. Initialize Components
    meter = SmartMeter(meter_config)
    engine = SimulationEngine([meter], mock_transport)
    
    # 4. Run one tick
    await engine.tick()
    
    # 5. Verify Transport Call
    assert mock_transport.send_reading.called
    assert mock_transport.send_reading.call_count == 1
    
    # 6. Verify Payload
    call_args = mock_transport.send_reading.call_args
    reading = call_args[0][0]
    
    assert isinstance(reading, EnergyReading)
    assert reading.meter_id == 'TEST_METER_001'
    assert reading.meter_signature is not None
    
    # 7. Verify Signature
    # Reconstruct payload to verify
    kwh_str = f"{reading.energy_generated:.6f}"
    timestamp_str = reading.timestamp.isoformat()
    expected_payload = f"{kwh_str}|{timestamp_str}"
    
    from smart_meter_simulator.utils.crypto import verify_signature
    public_key = meter.key_manager.get_public_key()
    
    is_valid = verify_signature(public_key, expected_payload, reading.meter_signature)
    assert is_valid, "Signature verification failed"
    
    print("\nIntegration test passed: Reading generated, signed, and sent.")

def test_simulation_flow():
    asyncio.run(_test_simulation_flow_async())

if __name__ == "__main__":
    asyncio.run(test_simulation_flow())
