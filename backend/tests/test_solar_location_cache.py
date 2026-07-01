"""Solar.pvlib Location caching — avoid a per-tick HDF5 elevation lookup.

pvlib.location.Location.__init__ does a real elevation lookup against a
bundled HDF5 dataset (h5py disk I/O). Rebuilding it every call means every
PV-enabled meter pays that cost on every single reading; at fleet scale
(thousands of PV meters) that dominates tick time. Solar caches it per
(latitude, longitude) instead.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

pvlib = pytest.importorskip("pvlib")

from smart_meter_simulator.devices.solar import Solar


def _config(**overrides):
    cfg = {"latitude": 13.75, "longitude": 100.5, "solar_capacity": 5.0}
    cfg.update(overrides)
    return cfg


def test_location_built_once_across_repeated_calls(monkeypatch):
    calls = []
    real_location = pvlib.location.Location

    def counting_location(lat, lon, *a, **k):
        calls.append((lat, lon))
        return real_location(lat, lon, *a, **k)

    monkeypatch.setattr(pvlib.location, "Location", counting_location)

    solar = Solar(_config())
    ts = datetime(2026, 6, 1, 12, 0, tzinfo=timezone.utc)
    for _ in range(5):
        solar.get_generation_kw(ts, "Sunny")

    assert calls == [(13.75, 100.5)]  # built once, reused for the other 4 ticks


def test_location_rebuilt_if_latlon_changes(monkeypatch):
    calls = []
    real_location = pvlib.location.Location

    def counting_location(lat, lon, *a, **k):
        calls.append((lat, lon))
        return real_location(lat, lon, *a, **k)

    monkeypatch.setattr(pvlib.location, "Location", counting_location)

    solar = Solar(_config())
    ts = datetime(2026, 6, 1, 12, 0, tzinfo=timezone.utc)
    solar.get_generation_kw(ts, "Sunny")
    solar.config["latitude"] = 14.0  # simulate a config mutation
    solar.get_generation_kw(ts, "Sunny")

    assert calls == [(13.75, 100.5), (14.0, 100.5)]
