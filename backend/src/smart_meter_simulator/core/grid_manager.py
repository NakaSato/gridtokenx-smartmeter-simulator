import logging
from typing import Any, Dict, List, Optional
from ..config import get_config

logger = logging.getLogger(__name__)


class GridManager:
    """
    Simplified Grid Manager without Pandapower or AI dependencies.
    Provides basic nodal pricing and carbon intensity metrics.
    """

    def __init__(self, adapter: Optional[Any] = None):
        self.adapter = adapter
        self.net = None
        self.meter_to_bus = {}
        self.nodal_prices = {}
        self.avg_nodal_price = 0.28
        self.carbon_intensity = 250.0
        self.last_estimation_results = None

    def initialize_network(self, meters: List[Any]):
        """No-op initialization (Grid Topology removed)."""
        logger.info("GridManager initialized in simplified mode (AMI only)")
        return

    def update_grid_state(self, meters: List[Any], readings: List[Any]):
        """Update basic grid metrics based on readings."""
        # Calculate aggregate stats for simple metrics
        total_gen = sum(r.energy_generated for r in readings)
        total_cons = sum(r.energy_consumed for r in readings)

        # Simple carbon intensity model
        self.carbon_intensity = max(
            50.0, 500.0 * (1.0 - (total_gen / (total_cons + 0.1)))
        )

        # Constant nodal prices for now
        config = get_config()
        self.avg_nodal_price = config.grid_purchase_rate
        for meter in meters:
            self.nodal_prices[meter.meter_id] = self.avg_nodal_price

    def run_state_estimation(self, meters: List[Any], readings: List[Any]):
        """State estimation is no longer available."""
        return None

    def calculate_nodal_prices(self) -> Dict[str, float]:
        """Return cached nodal prices."""
        return self.nodal_prices
