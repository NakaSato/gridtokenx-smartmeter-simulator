"""PostGIS persistence for the GLM grid simulator.

Optional egress that mirrors the Oracle Bridge emitter shape: a non-blocking
per-tick writer (:class:`ReadingStore`) batch-inserts readings into the parent
``grid.meter_readings`` table so a run is queryable for replay/history and geo
lookups. Off unless ``POSTGIS_ENABLED`` is set.
"""

from __future__ import annotations

from smart_meter_simulator.persistence.reading_store import ReadingStore

__all__ = ["ReadingStore"]
