"""
Meter Generator Module
Handles meter initialization and configuration
"""

import random
import uuid
from typing import List, Dict, Any

from app.config import (
    MeterType,
    SimulatorConfig,
)


class MeterGenerator:
    """Generates and manages meter configurations"""

    def __init__(self, num_meters: int):
        self.num_meters = num_meters
        self.meters: List[Dict[str, Any]] = []

    def generate_meters(self) -> List[Dict[str, Any]]:
        """Generate meter configurations"""
        self.meters = []
        meter_types = [
            MeterType.SOLAR_PROSUMER,
            MeterType.GRID_CONSUMER,
            MeterType.HYBRID_PROSUMER,
            MeterType.BATTERY_STORAGE,
        ]

        ratios = [
            SimulatorConfig.SOLAR_PROSUMER_RATIO,
            SimulatorConfig.GRID_CONSUMER_RATIO,
            SimulatorConfig.HYBRID_PROSUMER_RATIO,
            SimulatorConfig.BATTERY_STORAGE_RATIO,
        ]

        meter_counts = self._calculate_meter_counts(ratios)

        meter_id = 1
        for meter_type, count in zip(meter_types, meter_counts):
            for _ in range(count):
                meter = self._create_meter_config(meter_id, meter_type)
                self.meters.append(meter)
                meter_id += 1

        return self.meters

    def _calculate_meter_counts(self, ratios: List[float]) -> List[int]:
        """Calculate meter counts based on ratios"""
        counts = [int(self.num_meters * ratio) for ratio in ratios]

        # Adjust for rounding
        total = sum(counts)
        if total < self.num_meters:
            counts[0] += self.num_meters - total

        return counts

    def _create_meter_config(
        self, meter_id: int, meter_type: MeterType
    ) -> Dict[str, Any]:
        """Create individual meter configuration"""
        user_type = self._get_user_type(meter_type)

        # Base configuration
        config = {
            "meter_id": str(uuid.uuid4()),
            "meter_type": meter_type.value,
            "location": f"Zone_{random.randint(1, 5)}_Building_{random.randint(1, 10)}",
            "user_type": user_type,
            "latitude": None,
            "longitude": None,
            "trading_preference": "Moderate",  # Default
        }

        # User Type Specific Settings
        if user_type == "Industrial":
            config["base_consumption"] = random.uniform(50.0, 150.0)  # High consumption
            config["solar_capacity"] = random.uniform(50.0, 200.0)  # Large solar array
            config["battery_capacity"] = random.uniform(100.0, 500.0)  # Large battery
            config["trading_preference"] = "Aggressive"

        elif user_type == "Commercial":
            config["base_consumption"] = random.uniform(10.0, 40.0)
            config["solar_capacity"] = random.uniform(20.0, 50.0)
            config["battery_capacity"] = random.uniform(30.0, 100.0)
            config["trading_preference"] = random.choice(["Aggressive", "Moderate"])

        else:  # Residential (Consumer/Prosumer)
            config["base_consumption"] = random.uniform(0.5, 3.0)
            config["solar_capacity"] = random.uniform(3.0, 10.0)
            config["battery_capacity"] = random.uniform(5.0, 15.0)
            config["trading_preference"] = random.choice(["Moderate", "Conservative"])

        # Feature Flags based on Meter Type
        has_solar = meter_type in [MeterType.SOLAR_PROSUMER, MeterType.HYBRID_PROSUMER]
        has_battery = meter_type in [
            MeterType.HYBRID_PROSUMER,
            MeterType.BATTERY_STORAGE,
        ]

        config["has_solar"] = has_solar
        config["has_battery"] = has_battery

        # Solar Details
        if has_solar:
            config["panel_efficiency"] = random.uniform(
                SimulatorConfig.SOLAR_EFFICIENCY_MIN,
                SimulatorConfig.SOLAR_EFFICIENCY_MAX,
            )
        else:
            config["solar_capacity"] = 0.0
            config["panel_efficiency"] = 0.0

        # Battery Details
        if has_battery:
            config["current_battery_level"] = random.uniform(
                config["battery_capacity"] * 0.2, config["battery_capacity"] * 0.8
            )
            config["battery_efficiency"] = random.uniform(
                SimulatorConfig.BATTERY_EFFICIENCY_MIN,
                SimulatorConfig.BATTERY_EFFICIENCY_MAX,
            )
        else:
            config["battery_capacity"] = 0.0
            config["current_battery_level"] = 0.0
            config["battery_efficiency"] = 0.0

        # Trading Configuration
        config["max_sell_price"] = random.uniform(
            SimulatorConfig.MIN_SELL_PRICE, SimulatorConfig.MAX_SELL_PRICE
        )
        config["max_buy_price"] = random.uniform(
            SimulatorConfig.MIN_BUY_PRICE, SimulatorConfig.MAX_BUY_PRICE
        )

        return config

    @staticmethod
    def _get_user_type(meter_type: MeterType) -> str:
        """Get user type based on meter type and random chance"""
        # 10% Industrial, 30% Commercial, 60% Residential
        rand = random.random()
        if rand < 0.1:
            return "Industrial"
        elif rand < 0.4:
            return "Commercial"
        else:
            return "Residential"
