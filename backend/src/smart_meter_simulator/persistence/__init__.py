"""Persistence egress for the GLM grid simulator.

Optional sinks that mirror the Aggregator Bridge emitter shape — non-blocking
per-tick writers that drop a tick if the prior batch is still in flight:

- :class:`ReadingStore` — PostGIS; batch-inserts into the parent
  ``grid.meter_readings`` table for replay/history + geo lookups
  (``POSTGIS_ENABLED``).
- :class:`InfluxReadingStore` — InfluxDB 2.x; writes points tagged by run_id to a
  standalone sim bucket for time-series plotting (``INFLUX_ENABLED``).

Both are independent and off by default.
"""

from __future__ import annotations

from smart_meter_simulator.persistence.influx_store import InfluxReadingStore
from smart_meter_simulator.persistence.reading_store import ReadingStore

__all__ = ["ReadingStore", "InfluxReadingStore"]
