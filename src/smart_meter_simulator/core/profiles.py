import math
import random
from abc import ABC, abstractmethod
from datetime import datetime


class LoadProfile(ABC):
    """Abstract base class for consumption load profiles."""

    @abstractmethod
    def calculate_consumption(self, timestamp: datetime, base_load: float) -> float:
        pass


class ResidentialProfile(LoadProfile):
    """
    Residential profile:
    - Morning peak (7-9 AM)
    - Evening peak (6-10 PM)
    - Low during day (if working)
    - Lower at night
    - Weekend variation: Higher day load
    """

    def calculate_consumption(self, timestamp: datetime, base_load: float) -> float:
        hour = timestamp.hour + timestamp.minute / 60.0
        is_weekend = timestamp.weekday() >= 5

        # Base load factor
        factor = 0.3

        # Morning Peak (7-9 AM)
        morning_peak = 1.5 * math.exp(-((hour - 8) ** 2) / (2 * 1.0**2))

        # Evening Peak (6-10 PM)
        evening_peak = 2.0 * math.exp(-((hour - 20) ** 2) / (2 * 2.0**2))

        if is_weekend:
            # Higher midday load on weekends
            midday_load = 0.8 * math.exp(-((hour - 13) ** 2) / (2 * 4.0**2))
            factor += midday_load

        factor += morning_peak + evening_peak

        # Random noise
        noise = random.gauss(0, 0.1)

        return max(0.1, base_load * (factor + noise))


class CommercialProfile(LoadProfile):
    """
    Commercial profile:
    - High load during business hours (8 AM - 6 PM)
    - Low load at night
    - Low load on weekends
    """

    def calculate_consumption(self, timestamp: datetime, base_load: float) -> float:
        hour = timestamp.hour + timestamp.minute / 60.0
        is_weekend = timestamp.weekday() >= 5

        factor = 0.2  # Night/Base load

        if not is_weekend:
            # Business hours ramp up/down
            if 8 <= hour <= 18:
                # Plateau with slight curve
                work_factor = 1.0 - 0.2 * ((hour - 13) / 5) ** 2
                factor += work_factor * 2.5
            elif 7 <= hour < 8:  # Ramp up
                factor += (hour - 7) * 2.0
            elif 18 < hour <= 19:  # Ramp down
                factor += (19 - hour) * 2.0

        else:
            # Weekend low load
            factor = 0.3

        noise = random.gauss(0, 0.05)
        return max(0.1, base_load * (factor + noise))


class IndustrialProfile(LoadProfile):
    """
    Industrial profile:
    - Constant high load (24/7 operations or shifts)
    - Minor fluctuations
    """

    def calculate_consumption(self, timestamp: datetime, base_load: float) -> float:
        # Constant high load
        factor = 2.0

        # Shift changes (e.g., 6am, 2pm, 10pm) might show spikes/drops
        # Simplified: just random process noise
        noise = random.gauss(0, 0.2)

        return max(0.5, base_load * (factor + noise))


def get_profile(user_type: str) -> LoadProfile:
    if user_type == "Residential":
        return ResidentialProfile()
    elif user_type == "Commercial":
        return CommercialProfile()
    elif user_type == "Industrial":
        return IndustrialProfile()
    else:
        return ResidentialProfile()  # Default
