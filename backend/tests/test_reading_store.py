"""Unit tests for the PostGIS ReadingStore — no live database.

Row mapping, back-pressure (drop-when-in-flight), emit cadence, and the read-side
helpers are exercised against a fake asyncpg pool/connection so the wire shape is
pinned without a running Postgres+PostGIS.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone

import pytest

from smart_meter_simulator.models.reading import EnergyReading
from smart_meter_simulator.persistence.reading_store import ReadingStore


def _reading(**overrides) -> EnergyReading:
    base = dict(
        meter_id="METER-001",
        timestamp=datetime(2026, 6, 6, 8, 30, 0, tzinfo=timezone.utc),
        energy_generated=5.0,
        energy_consumed=10.0,
        surplus_energy=0.0,
        deficit_energy=5.0,
        voltage=230.5,
        current=4.2,
        reactive_power_kvar=1.1,
        power_factor=0.98,
        frequency=50.0,
        voltage_pu=1.01,
        sequence_number=7,
        interval_seconds=15,
        location="bus-1",
        meter_type="grid_consumer",
        user_type="residential",
    )
    base.update(overrides)
    return EnergyReading(**base)


class _FakeConn:
    def __init__(self, recorder):
        self._recorder = recorder

    async def executemany(self, query, rows):
        self._recorder.append(("executemany", query, list(rows)))

    async def fetch(self, query, *args):
        self._recorder.append(("fetch", query, args))
        return []

    async def fetchval(self, query, *args):
        self._recorder.append(("fetchval", query, args))
        return None


class _FakeAcquire:
    def __init__(self, conn):
        self._conn = conn

    async def __aenter__(self):
        return self._conn

    async def __aexit__(self, *exc):
        return False


class _FakePool:
    def __init__(self):
        self.calls = []
        self.closed = False

    def acquire(self):
        return _FakeAcquire(_FakeConn(self.calls))

    async def close(self):
        self.closed = True


def _store_with_fake_pool(**kwargs) -> tuple[ReadingStore, _FakePool]:
    store = ReadingStore("postgresql://fake", **kwargs)
    pool = _FakePool()
    store._pool = pool
    store._started = True
    return store, pool


# --- row mapping ------------------------------------------------------------


def test_reading_row_matches_insert_column_order():
    row = ReadingStore._reading_row(_reading())
    assert row == (
        "METER-001",
        datetime(2026, 6, 6, 8, 30, 0, tzinfo=timezone.utc),
        5.0,
        10.0,
        0.0,
        5.0,
        230.5,
        4.2,
        50.0,
        1.1,
        0.98,
        1.01,
        7,
        15,
    )


def test_meter_row_uses_config_coords():
    store = ReadingStore("postgresql://fake", fallback_lat=1.0, fallback_lon=2.0)

    class _Meter:
        meter_id = "M-9"
        config = {
            "meter_id": "M-9",
            "serial_number": "SN-9",
            "meter_type": "solar_prosumer",
            "latitude": 13.7,
            "longitude": 100.5,
            "location_name": "Site A",
        }

    # (meter_id, serial, type, lon, lat, province) — lon before lat for ST_MakePoint
    assert store._meter_row(_Meter()) == (
        "M-9",
        "SN-9",
        "solar_prosumer",
        100.5,
        13.7,
        "Site A",
    )


def test_meter_row_falls_back_when_coords_missing():
    store = ReadingStore("postgresql://fake", fallback_lat=1.5, fallback_lon=2.5)

    class _Meter:
        meter_id = "M-1"
        config = {"meter_id": "M-1", "meter_type": "grid_consumer"}

    row = store._meter_row(_Meter())
    assert row[3] == 2.5  # fallback lon
    assert row[4] == 1.5  # fallback lat


def test_meter_row_skips_meter_without_id():
    store = ReadingStore("postgresql://fake")

    class _Meter:
        meter_id = None
        config = {}

    assert store._meter_row(_Meter()) is None


# --- back-pressure / cadence ------------------------------------------------


@pytest.mark.asyncio
async def test_persist_inserts_batch():
    store, pool = _store_with_fake_pool()
    store.persist([_reading(), _reading(meter_id="METER-002")])
    await store._inflight
    inserts = [c for c in pool.calls if c[0] == "executemany"]
    assert len(inserts) == 1
    assert len(inserts[0][2]) == 2  # two reading rows


@pytest.mark.asyncio
async def test_persist_drops_tick_when_previous_in_flight():
    store, pool = _store_with_fake_pool()

    async def _blocked():
        await asyncio.sleep(0.05)

    store._inflight = asyncio.create_task(_blocked())
    store.persist([_reading()])  # should be dropped, not awaited
    # the blocking task is still the inflight task — persist did not replace it
    assert not store._inflight.done() or store._inflight.cancelled()
    await asyncio.sleep(0.06)
    assert not [c for c in pool.calls if c[0] == "executemany"]


@pytest.mark.asyncio
async def test_persist_honours_emit_cadence():
    store, pool = _store_with_fake_pool(persist_every=2)
    store.persist([_reading()])  # tick 1 -> skipped
    assert store._inflight is None
    store.persist([_reading()])  # tick 2 -> writes
    await store._inflight
    assert len([c for c in pool.calls if c[0] == "executemany"]) == 1


@pytest.mark.asyncio
async def test_persist_noop_when_not_started():
    store = ReadingStore("postgresql://fake")
    store._pool = _FakePool()  # connected but not started
    store.persist([_reading()])
    assert store._inflight is None


@pytest.mark.asyncio
async def test_write_failure_is_swallowed_and_counted():
    from smart_meter_simulator.core import metrics

    store, _ = _store_with_fake_pool()

    class _BoomPool:
        def acquire(self):
            raise RuntimeError("db down")

    store._pool = _BoomPool()
    before = metrics.POSTGIS_PERSIST_FAILED._value.get()
    await store._write([_reading(), _reading()])  # must not raise
    after = metrics.POSTGIS_PERSIST_FAILED._value.get()
    assert after - before == 2


# --- read side --------------------------------------------------------------


@pytest.mark.asyncio
async def test_fetch_readings_clamps_limit():
    store, pool = _store_with_fake_pool()
    await store.fetch_readings(limit=99999)
    fetches = [c for c in pool.calls if c[0] == "fetch"]
    assert fetches[0][2][3] == 10000  # limit clamped to 10000


@pytest.mark.asyncio
async def test_close_cancels_inflight_and_closes_pool():
    store, pool = _store_with_fake_pool()

    async def _blocked():
        await asyncio.sleep(1.0)

    store._inflight = asyncio.create_task(_blocked())
    await store.close()
    assert pool.closed
    assert store._pool is None
    assert store._started is False
