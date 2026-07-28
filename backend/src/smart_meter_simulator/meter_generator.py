"""
Meter Generator Module
Handles meter initialization and configuration
"""

import hashlib
import math
import random
import uuid
from typing import Any, Dict, List, Optional, Sequence, Tuple

from smart_meter_simulator.config import MeterType, get_config

# Metres per degree of latitude (WGS84 mean); longitude scales by cos(lat).
_METERS_PER_DEG_LAT = 111_320.0


def synthesize_coordinates(
    key: str, center_lat: float, center_lon: float, spread_m: float
) -> Tuple[float, float]:
    """Deterministic WGS84 position for a topology element with no geo data.

    The GLM bus network carries no coordinates, so buses/meters are laid out
    inside a disc of ``spread_m`` metres around the configured center
    (``BASE_LATITUDE``/``BASE_LONGITUDE``). The position is derived from a
    SHA-256 hash of ``key`` (bus or meter name) — no RNG involved — so the
    layout is identical across restarts regardless of seeding order.
    """
    digest = hashlib.sha256(key.encode("utf-8")).digest()
    u_radius = int.from_bytes(digest[0:8], "big") / 2**64
    u_angle = int.from_bytes(digest[8:16], "big") / 2**64
    # sqrt() makes the density uniform over the disc area, not clustered at
    # the center.
    radius_m = spread_m * math.sqrt(u_radius)
    angle = 2.0 * math.pi * u_angle
    d_lat = (radius_m * math.cos(angle)) / _METERS_PER_DEG_LAT
    d_lon = (radius_m * math.sin(angle)) / (
        _METERS_PER_DEG_LAT * math.cos(math.radians(center_lat))
    )
    return round(center_lat + d_lat, 6), round(center_lon + d_lon, 6)


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
        battery_by_node: Optional[Dict[str, Dict[str, Any]]] = None,
        ev_by_node: Optional[Dict[str, Dict[str, Any]]] = None,
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
            # Bus anchor position (deterministic hash layout — GLM has no geo
            # data), plus a small per-meter offset so meters sharing a bus
            # don't stack on the exact same map pixel.
            bus_lat, bus_lon = synthesize_coordinates(
                node_id,
                self.config.base_latitude,
                self.config.base_longitude,
                self.config.geo_spread_m,
            )
            meter_lat, meter_lon = synthesize_coordinates(
                f"{node_id}#meter-{meter_id}", bus_lat, bus_lon, 15.0
            )
            loc_data = {
                "name": f"{node_id}_Meter_{meter_id}",
                "latitude": meter_lat,
                "longitude": meter_lon,
                # The bus's derived zone label (its PCC transformer name) when
                # the bus sits behind one, else the bus name — preserves the
                # bus-name-as-zone behaviour for unzoned topologies.
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

            # A GLM-authored BESS / EV station node takes precedence over the PV /
            # random meter-type assignment: it becomes a dedicated storage or
            # charging meter on its own transformer node.
            der_type = self._apply_der_asset(
                loc_data, node_id, battery_by_node, ev_by_node
            )
            if der_type is not None:
                m_type = der_type
            elif pv_on_every_bus:
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
                # Random type per meter, weighted by the configured ratios
                # (solar_prosumer_ratio / grid_consumer_ratio /
                # hybrid_prosumer_ratio) — same knobs as generate_meters().
                m_type = random.choices(
                    [
                        MeterType.GRID_CONSUMER,
                        MeterType.SOLAR_PROSUMER,
                        MeterType.HYBRID_PROSUMER,
                    ],
                    weights=[
                        self.config.grid_consumer_ratio,
                        self.config.solar_prosumer_ratio,
                        self.config.hybrid_prosumer_ratio,
                    ],
                )[0]

            meter = self._create_meter_config(meter_id, m_type, loc_data)
            meter["bus_idx"] = bus_id
            self.meters.append(meter)

        # Guarantee every BESS / EV station node has a dedicated meter even when
        # the meter fleet is spread thinly across buses (not one-per-bus): these
        # are explicit grid assets, not sampled load, so they must always appear.
        self._ensure_der_meters(
            node_ids, zone_by_node, zone_code_by_node, battery_by_node, ev_by_node
        )

        return self.meters

    def _apply_der_asset(
        self,
        loc_data: Dict[str, Any],
        node_id: str,
        battery_by_node: Optional[Dict[str, Dict[str, Any]]],
        ev_by_node: Optional[Dict[str, Dict[str, Any]]],
    ) -> Optional[MeterType]:
        """Tag ``loc_data`` as a BESS or EV station node and return its meter type.

        Battery wins over EV if a node somehow declares both. Returns ``None``
        when the node carries neither asset.
        """
        if battery_by_node and node_id in battery_by_node:
            spec = battery_by_node[node_id]
            loc_data["has_solar"] = False
            loc_data["solar_capacity"] = 0.0
            loc_data["has_battery"] = True
            if spec.get("power_kw"):
                loc_data["battery_power_kw"] = float(spec["power_kw"])
            if spec.get("energy_kwh"):
                loc_data["battery_capacity_kwh"] = float(spec["energy_kwh"])
            return MeterType.BESS

        if ev_by_node and node_id in ev_by_node:
            spec = ev_by_node[node_id]
            loc_data["has_solar"] = False
            loc_data["solar_capacity"] = 0.0
            loc_data["has_ev_charger"] = True
            if spec.get("max_charger_kw"):
                loc_data["ev_charger_kw"] = float(spec["max_charger_kw"])
            if spec.get("num_ports"):
                loc_data["ev_num_ports"] = int(spec["num_ports"])
            return (
                MeterType.DC_FAST_CHARGER
                if spec.get("dc_fast")
                else MeterType.EV_CHARGER
            )

        return None

    def _ensure_der_meters(
        self,
        node_ids: Optional[Sequence[str]],
        zone_by_node: Optional[Dict[str, str]],
        zone_code_by_node: Optional[Dict[str, int]],
        battery_by_node: Optional[Dict[str, Dict[str, Any]]],
        ev_by_node: Optional[Dict[str, Dict[str, Any]]],
    ) -> None:
        assigned = {m.get("node_id") for m in self.meters}
        der_nodes = list((battery_by_node or {}).keys()) + list(
            (ev_by_node or {}).keys()
        )
        index_of = {str(n): i for i, n in enumerate(node_ids or [])}
        for node_id in der_nodes:
            if node_id in assigned:
                continue
            meter_id = len(self.meters) + 1
            bus_id = index_of.get(str(node_id), 0)
            bus_lat, bus_lon = synthesize_coordinates(
                node_id,
                self.config.base_latitude,
                self.config.base_longitude,
                self.config.geo_spread_m,
            )
            meter_lat, meter_lon = synthesize_coordinates(
                f"{node_id}#meter-{meter_id}", bus_lat, bus_lon, 15.0
            )
            loc_data = {
                "name": f"{node_id}_Meter_{meter_id}",
                "latitude": meter_lat,
                "longitude": meter_lon,
                "zone": (zone_by_node.get(node_id) if zone_by_node else None)
                or node_id,
                "zone_code": (
                    zone_code_by_node.get(node_id, 0) if zone_code_by_node else 0
                ),
                "bus_idx": bus_id,
                "node_id": node_id,
                "bus_name": node_id,
            }
            m_type = self._apply_der_asset(
                loc_data, node_id, battery_by_node, ev_by_node
            )
            meter = self._create_meter_config(meter_id, m_type, loc_data)
            meter["bus_idx"] = bus_id
            self.meters.append(meter)
            assigned.add(node_id)

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
            # Zone partition for the reading. Prefer the topology's real zone_code
            # (a bus behind a PCC transformer); only an unzoned bus falls back to
            # spreading meters deterministically by index, so the egress payload
            # still carries a non-null zone_code.
            #
            # The fallback range is 1..9, bounded at both ends. 0 is excluded
            # because it is falsy and gets dropped from the DLMS payload, which
            # sends the bridge back to hash routing; and it means "unzoned"
            # anyway. 10 is excluded because the bridge only honours a code
            # strictly below IOT_NUM_ZONES (default 10) — `calculate_zone_index`
            # in aggregator-logic/src/router.rs hashes anything at or above that
            # to an arbitrary zone_<n> stream. Raising IOT_NUM_ZONES lets this
            # widen; a real topology-supplied code must respect the same bound.
            "zone_code": (
                location_data.get("zone_code")
                if location_data and location_data.get("zone_code")
                else (meter_id % 9) + 1
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

        # BESS / EV station device flags (dedicated-transformer grid assets). Only
        # set when the location data marks the node as such; carried straight into
        # the device model (see devices/battery.py, devices/ev.py).
        if location_data and location_data.get("has_battery"):
            config["has_battery"] = True
            for key in (
                "battery_power_kw",
                "battery_capacity_kwh",
                "battery_soc_init",
                "battery_reserve_soc_floor",
            ):
                if key in location_data:
                    config[key] = location_data[key]
        if location_data and location_data.get("has_ev_charger"):
            config["has_ev_charger"] = True
            for key in ("ev_charger_kw", "ev_num_ports", "ev_utilization"):
                if key in location_data:
                    config[key] = location_data[key]

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
