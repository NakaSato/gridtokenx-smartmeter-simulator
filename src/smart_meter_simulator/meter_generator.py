"""
Meter Generator Module
Handles meter initialization and configuration
"""

import random
import uuid
import json
import os
import logging
from typing import List, Dict, Any, Optional

from smart_meter_simulator.config import (
    MeterType,
    SimulatorConfig,
)

class MeterGenerator:
    """Generates and manages meter configurations"""

    def __init__(self, num_meters: int):
        self.num_meters = num_meters
        self.meters: List[Dict[str, Any]] = []
        self.locations = self._load_locations()

    def _load_locations(self) -> List[Dict[str, Any]]:
        """Load initial meter locations from config file."""
        try:
            loc_file = SimulatorConfig.INITIAL_LOCATIONS_FILE
            if os.path.exists(loc_file):
                with open(loc_file, 'r') as f:
                    data = json.load(f)
                    return data.get("locations", [])
        except Exception as e:
            logging.warning(f"Could not load initial locations from {SimulatorConfig.INITIAL_LOCATIONS_FILE}: {e}")
        return []

    def generate_meters(self) -> List[Dict[str, Any]]:
        """Generate meter configurations"""
        self.meters = []
        meter_types = [
            MeterType.SOLAR_PROSUMER,
            MeterType.GRID_CONSUMER,
            MeterType.HYBRID_PROSUMER,
            MeterType.BATTERY_STORAGE,
            MeterType.EV_CHARGER,
        ]

        ratios = [
            SimulatorConfig.SOLAR_PROSUMER_RATIO,
            SimulatorConfig.GRID_CONSUMER_RATIO,
            SimulatorConfig.HYBRID_PROSUMER_RATIO,
            SimulatorConfig.BATTERY_STORAGE_RATIO,
            SimulatorConfig.EV_CHARGER_RATIO,
        ]

        meter_counts = self._calculate_meter_counts(ratios)

        meter_id = 1
        for meter_type, count in zip(meter_types, meter_counts):
            for _ in range(count):
                loc_data = self.locations[meter_id - 1] if meter_id - 1 < len(self.locations) else None
                meter = self._create_meter_config(meter_id, meter_type, loc_data)
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
        meter_type: MeterType,
        location_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create individual meter configuration"""
        
        # Base configuration
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
        
        # Inject explicit GPS location if available
        if location_data:
            config['latitude'] = location_data.get('latitude')
            config['longitude'] = location_data.get('longitude')
            if 'name' in location_data:
                config['location_name'] = location_data['name']
        
        # Add meter type specific configurations
        if meter_type in [MeterType.SOLAR_PROSUMER, MeterType.HYBRID_PROSUMER]:
            config['has_solar'] = True
            config['solar_capacity'] = random.uniform(5.0, 15.0)  # kW
            config['panel_efficiency'] = config['solar_efficiency']
        else:
            config['has_solar'] = False
            config['solar_capacity'] = 0.0
            config['panel_efficiency'] = 0.0
            
        if meter_type in [MeterType.HYBRID_PROSUMER, MeterType.BATTERY_STORAGE, MeterType.EV_CHARGER]:
            config['has_battery'] = True
            config['current_battery_level'] = random.uniform(20.0, 80.0)
            if meter_type == MeterType.EV_CHARGER:
                # Use EV specific battery capacity range
                config['ev_battery_capacity'] = random.uniform(
                    SimulatorConfig.EV_BATTERY_CAPACITY_MIN,
                    SimulatorConfig.EV_BATTERY_CAPACITY_MAX
                )
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
        
        # Phase 19: Assign Priority
        if meter_type in [MeterType.COMMERCIAL, MeterType.FEEDER, MeterType.SUBSTATION]:
            config['priority'] = 1
        elif meter_type == MeterType.EV_CHARGER:
            config['priority'] = 3
        else:
            config['priority'] = 2

        # Phase 10: Assign Feeder ID for VPP Clusters
        location = config.get('location', '')
        if 'Zone_1' in location:
            config['feeder_id'] = 'ZONE-A-ST'
        elif 'Zone_2' in location:
            config['feeder_id'] = 'ZONE-B-MT'
        else:
            config['feeder_id'] = 'ZONE-C-HP'
        
        return config

    @staticmethod
    def _get_user_type(meter_type: MeterType) -> str:
        """Get user type based on meter type"""
        type_map = {
            MeterType.SOLAR_PROSUMER: 'Prosumer',
            MeterType.GRID_CONSUMER: 'Consumer',
            MeterType.HYBRID_PROSUMER: 'Prosumer',
            MeterType.BATTERY_STORAGE: 'Producer',
            MeterType.EV_CHARGER: 'Consumer',
        }
        return type_map.get(meter_type, 'Consumer')
