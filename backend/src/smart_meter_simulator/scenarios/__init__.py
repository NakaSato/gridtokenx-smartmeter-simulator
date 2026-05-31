"""
Scenario package for GridTokenX Smart Meter Simulator.

Provides TESP-inspired simulation scenarios as configurable presets:

- **loadshed**: TESP load shedding demonstration (IEEE 13-bus feeder)
- **te30**: TE30 transactive energy challenge (30-node)
- **dsot**: DSO+T market structure with double-auction clearing
- **thai_feeder**: Thai grid feeder scenario (EGAT + PEA)

Each scenario configures the simulator's grid topology, market behavior,
HELICS settings, and meter populations.
"""

from .base import ScenarioConfig

__all__ = ["ScenarioConfig"]
