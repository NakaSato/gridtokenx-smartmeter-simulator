import mosaik
import os
import asyncio
from datetime import datetime

# Sim configuration
SIM_CONFIG = {
    'SmartMeterSim': {
        'python': 'smart_meter_simulator.adapters.mosaik_adapter:MosaikAdapter',
    },
}

def run_simulation():
    """
    Run a simple Mosaik co-simulation scenario.
    """
    # 1. Initialize Mosaik World
    world = mosaik.World(SIM_CONFIG)

    # 2. Start the SmartMeter simulator with auto-initialization
    sm_sim = world.start('SmartMeterSim', step_size=900, num_meters=5)

    # 3. Instantiate entities
    # we use IDs that exist or will be created by the simulator
    meters = sm_sim.Meter.create(1, meter_id='meter_001')
    meters += sm_sim.Meter.create(1, meter_id='meter_002')

    # 4. Run simulation for 4 steps (1 hour at 15-min steps)
    until = 3600 # 1 hour
    print(f"Starting Mosaik simulation until {until}s...")
    world.run(until=until)
    print("Mosaik simulation completed successfully.")

if __name__ == '__main__':
    # Mosaik is sync, but our simulator needs an event loop.
    # The Adapter handles loop creation in init().
    run_simulation()
