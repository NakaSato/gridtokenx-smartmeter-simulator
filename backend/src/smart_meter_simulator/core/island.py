import logging
from typing import Optional, List, Dict, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class IslandState:
    is_islanded: bool
    slack_bus_id: Optional[int]  # ID of the bus acting as reference
    grid_forming_meter_id: Optional[str]  # Meter ID of the battery forming the grid


class IslandManager:
    """
    Manages the connection status of the microgrid to the main grid (Simplified).
    """

    def __init__(self):
        self.state = IslandState(
            is_islanded=False, slack_bus_id=None, grid_forming_meter_id=None
        )

    def disconnect(self, net, meters: List[Any], meter_to_bus: Dict[str, int]) -> bool:
        """
        Disconnect from main grid (Island Mode).
        """
        if self.state.is_islanded:
            return False

        logger.info("Initiating Islanding Sequence...")

        candidates = [m for m in meters if m.config.get("has_battery")]
        if not candidates:
            logger.error("Islanding Failed: No Grid Forming capability (No Batteries).")
            return False

        best_candidate = sorted(
            candidates, key=lambda m: m.battery_level, reverse=True
        )[0]

        self.state.is_islanded = True
        self.state.grid_forming_meter_id = best_candidate.meter_id

        logger.info(f"Islanding Successful (Meter: {best_candidate.meter_id})")
        return True

    def reconnect(self, net) -> bool:
        """
        Reconnect to main grid.
        """
        if not self.state.is_islanded:
            return False

        logger.info("Initiating Reconnection Sequence...")
        self.state.is_islanded = False
        self.state.grid_forming_meter_id = None

        logger.info("Reconnection Successful.")
        return True

    def black_start_sequence(self, vpp: Any) -> bool:
        """
        Black Start Sequence.
        """
        if not self.state.is_islanded:
            return False

        logger.info("VPP HEALING: Initiating Black Start Sequence...")
        return True
