"""
Meter Generator Module
Handles meter initialization and configuration
"""

import random
import uuid
from typing import Any, Dict, List, Optional, Sequence

from smart_meter_simulator.config import MeterType, get_config


def _seeded_uuid4() -> uuid.UUID:
    """A version-4 UUID drawn from the seeded `random` module.

    `uuid.uuid4()` pulls from `os.urandom`, which `random.seed()` cannot make
    reproducible. Sourcing the 128 bits from the seeded global RNG keeps meter
    IDs and serials deterministic across runs.
    """
    return uuid.UUID(int=random.getrandbits(128), version=4)


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
        ]

        ratios = [
            self.config.solar_prosumer_ratio,
            self.config.grid_consumer_ratio,
            self.config.hybrid_prosumer_ratio,
        ]

        meter_counts = self._calculate_meter_counts(ratios)

        meter_id = 1
        for meter_type, count in zip(meter_types, meter_counts):
            for _ in range(count):
                meter = self._create_meter_config(meter_id, meter_type, None)
                self.meters.append(meter)
                meter_id += 1

        return self.meters

    def generate_ieee_meters(
        self,
        num_nodes: int,
        target_meters: int,
        pv_on_every_bus: bool = False,
        node_ids: Optional[Sequence[str]] = None,
        pv_capacity_kw_by_node: Optional[Dict[str, float]] = None,
        zone_by_node: Optional[Dict[str, str]] = None,
        zone_code_by_node: Optional[Dict[str, int]] = None,
    ) -> List[Dict[str, Any]]:
        """Generate meters across topology nodes.

        The returned list always has ``target_meters`` items.  When there are
        more buses than meters, meters are spread across the bus index range
        instead of accidentally creating one meter per bus.

        When ``pv_on_every_bus`` is enabled, the topology drives the count: one
        solar-enabled meter is created for each bus.
        """
        self.meters = []
        if num_nodes <= 0 or target_meters <= 0:
            return self.meters

        meter_count = num_nodes if pv_on_every_bus else target_meters
        pv_bus_set = (
            self._select_pv_buses(num_nodes, node_ids, pv_capacity_kw_by_node)
            if pv_on_every_bus
            else set()
        )

        for offset in range(meter_count):
            meter_id = offset + 1
            bus_id = (
                offset
                if pv_on_every_bus
                else min(num_nodes - 1, int(offset * num_nodes / target_meters))
            )
            node_id = (
                str(node_ids[bus_id])
                if node_ids is not None and bus_id < len(node_ids)
                else f"node_{bus_id}"
            )
            loc_data = {
                "name": f"{node_id}_Meter_{meter_id}",
                # Real GLM zone (groupid/zone) when authored, else bus name —
                # preserves the prior bus-name-as-zone behaviour for ungrouped
                # topologies.
                "zone": (zone_by_node.get(node_id) if zone_by_node else None)
                or node_id,
                # Numeric zone code (0 = unzoned); matches parent zone_<code>.
                "zone_code": (
                    zone_code_by_node.get(node_id, 0) if zone_code_by_node else 0
                ),
                "bus_idx": bus_id,  # explicitly tag to bus index
                "node_id": node_id,
                "bus_name": node_id,
            }

            if pv_on_every_bus:
                if node_id in pv_bus_set:
                    pv_capacity_kw = self._bus_pv_capacity_kw(
                        node_id, pv_capacity_kw_by_node
                    )
                    loc_data["has_solar"] = True
                    loc_data["solar_capacity"] = pv_capacity_kw
                    m_type = MeterType.SOLAR_PROSUMER
                else:
                    loc_data["has_solar"] = False
                    loc_data["solar_capacity"] = 0.0
                    m_type = MeterType.GRID_CONSUMER
            else:
                # Mostly consumers with some prosumers
                m_type = random.choices(
                    [
                        MeterType.GRID_CONSUMER,
                        MeterType.SOLAR_PROSUMER,
                        MeterType.HYBRID_PROSUMER,
                    ],
                    weights=[0.7, 0.2, 0.1],
                )[0]

            meter = self._create_meter_config(meter_id, m_type, loc_data)
            meter["bus_idx"] = bus_id
            self.meters.append(meter)

        return self.meters

    def _select_pv_buses(
        self,
        num_nodes: int,
        node_ids: Optional[Sequence[str]],
        pv_capacity_kw_by_node: Optional[Dict[str, float]],
    ) -> set[str]:
        """Pick which buses carry rooftop PV given ``config.pv_bus_penetration``.

        Deterministic (no RNG) so a restart reproduces the same PV layout:
        GLM-authored PV buses are taken first, then the remaining slots are
        spread evenly across the rest of the feeder by bus index.
        """
        names = [
            (
                str(node_ids[i])
                if node_ids is not None and i < len(node_ids)
                else f"node_{i}"
            )
            for i in range(num_nodes)
        ]
        penetration = self.config.pv_bus_penetration
        if penetration >= 1.0:
            return set(names)
        target = round(num_nodes * max(0.0, penetration))
        if target <= 0:
            return set()

        selected: list[str] = []
        if pv_capacity_kw_by_node:
            for name in names:
                if pv_capacity_kw_by_node.get(name, 0.0) > 0:
                    selected.append(name)
                    if len(selected) >= target:
                        return set(selected[:target])

        remaining = target - len(selected)
        if remaining > 0:
            chosen = set(selected)
            pool = [name for name in names if name not in chosen]
            if pool:
                step = max(1, len(pool) // remaining)
                for k in range(remaining):
                    selected.append(pool[min(len(pool) - 1, k * step)])
        return set(selected)

    def _bus_pv_capacity_kw(
        self, node_id: str, pv_capacity_kw_by_node: Optional[Dict[str, float]]
    ) -> float:
        if pv_capacity_kw_by_node and node_id in pv_capacity_kw_by_node:
            return max(0.0, float(pv_capacity_kw_by_node[node_id]))

        min_kw = min(
            self.config.bus_pv_capacity_min_kw,
            self.config.bus_pv_capacity_max_kw,
        )
        max_kw = max(
            self.config.bus_pv_capacity_min_kw,
            self.config.bus_pv_capacity_max_kw,
        )
        if max_kw <= 0:
            return 0.0
        return random.uniform(min_kw, max_kw)

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

    def create_meter_config(
        self,
        seq: int,
        meter_type: MeterType,
        location_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Public builder for a meter config from explicit location data.

        Used by the meter registry to construct configs for real, bus-pinned meters
        while reusing the same defaulting logic as the synthetic generator.
        """
        return self._create_meter_config(seq, meter_type, location_data)

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
            "meter_id": (
                location_data.get("meter_id")
                if location_data and "meter_id" in location_data
                else str(_seeded_uuid4())
            ),
            "serial_number": (
                location_data.get("serial_number")
                if location_data and "serial_number" in location_data
                else f"SN-{_seeded_uuid4().hex[:8].upper()}"
            ),
            "meter_type": meter_type.value,
            "location": location_string,
            "location_name": location_name,
            "latitude": latitude,
            "longitude": longitude,
            "bus_idx": location_data.get("bus_idx") if location_data else None,
            "node_id": location_data.get("node_id") if location_data else None,
            "bus_name": location_data.get("bus_name") if location_data else None,
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
            "solar_efficiency": random.uniform(
                self.config.solar_efficiency_min, self.config.solar_efficiency_max
            ),
            "zone": (
                location_data.get("zone", "Village") if location_data else "Village"
            ),
            # Zone partition for the reading. Prefer a topology-supplied zone_code;
            # otherwise spread meters deterministically across 10 zones (1..10) by
            # index so the egress payload carries a real, non-null zone_code.
            # zone_code 0 was falsy and got dropped from the payload (bridge then
            # fell back to hash routing) — 1..10 keeps zone-accurate partitioning.
            "zone_code": (
                location_data.get("zone_code")
                if location_data and location_data.get("zone_code")
                else (meter_id % 10) + 1
            ),
            "is_critical": (
                location_data.get("is_critical", False) if location_data else False
            ),
            "is_slack": (
                location_data.get("is_slack", False) if location_data else False
            ),
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
        }
        return type_map.get(meter_type, "Consumer")
