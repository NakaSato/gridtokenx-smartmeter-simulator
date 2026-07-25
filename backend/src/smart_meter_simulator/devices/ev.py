"""EV charging station device model.

An EV charging station sits on its own dedicated-transformer node and is modeled
as a large, constant-power additive load (no ZIP voltage scaling — the EVSE
regulates its own output). A diurnal utilization profile shapes how many ports
are drawing: AC destination chargers (``EV_Charger``) peak in the evening as
vehicles plug in at home/work; DC fast chargers (``DC_Fast_Charger``) peak around
midday with highway/retail traffic. Per-meter Gaussian noise keeps runs
deterministic via the meter's own RNG stream.
"""

from __future__ import annotations

import math
import random
from datetime import datetime
from typing import Any, Dict, Optional

from smart_meter_simulator.config import MeterType, get_config


class EVCharger:
    """Per-meter EV charging station — additive positive load (kW)."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        cfg = get_config()

        meter_type = str(config.get("meter_type", ""))
        self.is_dc_fast = meter_type == MeterType.DC_FAST_CHARGER.value

        default_kw = cfg.ev_dc_fast_max_kw if self.is_dc_fast else cfg.ev_max_charger_kw
        self.max_charger_kw = float(config.get("ev_charger_kw", default_kw))
        self.num_ports = int(config.get("ev_num_ports", cfg.ev_num_ports))
        self.utilization = float(config.get("ev_utilization", cfg.ev_utilization))
        self.last_noise = 0.0

    def get_charge_kw(
        self, timestamp: datetime, rng: Optional[random.Random] = None
    ) -> float:
        """Aggregate charging draw (kW) across all ports for this tick."""
        _rng = rng or random
        hour = timestamp.hour + timestamp.minute / 60.0
        shape = self._diurnal_shape(hour)

        base_kw = self.num_ports * self.max_charger_kw * self.utilization * shape
        if base_kw <= 0.0:
            self.last_noise = 0.0
            return 0.0

        innovation = _rng.gauss(0, base_kw * 0.05)
        self.last_noise = 0.8 * self.last_noise + innovation
        return max(0.0, base_kw + self.last_noise)

    def _diurnal_shape(self, hour: float) -> float:
        """Utilization multiplier in [0, ~1] over the day."""
        if self.is_dc_fast:
            # Midday peak (highway / retail fast charging).
            return 0.2 + 0.8 * math.exp(-((hour - 13.0) ** 2) / (2 * 3.0**2))
        # Evening peak (destination / overnight charging), small morning bump.
        evening = math.exp(-((hour - 19.0) ** 2) / (2 * 2.5**2))
        morning = 0.3 * math.exp(-((hour - 8.0) ** 2) / (2 * 1.5**2))
        return 0.15 + 0.85 * evening + morning
