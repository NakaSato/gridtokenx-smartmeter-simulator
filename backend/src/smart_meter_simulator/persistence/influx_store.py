"""Non-blocking InfluxDB 2.x writer + query layer for per-tick readings.

A time-series counterpart to :class:`ReadingStore` (PostGIS). Each tick's
:class:`EnergyReading`\\ s are written as points tagged with the **run_id** — the
deterministic-run identity (seed + clock + interval + fleet) — so one run is a
single queryable series for plotting.

Back-pressure matches the other egress: :meth:`persist` returns immediately and
drops the tick if the previous batch is still in flight. All write failures are
logged and counted (``influx_persist_failed_total``); none propagate into the tick.

Standalone sim bucket (``INFLUX_*`` config), independent of PostGIS — both can run
at once, each behind its own env flag.
"""

from __future__ import annotations

import asyncio
import logging
import re
from typing import Any, Optional

from smart_meter_simulator.core.metrics import INFLUX_PERSIST_FAILED
from smart_meter_simulator.models.reading import EnergyReading

logger = logging.getLogger(__name__)

# run_id is inlined into Flux; restrict to a safe charset so a value can never
# break out of the string literal (defense in depth — run_ids are generated).
_SAFE_ID = re.compile(r"[^A-Za-z0-9_.:+-]")

# Optional numeric fields copied onto each point when present on the reading.
_OPTIONAL_FIELDS = (
    "voltage",
    "current",
    "frequency",
    "reactive_power_kvar",
    "power_factor",
    "temperature",
    "voltage_pu",
    "battery_power_kw",
    "battery_soc_kwh",
)

# Numeric grid-state fields lifted off the engine's per-tick summary into the
# grid_state measurement (one point per tick). Anything non-numeric/absent is
# skipped, so the tuple can list more than any single summary carries.
_GRID_STATE_FIELDS = (
    "reading_count",
    "total_generation_kwh",
    "total_consumption_kwh",
    "net_energy_kwh",
    "grid_stress_multiplier",
    "total_losses_kw",
    "transformer_loss_kw",
    "transformer_loading_pct",
    "transformer_tap_pos",
    "total_curtailed_kw",
    "total_reactive_support_kvar",
    "frequency_hz",
    "fault_count",
    "islanded_bus_count",
)


def _sanitize(run_id: str) -> str:
    return _SAFE_ID.sub("_", run_id)


class InfluxReadingStore:
    """Async InfluxDB persistence + read API for simulator runs.

    Lifecycle mirrors :class:`ReadingStore`: construct cheaply, :meth:`connect`
    from an async context on engine start, :meth:`persist` (sync, non-blocking)
    each tick, :meth:`close` on stop.
    """

    def __init__(
        self,
        url: str,
        token: str,
        org: str,
        bucket: str,
        *,
        measurement: str = "meter_reading",
        grid_measurement: str = "grid_state",
        carbon_measurement: str = "meter_carbon",
        bill_measurement: str = "meter_bill",
        persist_every: int = 1,
        persist_grid_state: bool = True,
        persist_carbon: bool = True,
        persist_bill: bool = True,
        carbon_factors: Optional[tuple] = None,
        tariff_params: Optional[tuple] = None,
    ) -> None:
        self._url = url
        self._token = token
        self._org = org
        self._bucket = bucket
        self._measurement = measurement
        self._grid_measurement = grid_measurement
        self._carbon_measurement = carbon_measurement
        self._bill_measurement = bill_measurement
        self._persist_every = max(1, persist_every)
        self._persist_grid_state = persist_grid_state
        self._persist_carbon = persist_carbon
        self._persist_bill = persist_bill
        # (grid_intensity, solar_intensity, kg_per_tree_year)
        self._carbon_factors = carbon_factors
        # (ft_per_kwh, vat_rate, export_per_kwh)
        self._tariff_params = tariff_params
        self._client: Optional[Any] = None
        self._inflight: Optional[asyncio.Task] = None
        self._tick_count = 0
        self._started = False
        # Write-path health, surfaced via :meth:`health` for the status API.
        self._writes_ok = 0
        self._writes_failed = 0
        self._last_error: Optional[str] = None

    async def connect(self) -> None:
        """Open the async client and verify it can actually write. Idempotent.

        ``ping()`` alone is not enough: it succeeds even with an empty/invalid
        token or a missing bucket, after which every per-tick write 401s and is
        swallowed — the classic "connected but nothing saves" failure. So we
        also confirm the bucket is reachable with the supplied token, turning a
        silent per-tick loss into one loud, actionable startup error.
        """
        if self._client is not None:
            return
        from influxdb_client.client.influxdb_client_async import InfluxDBClientAsync

        self._client = InfluxDBClientAsync(
            url=self._url, token=self._token, org=self._org
        )
        ok = await self._client.ping()
        if not ok:
            raise ConnectionError(f"InfluxDB ping failed at {self._url}")
        await self._verify_write()
        self._started = True
        logger.info("InfluxDB store connected (bucket=%s)", self._bucket)

    async def _verify_write(self) -> None:
        """Probe the real write path at startup.

        ``ping()`` succeeds even with an empty/invalid token or a missing
        bucket, after which every per-tick write 401s and is swallowed — the
        classic "connected but nothing saves". A single probe point exercises
        auth + bucket for real, so misconfiguration raises one loud, actionable
        startup error instead of silently dropping every tick. The probe lands
        in its own ``_healthcheck`` measurement, never the data series.
        """
        from influxdb_client import Point

        probe = Point("_healthcheck").field("ok", 1)
        try:
            await self._client.write_api().write(bucket=self._bucket, record=probe)
        except Exception as exc:  # ApiException (401/403/404), network, etc.
            raise ConnectionError(
                f"InfluxDB write probe failed for bucket '{self._bucket}' at "
                f"{self._url}: {exc}. Check INFLUX_TOKEN has write on org "
                f"'{self._org}' and that INFLUX_BUCKET exists."
            ) from exc

    def health(self) -> dict:
        """Write-path health snapshot for the status API."""
        return {
            "connected": self._started,
            "bucket": self._bucket,
            "writes_ok": self._writes_ok,
            "writes_failed": self._writes_failed,
            "last_error": self._last_error,
        }

    # ---- write path ----------------------------------------------------

    def persist(
        self,
        readings,
        run_id: str,
        *,
        grid_summary: Optional[dict] = None,
        meter_states: Optional[list] = None,
    ) -> None:
        """Schedule a background batch write of *all* this tick's data.

        Writes, in one batch under one in-flight slot: per-meter readings, a
        grid_state point (from ``grid_summary``), and per-meter carbon + bill
        points (from ``meter_states`` = ``[(meter_id, meter_type, import_kwh,
        export_kwh, peak_kwh, offpeak_kwh), ...]``). Synchronous and
        non-blocking. Drops the tick if the store is not started, the cadence
        skips it, or a prior batch is still in flight.
        """
        if not self._started or self._client is None or not readings:
            return
        self._tick_count += 1
        if self._tick_count % self._persist_every != 0:
            return
        if self._inflight is not None and not self._inflight.done():
            logger.debug("Influx persist skipped: previous batch still in flight")
            return
        # Snapshot mutable inputs so the background write sees a stable frame.
        snapshot = list(readings)
        grid_snapshot = dict(grid_summary) if grid_summary else None
        states_snapshot = list(meter_states) if meter_states else None
        ts = snapshot[0].timestamp
        self._inflight = asyncio.create_task(
            self._write(snapshot, run_id, grid_snapshot, states_snapshot, ts)
        )

    async def _write(self, readings, run_id, grid_summary, meter_states, ts) -> None:
        try:
            points = [self._point(r, run_id) for r in readings]
            if self._persist_grid_state and grid_summary:
                grid_point = self._grid_point(grid_summary, run_id, ts)
                if grid_point is not None:
                    points.append(grid_point)
            if meter_states:
                points.extend(self._derived_points(meter_states, run_id, ts))
            write_api = self._client.write_api()
            await write_api.write(bucket=self._bucket, record=points)
            self._writes_ok += 1
        except Exception as exc:
            INFLUX_PERSIST_FAILED.inc(len(readings))
            self._writes_failed += 1
            self._last_error = f"{type(exc).__name__}: {exc}"
            # First failure after any success is the actionable one — log it
            # at ERROR so a "connected but not saving" run is visible, not
            # buried. Steady-state repeats drop to debug to avoid log spam.
            if self._writes_failed == 1 or self._writes_ok > 0:
                logger.error(
                    "InfluxDB batch persist failed (bucket=%s, %d ok / %d failed): %s",
                    self._bucket,
                    self._writes_ok,
                    self._writes_failed,
                    self._last_error,
                )
            else:
                logger.debug("InfluxDB batch persist failed: %s", self._last_error)

    def _point(self, r: EnergyReading, run_id: str) -> Any:
        from influxdb_client import Point

        point = (
            Point(self._measurement)
            .tag("run_id", run_id)
            .tag("meter_id", r.meter_id)
            .tag("meter_type", r.meter_type)
            .field("energy_generated", float(r.energy_generated))
            .field("energy_consumed", float(r.energy_consumed))
            .field("surplus_energy", float(r.surplus_energy))
            .field("deficit_energy", float(r.deficit_energy))
            .field("interval_seconds", int(r.interval_seconds))
            .field("sequence_number", int(r.sequence_number))
            .time(r.timestamp)
        )
        for name in _OPTIONAL_FIELDS:
            value = getattr(r, name, None)
            if value is not None:
                point = point.field(name, float(value))
        return point

    def _grid_point(self, summary: dict, run_id: str, ts) -> Optional[Any]:
        from influxdb_client import Point

        point = Point(self._grid_measurement).tag("run_id", run_id).time(ts)
        weather = summary.get("weather")
        if weather is not None:
            point = point.tag("weather", str(weather))
        wrote_any = False
        for name in _GRID_STATE_FIELDS:
            value = summary.get(name)
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                point = point.field(name, float(value))
                wrote_any = True
        return point if wrote_any else None

    def _derived_points(self, meter_states, run_id: str, ts) -> list:
        """Build per-meter carbon + bill points from cumulative-energy states."""
        points: list = []
        carbon_on = self._persist_carbon and self._carbon_factors is not None
        bill_on = self._persist_bill and self._tariff_params is not None
        if not carbon_on and not bill_on:
            return points

        from influxdb_client import Point

        if carbon_on:
            from smart_meter_simulator.emissions import compute_offset

            grid_int, solar_int, kg_tree = self._carbon_factors
        if bill_on:
            from smart_meter_simulator.pricing import TariffClass, compute_bill

            ft, vat, export_rate = self._tariff_params

        for meter_id, _mtype, imp, exp, peak, offpeak in meter_states:
            if carbon_on:
                off = compute_offset(
                    import_kwh=imp,
                    export_kwh=exp,
                    grid_intensity=grid_int,
                    solar_intensity=solar_int,
                    kg_per_tree_year=kg_tree,
                )
                points.append(
                    Point(self._carbon_measurement)
                    .tag("run_id", run_id)
                    .tag("meter_id", meter_id)
                    .field("import_kwh", off.import_kwh)
                    .field("export_kwh", off.export_kwh)
                    .field("grid_emissions_kg", off.grid_emissions_kg)
                    .field("offset_kg", off.offset_kg)
                    .field("net_emissions_kg", off.net_emissions_kg)
                    .field("trees_equivalent", off.trees_equivalent)
                    .time(ts)
                )
            if bill_on:
                try:
                    bill = compute_bill(
                        TariffClass.RESIDENTIAL_AUTO,
                        kwh=imp,
                        peak_kwh=peak,
                        off_peak_kwh=offpeak,
                        ft_per_kwh=ft,
                        vat_rate=vat,
                        export_kwh=exp,
                        export_per_kwh=export_rate,
                    )
                except ValueError:
                    continue
                points.append(
                    Point(self._bill_measurement)
                    .tag("run_id", run_id)
                    .tag("meter_id", meter_id)
                    .field("kwh_total", float(bill.kwh_total))
                    .field("energy_charge", float(bill.energy_charge))
                    .field("ft_charge", float(bill.ft_charge))
                    .field("total", float(bill.total))
                    .field("export_credit", float(bill.export_credit))
                    .field("net_total", float(bill.net_total))
                    .time(ts)
                )
        return points

    # ---- read path -----------------------------------------------------

    async def list_runs(self) -> list[str]:
        """Distinct run_id tag values present in the bucket (newest writes first)."""
        if self._client is None:
            return []
        flux = (
            'import "influxdata/influxdb/schema"\n'
            f'schema.tagValues(bucket: "{self._bucket}", tag: "run_id")'
        )
        records = await self._query_records(flux)
        return [rec.get_value() for rec in records if rec.get_value()]

    async def aggregate_series(self, run_id: str) -> list[dict]:
        """Fleet-wide series for a run: per-tick total gen/con + mean frequency."""
        rid = _sanitize(run_id)
        flux = (
            f'from(bucket: "{self._bucket}")\n'
            "  |> range(start: 0)\n"
            "  |> filter(fn: (r) => r._measurement == "
            f'"{self._measurement}" and r.run_id == "{rid}")\n'
            "  |> filter(fn: (r) => r._field == \"energy_generated\" or "
            'r._field == "energy_consumed" or r._field == "frequency")\n'
            '  |> keep(columns: ["_time", "_field", "_value"])'
        )
        records = await self._query_records(flux)
        # Aggregate across meters in Python: energy fields sum, frequency averages.
        acc: dict[str, dict] = {}
        for rec in records:
            t = rec.get_time().isoformat()
            field = rec.get_field()
            value = rec.get_value()
            bucket = acc.setdefault(
                t, {"gen": 0.0, "con": 0.0, "freq_sum": 0.0, "freq_n": 0}
            )
            if field == "energy_generated":
                bucket["gen"] += value
            elif field == "energy_consumed":
                bucket["con"] += value
            elif field == "frequency":
                bucket["freq_sum"] += value
                bucket["freq_n"] += 1
        series = []
        for t in sorted(acc):
            b = acc[t]
            series.append(
                {
                    "time": t,
                    "energy_generated": round(b["gen"], 6),
                    "energy_consumed": round(b["con"], 6),
                    "net": round(b["gen"] - b["con"], 6),
                    "frequency": (
                        round(b["freq_sum"] / b["freq_n"], 4) if b["freq_n"] else None
                    ),
                }
            )
        return series

    async def meter_series(self, run_id: str, meter_id: str) -> list[dict]:
        """Per-meter series for a run: gen/con/voltage over sim time."""
        rid = _sanitize(run_id)
        mid = meter_id.replace('"', "")
        flux = (
            f'from(bucket: "{self._bucket}")\n'
            "  |> range(start: 0)\n"
            "  |> filter(fn: (r) => r._measurement == "
            f'"{self._measurement}" and r.run_id == "{rid}" '
            f'and r.meter_id == "{mid}")\n'
            "  |> filter(fn: (r) => r._field == \"energy_generated\" or "
            'r._field == "energy_consumed" or r._field == "voltage")\n'
            '  |> pivot(rowKey: ["_time"], columnKey: ["_field"], '
            'valueColumn: "_value")'
        )
        records = await self._query_records(flux)
        series = []
        for rec in records:
            values = rec.values
            series.append(
                {
                    "time": rec.get_time().isoformat(),
                    "energy_generated": values.get("energy_generated"),
                    "energy_consumed": values.get("energy_consumed"),
                    "voltage": values.get("voltage"),
                }
            )
        series.sort(key=lambda row: row["time"])
        return series

    async def _query_records(self, flux: str) -> list[Any]:
        tables = await self._client.query_api().query(flux, org=self._org)
        records: list[Any] = []
        for table in tables:
            records.extend(table.records)
        return records

    async def close(self) -> None:
        """Cancel any in-flight batch and close the client."""
        self._started = False
        if self._inflight is not None and not self._inflight.done():
            self._inflight.cancel()
        if self._client is not None:
            await self._client.close()
            self._client = None
