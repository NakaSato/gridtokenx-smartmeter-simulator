"""
Grid Telemetry Service (Simplified)
"""

import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class GridTelemetryService:
    """
    Service for managing grid sensor data.
    """

    @staticmethod
    def map_solar_to_grid(
        net, solar_inventory: List[Dict[str, Any]]
    ) -> Dict[int, float]:
        """Spatial matching disabled."""
        return {}

    @staticmethod
    def inject_pseudo_measurements(net, force_all: bool = False):
        """Pseudo-measurement injection disabled."""
        pass
