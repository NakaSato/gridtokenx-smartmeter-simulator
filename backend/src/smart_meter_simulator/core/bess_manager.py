"""BESS fleet status + runtime reserve control.

Battery dispatch is autonomous — it lives in the per-meter ``Battery`` device
model (frequency-reserve droop + congestion relief). This controller is the
read/observe surface (mirroring ``ZoneController``): it derives fleet state live
from the storage meters and lets an operator nudge a battery's reserve floor
without touching the dispatch loop. It holds no private mutable state beyond a
reference to the engine, so it stays consistent across resets and topology swaps.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional


class BessController:
    """Live view over the fleet's battery meters + reserve-floor override."""

    def __init__(self, engine: Any):
        self._engine = engine

    def _battery_meters(self) -> List[Any]:
        return [m for m in self._engine.meters if getattr(m, "battery", None)]

    def _find(self, meter_id: str) -> Optional[Any]:
        for meter in self._battery_meters():
            if meter.meter_id == meter_id:
                return meter
        return None

    def _dispatch_mode(self, battery: Any) -> str:
        disp = battery.last_dispatch_kw
        if disp > 1e-9:
            return "discharging"
        if disp < -1e-9:
            return "charging"
        return "idle"

    def _status(self, meter: Any) -> Dict[str, Any]:
        battery = meter.battery
        return {
            "meter_id": meter.meter_id,
            "bus": meter.config.get("bus_name") or meter.config.get("node_id"),
            "zone_code": meter.config.get("zone_code", 0),
            "soc_pct": round(battery.soc_pct, 3),
            "dispatch_kw": round(battery.last_dispatch_kw, 3),
            "mode": self._dispatch_mode(battery),
            "power_rating_kw": battery.power_rating_kw,
            "capacity_kwh": battery.capacity_kwh,
            "reserve_soc_floor": battery.reserve_soc_floor,
            "soc_min": battery.soc_min,
            "soc_max": battery.soc_max,
        }

    def status(self, meter_id: str) -> Dict[str, Any]:
        """Status for one BESS; raises ``KeyError`` if not found."""
        meter = self._find(meter_id)
        if meter is None:
            raise KeyError(meter_id)
        return self._status(meter)

    def list_status(self) -> List[Dict[str, Any]]:
        return [self._status(m) for m in self._battery_meters()]

    def set_reserve_floor(self, meter_id: str, frac: float) -> Dict[str, Any]:
        """Override a battery's reserve SoC floor at runtime (0..1).

        Raises ``KeyError`` for an unknown meter, ``ValueError`` for an
        out-of-range or inconsistent (below soc_min / above soc_max) value.
        """
        meter = self._find(meter_id)
        if meter is None:
            raise KeyError(meter_id)
        if not 0.0 <= frac <= 1.0:
            raise ValueError("reserve_soc_floor must be in [0, 1]")
        battery = meter.battery
        if frac < battery.soc_min or frac > battery.soc_max:
            raise ValueError("reserve_soc_floor must lie within [soc_min, soc_max]")
        battery.reserve_soc_floor = frac
        return self._status(meter)
