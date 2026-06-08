"""Non-blocking PostGIS writer for per-tick meter readings.

The persistence counterpart of the Aggregator Bridge ``AggregatorBridgeEmitter``:
each tick's :class:`EnergyReading`\\ s are batch-inserted into the parent
``grid.meter_readings`` table (PostGIS asset schema under ``database/migrations``).
The meter population is upserted into ``grid.meters`` once on :meth:`start` so the
reading foreign key resolves and geo lookups (``find_nearest_transformer``,
``get_meters_in_radius``) work against the live fleet.

Back-pressure matches the emitter: :meth:`persist` returns immediately and drops
the tick if the previous batch is still in flight, keeping the simulation loop
real-time. All failures are logged and counted (``postgis_persist_failed_total``);
none propagate into the tick.

Numeric parameters are cast ``::float8`` in SQL so plain Python floats insert into
the ``NUMERIC`` columns without round-tripping through :class:`decimal.Decimal`.

Requires migrations ``002_postgis_simple.sql`` + ``004_reading_replay_columns.sql``.
"""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime
from typing import Any, Iterable, Optional

from smart_meter_simulator.core.metrics import POSTGIS_PERSIST_FAILED
from smart_meter_simulator.models.reading import EnergyReading

logger = logging.getLogger(__name__)

_UPSERT_METER = """
INSERT INTO grid.meters (meter_id, serial_number, meter_type, location, province)
VALUES (
    $1, $2, $3,
    ST_SetSRID(ST_MakePoint($4::float8, $5::float8), 4326)::geography,
    $6
)
ON CONFLICT (meter_id) DO UPDATE SET
    serial_number = EXCLUDED.serial_number,
    meter_type = EXCLUDED.meter_type,
    location = EXCLUDED.location,
    province = EXCLUDED.province,
    updated_at = CURRENT_TIMESTAMP
"""

_INSERT_READING = """
INSERT INTO grid.meter_readings (
    meter_id, timestamp,
    energy_generated_kwh, energy_consumed_kwh,
    surplus_energy_kwh, deficit_energy_kwh,
    voltage_v, current_a, frequency_hz,
    reactive_power_kvar, power_factor, voltage_pu,
    sequence_number, interval_seconds
)
VALUES (
    $1, $2,
    $3::float8, $4::float8,
    $5::float8, $6::float8,
    $7::float8, $8::float8, $9::float8,
    $10::float8, $11::float8, $12::float8,
    $13::bigint, $14::int
)
"""

_SELECT_READINGS = """
SELECT meter_id, timestamp,
       energy_generated_kwh, energy_consumed_kwh,
       surplus_energy_kwh, deficit_energy_kwh,
       voltage_v, current_a, frequency_hz,
       reactive_power_kvar, power_factor, voltage_pu,
       sequence_number, interval_seconds
FROM grid.meter_readings
WHERE ($1::text IS NULL OR meter_id = $1)
  AND ($2::timestamptz IS NULL OR timestamp >= $2)
  AND ($3::timestamptz IS NULL OR timestamp <= $3)
ORDER BY timestamp DESC, meter_id
LIMIT $4::int
"""


class ReadingStore:
    """Async PostGIS persistence for simulator readings.

    Lifecycle mirrors the engine's other optional egress: construct cheaply,
    :meth:`connect` + :meth:`register_meters` from an async context on engine
    start, :meth:`persist` (sync, non-blocking) each tick, :meth:`close` on stop.
    """

    def __init__(
        self,
        dsn: str,
        *,
        persist_every: int = 1,
        fallback_lat: float = 0.0,
        fallback_lon: float = 0.0,
        pool_max_size: int = 4,
    ) -> None:
        self._dsn = dsn
        self._persist_every = max(1, persist_every)
        self._fallback_lat = fallback_lat
        self._fallback_lon = fallback_lon
        self._pool_max_size = pool_max_size
        self._pool: Optional[Any] = None
        self._inflight: Optional[asyncio.Task] = None
        self._tick_count = 0
        self._started = False

    async def connect(self) -> None:
        """Open the connection pool. Idempotent."""
        if self._pool is not None:
            return
        import asyncpg

        self._pool = await asyncpg.create_pool(
            self._dsn, min_size=1, max_size=self._pool_max_size
        )
        self._started = True
        logger.info("PostGIS reading store connected")

    async def register_meters(self, meters: Iterable[Any]) -> None:
        """Upsert the meter population into ``grid.meters``.

        Readings carry a foreign key to ``grid.meters(meter_id)``, so this must
        run (once) before the first :meth:`persist`. Meters without geo coordinates
        fall back to the configured base location so the ``NOT NULL`` ``location``
        column is always satisfiable.
        """
        if self._pool is None:
            return
        rows = [self._meter_row(m) for m in meters]
        rows = [r for r in rows if r is not None]
        if not rows:
            return
        async with self._pool.acquire() as conn:
            await conn.executemany(_UPSERT_METER, rows)
        logger.info("Registered %d meter(s) in grid.meters", len(rows))

    def _meter_row(self, meter: Any) -> Optional[tuple]:
        config = getattr(meter, "config", {}) or {}
        meter_id = getattr(meter, "meter_id", None) or config.get("meter_id")
        if not meter_id:
            return None
        lat = config.get("latitude")
        lon = config.get("longitude")
        return (
            str(meter_id),
            config.get("serial_number"),
            config.get("meter_type"),
            float(lon) if lon is not None else self._fallback_lon,
            float(lat) if lat is not None else self._fallback_lat,
            config.get("location_name") or config.get("location"),
        )

    def persist(self, readings) -> None:
        """Schedule a background batch insert for this tick's readings.

        Synchronous and non-blocking. Drops the tick if the store is not started,
        the emit cadence skips it, or a prior batch is still in flight.
        """
        if not self._started or self._pool is None or not readings:
            return
        self._tick_count += 1
        if self._tick_count % self._persist_every != 0:
            return
        if self._inflight is not None and not self._inflight.done():
            logger.debug("PostGIS persist skipped: previous batch still in flight")
            return
        snapshot = list(readings)
        self._inflight = asyncio.create_task(self._write(snapshot))

    async def _write(self, readings) -> None:
        try:
            rows = [self._reading_row(r) for r in readings]
            async with self._pool.acquire() as conn:
                await conn.executemany(_INSERT_READING, rows)
        except Exception:
            POSTGIS_PERSIST_FAILED.inc(len(readings))
            logger.exception("PostGIS reading batch persist failed")

    @staticmethod
    def _reading_row(r: EnergyReading) -> tuple:
        return (
            r.meter_id,
            r.timestamp,
            r.energy_generated,
            r.energy_consumed,
            r.surplus_energy,
            r.deficit_energy,
            r.voltage,
            r.current,
            r.frequency,
            r.reactive_power_kvar,
            r.power_factor,
            r.voltage_pu,
            r.sequence_number,
            r.interval_seconds,
        )

    async def fetch_readings(
        self,
        *,
        meter_id: Optional[str] = None,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        limit: int = 500,
    ) -> list[dict]:
        """Return persisted readings (newest first) for replay/history."""
        if self._pool is None:
            return []
        async with self._pool.acquire() as conn:
            records = await conn.fetch(
                _SELECT_READINGS, meter_id, start, end, max(1, min(limit, 10000))
            )
        return [dict(rec) for rec in records]

    async def network_geojson(
        self, voltage_min: float = 0.0, voltage_max: float = 500.0
    ) -> Optional[dict]:
        """Asset network as GeoJSON via ``grid.export_network_geojson``."""
        if self._pool is None:
            return None
        async with self._pool.acquire() as conn:
            raw = await conn.fetchval(
                "SELECT grid.export_network_geojson($1::numeric, $2::numeric)",
                voltage_min,
                voltage_max,
            )
        return json.loads(raw) if isinstance(raw, str) else raw

    async def network_stats(self) -> Optional[dict]:
        """Asset network statistics via ``grid.get_network_stats``."""
        if self._pool is None:
            return None
        async with self._pool.acquire() as conn:
            raw = await conn.fetchval("SELECT grid.get_network_stats()")
        return json.loads(raw) if isinstance(raw, str) else raw

    async def close(self) -> None:
        """Cancel any in-flight batch and close the pool."""
        self._started = False
        if self._inflight is not None and not self._inflight.done():
            self._inflight.cancel()
        if self._pool is not None:
            await self._pool.close()
            self._pool = None
