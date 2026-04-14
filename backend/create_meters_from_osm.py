#!/usr/bin/env python3
"""
Create SmartMeter instances at real OSM substation locations.

Maps pandapower buses (from OSM substations) to SmartMeter instances:
- Transmission substations → High-capacity prosumer meters (CLASS_0_5)
- Distribution substations → Commercial meters (CLASS_1_0)
- Loads at each bus → Consumer meters (CLASS_2_0)

Usage:
    uv run python create_meters_from_osm.py
"""

import json
import logging
from pathlib import Path
from typing import Any

import numpy as np

try:
    import pandapower as pp
    PANDAPOWER_AVAILABLE = True
except ImportError:
    PANDAPOWER_AVAILABLE = False

from smart_meter_simulator.core.meter import SmartMeter
from smart_meter_simulator.config.enums import MeterType, AccuracyClass
from smart_meter_simulator.config.settings import SimulatorConfig

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def determine_meter_type(voltage_kv: float, substation_type: str, has_load: bool) -> tuple[MeterType, AccuracyClass]:
    """Determine appropriate meter type and accuracy class based on substation characteristics"""
    if voltage_kv >= 69:
        # Transmission level - high accuracy, battery storage type for grid-scale
        return MeterType.BATTERY_STORAGE, AccuracyClass.CLASS_0_5
    elif substation_type == "transmission":
        return MeterType.HYBRID_PROSUMER, AccuracyClass.CLASS_1_0
    elif has_load:
        # Distribution with load - commercial prosumer
        return MeterType.SOLAR_PROSUMER, AccuracyClass.CLASS_1_0
    else:
        return MeterType.GRID_CONSUMER, AccuracyClass.CLASS_2_0


def create_meters_from_pandapower(
    net: pp.pandapowerNet,
    osm_mapping: dict,
    config: SimulatorConfig,
) -> list[SmartMeter]:
    """
    Create SmartMeter instances from pandapower network and OSM mapping.

    Args:
        net: Pandapower network
        osm_mapping: OSM → pandapower mapping (from build_pandapower_from_osm.py)
        config: Simulator configuration

    Returns:
        List of SmartMeter instances
    """
    meters = []

    substations = osm_mapping.get("substations", {})

    for osm_id, sub_info in substations.items():
        bus_idx = sub_info["bus_idx"]
        voltage_kv = sub_info["vn_kv"]
        sub_type = sub_info.get("category", "distribution")

        # Get bus name from pandapower
        bus_name = net.bus.at[bus_idx, "name"] if bus_idx in net.bus.index else f"Bus-{osm_id}"

        # Check if bus has load
        has_load = bus_idx in net.load.bus.values

        # Get load at this bus
        load_p_mw = 0.0
        if has_load:
            bus_loads = net.load[net.load.bus == bus_idx]
            if len(bus_loads) > 0:
                load_p_mw = bus_loads.p_mw.sum()

        # Determine meter type
        meter_type, accuracy_class = determine_meter_type(voltage_kv, sub_type, has_load and load_p_mw > 0)

        # Create meter
        meter_id = f"OSM_{osm_id}"
        meter_config = {
            "meter_id": meter_id,
            "meter_type": meter_type.value,
            "current_battery_level": 0.0,
            "priority": 2,
            "location": {
                "name": bus_name,
                "osm_id": osm_id,
                "voltage_kv": voltage_kv,
            },
        }
        meter = SmartMeter(meter_config)

        meters.append(meter)
        logger.info(
            f"  Created meter: {meter_id} | {bus_name} | "
            f"{meter_type.value} | {accuracy_class.value}% | "
            f"{voltage_kv:.0f}kV | Load: {load_p_mw:.1f} MW"
        )

    return meters


def create_consumer_meters_at_loads(
    net: pp.pandapowerNet,
    osm_mapping: dict,
    config: SimulatorConfig,
    num_per_bus: int = 5,
) -> list[SmartMeter]:
    """
    Create consumer meters representing loads at each bus.

    Args:
        net: Pandapower network
        osm_mapping: OSM → pandapower mapping
        config: Simulator configuration
        num_per_bus: Number of consumer meters per bus

    Returns:
        List of SmartMeter instances (consumer meters)
    """
    meters = []

    for bus_idx, bus_row in net.bus.iterrows():
        # Find loads at this bus
        bus_loads = net.load[net.load.bus == bus_idx]
        if len(bus_loads) == 0:
            continue

        total_load_mw = bus_loads.p_mw.sum()
        voltage_kv = bus_row.vn_kv

        # Create representative consumer meters
        for i in range(num_per_bus):
            load_share = total_load_mw / num_per_bus

            meter_id = f"LOAD_{bus_idx}_{i:02d}"
            meter_config = {
                "meter_id": meter_id,
                "meter_type": (MeterType.RESIDENTIAL if voltage_kv < 35 else MeterType.COMMERCIAL).value,
                "current_battery_level": 0.0,
                "priority": 2,
                "location": {
                    "bus_name": bus_row["name"],
                    "bus_idx": int(bus_idx),
                    "voltage_kv": voltage_kv,
                    "load_mw": load_share,
                },
            }
            meter = SmartMeter(meter_config)

            meters.append(meter)

    logger.info(f"Created {len(meters)} consumer meters at {len(set(m.config['location']['bus_idx'] for m in meters))} buses")
    return meters


def save_meters_config(meters: list[SmartMeter], output_dir: Path):
    """Save meter configuration to JSON"""
    output_dir.mkdir(parents=True, exist_ok=True)

    meters_config = {
        "meters": [
            {
                "meter_id": m.meter_id,
                "meter_type": m.config.get("meter_type"),
                "accuracy_class": m.accuracy_class.value if hasattr(m.accuracy_class, 'value') else str(m.accuracy_class),
                "location": m.config.get("location"),
            }
            for m in meters
        ],
        "total_meters": len(meters),
    }

    with open(output_dir / "osm_meters.json", "w") as f:
        json.dump(meters_config, f, indent=2, ensure_ascii=False)

    logger.info(f"Saved {len(meters)} meter configurations to {output_dir / 'osm_meters.json'}")


def main():
    if not PANDAPOWER_AVAILABLE:
        logger.error("pandapower not installed. Run: uv sync")
        return

    data_dir = Path(__file__).parent / "data" / "korat"

    # Load pandapower network
    net_file = data_dir / "pandapower_network.json"
    if not net_file.exists():
        logger.error(f"Pandapower network not found: {net_file}")
        logger.info("Run build_pandapower_from_osm.py first")
        return

    net = pp.from_json(str(net_file))

    # Load OSM mapping
    mapping_file = data_dir / "pandapower_mapping.json"
    if not mapping_file.exists():
        logger.error(f"OSM mapping not found: {mapping_file}")
        return

    with open(mapping_file) as f:
        osm_mapping = json.load(f)

    logger.info(f"Loaded pandapower network: {len(net.bus)} buses, {len(net.line)} lines")
    logger.info(f"OSM mapping: {len(osm_mapping['substations'])} substations")

    # Create configuration
    config = SimulatorConfig()

    # Create substation meters
    logger.info("\n=== Creating Substation Meters ===")
    sub_meters = create_meters_from_pandapower(net, osm_mapping, config)

    # Create consumer meters at loads
    logger.info("\n=== Creating Consumer Meters ===")
    consumer_meters = create_consumer_meters_at_loads(net, osm_mapping, config, num_per_bus=3)

    # Total meters
    all_meters = sub_meters + consumer_meters
    logger.info(f"\n=== Total: {len(all_meters)} meters ===")
    logger.info(f"  Substation meters: {len(sub_meters)}")
    logger.info(f"  Consumer meters: {len(consumer_meters)}")

    # Save configuration
    save_meters_config(all_meters, data_dir)


if __name__ == "__main__":
    main()
