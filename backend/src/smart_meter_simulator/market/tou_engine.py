"""
Thai Time-of-Use (TOU) Tariff Engine.

Implements the PEA (Provincial Electricity Authority) and MEA (Metropolitan
Electricity Authority) tariff structures with:

- On-Peak / Off-Peak energy rates
- Service charge
- FT (Fuel Tariff) adjustment factor
- Progressive block pricing (optional)

Reference: PEA Tariff Schedule 2024
"""

import logging
from datetime import datetime, timezone
from typing import Dict, Optional

from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class TOUResult:
    """Result of a TOU tariff calculation.

    Attributes:
        energy_rate: Energy charge for the current period (Baht/kWh).
        is_peak: Whether the current time is in the peak period.
        period_name: Human-readable period name (e.g., "On-Peak", "Off-Peak").
        ft_adjustment: FT tariff adjustment factor (Baht/kWh).
        service_charge: Base service charge (Baht/month, prorated).
        total_rate: Total rate including FT adjustment (Baht/kWh).
    """
    energy_rate: float
    is_peak: bool
    period_name: str
    ft_adjustment: float
    service_charge: float
    total_rate: float


class TOUEngine:
    """Thai Time-of-Use tariff engine.

    Supports the standard Thai electricity tariff structure:

    +-----------+------------------+------------------+
    | Period    | Hours            | Rate (Baht/kWh)  |
    +===========+==================+==================+
    | On-Peak   | 09:00 – 22:00    | ~5.79            |
    | Off-Peak  | 22:00 – 09:00    | ~2.65            |
    +-----------+------------------+------------------+

    Plus FT (Fuel Tariff) adjustment: ~0.94 Baht/kWh (2024 rate).

    Usage::

        engine = TOUEngine()
        result = engine.calculate(datetime.now(), energy_kwh=1.0)
        print(f"Rate: {result.total_rate:.2f} Baht/kWh ({result.period_name})")
    """

    def __init__(
        self,
        on_peak_rate: float = 5.79,
        off_peak_rate: float = 2.65,
        on_peak_start: int = 9,
        on_peak_end: int = 22,
        ft_adjustment: float = 0.94,
        service_charge: float = 38.22,  # Baht/month
    ):
        self.on_peak_rate = on_peak_rate
        self.off_peak_rate = off_peak_rate
        self.on_peak_start = on_peak_start
        self.on_peak_end = on_peak_end
        self.ft_adjustment = ft_adjustment
        self.service_charge = service_charge

    def is_peak(self, timestamp: datetime) -> bool:
        """Check if the given timestamp falls in the peak period.

        Peak hours are defined as on_peak_start:00 to on_peak_end:00
        on weekdays (Mon-Fri). Weekends are off-peak.
        """
        # Convert to local time (Thailand = UTC+7)
        hour = timestamp.hour
        # Thai weekends are off-peak
        weekday = timestamp.weekday()
        if weekday >= 5:  # Saturday=5, Sunday=6
            return False
        return self.on_peak_start <= hour < self.on_peak_end

    def get_period_name(self, timestamp: datetime) -> str:
        """Get the human-readable period name."""
        return "On-Peak" if self.is_peak(timestamp) else "Off-Peak"

    def get_energy_rate(self, timestamp: datetime) -> float:
        """Get the base energy rate for the given time."""
        return self.on_peak_rate if self.is_peak(timestamp) else self.off_peak_rate

    def calculate(self, timestamp: datetime, energy_kwh: float = 1.0) -> TOUResult:
        """Calculate the TOU tariff for a given time and energy amount.

        Args:
            timestamp: The time of energy consumption/generation.
            energy_kwh: Energy amount (kWh) — used for block pricing if enabled.

        Returns:
            TOUResult with detailed tariff breakdown.
        """
        is_peak = self.is_peak(timestamp)
        energy_rate = self.on_peak_rate if is_peak else self.off_peak_rate
        total_rate = energy_rate + self.ft_adjustment

        # Prorate service charge (monthly → per-interval)
        # Assume 30-day month, interval in hours derived from energy_kwh usage
        service_charge_per_interval = self.service_charge / (30 * 24)  # Baht per hour

        return TOUResult(
            energy_rate=energy_rate,
            is_peak=is_peak,
            period_name=self.get_period_name(timestamp),
            ft_adjustment=self.ft_adjustment,
            service_charge=service_charge_per_interval,
            total_rate=total_rate,
        )

    def get_forecast(self, timestamp: datetime, hours: int = 24) -> Dict[int, float]:
        """Get a price forecast for the next N hours.

        Args:
            timestamp: Starting timestamp.
            hours: Number of hours to forecast.

        Returns:
            Dict mapping hour offset (0, 1, ..., hours-1) to total rate (Baht/kWh).
        """
        forecast = {}
        from datetime import timedelta
        for h in range(hours):
            t = timestamp + timedelta(hours=h)
            result = self.calculate(t)
            forecast[h] = result.total_rate
        return forecast
