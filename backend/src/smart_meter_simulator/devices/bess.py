from typing import Optional, Dict, Any


class BESS:
    """
    Battery Energy Storage System (BESS)
    Models a residential or commercial home battery system.
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        # Capacity in kWh
        self.capacity = config.get("battery_capacity", 10.0)
        # Current energy stored in kWh
        self.current_energy_kwh = config.get("current_battery_level", 0.0)
        if self.current_energy_kwh > self.capacity:
            self.current_energy_kwh = self.capacity

        self.efficiency = config.get("battery_efficiency", 0.95)

    def update(
        self,
        gen_kw: float,
        cons_kw: float,
        forced_dispatch_kw: Optional[float] = None,
        interval_hours: float = 0.25,
    ) -> None:
        """
        Update the battery state based on generation, consumption, and dispatch signals.
        Values are in kW.
        """
        net_kw = gen_kw - cons_kw
        net_kwh = net_kw * interval_hours

        if forced_dispatch_kw is not None:
            dispatch_kwh = forced_dispatch_kw * interval_hours
            if dispatch_kwh > 0:
                # Discharging
                self.current_energy_kwh -= min(dispatch_kwh, self.current_energy_kwh)
            else:
                # Charging
                self.current_energy_kwh += min(
                    abs(dispatch_kwh), self.capacity - self.current_energy_kwh
                )
        else:
            if net_kwh > 0:
                # Surplus generation, charge battery
                charge_amount = min(
                    net_kwh * self.efficiency, self.capacity - self.current_energy_kwh
                )
                self.current_energy_kwh += charge_amount
            else:
                # Deficit generation, discharge battery
                discharge_amount = min(
                    abs(net_kwh) / self.efficiency, self.current_energy_kwh
                )
                self.current_energy_kwh -= discharge_amount

        # Clamp to bounds
        self.current_energy_kwh = max(0.0, min(self.capacity, self.current_energy_kwh))

    def get_soc_percent(self) -> float:
        """Return the State of Charge as a percentage (0-100)"""
        if self.capacity <= 0:
            return 0.0
        return (self.current_energy_kwh / self.capacity) * 100.0
