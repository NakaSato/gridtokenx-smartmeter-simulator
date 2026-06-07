"""Behind-the-meter battery energy storage (BESS) device model.

A simple self-consumption battery: it charges from a household's PV surplus and
discharges to cover its deficit, flattening the meter's net exchange with the
grid. State of charge (``soc_kwh``) is mutable and persists across ticks, like
the rest of the device state on a ``SmartMeter``.

Energy accounting respects a round-trip efficiency split evenly between the
charge and discharge legs (``eff = sqrt(round_trip)``): storing ``p`` kW for
``h`` hours adds ``p·h·eff`` to the cells, while delivering ``p`` kW draws
``p·h/eff`` from them. SoC is bounded by ``[min_soc, capacity]``.
"""

from __future__ import annotations

from typing import Any, Dict, Tuple

from smart_meter_simulator.config import get_config


class Battery:
    """Self-consumption BESS attached to a meter.

    Per-meter overrides may be supplied via the meter config keys
    ``battery_capacity_kwh`` / ``battery_max_charge_kw`` /
    ``battery_max_discharge_kw``; otherwise the global config defaults apply.
    """

    def __init__(self, config: Dict[str, Any]):
        cfg = get_config()
        self.capacity_kwh: float = float(
            config.get("battery_capacity_kwh") or cfg.battery_capacity_kwh
        )
        self.max_charge_kw: float = float(
            config.get("battery_max_charge_kw") or cfg.battery_max_charge_kw
        )
        self.max_discharge_kw: float = float(
            config.get("battery_max_discharge_kw") or cfg.battery_max_discharge_kw
        )
        leg_eff = max(cfg.battery_round_trip_efficiency, 1e-6) ** 0.5
        self.eff_charge: float = leg_eff
        self.eff_discharge: float = leg_eff
        self.min_soc_kwh: float = self.capacity_kwh * cfg.battery_min_soc_frac
        initial = max(cfg.battery_min_soc_frac, cfg.battery_initial_soc_frac)
        self.soc_kwh: float = self.capacity_kwh * initial

    @property
    def soc_frac(self) -> float:
        return self.soc_kwh / self.capacity_kwh if self.capacity_kwh > 0 else 0.0

    def dispatch(self, net_kw: float, time_factor: float) -> Tuple[float, float]:
        """Self-consumption dispatch over an interval of ``time_factor`` hours.

        ``net_kw`` is the household balance before the battery (generation minus
        consumption): positive = PV surplus available to charge, negative =
        deficit to cover. Returns ``(charge_kw, discharge_kw)`` (one is always 0)
        and updates the state of charge. Both are average powers over the interval.
        """
        if time_factor <= 0:
            return 0.0, 0.0

        if net_kw > 0:
            # Surplus -> charge. Limit by C-rate and by remaining headroom (the
            # cells only accept eff_charge of the drawn energy).
            room_kwh = max(0.0, self.capacity_kwh - self.soc_kwh)
            accept_kw = min(
                self.max_charge_kw,
                net_kw,
                room_kwh / (time_factor * self.eff_charge),
            )
            charge_kw = max(0.0, accept_kw)
            self.soc_kwh += charge_kw * time_factor * self.eff_charge
            return charge_kw, 0.0

        if net_kw < 0:
            # Deficit -> discharge. Limit by C-rate and by usable energy (the
            # cells must release deliver/eff_discharge to deliver the load).
            deficit_kw = -net_kw
            usable_kwh = max(0.0, self.soc_kwh - self.min_soc_kwh)
            deliver_kw = min(
                self.max_discharge_kw,
                deficit_kw,
                usable_kwh * self.eff_discharge / time_factor,
            )
            discharge_kw = max(0.0, deliver_kw)
            self.soc_kwh -= discharge_kw * time_factor / self.eff_discharge
            return 0.0, discharge_kw

        return 0.0, 0.0
