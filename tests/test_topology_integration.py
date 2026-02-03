
import sys
import os
import asyncio
from datetime import datetime

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.app.core.engine import SimulationEngine
from src.app.core.meter import SmartMeter, MeterType
from src.app.adapters.pandapower_adapter import PandapowerAdapter
from src.app.transport.base import TransportLayer

# Mock classes
class MockTransport(TransportLayer):
    async def connect(self): pass
    async def disconnect(self): pass
    async def send_reading(self, reading): return True
    async def send_grid_status(self, status): pass
    def is_connected(self): return True
    async def send_batch(self, readings): return True

async def test_topology_integration():
    print("Starting Topology Integration Test...")
    
    # 1. Create many meters to force multi-feeder logic (threshold is 10 per feeder)
    num_meters = 25
    meters = []
    for i in range(num_meters):
        config = {
            'meter_id': f'METER_{i:03d}',
            'meter_type': MeterType.RESIDENTIAL.value,
            'location': f'Zone_{i//10}',
            'user_type': 'Consumer',
            'base_consumption': 1.0
        }
        meters.append(SmartMeter(config))
        
    print(f"Created {len(meters)} meters.")
    
    # 2. Initialize Engine with Adapter
    adapter = PandapowerAdapter()
    engine = SimulationEngine(meters, MockTransport(), adapter=adapter)
    
    # Manually trigger the network initialization part of start()
    # (Copying logic from start() for testing without full loop)
    engine.net, engine.meter_to_bus = engine.adapter.build_network_from_meters(engine.meters)
    
    # 3. Verify Topology
    print("\nVerifying Topology:")
    print(f"Number of buses: {len(engine.net.bus)}")
    print(f"Number of lines: {len(engine.net.line)}")
    print(f"Meters mapped: {len(engine.meter_to_bus)}")
    
    # Check if we have multiple feeders
    # Logic: 25 meters -> 3 feeders (10+10+5). 
    # Buses: Substation + 3 feeders * ~10 buses each. 
    # Wait, simple logic: num_feeders = ceil(25/10) = 3. 
    # buses_per_feeder = max(10, ceil(25/3)=9) = 10.
    # Total buses = Substation(1) + 3*10 = 31 buses.
    
    assert len(engine.net.bus) > 20, "Should have created multiple buses for 25 meters"
    assert len(engine.meter_to_bus) == 25, "All meters should be mapped"
    
    # Verify bus indices are valid
    max_bus_idx = max(engine.net.bus.index)
    for m_id, b_idx in engine.meter_to_bus.items():
        assert b_idx <= max_bus_idx, f"Bus index {b_idx} out of range"
        assert b_idx in engine.net.bus.index, f"Bus index {b_idx} not in net.bus"
        
    print("Topology verification PASSED")
    
    # 4. Integrate Load Elements
    # Engine does this in start(), lets verify manual creation works
    import pandapower as pp
    for meter in engine.meters:
        bus_idx = engine.meter_to_bus.get(meter.meter_id)
        if bus_idx is not None:
             pp.create_load(engine.net, bus=bus_idx, p_mw=0, q_mvar=0, name=f"L_{meter.meter_id}")

    assert len(engine.net.load) == 25, "Should have created 25 loads"
    print("Load creation verification PASSED")

    print("\nALL TESTS PASSED")

if __name__ == "__main__":
    try:
        asyncio.run(test_topology_integration())
    except Exception as e:
        print(f"TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
