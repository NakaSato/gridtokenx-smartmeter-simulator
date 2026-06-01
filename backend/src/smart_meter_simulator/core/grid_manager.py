import logging
from typing import Any, Dict, List, Optional
from ..config import get_config
from .metrics import SIMULATION_SOLVER_TIME, measure_time

logger = logging.getLogger(__name__)


class GridManager:
    """
    Grid Manager. Handles Pandapower power flow if an adapter is provided,
    otherwise provides basic nodal pricing and carbon intensity metrics.
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
        """Initialize the grid topology if an adapter is available."""
        if self.adapter:
            logger.info("Initializing Grid Topology using adapter.")
            if hasattr(self.adapter, 'net') and self.adapter.net is not None:
                self.net = self.adapter.net
            else:
                self.net = self.adapter.build_island_hub() # Default, CLI can override
            
            # Use direct mapping if the adapter has it (e.g. for IEEE node meters)
            if hasattr(self.adapter, 'map_meters_to_buses_direct') and any('bus_idx' in getattr(m, 'config', {}) for m in meters):
                self.meter_to_bus = self.adapter.map_meters_to_buses_direct(meters)
            elif hasattr(self.adapter, 'map_meters_to_buses_spatial'):
                self.meter_to_bus = self.adapter.map_meters_to_buses_spatial(meters)
            else:
                self.meter_to_bus = self.adapter.map_meters_to_buses(meters)
        else:
            logger.info("GridManager initialized in simplified mode (AMI only)")

    def update_grid_state(self, meters: List[Any], readings: List[Any]):
        """Update basic grid metrics based on readings, run power flow if adapter is present."""
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

        # Update and run power flow
        if self.adapter and hasattr(self.adapter, 'update_measurements') and hasattr(self.adapter, 'run_power_flow'):
            try:
                self.adapter.update_measurements(readings)
                with measure_time(SIMULATION_SOLVER_TIME):
                    self.adapter.run_power_flow()
            except Exception as e:
                logger.error(f"Failed to update and run power flow: {e}")

    def run_state_estimation(self, meters: List[Any], readings: List[Any]):
        """State estimation is no longer available."""
        return None

    def calculate_nodal_prices(self) -> Dict[str, float]:
        """Return cached nodal prices."""
        return self.nodal_prices
