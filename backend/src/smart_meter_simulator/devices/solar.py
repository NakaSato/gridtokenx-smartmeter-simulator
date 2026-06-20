import random
from datetime import timezone
from typing import Any, Dict, Optional
from zoneinfo import ZoneInfo

from smart_meter_simulator.config import get_config

from ..core.meter_logic import profiles

_WEATHER_FACTORS = {
    "sunny": 1.0,
    "partly cloudy": 0.72,
    "partly_cloudy": 0.72,
    "cloudy": 0.42,
    "overcast": 0.18,
    "rainy": 0.10,
    "stormy": 0.05,
}


class Solar:
    """
    Solar Photovoltaic (PV) Model.
    Uses pvlib/PVWatts when available, with the old profile as fallback.
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.last_noise = 0.0

    def get_generation_kw(
        self, timestamp: Any, weather: str, rng: Optional[random.Random] = None
    ) -> float:
        """Calculate AC PV generation in kW."""
        _rng = rng or random
        cfg = get_config()
        if cfg.pv_model_enabled:
            try:
                generation = self._get_pvlib_generation_kw(timestamp, weather)
                if generation <= 0.0:
                    self.last_noise = 0.0
                    return 0.0
                innovation = _rng.gauss(0, max(generation, 0.01) * 0.01)
                self.last_noise = 0.8 * self.last_noise + innovation
                return max(0.0, generation + self.last_noise)
            except Exception:
                pass

        gen, self.last_noise = profiles.calculate_solar_generation(
            timestamp, self.config, weather, self.last_noise, rng=rng
        )
        return gen

    def _get_pvlib_generation_kw(self, timestamp: Any, weather: str) -> float:
        import pandas as pd
        import pvlib

        cfg = get_config()
        latitude = float(self.config.get("latitude") or cfg.base_latitude)
        longitude = float(self.config.get("longitude") or cfg.base_longitude)
        capacity_kw = float(self.config.get("solar_capacity", 5.0))
        if capacity_kw <= 0:
            return 0.0

        # The sim clock is wall-clock local time-of-day. Reinterpret its clock
        # reading in the grid's timezone so pvlib computes solar position for local
        # noon, not UTC noon (which is night at this longitude → zero generation).
        # The engine stamps sim_time UTC-aware, so we replace (not convert) the tz:
        # `.replace` keeps the H:M numbers and only swaps the offset. A prior
        # `is None` guard skipped this for the tz-aware engine clock, leaving every
        # solar meter at 0 kW.
        ts = timestamp
        try:
            ts = ts.replace(tzinfo=ZoneInfo(cfg.timezone))
        except Exception:
            ts = ts.replace(tzinfo=timezone.utc)
        times = pd.DatetimeIndex([ts])

        location = pvlib.location.Location(latitude, longitude)
        solar_position = location.get_solarposition(times)
        clearsky = location.get_clearsky(times, model="ineichen")
        poa = pvlib.irradiance.get_total_irradiance(
            surface_tilt=float(self.config.get("pv_tilt_deg", cfg.pv_surface_tilt_deg)),
            surface_azimuth=float(
                self.config.get("pv_azimuth_deg", cfg.pv_surface_azimuth_deg)
            ),
            solar_zenith=solar_position["apparent_zenith"],
            solar_azimuth=solar_position["azimuth"],
            dni=clearsky["dni"],
            ghi=clearsky["ghi"],
            dhi=clearsky["dhi"],
        )

        weather_factor = _WEATHER_FACTORS.get(str(weather).lower(), 1.0)
        poa_effective = max(0.0, float(poa["poa_global"].iloc[0])) * weather_factor
        if poa_effective <= 0:
            return 0.0

        ambient_temp_c = float(self.config.get("ambient_temperature_c", 30.0))
        cell_temp_c = ambient_temp_c + (poa_effective / 800.0) * 20.0
        dc_kw = float(
            pvlib.pvsystem.pvwatts_dc(
                effective_irradiance=poa_effective,
                temp_cell=cell_temp_c,
                pdc0=capacity_kw,
                gamma_pdc=float(
                    self.config.get(
                        "pv_temperature_coefficient",
                        cfg.pv_temperature_coefficient,
                    )
                ),
            )
        )
        inverter_kw = capacity_kw / float(
            self.config.get("pv_dc_ac_ratio", cfg.pv_dc_ac_ratio)
        )
        ac_kw = float(pvlib.inverter.pvwatts(dc_kw, pdc0=inverter_kw))
        return min(capacity_kw, max(0.0, ac_kw))
