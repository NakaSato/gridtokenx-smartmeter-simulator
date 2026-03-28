import mosaik_api_v3
import asyncio
import logging
import threading
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

META = {
    'type': 'hybrid',
    'models': {
        'Meter': {
            'public': True,
            'any_inputs': True,
            'params': ['meter_id'],
            'attrs': [
                'p_kw',          # Active power (Load +)
                'q_kvar',        # Reactive power
                'power_factor',  # Current power factor
                'soc',           # Battery State of Charge
                'gen_p_kw',      # Solar generation
                'con_p_kw',      # Building consumption
            ],
        },
    },
}

class MosaikAdapter(mosaik_api_v3.Simulator):
    """
    Mosaik adapter for the Smart Meter Simulator.
    Allows synchronization with external power system simulators.
    """
    def __init__(self):
        super().__init__(META)
        self.sid = None
        self.engine = None
        self.entities = {} # eid -> meter_id
        self.time_resolution = 1.0
        self.step_size = 900 # Default 15 min
        
        # Threading for async bridge
        self._loop = None
        self._thread = None

    def _start_loop(self):
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        self._loop.run_forever()

    def init(self, sid, time_resolution=1.0, **sim_params):
        self.sid = sid
        self.time_resolution = time_resolution
        self.step_size = sim_params.get('step_size', 900)
        
        # Start background thread for async engine
        self._thread = threading.Thread(target=self._start_loop, daemon=True)
        self._thread.start()
        
        # Wait for loop to be ready
        import time
        while self._loop is None or not self._loop.is_running():
            time.sleep(0.1)
            
        # Support auto-initialization of engine for testing etc.
        if 'num_meters' in sim_params:
            from ..core.engine import SimulationEngine
            from ..core.meter import SmartMeter
            from ..meter_generator import MeterGenerator
            from ..transport.http import HttpTransport
            
            num = sim_params['num_meters']
            generator = MeterGenerator(num)
            meters = [SmartMeter(cfg) for cfg in generator.generate_meters()]
            self.engine = SimulationEngine(meters, HttpTransport())
            self.engine.external_clock = True
            
            # Start the engine in the background thread
            future = asyncio.run_coroutine_threadsafe(self.engine.start(), self._loop)
            future.result() # Safe to wait here because we are in a different thread
            
        return self.meta

    def create(self, num, model, **model_params):
        if model != 'Meter':
            raise ValueError(f"Unknown model: {model}")

        meter_id = model_params.get('meter_id')
        if not meter_id:
            raise ValueError("meter_id is required for Meter model")

        entities = []
        for i in range(num):
            actual_meter_id = f"{meter_id}_{i}" if num > 1 else meter_id
            eid = f"Meter_{actual_meter_id}"
            self.entities[eid] = actual_meter_id
            
            entities.append({
                'eid': eid,
                'type': model,
                'rel': [],
            })
        return entities

    def step(self, time, inputs, max_advance):
        """
        Execute one simulation step.
        'time' is seconds since simulation start.
        """
        if not self.engine:
            logger.error("MosaikAdapter: SimulationEngine not set!")
            return time + self.step_size

        # 1. Process inputs from other simulators
        for eid, attrs in inputs.items():
            # ... process inputs if needed
            pass

        # 2. Trigger engine tick and WAIT for completion
        timestamp = self.engine.current_sim_time
        future = asyncio.run_coroutine_threadsafe(self.engine.tick_once(timestamp), self._loop)
        future.result() # Wait for async tick to complete
        
        return time + self.step_size

    def get_data(self, outputs):
        """
        Return current state for requested attributes.
        """
        data = {}
        for eid, attrs in outputs.items():
            meter_id = self.entities.get(eid)
            if not meter_id: continue
            
            meter = next((m for m in self.engine.meters if m.meter_id == meter_id), None)
            if not meter: 
                data[eid] = {}
                continue

            values = {}
            kw_factor = 3600.0 / self.step_size
            
            for attr in attrs:
                if attr == 'p_kw':
                    values[attr] = (meter.energy_consumed - meter.energy_generated) * kw_factor
                elif attr == 'gen_p_kw':
                    values[attr] = meter.energy_generated * kw_factor
                elif attr == 'con_p_kw':
                    values[attr] = meter.energy_consumed * kw_factor
                elif attr == 'soc':
                    values[attr] = getattr(meter, 'battery_level', 0.0)
                elif attr == 'q_kvar':
                    if meter.last_reading and meter.last_reading.reactive_power_kvar is not None:
                        values[attr] = meter.last_reading.reactive_power_kvar
                    else:
                        p_val = (meter.energy_consumed - meter.energy_generated) * kw_factor
                        pf = meter.config.get('power_factor', 0.95)
                        import math
                        q_factor = math.sqrt(1 - pf**2) / pf if pf > 0 else 0
                        values[attr] = p_val * q_factor
                elif attr == 'power_factor':
                    values[attr] = meter.config.get('power_factor', 0.95)
            
            data[eid] = values
        
        return data

# Helper for starting the simulator as a service
def main():
    return mosaik_api_v3.start_simulation(MosaikAdapter())

if __name__ == '__main__':
    main()
