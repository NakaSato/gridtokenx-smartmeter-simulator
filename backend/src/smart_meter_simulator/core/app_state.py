from typing import Optional
from smart_meter_simulator.core.engine import SimulationEngine

engine: Optional[SimulationEngine] = None


def get_simulation_engine() -> Optional[SimulationEngine]:
    """Get the current simulation engine instance."""
    return engine
