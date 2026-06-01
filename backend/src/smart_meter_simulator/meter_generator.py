"""
Meter Generator Module
Handles meter initialization and configuration
"""

import random
import uuid
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

        meter_id = 1
        for meter_type, count in zip(meter_types, meter_counts):
            for _ in range(count):
                meter = self._create_meter_config(meter_id, meter_type, None)
                self.meters.append(meter)
                meter_id += 1

        return self.meters

    def generate_ieee_meters(self, num_nodes: int, target_meters: int) -> List[Dict[str, Any]]:
        """Generate meters grouped by IEEE node distributions."""
        self.meters = []
        meters_per_node = max(1, target_meters // num_nodes)
        
        meter_id = 1
        for bus_id in range(num_nodes):
            # Calculate how many meters to put on this bus
            count = meters_per_node
            if bus_id == num_nodes - 1:
                # Add remainder to last bus
                count += target_meters - (meters_per_node * num_nodes)
                
            for _ in range(count):
                loc_data = {
                    "name": f"IEEE_Node_{bus_id}_Meter_{meter_id}",
                    "zone": f"IEEE_Node_{bus_id}",
                    "bus_idx": bus_id  # explicitly tag to bus index
                }
                
                # Mostly consumers with some prosumers
                m_type = random.choices(
                    [MeterType.GRID_CONSUMER, MeterType.SOLAR_PROSUMER, MeterType.HYBRID_PROSUMER],
                    weights=[0.7, 0.2, 0.1]
                )[0]
                
                meter = self._create_meter_config(meter_id, m_type, loc_data)
                meter["bus_idx"] = bus_id
                self.meters.append(meter)
                meter_id += 1
                
        return self.meters

    def create_meter(
        self,
        meter_type: str,
        lat: Optional[float] = None,
        lon: Optional[float] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Create a single meter configuration dynamically."""
        try:
            m_type = MeterType(meter_type)
        except ValueError:
            m_type = MeterType.GRID_CONSUMER

        loc_data = {"latitude": lat, "longitude": lon, **kwargs}

        # Use a high meter ID or UUID for dynamic meters
        meter_id = random.randint(10000, 99999)
        return self._create_meter_config(meter_id, m_type, loc_data)

    def _calculate_meter_counts(self, ratios: List[float]) -> List[int]:
        """Calculate meter counts based on ratios"""
        counts = [int(self.num_meters * ratio) for ratio in ratios]

        # Adjust for rounding
        total = sum(counts)
        if total < self.num_meters:
            counts[0] += self.num_meters - total

        return counts

    def _create_meter_config(
        self,
        meter_id: int,
        meter_type: MeterType,
        location_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Create individual meter configuration"""

        # Use location data from config file if available, otherwise fallback
        if location_data:
            location_name = location_data.get("name", f"Meter_{meter_id}")
            location_string = location_name.replace(" ", "_").upper()
            latitude = location_data.get("latitude")
            longitude = location_data.get("longitude")
            phase = location_data.get("phase", "A")
            building_type = location_data.get("building_type", "commercial")
            floor = location_data.get("floor", 1)
        else:
            # Fallback for meters beyond configured locations
            location_name = (
                f"Zone_{random.randint(1, 5)}_Building_{random.randint(1, 10)}"
            )
            location_string = location_name
            latitude = self.config.base_latitude + random.uniform(-0.001, 0.001)
            longitude = self.config.base_longitude + random.uniform(-0.001, 0.001)
            phase = random.choice(["A", "B", "C"])
            building_type = "commercial"
            floor = random.randint(1, 10)

        # Base configuration
        config = {
            "meter_id": location_data.get("meter_id")
            if location_data and "meter_id" in location_data
            else str(uuid.uuid4()),
            "serial_number": location_data.get("serial_number")
            if location_data and "serial_number" in location_data
            else f"SN-{uuid.uuid4().hex[:8].upper()}",
            "wallet_address": location_data.get("wallet_address")
            if location_data and "wallet_address" in location_data
            else f"0x{uuid.uuid4().hex}",
            "meter_type": meter_type.value,
            "location": location_string,
            "location_name": location_name,
            "latitude": latitude,
            "longitude": longitude,
            "phase": phase,
            "building_type": building_type,
            "floor": floor,
            "user_type": self._get_user_type(meter_type),
            "manufacturer_id": random.choice(
                ["KMP", "LGZ", "MSK", "ELS", "GXT"]
            ),  # Kamstrup, Landis+Gyr, Mitsubishi, Elster, GridTokenX
            "logical_device_name": f"LDN-{meter_id:08d}",
            "base_generation": random.uniform(
                self.config.base_generation_min, self.config.base_generation_max
            ),
            "base_consumption": random.uniform(
                self.config.base_consumption_min, self.config.base_consumption_max
            ),
            "battery_capacity": location_data.get("battery_capacity")
            if location_data and "battery_capacity" in location_data
            else random.uniform(
                self.config.battery_capacity_min, self.config.battery_capacity_max
            ),
            "solar_efficiency": random.uniform(
                self.config.solar_efficiency_min, self.config.solar_efficiency_max
            ),
            "battery_efficiency": random.uniform(
                self.config.battery_efficiency_min, self.config.battery_efficiency_max
            ),
            "trading_preference": random.choice(
                ["Aggressive", "Moderate", "Conservative"]
            ),
            "zone": location_data.get("zone", "Village")
            if location_data
            else "Village",
            "is_critical": location_data.get("is_critical", False)
            if location_data
            else False,
            "is_slack": location_data.get("is_slack", False)
            if location_data
            else False,
        }

        # Add meter type specific configurations
        if location_data and "has_solar" in location_data:
            config["has_solar"] = location_data["has_solar"]
            config["solar_capacity"] = location_data.get("solar_capacity", 5.0)
        elif meter_type in [MeterType.SOLAR_PROSUMER, MeterType.HYBRID_PROSUMER]:
            config["has_solar"] = True
            config["solar_capacity"] = random.uniform(5.0, 15.0)  # kW
        else:
            config["has_solar"] = False
            config["solar_capacity"] = 0.0

        config["panel_efficiency"] = (
            config.get("solar_efficiency", 0.18) if config.get("has_solar") else 0.0
        )

        if location_data and "has_battery" in location_data:
            config["has_battery"] = location_data["has_battery"]
            config["current_battery_level"] = location_data.get(
                "current_battery_level", 50.0
            )
        elif meter_type in [
            MeterType.HYBRID_PROSUMER,
            MeterType.BATTERY_STORAGE,
            MeterType.EV_CHARGER,
            MeterType.DC_FAST_CHARGER,
        ]:
            config["has_battery"] = True
            config["current_battery_level"] = random.uniform(20.0, 80.0)
        else:
            config["has_battery"] = False
            config["current_battery_level"] = 0.0

        if config.get("has_battery"):
            if meter_type == MeterType.EV_CHARGER:
                config["ev_battery_capacity"] = random.uniform(
                    self.config.ev_battery_capacity_min,
                    self.config.ev_battery_capacity_max,
                )
                config["ev_charge_rate_kw"] = self.config.ev_charge_rate_kw
                config["ev_v2g_discharge_rate_kw"] = (
                    self.config.ev_v2g_discharge_rate_kw
                )
                config["ev_v2g_threshold_soc"] = self.config.ev_v2g_threshold_soc
            elif meter_type == MeterType.DC_FAST_CHARGER:
                config["ev_battery_capacity"] = random.uniform(
                    self.config.ev_battery_capacity_min,
                    self.config.ev_battery_capacity_max,
                )
                config["ev_charge_rate_kw"] = random.choice(
                    self.config.dc_charge_rate_tiers
                )
                config["ev_v2g_discharge_rate_kw"] = 0.0
                config["ev_v2g_threshold_soc"] = 0.0
                config["connector_count"] = random.randint(
                    self.config.dc_connector_count_min,
                    self.config.dc_connector_count_max,
                )
                config["max_station_capacity_kw"] = (
                    self.config.dc_max_station_capacity_kw
                )

            # Special large-scale battery handling
            if location_data and "max_power_kw" in location_data:
                config["max_power_kw"] = location_data["max_power_kw"]

        # Assign Priority
        if location_data and "priority" in location_data:
            config["priority"] = location_data["priority"]
        elif meter_type in [
            MeterType.COMMERCIAL,
            MeterType.FEEDER,
            MeterType.SUBSTATION,
        ]:
            config["priority"] = 1
        elif meter_type == MeterType.EV_CHARGER:
            config["priority"] = 3
        elif meter_type == MeterType.DC_FAST_CHARGER:
            config["priority"] = 2
        else:
            config["priority"] = 2

        # Assign Feeder ID
        if location_data and "zone" in location_data:
            config["feeder_id"] = f"{location_data['zone'].upper()}-FEEDER"
        else:
            phase = config.get("phase", "A")
            config["feeder_id"] = f"ZONE-{phase}-ST"

        return config

    @staticmethod
    def _get_user_type(meter_type: MeterType) -> str:
        """Get user type based on meter type"""
        type_map = {
            MeterType.SOLAR_PROSUMER: "Prosumer",
            MeterType.GRID_CONSUMER: "Consumer",
            MeterType.HYBRID_PROSUMER: "Prosumer",
            MeterType.BATTERY_STORAGE: "Producer",
            MeterType.EV_CHARGER: "Consumer",
            MeterType.DC_FAST_CHARGER: "Producer",  # Station operator
        }
        return type_map.get(meter_type, "Consumer")
