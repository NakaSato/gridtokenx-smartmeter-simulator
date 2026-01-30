import pytest
import asyncio
from datetime import datetime, timezone
from unittest.mock import MagicMock, AsyncMock

from app.core.engine import SimulationEngine
from app.core.meter import SmartMeter
from app.adapters.pandapower_adapter import PandapowerAdapter
from app.transport.base import TransportLayer

class MockTransport(TransportLayer):
    async def connect(self): return True
    async def disconnect(self): return True
    async def send_reading(self, reading): return True
    async def send_batch(self, readings): return True

@pytest.mark.asyncio
async def test_digital_twin_estimation_loop():
    """Test that the simulation engine runs estimation correctly during ticks."""
    # 1. Setup
    meter_config = {
        'meter_id': 'M1',
        'meter_type': 'Solar_Prosumer',
        'location': 'Test',
        'user_type': 'Prosumer',
        'has_solar': True
    }
    meter = SmartMeter(meter_config)
    transport = MockTransport()
    adapter = PandapowerAdapter()
    
    engine = SimulationEngine([meter], transport, adapter=adapter)
    
    # 2. Initialize
    # We must populate meter_to_bus and net elements
    engine.net = adapter.create_simple_network(num_buses=2)
    engine.meter_to_bus['M1'] = 1
    import pandapower as pp
    pp.create_load(engine.net, bus=1, p_mw=0, q_mvar=0, name="L_M1")
    pp.create_sgen(engine.net, bus=1, p_mw=0, q_mvar=0, name="G_M1")
    
    # 3. Run one tick
    await engine.tick()
    
    # 3. Verify
    assert engine.last_estimation_results is not None
    assert engine.last_estimation_results.converged is True
    assert engine.last_estimation_results.num_measurements > 0
    
    # Check if meter has last_reading stored
    assert hasattr(meter, 'last_reading')
    assert meter.last_reading is not None

@pytest.mark.asyncio
async def test_engine_init_grid_on_start():
    """Test that engine initializes the grid network when starting."""
    meter = SmartMeter({'meter_id': 'M1', 'location': 'L1', 'meter_type': 'Grid_Consumer', 'user_type': 'Residential'})
    adapter = PandapowerAdapter()
    engine = SimulationEngine([meter], MockTransport(), adapter=adapter)
    
    # Run start for a very short time
    engine.running = True
    task = asyncio.create_task(engine.start())
    await asyncio.sleep(0.1)
    engine.running = False
    await task
    
    assert engine.net is not None
    assert len(engine.net.bus) == 2 # 1 meter + 1 swing bus
