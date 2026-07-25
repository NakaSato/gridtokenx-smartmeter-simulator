"""Battery Energy Storage System (BESS) device model.

A BESS sits on its own dedicated-transformer node and dispatches autonomously for
two objectives, both reacting to the *previous* tick's grid signals (the same
one-tick governor lag the generator frequency-watt droop uses, so the battery
never enters the power-flow fixed point — no oscillation risk):

- **Frequency reserve** — discharge on under-frequency (deficit), charge on
  over-frequency (surplus), via a droop law. This drains SoC only down to a
  reserved floor, keeping headroom for congestion / contingency.
- **Congestion relief** — discharge when the local distribution transformer is
  overloaded, with hysteresis to avoid relay-style toggling. Congestion may draw
  the reserved band down to ``soc_min`` — that is what the reserve is for.

Discharge maps to the reading's ``energy_generated`` (grid injection); charge
maps to ``energy_consumed``. Dispatch is a pure deterministic function of the
lagged signals and SoC — no RNG — so runs are byte-reproducible.
"""

from __future__ import annotations

from typing import Any, Dict

from smart_meter_simulator.config import get_config


class Battery:
    """Per-meter battery storage with autonomous frequency + congestion dispatch."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        cfg = get_config()

        self.power_rating_kw = float(
            config.get("battery_power_kw", cfg.bess_power_rating_kw)
        )
        self.capacity_kwh = max(
            1e-9, float(config.get("battery_capacity_kwh", cfg.bess_capacity_kwh))
        )
        self.soc_min = float(config.get("battery_soc_min", cfg.bess_soc_min))
        self.soc_max = float(config.get("battery_soc_max", cfg.bess_soc_max))
        self.reserve_soc_floor = float(
            config.get("battery_reserve_soc_floor", cfg.bess_reserve_soc_floor)
        )
        self.charge_eff = float(config.get("battery_charge_eff", cfg.bess_charge_eff))
        self.discharge_eff = float(
            config.get("battery_discharge_eff", cfg.bess_discharge_eff)
        )
        self.droop_percent = float(
            config.get("battery_droop_percent", cfg.bess_droop_percent)
        )
        self.deadband_hz = float(
            config.get("battery_freq_deadband_hz", cfg.bess_freq_deadband_hz)
        )
        self.congest_high_pct = float(
            config.get("battery_congest_high_pct", cfg.bess_congest_high_pct)
        )
        self.congest_low_pct = float(
            config.get("battery_congest_low_pct", cfg.bess_congest_low_pct)
        )
        self.slew_kw = float(
            config.get("battery_slew_kw_per_tick", cfg.bess_slew_kw_per_tick)
        )
        self.freq_nominal_hz = float(cfg.freq_nominal_hz)

        # Runtime state.
        soc_init = float(config.get("battery_soc_init", cfg.bess_soc_init))
        self.soc = min(self.soc_max, max(self.soc_min, soc_init))
        self.last_dispatch_kw = 0.0
        # Held congestion-discharge level (kW) inside the hysteresis band.
        self._congest_hold_kw = 0.0

    def dispatch(
        self,
        frequency_hz: float,
        transformer_loading_pct: float,
        interval_seconds: int,
    ) -> float:
        """Compute this tick's signed dispatch (kW) and integrate SoC.

        Positive = discharge (grid injection); negative = charge (load). Both
        inputs are the *previous* tick's values.
        """
        hours = max(interval_seconds / 3600.0, 1e-9)

        p_droop = self._frequency_droop_kw(frequency_hz, hours)
        p_cong = self._congestion_kw(transformer_loading_pct, hours)

        # Congestion can only reinforce discharge: it raises the command toward a
        # higher discharge but never overrides a charge command when there is no
        # congestion (p_cong == 0 imposes no floor).
        p_cmd = p_droop
        if p_cong > 0.0 and p_cong > p_cmd:
            p_cmd = p_cong
        p_cmd = max(-self.power_rating_kw, min(self.power_rating_kw, p_cmd))

        # Optional slew limit damps ringing on large step disturbances.
        if self.slew_kw > 0.0:
            lo = self.last_dispatch_kw - self.slew_kw
            hi = self.last_dispatch_kw + self.slew_kw
            p_cmd = max(lo, min(hi, p_cmd))

        self._integrate_soc(p_cmd, hours)
        self.last_dispatch_kw = p_cmd
        return p_cmd

    def _frequency_droop_kw(self, frequency_hz: float, hours: float) -> float:
        """Signed droop response, bounded by SoC down to the reserve floor."""
        f_dev = frequency_hz - self.freq_nominal_hz
        if abs(f_dev) <= self.deadband_hz:
            return 0.0
        # Under-frequency (f_dev < 0) -> positive (discharge); over-frequency ->
        # negative (charge). Full rating at (droop_percent/100 * nominal) Hz.
        span_hz = (self.droop_percent / 100.0) * self.freq_nominal_hz
        if span_hz <= 0.0:
            return 0.0
        p = -(f_dev / span_hz) * self.power_rating_kw
        p = max(-self.power_rating_kw, min(self.power_rating_kw, p))

        if p > 0:  # discharge — droop respects the reserve floor
            dis_cap = (
                max(0.0, (self.soc - self.reserve_soc_floor) * self.capacity_kwh)
                * self.discharge_eff
                / hours
            )
            return min(p, dis_cap)
        # charge — fill only up to soc_max
        chg_cap = max(0.0, (self.soc_max - self.soc) * self.capacity_kwh) / (
            self.charge_eff * hours
        )
        return max(p, -chg_cap)

    def _congestion_kw(self, loading_pct: float, hours: float) -> float:
        """Discharge-only congestion relief with a hysteresis hold band.

        May draw the reserved band down to ``soc_min`` (the reserve's purpose).
        """
        if loading_pct >= self.congest_high_pct:
            denom = max(1e-9, 100.0 - self.congest_high_pct)
            frac = min(1.0, (loading_pct - self.congest_high_pct) / denom)
            target = self.power_rating_kw * frac
        elif loading_pct <= self.congest_low_pct:
            target = 0.0
        else:
            target = self._congest_hold_kw  # inside the band — hold prior level

        dis_cap = (
            max(0.0, (self.soc - self.soc_min) * self.capacity_kwh)
            * self.discharge_eff
            / hours
        )
        target = max(0.0, min(target, dis_cap))
        self._congest_hold_kw = target
        return target

    def _integrate_soc(self, dispatch_kw: float, hours: float) -> None:
        if dispatch_kw > 0:  # discharge: cell energy out exceeds delivered energy
            self.soc -= (dispatch_kw / self.discharge_eff) * hours / self.capacity_kwh
        elif dispatch_kw < 0:  # charge: stored energy is less than energy drawn
            self.soc += (-dispatch_kw * self.charge_eff) * hours / self.capacity_kwh
        self.soc = max(self.soc_min, min(self.soc_max, self.soc))

    @property
    def soc_pct(self) -> float:
        return self.soc * 100.0
