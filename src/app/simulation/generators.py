"""
Enhanced Data Generators Module

Provides realistic energy data generation patterns including:
- Solar curves with cloud cover variability
- Industrial demand patterns (shift-based, peak load)
- Seasonal adjustments
- Configurable meter templates
"""

import math
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

import numpy as np


class Season(Enum):
    """Thailand has 3 seasons"""
    HOT = "hot"  # March-May
    RAINY = "rainy"  # June-October
    COOL = "cool"  # November-February


class MeterTemplate(Enum):
    """Pre-configured meter templates"""
    RESIDENTIAL_SMALL = "residential_small"
    RESIDENTIAL_MEDIUM = "residential_medium"
    RESIDENTIAL_LARGE = "residential_large"
    COMMERCIAL_OFFICE = "commercial_office"
    COMMERCIAL_RETAIL = "commercial_retail"
    INDUSTRIAL_LIGHT = "industrial_light"
    INDUSTRIAL_HEAVY = "industrial_heavy"
    INDUSTRIAL_24H = "industrial_24h"


@dataclass
class MeterTemplateConfig:
    """Configuration for a meter template"""
    name: str
    base_consumption_kwh: float  # Base hourly consumption
    solar_capacity_kw: float  # Solar panel capacity
    battery_capacity_kwh: float  # Battery storage capacity
    peak_multiplier: float  # Peak hour multiplier
    weekend_factor: float  # Weekend consumption factor
    has_solar: bool = True
    has_battery: bool = False
    shift_count: int = 0  # Number of work shifts (0 for residential)


# Pre-defined meter templates
METER_TEMPLATES: Dict[MeterTemplate, MeterTemplateConfig] = {
    MeterTemplate.RESIDENTIAL_SMALL: MeterTemplateConfig(
        name="Residential Small",
        base_consumption_kwh=0.5,
        solar_capacity_kw=3.0,
        battery_capacity_kwh=5.0,
        peak_multiplier=1.5,
        weekend_factor=1.2,
        has_solar=True,
        has_battery=False,
    ),
    MeterTemplate.RESIDENTIAL_MEDIUM: MeterTemplateConfig(
        name="Residential Medium",
        base_consumption_kwh=1.5,
        solar_capacity_kw=5.0,
        battery_capacity_kwh=10.0,
        peak_multiplier=1.8,
        weekend_factor=1.3,
        has_solar=True,
        has_battery=True,
    ),
    MeterTemplate.RESIDENTIAL_LARGE: MeterTemplateConfig(
        name="Residential Large",
        base_consumption_kwh=3.0,
        solar_capacity_kw=10.0,
        battery_capacity_kwh=15.0,
        peak_multiplier=2.0,
        weekend_factor=1.5,
        has_solar=True,
        has_battery=True,
    ),
    MeterTemplate.COMMERCIAL_OFFICE: MeterTemplateConfig(
        name="Commercial Office",
        base_consumption_kwh=15.0,
        solar_capacity_kw=50.0,
        battery_capacity_kwh=100.0,
        peak_multiplier=1.4,
        weekend_factor=0.2,  # Low weekend usage
        has_solar=True,
        has_battery=True,
    ),
    MeterTemplate.COMMERCIAL_RETAIL: MeterTemplateConfig(
        name="Commercial Retail",
        base_consumption_kwh=25.0,
        solar_capacity_kw=30.0,
        battery_capacity_kwh=50.0,
        peak_multiplier=1.6,
        weekend_factor=1.5,  # Higher weekend
        has_solar=True,
        has_battery=False,
    ),
    MeterTemplate.INDUSTRIAL_LIGHT: MeterTemplateConfig(
        name="Industrial Light",
        base_consumption_kwh=50.0,
        solar_capacity_kw=100.0,
        battery_capacity_kwh=200.0,
        peak_multiplier=1.2,
        weekend_factor=0.3,
        has_solar=True,
        has_battery=True,
        shift_count=1,
    ),
    MeterTemplate.INDUSTRIAL_HEAVY: MeterTemplateConfig(
        name="Industrial Heavy",
        base_consumption_kwh=150.0,
        solar_capacity_kw=200.0,
        battery_capacity_kwh=500.0,
        peak_multiplier=1.3,
        weekend_factor=0.1,
        has_solar=True,
        has_battery=True,
        shift_count=2,
    ),
    MeterTemplate.INDUSTRIAL_24H: MeterTemplateConfig(
        name="Industrial 24/7",
        base_consumption_kwh=200.0,
        solar_capacity_kw=300.0,
        battery_capacity_kwh=1000.0,
        peak_multiplier=1.1,  # Minimal variation
        weekend_factor=0.9,  # Nearly same
        has_solar=True,
        has_battery=True,
        shift_count=3,
    ),
}


class SolarCurveGenerator:
    """
    Generates realistic solar power curves with:
    - Sinusoidal base pattern (sunrise to sunset)
    - Cloud cover variability
    - Seasonal adjustments
    - Temperature efficiency impact
    """

    def __init__(
        self,
        capacity_kw: float,
        panel_efficiency: float = 0.18,
        latitude: float = 13.75,  # Bangkok
    ):
        self.capacity_kw = capacity_kw
        self.panel_efficiency = panel_efficiency
        self.latitude = latitude

    def generate_daily_curve(
        self,
        date: datetime,
        cloud_cover: float = 0.0,  # 0.0 = clear, 1.0 = overcast
        resolution_minutes: int = 15,
    ) -> List[float]:
        """
        Generate solar output for a day.
        
        Returns list of power outputs in kW for each time step.
        """
        steps_per_day = 24 * 60 // resolution_minutes
        outputs = []
        
        # Get sunrise/sunset for this date
        sunrise, sunset = self._get_sun_times(date)
        daylight_hours = (sunset - sunrise).total_seconds() / 3600
        
        # Season adjustment
        season = self._get_season(date)
        season_factor = {
            Season.HOT: 1.1,   # More sun, but hotter = less efficient
            Season.RAINY: 0.7,  # Cloud cover
            Season.COOL: 1.0,   # Good efficiency
        }[season]
        
        for step in range(steps_per_day):
            time = datetime.combine(date.date(), datetime.min.time()) + timedelta(
                minutes=step * resolution_minutes
            )
            
            if sunrise <= time <= sunset:
                # Calculate position in daylight arc (0 to 1)
                daylight_fraction = (time - sunrise).total_seconds() / (
                    sunset - sunrise
                ).total_seconds()
                
                # Sinusoidal curve: peak at solar noon
                sun_angle = math.sin(math.pi * daylight_fraction)
                
                # Apply cloud cover (random variability)
                cloud_factor = 1.0 - cloud_cover
                if cloud_cover > 0:
                    # Add cloud variability (random dips)
                    cloud_factor *= random.uniform(0.8, 1.0)
                
                # Calculate output
                output = (
                    self.capacity_kw
                    * sun_angle
                    * self.panel_efficiency
                    * cloud_factor
                    * season_factor
                )
                
                outputs.append(max(0, output))
            else:
                outputs.append(0.0)
        
        return outputs

    def _get_sun_times(self, date: datetime) -> Tuple[datetime, datetime]:
        """Get approximate sunrise/sunset for Bangkok area"""
        # Simplified: Bangkok sunrise ~6:00-6:30, sunset ~18:00-18:30
        day_of_year = date.timetuple().tm_yday
        
        # Seasonal variation (±30 min)
        variation_minutes = 30 * math.sin(2 * math.pi * (day_of_year - 80) / 365)
        
        sunrise = datetime.combine(date.date(), datetime.min.time()) + timedelta(
            hours=6, minutes=15 + variation_minutes
        )
        sunset = datetime.combine(date.date(), datetime.min.time()) + timedelta(
            hours=18, minutes=15 - variation_minutes
        )
        
        return sunrise, sunset

    @staticmethod
    def _get_season(date: datetime) -> Season:
        """Determine Thai season from date"""
        month = date.month
        if 3 <= month <= 5:
            return Season.HOT
        elif 6 <= month <= 10:
            return Season.RAINY
        else:
            return Season.COOL


class LoadProfileGenerator:
    """
    Generates realistic load profiles based on:
    - User type (residential, commercial, industrial)
    - Day of week (weekday vs weekend)
    - Shift patterns (for industrial)
    - Seasonal adjustments
    """

    def __init__(self, template: MeterTemplateConfig):
        self.template = template

    def generate_daily_profile(
        self,
        date: datetime,
        resolution_minutes: int = 15,
    ) -> List[float]:
        """Generate load profile for a day in kWh per interval"""
        steps_per_day = 24 * 60 // resolution_minutes
        outputs = []
        
        is_weekend = date.weekday() >= 5
        season = SolarCurveGenerator._get_season(date)
        
        # Base consumption per interval
        interval_hours = resolution_minutes / 60
        base_per_interval = self.template.base_consumption_kwh * interval_hours
        
        # Weekend adjustment
        if is_weekend:
            base_per_interval *= self.template.weekend_factor
        
        # Season adjustment for cooling load
        season_factor = {
            Season.HOT: 1.3,  # More AC
            Season.RAINY: 1.1,
            Season.COOL: 0.9,
        }[season]
        
        for step in range(steps_per_day):
            hour = (step * resolution_minutes) // 60
            
            # Calculate load factor based on time of day
            load_factor = self._get_hourly_factor(hour, is_weekend)
            
            # Apply all factors
            consumption = (
                base_per_interval
                * load_factor
                * season_factor
                * random.uniform(0.95, 1.05)  # Small random noise
            )
            
            outputs.append(max(0, consumption))
        
        return outputs

    def _get_hourly_factor(self, hour: int, is_weekend: bool) -> float:
        """Get load factor for given hour"""
        if self.template.shift_count > 0:
            # Industrial shift-based profile
            return self._get_industrial_factor(hour)
        elif is_weekend:
            # Residential weekend profile
            return self._get_residential_weekend_factor(hour)
        else:
            # Standard profile based on type
            if "commercial" in self.template.name.lower():
                return self._get_commercial_factor(hour)
            else:
                return self._get_residential_weekday_factor(hour)

    def _get_residential_weekday_factor(self, hour: int) -> float:
        """Residential weekday: morning + evening peaks"""
        factors = {
            0: 0.3, 1: 0.25, 2: 0.2, 3: 0.2, 4: 0.2, 5: 0.3,
            6: 0.6, 7: 0.8, 8: 0.5, 9: 0.4, 10: 0.4, 11: 0.4,
            12: 0.5, 13: 0.5, 14: 0.4, 15: 0.4, 16: 0.5, 17: 0.7,
            18: 0.9, 19: 1.0, 20: 0.95, 21: 0.85, 22: 0.7, 23: 0.5,
        }
        return factors.get(hour, 0.5) * self.template.peak_multiplier

    def _get_residential_weekend_factor(self, hour: int) -> float:
        """Residential weekend: later start, higher daytime"""
        factors = {
            0: 0.3, 1: 0.25, 2: 0.2, 3: 0.2, 4: 0.2, 5: 0.2,
            6: 0.3, 7: 0.4, 8: 0.6, 9: 0.8, 10: 0.9, 11: 1.0,
            12: 1.0, 13: 0.95, 14: 0.9, 15: 0.85, 16: 0.8, 17: 0.85,
            18: 0.9, 19: 1.0, 20: 0.95, 21: 0.85, 22: 0.7, 23: 0.5,
        }
        return factors.get(hour, 0.5) * self.template.peak_multiplier

    def _get_commercial_factor(self, hour: int) -> float:
        """Commercial: business hours peak"""
        factors = {
            0: 0.1, 1: 0.1, 2: 0.1, 3: 0.1, 4: 0.1, 5: 0.1,
            6: 0.15, 7: 0.3, 8: 0.7, 9: 1.0, 10: 1.0, 11: 1.0,
            12: 0.95, 13: 1.0, 14: 1.0, 15: 1.0, 16: 0.95, 17: 0.8,
            18: 0.5, 19: 0.3, 20: 0.2, 21: 0.15, 22: 0.1, 23: 0.1,
        }
        return factors.get(hour, 0.5) * self.template.peak_multiplier

    def _get_industrial_factor(self, hour: int) -> float:
        """Industrial: shift-based patterns"""
        if self.template.shift_count == 3:
            # 24/7 operation: nearly flat
            return 0.9 + random.uniform(0, 0.1)
        elif self.template.shift_count == 2:
            # Double shift (6am - 10pm)
            if 6 <= hour < 22:
                return 1.0 + random.uniform(-0.05, 0.05)
            else:
                return 0.2
        else:
            # Single shift (8am - 5pm)
            if 8 <= hour < 17:
                return 1.0 + random.uniform(-0.05, 0.05)
            else:
                return 0.15


class BatchSimulator:
    """
    Batch simulation for stress testing.
    Generates readings for multiple meters simultaneously.
    """

    def __init__(self, meter_configs: List[Dict]):
        self.meter_configs = meter_configs

    def simulate_batch(
        self,
        start_time: datetime,
        end_time: datetime,
        resolution_minutes: int = 15,
    ) -> List[Dict]:
        """
        Generate readings for all meters in the batch.
        
        Returns list of reading records suitable for API submission.
        """
        readings = []
        current_time = start_time
        
        while current_time < end_time:
            for config in self.meter_configs:
                template = METER_TEMPLATES.get(
                    MeterTemplate(config.get("template", "residential_medium")),
                    METER_TEMPLATES[MeterTemplate.RESIDENTIAL_MEDIUM],
                )
                
                # Generate load
                load_gen = LoadProfileGenerator(template)
                hour = current_time.hour
                is_weekend = current_time.weekday() >= 5
                load_factor = load_gen._get_hourly_factor(hour, is_weekend)
                consumption = template.base_consumption_kwh * load_factor * (resolution_minutes / 60)
                
                # Generate solar if applicable
                generation = 0.0
                if template.has_solar:
                    solar_gen = SolarCurveGenerator(template.solar_capacity_kw)
                    sunrise, sunset = solar_gen._get_sun_times(current_time)
                    if sunrise <= current_time <= sunset:
                        daylight_fraction = (current_time - sunrise).total_seconds() / (
                            sunset - sunrise
                        ).total_seconds()
                        sun_angle = math.sin(math.pi * daylight_fraction)
                        generation = (
                            template.solar_capacity_kw
                            * sun_angle
                            * 0.18
                            * (resolution_minutes / 60)
                        )
                
                readings.append({
                    "meter_id": config.get("meter_id"),
                    "timestamp": current_time.isoformat(),
                    "consumption_kwh": round(consumption, 4),
                    "generation_kwh": round(generation, 4),
                    "net_energy_kwh": round(generation - consumption, 4),
                    "voltage": round(220 + random.uniform(-5, 5), 1),
                    "frequency": round(50 + random.uniform(-0.1, 0.1), 2),
                })
            
            current_time += timedelta(minutes=resolution_minutes)
        
        return readings
