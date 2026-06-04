"""Configuration exports for the GLM grid model simulator."""

from __future__ import annotations

import sys

from smart_meter_simulator.config.channels import METER_TYPE_CHANNELS
from smart_meter_simulator.config.enums import (
    AccuracyClass,
    GridConnectionStatus,
    MeterType,
    SimulationMode,
    WeatherCondition,
)
from smart_meter_simulator.config.settings import SimulatorConfig, get_config

_settings_module = sys.modules["smart_meter_simulator.config.settings"]


def __getattr__(name: str):
    return getattr(_settings_module, name)


def __dir__():
    return list(globals().keys()) + [
        "SIMULATION_INTERVAL",
        "NUM_METERS",
        "OUTPUT_FILE",
        "AUTOSTART_SIMULATION",
        "GRID_TOPOLOGY",
        "SOLAR_PROSUMER_RATIO",
        "GRID_CONSUMER_RATIO",
        "HYBRID_PROSUMER_RATIO",
        "PV_MODEL_ENABLED",
        "PV_SURFACE_TILT_DEG",
        "PV_SURFACE_AZIMUTH_DEG",
        "PV_TEMPERATURE_COEFFICIENT",
        "PV_DC_AC_RATIO",
        "PV_ON_EVERY_BUS",
        "BUS_PV_CAPACITY_MIN_KW",
        "BUS_PV_CAPACITY_MAX_KW",
        "ZIP_IMPEDANCE_FRACTION",
        "ZIP_CURRENT_FRACTION",
        "ZIP_POWER_FRACTION",
        "LINE_LENGTH_UNIT",
        "LINE_RESISTANCE_OHM_PER_KM",
        "LINE_REACTANCE_OHM_PER_KM",
        "LINE_CAPACITY_KW",
        "LOG_LEVEL",
        "METRICS_PORT",
    ]


__all__ = [
    "MeterType",
    "AccuracyClass",
    "WeatherCondition",
    "GridConnectionStatus",
    "SimulationMode",
    "METER_TYPE_CHANNELS",
    "SimulatorConfig",
    "get_config",
]
