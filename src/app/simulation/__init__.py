"""
Simulation package for physics-based grid modeling.

Provides:
- PhysicsSimulationEngine: Main engine with pandapower integration
- DynamicCommunityGrid: Flexible grid model from meter locations
- ThaiGridModel: Pre-built Thai grid topology
- UTCCSmartCampus: UTCC campus microgrid model
- GridState: Grid state dataclass (re-exported from models)
"""

from .engine import PhysicsSimulationEngine
from .dynamic_grid import DynamicCommunityGrid
from .thai_grid import ThaiGridModel
from .utcc_campus import UTCCSmartCampus
from .power_quality import estimate_thd_for_bus

# Re-export GridState for backward compatibility
from ..models.grid_state import GridState

__all__ = [
    "PhysicsSimulationEngine",
    "DynamicCommunityGrid",
    "ThaiGridModel",
    "UTCCSmartCampus",
    "GridState",
    "estimate_thd_for_bus",
]