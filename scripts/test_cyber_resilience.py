import asyncio
import time
from datetime import datetime
from smart_meter_simulator.core.engine import SimulationEngine, SimulationMode
from smart_meter_simulator.core.meter import SmartMeter
from smart_meter_simulator.config import MeterType
from smart_meter_simulator.transport.base import TransportLayer
from smart_meter_simulator.adapters.pandapower_adapter import PandapowerAdapter

class MockTransport(TransportLayer):
    async def connect(self): pass
    async def disconnect(self): pass
    async def broadcast(self, data): pass
    def is_connected(self): return True
    async def send_reading(self, reading): pass
    async def send_batch(self, readings): pass
    async def send_grid_status(self, status): pass
    async def send_auction_bid(self, bid): pass

test_meters_config = [
    {"meter_id": "TEST_METER_1", "meter_type": MeterType.RESIDENTIAL, "location": "Zone A", "user_type": "residential", "has_solar": True},
    {"meter_id": "TEST_METER_2", "meter_type": MeterType.RESIDENTIAL, "location": "Zone A", "user_type": "residential"},
]

async def test_cyber_resilience():
    print("--- Cyber-Security & Resilience Test ---")
    
    # 1. Initialize Engine
    meters = [SmartMeter(cfg) for cfg in test_meters_config]
    transport = MockTransport()
    adapter = PandapowerAdapter()
    engine = SimulationEngine(meters=meters, transport=transport, adapter=adapter)
    engine.mode = SimulationMode.RANDOM
    
    # Manual initialization (bypassing the start() loop)
    await engine.transport.connect()
    engine.net, engine.meter_to_bus = adapter.build_network_from_meters(meters)
    import pandapower as pp
    for meter in meters:
        bus_idx = engine.meter_to_bus.get(meter.meter_id)
        if bus_idx is not None:
            pp.create_load(engine.net, bus=bus_idx, p_mw=0, q_mvar=0, name=f"L_{meter.meter_id}")
            if meter.config.get('has_solar'):
                pp.create_sgen(engine.net, bus=bus_idx, p_mw=0, q_mvar=0, name=f"G_{meter.meter_id}")

    # 2. Baseline Step (No Attack)
    print("\n[Step 1] Baseline (No Attack)")
    await engine.tick()
    summary = engine.analytics.get_summary()
    latest = summary['latest']
    print(f"Health Score: {latest['health_score']:.1f}")
    print(f"Anomaly Score: {latest['anomaly_score']:.1f}")
    print(f"Under Attack: {latest['under_attack']}")

    # 3. Blatant FDI Attack
    print("\n[Step 2] Blatant FDI Attack (Bias = 5.0 kW, Stealth = False)")
    target_meter = test_meters_config[0]['meter_id']
    engine.attacker.configure(
        active=True, 
        targets=[target_meter], 
        mode="bias", 
        bias=5.0, 
        stealthy=False
    )
    
    await engine.tick()
    summary = engine.analytics.get_summary()
    latest = summary['latest']
    print(f"Health Score: {latest['health_score']:.1f}")
    print(f"Anomaly Score: {latest['anomaly_score']:.1f}")
    print(f"Under Attack: {latest['under_attack']}")
    if latest['under_attack']:
        report = engine.analytics.history[-1]
        for alert in report.attack_alerts:
            print(f" ALERT: {alert['type']} on {alert['meter_id']} (Residual: {alert['residual']:.2f})")

    # 4. Stealthy FDI Attack
    print("\n[Step 3] Stealthy FDI Attack (Bias = 5.0 kW, Stealth = True)")
    # Reset EWMA for a clean stealth test
    engine.analytics.residual_ewma = {}
    
    engine.attacker.configure(
        active=True, 
        targets=[target_meter], 
        mode="bias", 
        bias=5.0, 
        stealthy=True
    )
    
    # Run a few ticks to let EWMA build up
    for i in range(5):
        await engine.tick()
        summary = engine.analytics.get_summary()
        latest = summary['latest']
        print(f" Tick {i+1}: Anomaly Score: {latest['anomaly_score']:.1f}, EWMA: {engine.analytics.residual_ewma.get(target_meter, 0):.2f}")
    
    if latest['under_attack']:
        print(" SUCCESS: Stealthy attack detected via persistent residual monitoring!")
    else:
        print(" FAILED: Stealthy attack went undetected.")

if __name__ == "__main__":
    asyncio.run(test_cyber_resilience())
