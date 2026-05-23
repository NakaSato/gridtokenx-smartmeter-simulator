import random
from datetime import datetime
from typing import Dict, Any, Tuple
from ..config import get_config, MeterType


class EVCharger:
    """
    Electric Vehicle (EV) Charger Model
    Handles AC Level 2 (Residential) and DC Fast Charging behavior.
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.meter_type = MeterType(
            config.get("meter_type", MeterType.EV_CHARGER.value)
        )

        # State of Charge in percentage (0-100)
        self.soc_percent = config.get("current_battery_level", 50.0)

        cfg = get_config()
        if self.meter_type == MeterType.DC_FAST_CHARGER:
            self.capacity_kwh = config.get("ev_battery_capacity", 60.0)
        else:
            self.capacity_kwh = config.get(
                "ev_battery_capacity", cfg.ev_battery_capacity_max
            )

    def update(self, timestamp: datetime) -> Tuple[float, float]:
        """
        Simulate EV charging and V2G behavior.
        Returns (generation_kwh, consumption_kwh)
        """
        if self.meter_type == MeterType.DC_FAST_CHARGER:
            return self._calculate_dc_charger_behavior(timestamp)
        return self._calculate_residential_ev_behavior(timestamp)

    def _calculate_residential_ev_behavior(
        self, timestamp: datetime
    ) -> Tuple[float, float]:
        hour = timestamp.hour + timestamp.minute / 60.0
        is_at_station = hour >= 18 or hour <= 8

        if not is_at_station:
            # EV is driving, battery depletes
            if 8 < hour < 18:
                self.soc_percent = max(
                    20.0, self.soc_percent - random.uniform(0.1, 0.8)
                )
            return 0.0, 0.0

        gen_kwh = 0.0
        cons_kwh = 0.0
        config = get_config()

        # V2G during peak hours
        is_peak = 18 <= hour <= 21
        if is_peak and self.soc_percent > (config.ev_v2g_threshold_soc * 100):
            discharge_power = config.ev_v2g_discharge_rate_kw
            gen_kwh = discharge_power / 4.0  # 15 min interval
            self.soc_percent = max(
                0.0, self.soc_percent - (gen_kwh / self.capacity_kwh) * 100
            )
            return gen_kwh, cons_kwh

        # Normal Charging
        if self.soc_percent < 90.0:
            charge_power = config.ev_charge_rate_kw * random.uniform(0.8, 1.0)
            cons_kwh = charge_power / 4.0  # 15 min interval
            if self.capacity_kwh > 0:
                self.soc_percent = min(
                    100.0, self.soc_percent + (cons_kwh / self.capacity_kwh) * 100
                )

        return gen_kwh, cons_kwh

    def _calculate_dc_charger_behavior(
        self, timestamp: datetime
    ) -> Tuple[float, float]:
        hour = timestamp.hour + timestamp.minute / 60.0
        config = get_config()

        if 8 <= hour <= 22:
            utilization = random.uniform(0.6, 0.95)
        elif 6 <= hour < 8 or 22 < hour <= 24:
            utilization = random.uniform(0.3, 0.6)
        else:
            utilization = random.uniform(0.1, 0.3)

        connector_count = self.config.get("connector_count", 4)
        charge_rate_kw = self.config.get("ev_charge_rate_kw", config.dc_charge_rate_kw)
        max_station_capacity_kw = self.config.get(
            "max_station_capacity_kw", config.dc_max_station_capacity_kw
        )

        active_ports = max(1, int(connector_count * utilization))
        base_consumption_kw = charge_rate_kw * active_ports
        actual_consumption_kw = min(base_consumption_kw, max_station_capacity_kw)

        soc_fraction = self.soc_percent / 100.0
        if soc_fraction > 0.8:
            actual_consumption_kw *= 1.0 - ((soc_fraction - 0.8) / 0.2) * 0.6
        elif soc_fraction < 0.2:
            actual_consumption_kw *= 0.7 + (soc_fraction / 0.2) * 0.3

        cons_kwh = actual_consumption_kw / 4.0  # 15 min interval
        if self.capacity_kwh > 0:
            self.soc_percent = min(
                100.0, self.soc_percent + (cons_kwh / self.capacity_kwh) * 100
            )

        return 0.0, cons_kwh
