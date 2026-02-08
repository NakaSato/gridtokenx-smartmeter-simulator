import logging
import asyncio
import sys
import os
import time
from datetime import datetime

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from smart_meter_simulator.core.engine import SimulationEngine
from smart_meter_simulator.core.meter import SmartMeter
from smart_meter_simulator.transport.base import TransportLayer
from smart_meter_simulator.adapters.topology_builder import TopologyBuilder, BusConfig, VoltageLevel

# Configure logging to only show errors to keep output clean
logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MockTransport(TransportLayer):
    async def connect(self): pass
    async def disconnect(self): pass
    async def send_reading(self, reading): pass
    async def send_batch(self, readings): pass
    async def send_grid_status(self, status): pass
    async def send_auction_bid(self, bid, batch_id): pass
    @property
    def is_connected(self): return True

async def run_stress_test():
    print("🚀 Starting Phase 10 Scaling Stress Test (1000 Meters)...")
    
    # 1. Setup Large Topology
    print("Building Network Topology...")
    start_topo = time.time()
    builder = TopologyBuilder("StressGrid")
    builder.create_network()
    
    # 1 Substation
    root_config = BusConfig(
        bus_id="RootBus", 
        vn_kv=20.0, 
        name="Substation", 
        voltage_level=VoltageLevel.MV
    )
    builder.add_bus(root_config)
    
    # 20 Feeders with 50 buses each = 1000 buses
    num_feeders = 20
    buses_per_feeder = 50
    total_buses = 0
    
    for i in range(num_feeders):
        builder.add_feeder("RootBus", f"Feeder_{i}", buses_per_feeder, 0.4)
        total_buses += buses_per_feeder
        
    print(f"✅ Topology Built: {total_buses} buses + 1 substation. Time: {time.time() - start_topo:.4f}s")
    
    # 2. Setup 1000 Meters
    print("Initializing 1000 Smart Meters...")
    start_meters = time.time()
    meters = []
    for i in range(total_buses):
        config = {
            "meter_id": f"METER_{i}",
            "meter_type": "Residential" if i % 2 == 0 else "Solar_Prosumer",
            "user_type": "Residential",
            "location": f"Loc_{i}",
            "feeder_id": f"Feeder_{i // buses_per_feeder}",
            "has_battery": (i % 10 == 0),
            "battery_capacity": 10.0,
            "max_power_kw": 5.0,
        }
        meters.append(SmartMeter(config))
    print(f"✅ Meters Initialized. Time: {time.time() - start_meters:.4f}s")
    
    # ... Imports
    try:
        import pandapower as pp
    except ImportError:
        print("Pandapower not installed")
        return

    # 3. Initialize Engine
    print("Initializing Simulation Engine...")
    transport = MockTransport()
    engine = SimulationEngine(meters, transport)
    
    # Inject Topology
    if engine.adapter:
        engine.adapter.builder = builder
        engine.net = builder.net
        # Map METER_i -> Bus i+1 manually because builder.add_feeder created buses sequentially
        # Root=0. Feeder 0 buses=1..50. Feeder 1 buses=51..100.
        # Meter 0 is on Feeder 0 Bus 0? No, checking loop:
        # for i in range(total_buses): ... meters.append ...
        # i goes 0 to 999.
        # Bus indices for feeders start from 1.
        # So METER_i corresponds to Bus i+1.
        engine.meter_to_bus = {m.meter_id: i+1 for i, m in enumerate(meters)}
        print("✅ Meters mapped to Network Buses manually.")
        
        # Manual Initialization (Simulating start() without loop)
        engine.running = True
        await engine.transport.connect()
        
        # Register with VPP and Create Loads in Network
        print("Registering VPP attributes and Network Loads...")
        for meter in engine.meters:
            # Register VPP
            engine.vpp.register_meter(
                meter.meter_id, 
                meter.config, 
                {"battery_level": meter.battery_level}
            )
            
            # Create Load/Gen in Pandapower
            bus_idx = engine.meter_to_bus.get(meter.meter_id)
            if bus_idx is not None:
                pp.create_load(engine.net, bus=bus_idx, p_mw=0, q_mvar=0, name=f"L_{meter.meter_id}")
                if meter.config.get('has_solar'):
                    pp.create_sgen(engine.net, bus=bus_idx, p_mw=0, q_mvar=0, name=f"G_{meter.meter_id}")

    # 4. Run Simulation Loop
    print("\nStarting Simulation Loop (5 Ticks)...")
    times = []
    
    for i in range(5):
        start_tick = time.time()
        try:
            await engine.tick()
        except Exception as e:
            print(f"Tick {i+1} Failed: {e}")
            import traceback
            traceback.print_exc()
            break
            
        duration = time.time() - start_tick
        times.append(duration)
        print(f"  Tick {i+1}: {duration:.4f}s")
        
    if times:
        avg_time = sum(times) / len(times)
        print(f"\n✅ Stress Test Completed.")
        print(f"Average Tick Time: {avg_time:.4f}s")
        
        if avg_time < 2.0:
            print("Performance: EXCELLENT (<2s)")
        elif avg_time < 5.0:
            print("Performance: ACCEPTABLE (<5s)")
        else:
            print("Performance: SLOW (>5s)")
    
    await engine.stop()

if __name__ == "__main__":
    asyncio.run(run_stress_test())
