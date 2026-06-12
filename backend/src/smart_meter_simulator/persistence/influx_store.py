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
    "voltage_pu",
    "battery_power_kw",
    "battery_soc_kwh",
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
        persist_every: int = 1,
    ) -> None:
        self._url = url
        self._token = token
        self._org = org
        self._bucket = bucket
        self._measurement = measurement
        self._persist_every = max(1, persist_every)
        self._client: Optional[Any] = None
        self._inflight: Optional[asyncio.Task] = None
        self._tick_count = 0
        self._started = False

    async def connect(self) -> None:
        """Open the async client. Idempotent."""
        if self._client is not None:
            return
        from influxdb_client.client.influxdb_client_async import InfluxDBClientAsync

        self._client = InfluxDBClientAsync(
            url=self._url, token=self._token, org=self._org
        )
        ok = await self._client.ping()
        if not ok:
            raise ConnectionError(f"InfluxDB ping failed at {self._url}")
        self._started = True
        logger.info("InfluxDB store connected (bucket=%s)", self._bucket)

    # ---- write path ----------------------------------------------------

    def persist(self, readings, run_id: str) -> None:
        """Schedule a background point-batch write for this tick.

        Synchronous and non-blocking. Drops the tick if the store is not started,
        the cadence skips it, or a prior batch is still in flight.
        """
        if not self._started or self._client is None or not readings:
            return
        self._tick_count += 1
        if self._tick_count % self._persist_every != 0:
            return
        if self._inflight is not None and not self._inflight.done():
            logger.debug("Influx persist skipped: previous batch still in flight")
            return
        snapshot = list(readings)
        self._inflight = asyncio.create_task(self._write(snapshot, run_id))

    async def _write(self, readings, run_id: str) -> None:
        try:
            points = [self._point(r, run_id) for r in readings]
            write_api = self._client.write_api()
            await write_api.write(bucket=self._bucket, record=points)
        except Exception:
            INFLUX_PERSIST_FAILED.inc(len(readings))
            logger.exception("InfluxDB reading batch persist failed")

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
            .time(r.timestamp)
        )
        for name in _OPTIONAL_FIELDS:
            value = getattr(r, name, None)
            if value is not None:
                point = point.field(name, float(value))
        return point

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
