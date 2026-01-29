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
        counts = [
            int(self.num_meters * ratio) for ratio in ratios
        ]

        # Adjust for rounding
        total = sum(counts)
        if total < self.num_meters:
            counts[0] += self.num_meters - total

        return counts

    def _create_meter_config(
        self,
        meter_id: int,
        meter_type: MeterType
    ) -> Dict[str, Any]:
        """Create individual meter configuration"""
        config = {
            'meter_id': str(uuid.uuid4()),
            'meter_type': meter_type.value,
            'location': f'Zone_{random.randint(1, 5)}_Building_{random.randint(1, 10)}',
            'user_type': self._get_user_type(meter_type),
            'base_generation': random.uniform(
                SimulatorConfig.BASE_GENERATION_MIN,
                SimulatorConfig.BASE_GENERATION_MAX
            ),
            'base_consumption': random.uniform(
                SimulatorConfig.BASE_CONSUMPTION_MIN,
                SimulatorConfig.BASE_CONSUMPTION_MAX
            ),
            'battery_capacity': random.uniform(
                SimulatorConfig.BATTERY_CAPACITY_MIN,
                SimulatorConfig.BATTERY_CAPACITY_MAX
            ),
            'solar_efficiency': random.uniform(
                SimulatorConfig.SOLAR_EFFICIENCY_MIN,
                SimulatorConfig.SOLAR_EFFICIENCY_MAX
            ),
            'battery_efficiency': random.uniform(
                SimulatorConfig.BATTERY_EFFICIENCY_MIN,
                SimulatorConfig.BATTERY_EFFICIENCY_MAX
            ),
            'trading_preference': random.choice(
                ['Aggressive', 'Moderate', 'Conservative']
            ),
            # Use authority wallet for testing (all meters will mint to same wallet for now)
            'wallet_address': "2Xyfzwzq7vATKYYT2SPjERVbQESq8F4PXo1WNmo1Ba29",
        }
        
        # Add meter type specific configurations
        if meter_type in [MeterType.SOLAR_PROSUMER, MeterType.HYBRID_PROSUMER]:
            config['has_solar'] = True
            config['solar_capacity'] = random.uniform(5.0, 15.0)  # kW
            config['panel_efficiency'] = config['solar_efficiency']
        else:
            config['has_solar'] = False
            config['solar_capacity'] = 0.0
            config['panel_efficiency'] = 0.0
            
        if meter_type in [MeterType.HYBRID_PROSUMER, MeterType.BATTERY_STORAGE]:
            config['has_battery'] = True
            config['current_battery_level'] = random.uniform(20.0, 80.0)
        else:
            config['has_battery'] = False
            config['current_battery_level'] = 0.0
            
        # Add trading configuration
        config['max_sell_price'] = random.uniform(
            SimulatorConfig.MIN_SELL_PRICE,
            SimulatorConfig.MAX_SELL_PRICE
        )
        config['max_buy_price'] = random.uniform(
            SimulatorConfig.MIN_BUY_PRICE,
            SimulatorConfig.MAX_BUY_PRICE
        )
        
        return config

    @staticmethod
    def _get_user_type(meter_type: MeterType) -> str:
        """Get user type based on meter type"""
        type_map = {
            MeterType.SOLAR_PROSUMER: 'Prosumer',
            MeterType.GRID_CONSUMER: 'Consumer',
            MeterType.HYBRID_PROSUMER: 'Prosumer',
            MeterType.BATTERY_STORAGE: 'Producer',
        }
        return type_map.get(meter_type, 'Consumer')
