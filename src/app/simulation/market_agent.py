"""
Grid State Module for Physics-based Simulation.

This module is deprecated - GridState is now in models/grid_state.py.
This file is kept for backward compatibility only.

For new code, use:
    from app.models.grid_state import GridState
"""

# Re-export GridState from new location for backward compatibility
from ..models.grid_state import GridState

__all__ = ['GridState']
