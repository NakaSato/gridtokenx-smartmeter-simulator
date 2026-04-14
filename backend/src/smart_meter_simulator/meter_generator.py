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
    get_config,
)

class MeterGenerator:
    """Generates and manages meter configurations"""

    def __init__(self, num_meters: int):
        self.num_meters = num_meters
        self.meters: List[Dict[str, Any]] = []
        self.config = get_config()
        self.locations = self._load_locations()

    def _load_locations(self) -> List[Dict[str, Any]]:
        """Load initial meter locations from config file."""
        try:
            loc_file = self.config.initial_locations_file
            if os.path.exists(loc_file):
                with open(loc_file, 'r') as f:
                    data = json.load(f)
                    return data.get("locations", [])
        except Exception as e:
            logging.warning(f"Could not load initial locations from {self.config.initial_locations_file}: {e}")
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
            MeterType.DC_FAST_CHARGER,
        ]

        ratios = [
            self.config.solar_prosumer_ratio,
            self.config.grid_consumer_ratio,
            self.config.hybrid_prosumer_ratio,
            self.config.battery_storage_ratio,
            self.config.ev_charger_ratio,
            self.config.dc_charger_ratio,
        ]

        meter_counts = self._calculate_meter_counts(ratios)

        # Use the number of locations from config file if available
        num_locations = len(self.locations)
        if num_locations > 0:
            # Adjust num_meters to match available locations
            self.num_meters = num_locations
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
        
        # Use location data from config file if available, otherwise fallback
        if location_data:
            location_name = location_data.get('name', f'Meter_{meter_id}')
            location_string = location_name.replace(' ', '_').upper()
            latitude = location_data.get('latitude')
            longitude = location_data.get('longitude')
            phase = location_data.get('phase', 'A')
            building_type = location_data.get('building_type', 'commercial')
            floor = location_data.get('floor', 1)
        else:
            # Fallback for meters beyond configured locations
            location_name = f'Zone_{random.randint(1, 5)}_Building_{random.randint(1, 10)}'
            location_string = location_name
            latitude = self.config.base_latitude + random.uniform(-0.001, 0.001)
            longitude = self.config.base_longitude + random.uniform(-0.001, 0.001)
            phase = random.choice(['A', 'B', 'C'])
            building_type = 'commercial'
            floor = random.randint(1, 10)

        # Base configuration
        config = {
            'meter_id': str(uuid.uuid4()),
            'meter_type': meter_type.value,
            'location': location_string,
            'location_name': location_name,
            'latitude': latitude,
            'longitude': longitude,
            'phase': phase,
            'building_type': building_type,
            'floor': floor,
            'user_type': self._get_user_type(meter_type),
            'manufacturer_id': random.choice(['KMP', 'LGZ', 'MSK', 'ELS', 'GXT']), # Kamstrup, Landis+Gyr, Mitsubishi, Elster, GridTokenX
            'logical_device_name': f"LDN-{meter_id:08d}",
            'base_generation': random.uniform(
                self.config.base_generation_min,
                self.config.base_generation_max
            ),
            'base_consumption': random.uniform(
                self.config.base_consumption_min,
                self.config.base_consumption_max
            ),
            'battery_capacity': random.uniform(
                self.config.battery_capacity_min,
                self.config.battery_capacity_max
            ),
            'solar_efficiency': random.uniform(
                self.config.solar_efficiency_min,
                self.config.solar_efficiency_max
            ),
            'battery_efficiency': random.uniform(
                self.config.battery_efficiency_min,
                self.config.battery_efficiency_max
            ),
            'trading_preference': random.choice(
                ['Aggressive', 'Moderate', 'Conservative']
            ),
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
            
        if meter_type in [MeterType.HYBRID_PROSUMER, MeterType.BATTERY_STORAGE, MeterType.EV_CHARGER, MeterType.DC_FAST_CHARGER]:
            config['has_battery'] = True
            config['current_battery_level'] = random.uniform(20.0, 80.0)
            if meter_type == MeterType.EV_CHARGER:
                # Use EV specific battery capacity range
                config['ev_battery_capacity'] = random.uniform(
                    self.config.ev_battery_capacity_min,
                    self.config.ev_battery_capacity_max
                )
                config['ev_charge_rate_kw'] = self.config.ev_charge_rate_kw
                config['ev_v2g_discharge_rate_kw'] = self.config.ev_v2g_discharge_rate_kw
                config['ev_v2g_threshold_soc'] = self.config.ev_v2g_threshold_soc
            elif meter_type == MeterType.DC_FAST_CHARGER:
                # DC fast charger: vehicle battery capacity, high charge rate
                config['ev_battery_capacity'] = random.uniform(
                    self.config.ev_battery_capacity_min,
                    self.config.ev_battery_capacity_max
                )
                config['ev_charge_rate_kw'] = random.choice(self.config.dc_charge_rate_tiers)
                config['ev_v2g_discharge_rate_kw'] = 0.0  # DC doesn't V2G
                config['ev_v2g_threshold_soc'] = 0.0
                config['connector_count'] = random.randint(
                    self.config.dc_connector_count_min,
                    self.config.dc_connector_count_max
                )
                config['max_station_capacity_kw'] = self.config.dc_max_station_capacity_kw
        else:
            config['has_battery'] = False
            config['current_battery_level'] = 0.0

        # Assign Priority
        if meter_type in [MeterType.COMMERCIAL, MeterType.FEEDER, MeterType.SUBSTATION]:
            config['priority'] = 1
        elif meter_type == MeterType.EV_CHARGER:
            config['priority'] = 3
        elif meter_type == MeterType.DC_FAST_CHARGER:
            config['priority'] = 2  # High priority, harder to shed
        else:
            config['priority'] = 2

        # Assign Feeder ID for VPP Clusters based on phase
        phase = config.get('phase', 'A')
        if phase == 'A':
            config['feeder_id'] = 'ZONE-A-ST'
        elif phase == 'B':
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
            MeterType.DC_FAST_CHARGER: 'Producer',  # Station operator
        }
        return type_map.get(meter_type, 'Consumer')
