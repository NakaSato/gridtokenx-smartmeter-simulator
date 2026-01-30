import mosaik_api_v3
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)

class SmartMeterSimulator(mosaik_api_v3.Simulator):
    """
    A Mosaik-compliant adapter shim for the Smart Meter Simulator.
    Allows integration into multi-domain co-simulations (e.g., with Controller agents).
    """
    
    def __init__(self):
        super().__init__({
            'models': {
                'SmartMeter': {
                    'public': True,
                    'any_inputs': True,
                    'params': ['meter_id', 'location'],
                    'attrs': ['p_mw', 'q_mvar', 'v_pu'],
                },
            },
        })
        self.engine = None
        self.sid = None
        self.meters = {}

    def init(self, sid, time_resolution=1.0, **sim_params):
        self.sid = sid
        # Initialize the underlying simulation engine if needed
        # Or connect to an existing running instance
        logger.info(f"Mosaik Shim Initialized: {sid}")
        return self.meta

    def create(self, num, model, **model_params):
        if model != 'SmartMeter':
            raise ValueError(f"Unknown model: {model}")
            
        entities = []
        for i in range(num):
            eid = f"meter_{len(self.meters)}"
            entities.append({
                'eid': eid,
                'type': model,
                'rel': [],
            })
            self.meters[eid] = {
                'p_mw': 0.0,
                'q_mvar': 0.0,
                'v_pu': 1.0,
                'params': model_params
            }
        return entities

    def step(self, time, inputs, max_advance):
        # Apply inputs (e.g. set-points from a controller)
        for eid, attrs in inputs.items():
            for attr, val in attrs.items():
                logger.debug(f"Input received for {eid}: {attr}={val}")
                
        # Return next simulation time
        return time + 15 * 60 # 15 minutes

    def get_data(self, outputs):
        data = {}
        for eid, attrs in outputs.items():
            data[eid] = {}
            for attr in attrs:
                if attr in self.meters[eid]:
                    data[eid][attr] = self.meters[eid][attr]
        return data
