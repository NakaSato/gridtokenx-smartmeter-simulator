"""
Load Shedding Scenario Service.
Parses time-series scenario configs and orchestrates meter service state transitions.
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from ..devices.ami import SmartMeter

logger = logging.getLogger(__name__)


class LoadShedScenarioService:
    """
    Manages and runs time-series load shedding scenarios.
    Maps status strings (e.g. IN_SERVICE / OUT_OF_SERVICE) to meter states.
    Supports point-to-point network communication latency modeling.
    """

    def __init__(self):
        self.active_scenario: Dict[int, Dict[str, str]] = {}
        self.scenario_start_time: Optional[datetime] = None
        self.executed_steps: List[int] = []
        self.is_active: bool = False

        # Latency modeling state
        self.latency_enabled: bool = False
        self.latency_per_hop_seconds: float = 1.0
        self.pending_actions: List[Dict[str, Any]] = []
        self.meter_hop_counts: Dict[str, int] = {}

    def load_scenario(
        self,
        scenario_data: Dict[str, Any],
        latency_enabled: bool = False,
        latency_per_hop_seconds: float = 1.0,
    ) -> bool:
        """
        Load and parse a load shed scenario dictionary.
        Keys are elapsed seconds (castable to int) and values are dicts mapping meter_id to state.
        """
        try:
            parsed = {}
            for sec_str, actions in scenario_data.items():
                sec = int(sec_str)
                if not isinstance(actions, dict):
                    raise ValueError(f"Action entry for second {sec} must be a dictionary.")
                parsed[sec] = actions

            self.active_scenario = parsed
            self.executed_steps = []
            self.is_active = False
            self.scenario_start_time = None
            self.latency_enabled = latency_enabled
            self.latency_per_hop_seconds = latency_per_hop_seconds
            self.pending_actions = []
            self.meter_hop_counts = {}
            logger.info(
                f"Loaded load-shed scenario with {len(parsed)} steps. "
                f"Latency: {latency_enabled} (delay/hop: {latency_per_hop_seconds}s)"
            )
            return True
        except (ValueError, TypeError) as e:
            logger.error(f"Failed to parse load-shed scenario: {e}")
            return False

    def start(self, start_time: datetime):
        """Start the scenario timer matching the current simulation time."""
        self.scenario_start_time = start_time
        self.executed_steps = []
        self.pending_actions = []
        self.meter_hop_counts = {}
        self.is_active = True
        logger.info(f"Started load-shed scenario execution at {start_time.isoformat()}")

    def stop(self):
        """Stop scenario execution and clear running state."""
        self.is_active = False
        self.scenario_start_time = None
        self.pending_actions = []
        self.meter_hop_counts = {}
        logger.info("Stopped load-shed scenario execution.")

    def _calculate_hop_counts(self, meters: List[SmartMeter]):
        """Calculate geographical hop counts from virtual substation (grid center)."""
        coords = []
        for m in meters:
            lat = getattr(m, "config", {}).get("latitude")
            lon = getattr(m, "config", {}).get("longitude")
            if lat is not None and lon is not None:
                coords.append((m.meter_id, float(lat), float(lon)))

        if len(coords) > 0:
            avg_lat = sum(c[1] for c in coords) / len(coords)
            avg_lon = sum(c[2] for c in coords) / len(coords)

            distances = {}
            for m_id, lat, lon in coords:
                dist = ((lat - avg_lat) ** 2 + (lon - avg_lon) ** 2) ** 0.5
                distances[m_id] = dist

            max_dist = max(distances.values()) if distances else 0.0
            if max_dist == 0.0:
                max_dist = 1.0

            for m_id, dist in distances.items():
                # Map relative distance to 1-5 hops
                hops = int(round(dist / max_dist, 6) * 4) + 1
                self.meter_hop_counts[m_id] = hops

        # Fill in any missing meters (fallback to hash-based hop count)
        for m in meters:
            if m.meter_id not in self.meter_hop_counts:
                # Deterministic hop count from hash of meter ID
                self.meter_hop_counts[m.meter_id] = (abs(hash(m.meter_id)) % 5) + 1

    def update_step(self, current_time: datetime, meters: List[SmartMeter]) -> List[Dict[str, Any]]:
        """
        Evaluate elapsed simulation time and apply matching service status actions,
        taking cyber network latencies into account.

        Returns:
            A list of change log dicts showing updated meters and states.
        """
        if not self.is_active or not self.scenario_start_time:
            return []

        elapsed = int((current_time - self.scenario_start_time).total_seconds())
        changes = []

        # Lazy initialize hop-count mapping if latency is enabled
        if self.latency_enabled and not self.meter_hop_counts:
            self._calculate_hop_counts(meters)

        # 1. Evaluate scenario steps and schedule matching actions into pending queue
        for sec in sorted(self.active_scenario.keys()):
            if sec <= elapsed and sec not in self.executed_steps:
                actions = self.active_scenario[sec]
                logger.info(f"Scheduling load-shed scenario step at {sec}s (Elapsed: {elapsed}s)")

                for m_id, state_str in actions.items():
                    if self.latency_enabled:
                        hops = self.meter_hop_counts.get(m_id, 1)
                        delay = hops * self.latency_per_hop_seconds
                        scheduled_time = sec + int(delay)
                        logger.info(
                            f"Scheduled action for meter {m_id} -> {state_str} at sim second {scheduled_time} "
                            f"(base step: {sec}s, hops: {hops}, delay: {delay}s)"
                        )
                    else:
                        scheduled_time = sec

                    self.pending_actions.append(
                        {
                            "scheduled_time": scheduled_time,
                            "meter_id": m_id,
                            "state": state_str,
                        }
                    )

                self.executed_steps.append(sec)

        # 2. Evaluate pending queue and apply due actions to meters
        due_actions = [a for a in self.pending_actions if a["scheduled_time"] <= elapsed]
        for action in due_actions:
            m_id = action["meter_id"]
            state_str = action["state"]

            meter = next((m for m in meters if m.meter_id == m_id), None)
            if not meter:
                logger.warning(f"Scenario meter '{m_id}' not found in active simulation grid.")
                self.pending_actions.remove(action)
                continue

            normalized = state_str.strip().upper()
            is_shed = normalized in ("OUT_OF_SERVICE", "SHED", "TRUE", "1")

            if meter.is_shed != is_shed:
                meter.is_shed = is_shed
                changes.append(
                    {
                        "timestamp": current_time.isoformat(),
                        "elapsed_seconds": elapsed,
                        "meter_id": m_id,
                        "state": state_str,
                        "is_shed": is_shed,
                    }
                )
                logger.info(
                    f"Applied delayed status update: meter {m_id} is_shed={is_shed} (Elapsed: {elapsed}s, scheduled: {action['scheduled_time']}s)"
                )

            self.pending_actions.remove(action)

        return changes
