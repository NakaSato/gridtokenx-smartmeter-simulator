"""Carbon / emissions accounting for the simulator.

Re-export hub mirroring ``pricing``. The model is framework-free; the REST
surface lives in ``routers/carbon_v1.py`` and ``routers/meters_v1.py``.
"""

from smart_meter_simulator.emissions.carbon import (
    DEFAULT_GRID_INTENSITY_KGCO2_PER_KWH,
    DEFAULT_KG_PER_TREE_YEAR,
    DEFAULT_SOLAR_INTENSITY_KGCO2_PER_KWH,
    CarbonOffset,
    compute_offset,
)

__all__ = [
    "CarbonOffset",
    "compute_offset",
    "DEFAULT_GRID_INTENSITY_KGCO2_PER_KWH",
    "DEFAULT_SOLAR_INTENSITY_KGCO2_PER_KWH",
    "DEFAULT_KG_PER_TREE_YEAR",
]
