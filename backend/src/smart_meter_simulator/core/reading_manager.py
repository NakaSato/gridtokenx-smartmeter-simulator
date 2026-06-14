"""Reading generation for the GLM grid simulator."""

from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from smart_meter_simulator.models.reading import EnergyReading


class ReadingManager:
    """Generate smart-meter readings with the local Python device models."""

    async def generate_all(
        self,
        meters: List[Any],
        timestamp: datetime,
        interval: int,
        weather_mode: str,
        grid_stress: float,
        bus_voltages: Optional[Dict[str, float]] = None,
        meter_to_bus: Optional[Dict[str, Any]] = None,
        dr_controller: Optional[Any] = None,
    ) -> Tuple[List[EnergyReading], Dict[str, Any]]:
        for meter in meters:
            meter.update_weather(weather_mode)

        readings = await asyncio.to_thread(
            self._generate_python_loop,
            meters,
            timestamp,
            interval,
            grid_stress,
            bus_voltages,
            meter_to_bus,
            dr_controller,
        )
        return readings, {}

    def _generate_python_loop(
        self,
        meters: List[Any],
        timestamp: datetime,
        interval: int,
        grid_stress: float,
        bus_voltages: Optional[Dict[str, float]] = None,
        meter_to_bus: Optional[Dict[str, Any]] = None,
        dr_controller: Optional[Any] = None,
    ) -> List[EnergyReading]:
        readings = []
        # Resolve the DR load factor once per meter type per tick when any event
        # is active — most meters share a handful of types, so this is a small
        # cache that avoids re-scanning the event list for every meter.
        dr_active = dr_controller is not None and dr_controller.has_active(timestamp)
        dr_factor_cache: Dict[str, float] = {}
        for meter in meters:
            grid_voltage_pu = 1.0
            if bus_voltages and meter_to_bus:
                bus = meter_to_bus.get(meter.meter_id)
                if bus:
                    grid_voltage_pu = bus_voltages.get(bus, 1.0)

            dr_load_factor = 1.0
            if dr_active:
                meter_type = getattr(meter, "meter_type", "")
                if meter_type not in dr_factor_cache:
                    dr_factor_cache[meter_type] = dr_controller.load_factor(
                        timestamp, meter_type
                    )
                dr_load_factor = dr_factor_cache[meter_type]

            reading = meter.generate_reading(
                timestamp,
                override_gen=getattr(meter, "manual_override_gen", None),
                override_cons=getattr(meter, "manual_override_cons", None),
                override_reactive_kvar=getattr(
                    meter, "manual_override_reactive_kvar", None
                ),
                interval_seconds=interval,
                grid_stress=grid_stress,
                grid_voltage_pu=grid_voltage_pu,
                dr_load_factor=dr_load_factor,
            )
            if hasattr(meter, "manual_override_gen"):
                delattr(meter, "manual_override_gen")
            if hasattr(meter, "manual_override_cons"):
                delattr(meter, "manual_override_cons")
            if hasattr(meter, "manual_override_reactive_kvar"):
                delattr(meter, "manual_override_reactive_kvar")
            meter.last_reading = reading
            readings.append(reading)
        return readings
