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

# Selectable run-window presets (sim-clock duration from the resolved start).
_SIM_RANGES = ("hour", "day", "week", "month", "year")


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

        # Deterministic runs: seed the global RNG before any meter fleet
        # generation or per-tick noise. All randomness in this project uses the
        # stdlib `random` module (single global RNG), so one seed covers it.
        import random

        random.seed(self.config.random_seed)
        logger.info("Seeded RNG (random_seed=%s)", self.config.random_seed)

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
                zone_by_node = {
                    bus.name: bus.zone for bus in topology.buses if bus.zone
                }
                zone_code_by_node = {
                    bus.name: bus.zone_code for bus in topology.buses if bus.zone_code
                }
                meter_configs = generator.generate_ieee_meters(
                    num_nodes=len(topology.buses),
                    target_meters=target_meters,
                    pv_on_every_bus=self.config.pv_on_every_bus,
                    node_ids=[bus.name for bus in topology.buses],
                    pv_capacity_kw_by_node=pv_capacity_by_node,
                    zone_by_node=zone_by_node,
                    zone_code_by_node=zone_code_by_node,
                )
            else:
                meter_configs = generator.generate_meters()
            meters = [SmartMeter(config) for config in meter_configs]

        # Meter order is already deterministic by construction (the generator's
        # offset loop / registry order) and preserved here. Tick noise no longer
        # depends on iteration order — each meter draws from its own RNG stream
        # (see SmartMeter._rng) — so we must NOT reorder, or we'd break the
        # bus-index ordering the grid mapping and topology view rely on.
        self.meters = meters
        self.grid = GridManager(adapter=adapter, topology=topology)
        self.reading_manager = ReadingManager()
        # Demand-response controller: API-scheduled load-shed events evaluated
        # against the sim clock each tick (runtime control, like grid faults).
        from smart_meter_simulator.core.demand_response import DemandResponseController

        self.dr_controller = DemandResponseController()
        # Zone island/reconnect control: trips/clears a zone's PCC bus on the
        # grid. Reads zones live from grid.topology, so topology swap is
        # transparent (no rebuild needed here).
        from smart_meter_simulator.core.zone_manager import ZoneController

        self.zone_controller = ZoneController(self.grid)
        self.last_readings: List[Any] = []
        self.last_tick_summary: dict[str, Any] = {}

        self.running = False
        self.paused = False
        # True once a run is launched via reset_deterministic (seeded clock + fleet
        # => byte-identical replay). A plain start() leaves it False.
        self.is_deterministic = False
        self.mode = SimulationMode.RANDOM
        self.interval = self.config.simulation_interval
        self.real_time_interval = max(1.0, min(float(self.interval), 5.0))
        self.current_sim_time = self._initial_sim_time()
        # Pinned run origin: current_sim_time advances each tick, so capture the
        # start once here (and on reset_deterministic). _initial_sim_time() is
        # now()-based when no start is configured, so recomputing it per status
        # request would make the reported start drift every poll.
        self.sim_start_time = self.current_sim_time
        # Optional sim-clock end: when set (via reset_deterministic), the loop
        # auto-stops once current_sim_time reaches it, bounding the run to the
        # half-open window [start, end). None = open-ended (run until stopped).
        self.sim_end_time: Optional[datetime] = None
        # Run-progress counters. tick_count is the number of ticks executed;
        # wall-clock runtime accumulates real seconds the loop has been running,
        # surviving pause/stop/resume (frozen while stopped). Both reset on a
        # deterministic reset. Sim-clock elapsed is derived (tick_count * interval
        # == current_sim_time - sim_start_time).
        self.tick_count = 0
        self.wall_clock_accumulated_s = 0.0
        self.wall_clock_started_monotonic: Optional[float] = None
        self.weather_mode = "Sunny"
        self.grid_stress_multiplier = 1.0
        # System frequency, updated each tick from the supply/demand imbalance and
        # fed to the meters for frequency-watt droop (see _update_grid_frequency).
        self.grid_frequency_hz = self.config.freq_nominal_hz
        # Per-islanded-zone frequency (zone_code -> Hz). An islanded zone's
        # frequency decouples from the grid and floats on its own local
        # supply/demand balance; connected/unzoned meters track grid_frequency_hz.
        # Empty whenever nothing is islanded (full backward-compat with the
        # single-feeder global-frequency model). Reset on deterministic reset.
        self.zone_frequency_hz: dict[int, float] = {}
        self._task: Optional[asyncio.Task] = None

        from smart_meter_simulator.core.telemetry_source import build_telemetry_source

        self.telemetry_source = build_telemetry_source(
            self.config.telemetry_source, self.interval
        )
        if self.telemetry_source.name != "synthetic":
            logger.info("Telemetry source: %s", self.telemetry_source.name)

        # Optional DLMS/COSEM (IEC 62056) REST egress to the Aggregator Bridge.
        self.aggregator_emitter: Optional[Any] = None
        if self.config.aggregator_dlms_enabled:
            from smart_meter_simulator.transport.aggregator_bridge import (
                AggregatorBridgeEmitter,
                TouSchedule,
            )

            self.aggregator_emitter = AggregatorBridgeEmitter(
                self.config.aggregator_bridge_url,
                redis_url=self.config.redis_url,
                api_key=self.config.aggregator_api_key,
                emit_every=self.config.aggregator_dlms_emit_every,
                ownership=self.config.aggregator_meter_owner_map,
                zones={
                    str(m.meter_id): m.config["zone_code"]
                    for m in self.meters
                    if m.config.get("zone_code")
                },
                tou=TouSchedule(
                    enabled=self.config.aggregator_tou_enabled,
                    peak_start_hour=self.config.aggregator_tou_peak_start_hour,
                    peak_end_hour=self.config.aggregator_tou_peak_end_hour,
                ),
            )

        # Optional operational-telemetry egress (SCADA/DNP3/IEC-104-shaped grid +
        # microgrid state that OBIS cannot carry). Consumes the tick summary.
        self.operational_emitter: Optional[Any] = None
        if self.config.operational_telemetry_enabled:
            from smart_meter_simulator.transport.operational_telemetry import (
                OperationalTelemetryEmitter,
                build_operational_transport,
            )

            transport = build_operational_transport(
                self.config.operational_transport,
                base_url=self.config.operational_outstation_url,
                iec104_port=self.config.operational_iec104_port,
                iec104_common_address=self.config.operational_iec104_common_address,
            )
            self.operational_emitter = OperationalTelemetryEmitter(
                transport=transport,
                emit_every=self.config.operational_emit_every,
            )

        # Optional PostGIS persistence (replay/history + geo queries).
        self.reading_store: Optional[Any] = None
        if self.config.postgis_enabled:
            from smart_meter_simulator.persistence import ReadingStore

            self.reading_store = ReadingStore(
                self.config.postgis_url,
                persist_every=self.config.postgis_persist_every,
                fallback_lat=self.config.base_latitude,
                fallback_lon=self.config.base_longitude,
            )

        # Deterministic-run identity, tagged onto Influx points so one run is a
        # single queryable series. Recomputed on a deterministic reset.
        self.run_id = self._compute_run_id()

        # Optional InfluxDB time-series persistence (run plotting).
        self.influx_store: Optional[Any] = None
        if self.config.influx_enabled:
            from smart_meter_simulator.persistence import InfluxReadingStore

            self.influx_store = InfluxReadingStore(
                self.config.influx_url,
                self.config.influx_token,
                self.config.influx_org,
                self.config.influx_bucket,
                measurement=self.config.influx_measurement,
                grid_measurement=self.config.influx_grid_measurement,
                carbon_measurement=self.config.influx_carbon_measurement,
                bill_measurement=self.config.influx_bill_measurement,
                persist_every=self.config.influx_persist_every,
                persist_grid_state=self.config.influx_persist_grid_state,
                persist_carbon=self.config.influx_persist_carbon,
                persist_bill=self.config.influx_persist_bill,
                carbon_factors=(
                    self.config.carbon_grid_intensity_kgco2_per_kwh,
                    self.config.carbon_solar_intensity_kgco2_per_kwh,
                    self.config.carbon_kg_per_tree_year,
                ),
                tariff_params=(
                    self.config.tariff_ft_per_kwh,
                    self.config.tariff_vat_rate,
                    self.config.tariff_export_per_kwh,
                ),
            )

    def _compute_run_id(self) -> str:
        """Stable id for the current run: seed + sim-clock + interval + fleet size.

        Two runs with the same id are byte-identical replays, so their points
        coincide in Influx — re-running overwrites rather than duplicating.
        """
        stamp = self.current_sim_time.strftime("%Y%m%dT%H%M%S")
        return (
            f"seed{self.config.random_seed}-{stamp}"
            f"-i{self.interval}-m{len(self.meters)}"
        )

    def _initial_sim_time(self) -> datetime:
        """Pick the sim-clock start instant.

        When ``SIMULATION_START_TIME`` is set (ISO-8601), the clock starts there —
        pin it with ``RANDOM_SEED`` for byte-identical replay. A naive value is
        assumed UTC. Unset (or unparseable) falls back to today at 08:00 UTC.
        """
        configured = self.config.simulation_start_time
        if configured:
            try:
                parsed = datetime.fromisoformat(configured)
            except ValueError:
                logger.warning(
                    "Invalid SIMULATION_START_TIME %r; using today 08:00 UTC",
                    configured,
                )
            else:
                if parsed.tzinfo is None:
                    parsed = parsed.replace(tzinfo=timezone.utc)
                logger.info("Sim clock pinned to %s", parsed.isoformat())
                return parsed
        return datetime.now(timezone.utc).replace(
            hour=8, minute=0, second=0, microsecond=0
        )

    async def start(self) -> None:
        """Start the simulation loop."""
        if self.running:
            return

        logger.info("Starting GLM grid simulator with %s meters", len(self.meters))
        self.running = True
        if self.wall_clock_started_monotonic is None:
            self.wall_clock_started_monotonic = time.monotonic()
        self.grid.initialize_network(self.meters)
        ACTIVE_METERS.set(len(self.meters))
        if self.aggregator_emitter is not None:
            if self.config.aggregator_iam_onboard_enabled:
                await self._onboard_meter_owners()
            self.aggregator_emitter.start()
        if self.operational_emitter is not None:
            self.operational_emitter.start()
        if self.reading_store is not None:
            await self._start_reading_store()
        if self.influx_store is not None:
            await self._start_influx_store()
        self._task = asyncio.create_task(self._simulation_loop())

    async def _start_reading_store(self) -> None:
        """Connect the PostGIS store and register the meter population.

        Non-fatal: on any failure (DB down, schema missing) the store is disabled
        for the run so the simulation keeps ticking without persistence.
        """
        try:
            await self.reading_store.connect()
            await self.reading_store.register_meters(self.meters)
        except Exception:
            logger.exception("PostGIS store init failed; persistence disabled")
            self.reading_store = None

    async def _start_influx_store(self) -> None:
        """Connect the InfluxDB store. Non-fatal: on failure (DB down, bad token)
        the store is disabled for the run so the simulation keeps ticking."""
        try:
            await self.influx_store.connect()
        except Exception:
            logger.exception("InfluxDB store init failed; persistence disabled")
            self.influx_store = None

    async def _onboard_meter_owners(self) -> None:
        """Resolve meter owners via IAM onboarding and feed them to the emitter.

        IAM is the primary source. For meters IAM cannot resolve this run (e.g. an
        account that already exists but is not yet email-verified, so login can't
        return its user_id), fall back to reading any owner a prior run already
        seeded in the bridge's Redis registry — making re-runs idempotent without
        re-deriving every owner. Non-fatal: on any failure the emitter keeps the
        static owner map.
        """
        from smart_meter_simulator.transport.aggregator_bridge import (
            read_meter_owners_redis,
        )
        from smart_meter_simulator.transport.iam_onboarding import onboard_fleet

        try:
            meter_ids = [m.meter_id for m in self.meters]
            owners = await onboard_fleet(self.config.iam_gateway_url, meter_ids)

            missing = [mid for mid in meter_ids if mid not in owners]
            if missing:
                recovered = read_meter_owners_redis(self.config.redis_url, missing)
                if recovered:
                    owners.update(recovered)
                    logger.info(
                        "Recovered %d meter owner(s) from bridge Redis", len(recovered)
                    )

            if owners:
                self.aggregator_emitter.add_ownership(owners)
                logger.info("Resolved %d meter owner(s) for egress", len(owners))

            unresolved = [mid for mid in meter_ids if mid not in owners]
            if unresolved:
                logger.warning(
                    "%d meter(s) unattributed (no IAM user_id, none in Redis); "
                    "telemetry resolves to Uuid::nil and skips settlement. If the "
                    "IAM account exists but is unverified, verify its email to "
                    "enable login-based attribution. Meters: %s",
                    len(unresolved),
                    ", ".join(unresolved[:10]) + ("…" if len(unresolved) > 10 else ""),
                )
        except Exception:
            logger.exception("IAM onboarding failed; using static owner map only")

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

            if self._reached_end():
                logger.info(
                    "Sim end reached (%s); stopping run", self.sim_end_time.isoformat()
                )
                await self.stop()
                break

            elapsed = time.monotonic() - start_time
            await asyncio.sleep(max(0.0, self.real_time_interval - elapsed))

    def _reached_end(self) -> bool:
        """True once the sim clock has advanced to/past the configured end."""
        return (
            self.sim_end_time is not None and self.current_sim_time >= self.sim_end_time
        )

    @staticmethod
    def _range_end(start: datetime, key: str) -> datetime:
        """End instant for a window preset, calendar-aware for month/year.

        Day-of-month is clamped to the target month's last day (e.g. Jan 31 +
        1 month -> Feb 28/29) so the replace never raises.
        """
        if key == "hour":
            return start + timedelta(hours=1)
        if key == "day":
            return start + timedelta(days=1)
        if key == "week":
            return start + timedelta(weeks=1)
        import calendar

        if key == "month":
            month = start.month % 12 + 1
            year = start.year + (1 if start.month == 12 else 0)
        else:  # "year"
            month = start.month
            year = start.year + 1
        last_day = calendar.monthrange(year, month)[1]
        return start.replace(year=year, month=month, day=min(start.day, last_day))

    def sim_progress(self) -> Optional[float]:
        """Fraction [0,1] of the bounded window elapsed, or None if open-ended."""
        if self.sim_end_time is None:
            return None
        span = (self.sim_end_time - self.sim_start_time).total_seconds()
        if span <= 0:
            return 1.0
        return max(0.0, min(1.0, self.sim_elapsed_seconds() / span))

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
            dr_controller=self.dr_controller,
        )
        self.grid.update_grid_state(self.meters, readings)
        self._update_grid_frequency(readings)
        self.last_readings = readings
        self.last_tick_summary = self._summarize_tick(readings)
        if self.aggregator_emitter is not None:
            self.aggregator_emitter.emit(readings)
        if self.operational_emitter is not None:
            # Tie-switch status is not part of the canonical tick summary; thread
            # it in for the operational point map (binary switch-closed points).
            self.operational_emitter.emit(
                {
                    **self.last_tick_summary,
                    "switches": self.grid.switch_status()["switches"],
                }
            )
        if self.reading_store is not None:
            self.reading_store.persist(readings)
        if self.influx_store is not None:
            self.influx_store.persist(
                readings,
                self.run_id,
                grid_summary=self.last_tick_summary,
                meter_states=self._meter_energy_states(),
            )
        self.current_sim_time += timedelta(seconds=self.interval)
        self.tick_count += 1
        SIMULATION_TICK_TIME.observe(time.monotonic() - tick_started)
        return readings

    def runtime_seconds(self) -> float:
        """Real wall-clock seconds the simulation loop has been running.

        Accumulates across start/stop cycles and keeps counting while paused;
        frozen once stopped. Zero before the first start.
        """
        runtime = self.wall_clock_accumulated_s
        if self.wall_clock_started_monotonic is not None:
            runtime += time.monotonic() - self.wall_clock_started_monotonic
        return runtime

    def sim_elapsed_seconds(self) -> float:
        """Simulated-clock seconds advanced since the run origin."""
        return (self.current_sim_time - self.sim_start_time).total_seconds()

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

    def _freq_from_balance(self, gen: float, load: float) -> float:
        """Frequency for a supply/demand balance: nominal + full-swing × ratio.

        Surplus generation pushes above nominal, deficit pulls below; normalized
        by the larger of gen/load so it self-scales (ratio bounded to [-1, 1]).
        """
        base = max(gen, load, 1e-9)
        ratio = max(-1.0, min(1.0, (gen - load) / base))
        return self.config.freq_nominal_hz + self.config.freq_full_swing_hz * ratio

    def _update_grid_frequency(self, readings: List[Any]) -> None:
        """Derive frequency from this tick's imbalance and feed it to the meters
        for next-tick frequency-watt droop.

        The grid (utility-backed) frequency is derived from every *connected*
        meter's balance. Each commanded-islanded zone decouples: its frequency
        floats on only its own members' balance, so a generation-short island
        sags in frequency independently of the wider grid. The push is a one-tick
        governor lag — this tick's imbalance sets the frequency next tick reacts
        to. External telemetry frequency (set in `_apply_telemetry`, which runs
        first each tick) re-overrides before generation, so it stays
        authoritative when present.

        With nothing islanded this collapses to the original single global
        frequency over all readings — byte-identical to the pre-zone model.
        """
        if not self.config.freq_droop_enabled:
            return

        topology = self.grid.topology
        islanded_codes = (
            {code for code in topology.zones if self.zone_controller.is_islanded(code)}
            if topology and topology.zones
            else set()
        )
        code_by_meter = {
            meter.meter_id: meter.config.get("zone_code", 0) for meter in self.meters
        }

        grid_gen = grid_load = 0.0
        zone_acc: dict[int, list[float]] = {}
        for reading in readings:
            code = code_by_meter.get(getattr(reading, "meter_id", None), 0)
            if code in islanded_codes:
                acc = zone_acc.setdefault(code, [0.0, 0.0])
                acc[0] += reading.energy_generated
                acc[1] += reading.energy_consumed
            else:
                grid_gen += reading.energy_generated
                grid_load += reading.energy_consumed

        self.grid_frequency_hz = self._freq_from_balance(grid_gen, grid_load)
        self.zone_frequency_hz = {
            code: self._freq_from_balance(gen, load)
            for code, (gen, load) in zone_acc.items()
        }

        for meter in self.meters:
            code = code_by_meter.get(meter.meter_id, 0)
            hz = self.zone_frequency_hz.get(code, self.grid_frequency_hz)
            meter.receive_frequency(hz)

    def _summarize_tick(self, readings: List[Any]) -> dict[str, Any]:
        total_generation = sum(reading.energy_generated for reading in readings)
        total_consumption = sum(reading.energy_consumed for reading in readings)
        total_dr_shed_kw = sum(reading.dr_shed_kw or 0.0 for reading in readings)
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
            "transformer_tap_pos": self.grid.transformer_tap_pos,
            "total_curtailed_kw": self.grid.total_curtailed_kw,
            "total_reactive_support_kvar": self.grid.total_reactive_support_kvar,
            "frequency_hz": self.grid_frequency_hz,
            "fault_count": (
                len(self.grid.faulted_lines)
                + len(self.grid.faulted_buses)
                + len(self.grid.faulted_transformers)
            ),
            "islanded_bus_count": len(self.grid.islanded_buses),
            "total_dr_shed_kw": round(total_dr_shed_kw, 3),
            "active_dr_events": len(
                self.dr_controller.active_events(self.current_sim_time)
            ),
            "zones": self._zone_summaries(readings),
        }

    def _zone_summaries(self, readings: List[Any]) -> list[dict[str, Any]]:
        """Per-zone aggregates for this tick (energy + live island status).

        Empty for ungrouped topologies. Island status reuses the grid solver's
        per-tick reachability (``islanded_buses``) — a zone reads islanded when
        any member bus is cut off from the slack, so the flag is live even
        before the Phase-2 zone island/reconnect control exists.
        """
        topology = self.grid.topology
        if not topology or not topology.zones:
            return []
        code_by_meter = {
            meter.meter_id: meter.config.get("zone_code", 0) for meter in self.meters
        }
        agg: dict[int, list[float]] = {}
        for reading in readings:
            code = code_by_meter.get(reading.meter_id, 0)
            if not code:
                continue
            bucket = agg.setdefault(code, [0.0, 0.0, 0.0])
            bucket[0] += reading.energy_generated
            bucket[1] += reading.energy_consumed
            bucket[2] += 1
        islanded_buses = self.grid.islanded_buses
        summaries = []
        for code, spec in sorted(topology.zones.items()):
            gen, load, meter_count = agg.get(code, (0.0, 0.0, 0.0))
            summaries.append(
                {
                    "zone_code": code,
                    "label": spec.label,
                    "bus_count": len(spec.member_buses),
                    "meter_count": int(meter_count),
                    "generation_kwh": round(gen, 6),
                    "consumption_kwh": round(load, 6),
                    "net_energy_kwh": round(gen - load, 6),
                    "islandable": spec.islandable,
                    # Self-supporting: can island AND hold voltage via local DER.
                    "island_capable": bool(spec.islandable and spec.der_bus),
                    "commanded_island": self.zone_controller.is_islanded(code),
                    "islanded": bool(set(spec.member_buses) & islanded_buses),
                    # Islanded zone's own decoupled frequency; connected zones
                    # report the grid frequency they track.
                    "frequency_hz": self.zone_frequency_hz.get(
                        code, self.grid_frequency_hz
                    ),
                }
            )
        return summaries

    def _meter_energy_states(self) -> list:
        """Snapshot each meter's cumulative energy registers for Influx derived
        (carbon + bill) points. Cheap tuple list; built only when Influx is on."""
        return [
            (
                m.meter_id,
                getattr(m, "meter_type", ""),
                getattr(m, "cumulative_import_kwh", 0.0),
                getattr(m, "cumulative_export_kwh", 0.0),
                getattr(m, "cumulative_peak_import_kwh", 0.0),
                getattr(m, "cumulative_offpeak_import_kwh", 0.0),
            )
            for m in self.meters
        ]

    async def stop(self) -> None:
        """Stop the simulation loop."""
        self.running = False
        if self.wall_clock_started_monotonic is not None:
            self.wall_clock_accumulated_s += (
                time.monotonic() - self.wall_clock_started_monotonic
            )
            self.wall_clock_started_monotonic = None
        if self._task and self._task is not asyncio.current_task():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        self._task = None
        if self.aggregator_emitter is not None:
            await self.aggregator_emitter.close()
        if self.operational_emitter is not None:
            await self.operational_emitter.close()
        if self.reading_store is not None:
            await self.reading_store.close()
        if self.influx_store is not None:
            await self.influx_store.close()
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

    def _rebuild_fleet(self, target_meters: int) -> None:
        """Regenerate the meter population from the current grid topology.

        Mirrors ``__init__``'s fleet construction (registry first, else the
        generator) so a re-seeded run reproduces byte-identical meters. Call only
        after ``random.seed`` so seeded UUIDs/configs land deterministically.
        """
        from smart_meter_simulator.devices.ami import SmartMeter

        topology = self.grid.topology
        if self.config.meter_registry:
            from smart_meter_simulator.meter_registry import (
                build_meter_configs,
                load_meter_registry,
            )

            entries = load_meter_registry(self.config.meter_registry)
            meter_configs = build_meter_configs(entries, topology)
        else:
            from smart_meter_simulator.meter_generator import MeterGenerator

            generator = MeterGenerator(target_meters)
            if topology and topology.buses:
                pv_capacity_by_node = {pv.bus: pv.capacity_kw for pv in topology.pvs}
                zone_by_node = {
                    bus.name: bus.zone for bus in topology.buses if bus.zone
                }
                zone_code_by_node = {
                    bus.name: bus.zone_code for bus in topology.buses if bus.zone_code
                }
                meter_configs = generator.generate_ieee_meters(
                    num_nodes=len(topology.buses),
                    target_meters=target_meters,
                    pv_on_every_bus=self.config.pv_on_every_bus,
                    node_ids=[bus.name for bus in topology.buses],
                    pv_capacity_kw_by_node=pv_capacity_by_node,
                    zone_by_node=zone_by_node,
                    zone_code_by_node=zone_code_by_node,
                )
            else:
                meter_configs = generator.generate_meters()
        self.meters = [SmartMeter(config) for config in meter_configs]

    async def reset_deterministic(
        self,
        *,
        seed: Optional[int] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        time_range: Optional[str] = None,
        interval: Optional[int] = None,
        num_meters: Optional[int] = None,
        autostart: bool = True,
    ) -> dict[str, Any]:
        """Configure + (re)start a deterministic run from the API.

        Re-seeds the global RNG, rebuilds the fleet (so seeded UUIDs/configs and
        per-meter noise streams reproduce), and pins the sim clock — yielding
        byte-identical replay. Overrides persist on the config singleton so newly
        built ``SmartMeter`` instances pick up the seed. Raises ``ValueError`` on a
        bad ``start_time`` / non-positive ``interval``/``num_meters``.

        ``num_meters`` is a *soft* target: ``_rebuild_fleet`` runs IEEE meter
        generation, which is bus-bound under ``PV_ON_EVERY_BUS`` (one meter per
        topology bus), so the realized fleet is capped at the bus count regardless
        of the request (e.g. an 80-bus grid always yields 80 meters). The returned
        ``total_meters`` is the realized count.
        """
        import random

        if start_time is not None:
            try:
                datetime.fromisoformat(start_time)
            except ValueError as exc:
                raise ValueError(
                    f"Invalid start_time {start_time!r}; expected ISO-8601"
                ) from exc
        parsed_end: Optional[datetime] = None
        if end_time is not None:
            try:
                parsed_end = datetime.fromisoformat(end_time)
            except ValueError as exc:
                raise ValueError(
                    f"Invalid end_time {end_time!r}; expected ISO-8601"
                ) from exc
            if parsed_end.tzinfo is None:
                parsed_end = parsed_end.replace(tzinfo=timezone.utc)
            # Fail fast before any state mutation when both bounds are explicit.
            if start_time is not None:
                parsed_start = datetime.fromisoformat(start_time)
                if parsed_start.tzinfo is None:
                    parsed_start = parsed_start.replace(tzinfo=timezone.utc)
                if parsed_end <= parsed_start:
                    raise ValueError(
                        f"end_time {end_time!r} must be after start_time {start_time!r}"
                    )
        if time_range is not None:
            if time_range not in _SIM_RANGES:
                raise ValueError(
                    f"Invalid time_range {time_range!r}; expected one of "
                    f"{sorted(_SIM_RANGES)}"
                )
            if end_time is not None:
                raise ValueError("Pass either end_time or time_range, not both")
        if interval is not None and interval <= 0:
            raise ValueError("interval must be > 0")
        if num_meters is not None and num_meters <= 0:
            raise ValueError("num_meters must be > 0")

        if self.running:
            await self.stop()

        if seed is not None:
            self.config.random_seed = seed
        if start_time is not None:
            self.config.simulation_start_time = start_time
        if interval is not None:
            self.config.simulation_interval = interval
            self.interval = interval
            self.real_time_interval = max(1.0, min(float(interval), 5.0))

        random.seed(self.config.random_seed)
        logger.info("Seeded RNG (random_seed=%s)", self.config.random_seed)

        target = num_meters or len(self.meters) or self.config.num_meters
        self._rebuild_fleet(target)

        self.current_sim_time = self._initial_sim_time()
        self.sim_start_time = self.current_sim_time
        # A range preset (hour/day/week/month/year) sets the end relative to the
        # resolved start, so a UI can pick a window without computing the instant.
        if parsed_end is None and time_range is not None:
            parsed_end = self._range_end(self.sim_start_time, time_range)
        # Bounded run window: end must be strictly after start. None = open-ended.
        if parsed_end is not None and parsed_end <= self.sim_start_time:
            raise ValueError(
                f"end_time {parsed_end.isoformat()} must be after start_time "
                f"{self.sim_start_time.isoformat()}"
            )
        self.sim_end_time = parsed_end
        # Fresh run => fresh progress counters (start() re-arms the wall clock).
        self.tick_count = 0
        self.wall_clock_accumulated_s = 0.0
        self.wall_clock_started_monotonic = None
        self.grid.clear_all_faults()
        self.dr_controller.clear()
        self.grid.initialize_network(self.meters)
        self.last_readings = []
        self.last_tick_summary = {}
        self.grid_frequency_hz = self.config.freq_nominal_hz
        self.zone_frequency_hz = {}
        # New seed/clock/fleet => new run identity for Influx tagging.
        self.run_id = self._compute_run_id()
        self.is_deterministic = True

        if self.reading_store is not None:
            try:
                await self.reading_store.register_meters(self.meters)
            except Exception:
                logger.exception("PostGIS re-register failed after deterministic reset")

        logger.info(
            "Deterministic reset: seed=%s start=%s interval=%s meters=%s",
            self.config.random_seed,
            self.current_sim_time.isoformat(),
            self.interval,
            len(self.meters),
        )

        if autostart:
            await self.start()

        return {
            "seed": self.config.random_seed,
            "start_time": self.current_sim_time.isoformat(),
            "end_time": (self.sim_end_time.isoformat() if self.sim_end_time else None),
            "interval": self.interval,
            "total_meters": len(self.meters),
            "running": self.running,
            "run_id": self.run_id,
        }

    async def pause_simulation(self) -> bool:
        self.paused = True
        return True

    async def resume_simulation(self) -> bool:
        self.paused = False
        return True

    async def step_simulation(self) -> bool:
        await self.tick()
        return True
