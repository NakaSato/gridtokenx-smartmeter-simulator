"""Core GLM grid model simulation engine."""

from __future__ import annotations

import asyncio
import logging
import time
from datetime import datetime, timedelta, timezone
from typing import Any, List, Optional

from smart_meter_simulator.config import SimulationMode, get_config
from smart_meter_simulator.core.grid_manager import GridManager
from smart_meter_simulator.core.metrics import ACTIVE_METERS, SIMULATION_TICK_TIME
from smart_meter_simulator.core.reading_manager import ReadingManager

logger = logging.getLogger(__name__)


class SimulationEngine:
    """Run meter simulation against the native GLM topology model."""

    def __init__(
        self,
        meters: Optional[List[Any]] = None,
        adapter: Optional[Any] = None,
        grid_topology: Optional[str] = None,
        num_meters: Optional[int] = None,
        topology: Optional[Any] = None,
        **_: Any,
    ) -> None:
        self.config = get_config()

        if topology is None:
            from smart_meter_simulator.core.topology_factory import load_topology_spec

            topology = load_topology_spec(grid_topology or self.config.grid_topology)

        if meters is None and self.config.meter_registry:
            from smart_meter_simulator.devices.ami import SmartMeter
            from smart_meter_simulator.meter_registry import (
                build_meter_configs,
                load_meter_registry,
            )

            entries = load_meter_registry(self.config.meter_registry)
            meter_configs = build_meter_configs(entries, topology)
            meters = [SmartMeter(config) for config in meter_configs]
            logger.info(
                "Built %s meters from registry %s",
                len(meters),
                self.config.meter_registry,
            )

        if meters is None:
            from smart_meter_simulator.devices.ami import SmartMeter
            from smart_meter_simulator.meter_generator import MeterGenerator

            target_meters = num_meters or self.config.num_meters
            generator = MeterGenerator(target_meters)
            if topology and topology.buses:
                pv_capacity_by_node = {pv.bus: pv.capacity_kw for pv in topology.pvs}
                meter_configs = generator.generate_ieee_meters(
                    num_nodes=len(topology.buses),
                    target_meters=target_meters,
                    pv_on_every_bus=self.config.pv_on_every_bus,
                    node_ids=[bus.name for bus in topology.buses],
                    pv_capacity_kw_by_node=pv_capacity_by_node,
                )
            else:
                meter_configs = generator.generate_meters()
            meters = [SmartMeter(config) for config in meter_configs]

        self.meters = meters
        self.grid = GridManager(adapter=adapter, topology=topology)
        self.reading_manager = ReadingManager()
        self.last_readings: List[Any] = []
        self.last_tick_summary: dict[str, Any] = {}

        self.running = False
        self.paused = False
        self.mode = SimulationMode.RANDOM
        self.interval = self.config.simulation_interval
        self.real_time_interval = max(1.0, min(float(self.interval), 5.0))
        self.current_sim_time = datetime.now(timezone.utc).replace(
            hour=8, minute=0, second=0, microsecond=0
        )
        self.weather_mode = "Sunny"
        self.grid_stress_multiplier = 1.0
        self._task: Optional[asyncio.Task] = None

        from smart_meter_simulator.core.telemetry_source import build_telemetry_source

        self.telemetry_source = build_telemetry_source(
            self.config.telemetry_source, self.interval
        )
        if self.telemetry_source.name != "synthetic":
            logger.info("Telemetry source: %s", self.telemetry_source.name)

        # Optional binary Protocol-v4 gRPC egress to the Oracle Bridge.
        self.oracle_emitter: Optional[Any] = None
        if self.config.oracle_grpc_enabled:
            from smart_meter_simulator.transport.oracle_grpc import OracleGrpcEmitter

            self.oracle_emitter = OracleGrpcEmitter(
                self.config.oracle_grpc_target,
                emit_every=self.config.oracle_grpc_emit_every,
            )

    async def start(self) -> None:
        """Start the simulation loop."""
        if self.running:
            return

        logger.info("Starting GLM grid simulator with %s meters", len(self.meters))
        self.running = True
        self.grid.initialize_network(self.meters)
        ACTIVE_METERS.set(len(self.meters))
        if self.oracle_emitter is not None:
            self.oracle_emitter.start()
        self._task = asyncio.create_task(self._simulation_loop())

    async def _simulation_loop(self) -> None:
        """Run ticks until the engine is stopped."""
        while self.running:
            if self.paused:
                await asyncio.sleep(0.25)
                continue

            start_time = time.monotonic()
            try:
                await self.tick()
            except Exception:
                logger.exception("Simulation tick failed")

            elapsed = time.monotonic() - start_time
            await asyncio.sleep(max(0.0, self.real_time_interval - elapsed))

    async def tick(self, timestamp: Optional[datetime] = None) -> List[Any]:
        """Execute one simulation step and update GLM grid state."""
        tick_started = time.monotonic()
        if timestamp is not None:
            self.current_sim_time = timestamp

        self._apply_telemetry(self.current_sim_time)

        readings, _ = await self.reading_manager.generate_all(
            meters=self.meters,
            timestamp=self.current_sim_time,
            interval=self.interval,
            weather_mode=self.weather_mode,
            grid_stress=self.grid_stress_multiplier,
            bus_voltages=self.grid.bus_voltages,
            meter_to_bus=self.grid.meter_to_bus,
        )
        self.grid.update_grid_state(self.meters, readings)
        self.last_readings = readings
        self.last_tick_summary = self._summarize_tick(readings)
        if self.oracle_emitter is not None:
            self.oracle_emitter.emit(readings)
        self.current_sim_time += timedelta(seconds=self.interval)
        SIMULATION_TICK_TIME.observe(time.monotonic() - tick_started)
        return readings

    def _apply_telemetry(self, timestamp: datetime) -> None:
        """Override matched meters with real telemetry for this tick.

        Meters present in the frame are driven by real data (synthetic models bypassed);
        meters absent stay synthetic, so partial coverage is a hybrid run. Overrides are
        one-shot — ``ReadingManager`` consumes and clears them each tick.
        """
        try:
            frame = self.telemetry_source.poll(timestamp)
        except Exception:
            logger.exception("Telemetry poll failed; using synthetic models this tick")
            return
        if not frame:
            return

        for meter in self.meters:
            telemetry = frame.get(meter.meter_id)
            if telemetry is None:
                continue
            if telemetry.cons_kw is not None:
                meter.manual_override_cons = telemetry.cons_kw
            if telemetry.gen_kw is not None:
                meter.manual_override_gen = telemetry.gen_kw
            if telemetry.reactive_kvar is not None:
                meter.manual_override_reactive_kvar = telemetry.reactive_kvar
            if telemetry.frequency_hz is not None:
                meter.receive_frequency(telemetry.frequency_hz)

    def _summarize_tick(self, readings: List[Any]) -> dict[str, Any]:
        total_generation = sum(reading.energy_generated for reading in readings)
        total_consumption = sum(reading.energy_consumed for reading in readings)
        return {
            "timestamp": self.current_sim_time.isoformat(),
            "reading_count": len(readings),
            "total_generation_kwh": total_generation,
            "total_consumption_kwh": total_consumption,
            "net_energy_kwh": total_generation - total_consumption,
            "weather": self.weather_mode,
            "grid_stress_multiplier": self.grid_stress_multiplier,
            "total_losses_kw": self.grid.total_losses_kw,
            "transformer_loss_kw": self.grid.transformer_loss_kw,
            "transformer_loading_pct": self.grid.transformer_loading_pct,
            "total_curtailed_kw": self.grid.total_curtailed_kw,
        }

    async def stop(self) -> None:
        """Stop the simulation loop."""
        self.running = False
        if self._task and self._task is not asyncio.current_task():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        self._task = None
        if self.oracle_emitter is not None:
            await self.oracle_emitter.close()
        ACTIVE_METERS.set(0)
        logger.info("GLM grid simulator stopped")

    async def add_meter(self, meter: Any) -> bool:
        self.meters.append(meter)
        self.grid.initialize_network(self.meters)
        ACTIVE_METERS.set(len(self.meters))
        return True

    async def remove_meter(self, meter_id: str) -> bool:
        original_count = len(self.meters)
        self.meters = [meter for meter in self.meters if meter.meter_id != meter_id]
        if len(self.meters) == original_count:
            return False
        self.grid.initialize_network(self.meters)
        ACTIVE_METERS.set(len(self.meters))
        return True

    async def clear_meters(self) -> bool:
        self.meters = []
        self.grid.initialize_network(self.meters)
        ACTIVE_METERS.set(0)
        return True

    async def pause_simulation(self) -> bool:
        self.paused = True
        return True

    async def resume_simulation(self) -> bool:
        self.paused = False
        return True

    async def step_simulation(self) -> bool:
        await self.tick()
        return True
