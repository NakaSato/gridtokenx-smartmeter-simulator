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
    ) -> List[EnergyReading]:
        readings = []
        for meter in meters:
            grid_voltage_pu = 1.0
            if bus_voltages and meter_to_bus:
                bus = meter_to_bus.get(meter.meter_id)
                if bus:
                    grid_voltage_pu = bus_voltages.get(bus, 1.0)

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
