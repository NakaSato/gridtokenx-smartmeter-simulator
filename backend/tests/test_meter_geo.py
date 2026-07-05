"""Deterministic geo layout for GLM meters (map contract: real lat/lng).

The GLM bus network has no geo data, so bus/meter positions are synthesized
from a name hash around BASE_LATITUDE/BASE_LONGITUDE — non-null, inside the
configured spread, and byte-identical across regenerations (no RNG).
"""

from __future__ import annotations

import math

from smart_meter_simulator.config import get_config
from smart_meter_simulator.meter_generator import MeterGenerator, synthesize_coordinates

_METERS_PER_DEG_LAT = 111_320.0


def _distance_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    d_lat = (lat2 - lat1) * _METERS_PER_DEG_LAT
    d_lon = (lon2 - lon1) * _METERS_PER_DEG_LAT * math.cos(math.radians(lat1))
    return math.hypot(d_lat, d_lon)


def _generate(num_meters: int = 12, num_nodes: int = 12):
    generator = MeterGenerator(num_meters)
    node_ids = [f"ref_lv_bus_{i}" for i in range(1, num_nodes + 1)]
    return generator.generate_ieee_meters(
        num_nodes=num_nodes,
        target_meters=num_meters,
        pv_on_every_bus=False,
        node_ids=node_ids,
    )


def test_meters_get_real_coordinates_within_spread():
    config = get_config()
    configs = _generate()
    assert configs, "generator produced no meters"
    for meter in configs:
        assert meter["latitude"] is not None
        assert meter["longitude"] is not None
        distance = _distance_m(
            config.base_latitude,
            config.base_longitude,
            meter["latitude"],
            meter["longitude"],
        )
        # Disc radius plus the 15 m per-meter jitter, with rounding slack.
        assert distance <= config.geo_spread_m + 15.0 + 1.0


def test_layout_stable_across_regeneration():
    first = _generate()
    second = _generate()
    assert [(m["latitude"], m["longitude"]) for m in first] == [
        (m["latitude"], m["longitude"]) for m in second
    ]


def test_synthesize_coordinates_deterministic_and_distinct():
    a1 = synthesize_coordinates("ref_lv_bus_1", 13.7367, 100.5231, 400.0)
    a2 = synthesize_coordinates("ref_lv_bus_1", 13.7367, 100.5231, 400.0)
    b = synthesize_coordinates("ref_lv_bus_2", 13.7367, 100.5231, 400.0)
    assert a1 == a2
    assert a1 != b


def test_meters_sharing_a_bus_do_not_stack():
    # 6 meters over 2 buses — same-bus meters must still get distinct points.
    configs = _generate(num_meters=6, num_nodes=2)
    points = {(m["latitude"], m["longitude"]) for m in configs}
    assert len(points) == len(configs)
