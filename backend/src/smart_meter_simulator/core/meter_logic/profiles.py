import math
import random
from datetime import datetime
from typing import Optional

from ...config import MeterType


def calculate_solar_generation(
    timestamp: datetime,
    config: dict,
    current_weather: str,
    last_noise: float,
    rng: Optional[random.Random] = None,
) -> tuple:
    """Calculate solar generation based on time, weather, and capacity.

    ``rng`` is the per-meter random stream; falls back to global ``random``.
    """
    rng = rng or random
    hour = timestamp.hour + timestamp.minute / 60.0
    if not (6 <= hour <= 18):
        return 0.0, 0.0

    time_factor = math.sin(math.pi * (hour - 6) / 12) ** 2
    capacity = config.get("solar_capacity", 5.0)

    weather_factors = {
        "Sunny": 1.0,
        "Partly Cloudy": 0.7,
        "Cloudy": 0.4,
        "Rainy": 0.1,
        "Stormy": 0.05,
        "Eclipse": 0.01,
    }
    target_factor = weather_factors.get(current_weather, 1.0)

    base_gen = capacity * time_factor
    innovation = rng.gauss(0, base_gen * 0.02)
    new_noise = 0.8 * last_noise + innovation

    generation = max(0, base_gen * target_factor + new_noise)
    return generation, new_noise


def calculate_consumption(
    timestamp: datetime,
    config: dict,
    meter_id: str,
    last_noise: float,
    rng: Optional[random.Random] = None,
) -> tuple:
    """Calculate consumption based on meter type and profile.

    ``rng`` is the per-meter random stream; falls back to global ``random``.
    """
    rng = rng or random
    hour = timestamp.hour + timestamp.minute / 60.0
    weekday = timestamp.weekday() < 5
    base = config.get("base_consumption", 1.0)
    meter_type = MeterType(config["meter_type"])
    meter_offset = (hash(meter_id) % 100) / 100.0

    factor = 1.0
    if meter_type in [
        MeterType.RESIDENTIAL,
        MeterType.SOLAR_PROSUMER,
        MeterType.HYBRID_PROSUMER,
    ]:
        m_peak = 0.8 * math.exp(
            -((hour - (7.5 + meter_offset * 1.5)) ** 2) / (2 * 1.2**2)
        )
        e_peak = 1.5 * math.exp(
            -((hour - (18.5 + meter_offset * 2.0)) ** 2) / (2 * 2.5**2)
        )
        factor = (
            (1.2 + m_peak * 0.5 + e_peak * 1.2 + 0.3 * math.sin(math.pi * hour / 24))
            if not weekday
            else (0.6 + m_peak + e_peak)
        )
    elif meter_type == MeterType.COMMERCIAL:
        if weekday:
            business_hours = 1.8 if (9 <= hour <= 17) else 0.4
            if 7 <= hour < 9:
                business_hours = 0.4 + (1.4 * (hour - 7) / 2.0)
            elif 17 < hour <= 19:
                business_hours = 1.8 - (1.4 * (hour - 17) / 2.0)
            factor = business_hours + meter_offset * 0.2
        else:
            factor = 0.3 + meter_offset * 0.1
    else:
        factor = 1.0 + 0.2 * math.sin(2 * math.pi * hour / 24) + meter_offset

    consumption = base * factor
    innovation = rng.gauss(0, consumption * 0.015)
    new_noise = 0.85 * last_noise + innovation

    result = consumption + new_noise

    # Clamp to min/max load limits if specified in config
    min_load = config.get("min_load_kw", 0.1)
    max_load = config.get("max_load_kw", 500.0)
    result = max(min_load, min(max_load, result))

    return result, new_noise
