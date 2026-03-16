import mosaik_api
import asyncio
import logging
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
                'p_kw',          # Active power (Load -)
                'q_kvar',        # Reactive power
                'power_factor',  # Current power factor
                'soc',           # Battery State of Charge
                'gen_p_kw',      # Solar generation
                'con_p_kw',      # Building consumption
            ],
        },
    },
}

class MosaikAdapter(mosaik_api.Simulator):
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

    def init(self, sid, time_resolution=1.0, **sim_params):
        self.sid = sid
        self.time_resolution = time_resolution
        self.step_size = sim_params.get('step_size', 900)
        
        # Note: The engine should be passed or initialized via sim_params or separate setup
        # For GridTokenX, we usually have the engine already instantiated.
        return self.meta

    def create(self, num, model, **model_params):
        if model != 'Meter':
            raise ValueError(f"Unknown model: {model}")

        meter_id = model_params.get('meter_id')
        if not meter_id:
            raise ValueError("meter_id is required for Meter model")

        entities = []
        eid = f"Meter_{meter_id}"
        self.entities[eid] = meter_id
        
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

        # 1. Process inputs from other simulators (e.g., external weather or curtailment)
        for eid, attrs in inputs.items():
            meter_id = self.entities.get(eid)
            if not meter_id: continue
            
            meter = next((m for m in self.engine.meters if m.meter_id == meter_id), None)
            if not meter: continue

            # Example: Handle external setpoint or curtailment
            # if 'curtailment_kw' in attrs:
            #     meter.receive_dispatch(attrs['curtailment_kw'])
            pass

        # 2. Trigger engine tick
        # Since engine.tick is async, we need to run it in the loop
        asyncio.run_coroutine_threadsafe(self.engine.tick(), asyncio.get_event_loop())
        
        # 3. Advance internal time
        self.engine.current_sim_time += timedelta(seconds=self.step_size)
        
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
            # Factor to convert kWh (energy) back to kW (power)
            kw_factor = 3600.0 / meter.last_reading.interval_seconds if meter.last_reading else 4.0
            
            for attr in attrs:
                if attr == 'p_kw':
                    # Net power (Load reference: + is consuming from grid, - is injecting)
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
                        # Fallback: Calculate reactive power: Q = P * tan(acos(pf))
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
    return mosaik_api.start_simulation(MosaikAdapter())

if __name__ == '__main__':
    main()
