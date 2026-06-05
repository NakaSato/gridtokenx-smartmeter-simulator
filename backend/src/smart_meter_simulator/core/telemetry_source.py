"""Telemetry sources: drive meters from real measured data instead of device models.

A :class:`TelemetrySource` supplies a per-tick frame of ``{meter_id -> MeterTelemetry}``.
The engine applies those values as ``manual_override_gen/cons`` on matched meters
(see ``core/engine.py``), bypassing the synthetic load/solar models so the grid solver
computes voltages/flows/losses from *real* injections. Meters absent from a frame stay
synthetic, so partial coverage is a hybrid run.

Spec scheme mirrors ``GRID_TOPOLOGY=glm:``::

    TELEMETRY_SOURCE=synthetic                 # default — no overrides
    TELEMETRY_SOURCE=replay:data/telemetry.csv # replay a CSV of readings

See ``docs/realtime-telemetry.md``.
"""

from __future__ import annotations

import csv
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


@dataclass
class MeterTelemetry:
    """A single real reading for one meter, in instantaneous power (kW)."""

    meter_id: str
    cons_kw: Optional[float] = None
    gen_kw: Optional[float] = None
    reactive_kvar: Optional[float] = None
    voltage: Optional[float] = None
    frequency_hz: Optional[float] = None
    timestamp: Optional[datetime] = None


# A frame: the readings that apply at a given sim instant, keyed by meter_id.
Frame = Dict[str, MeterTelemetry]


class TelemetrySource(ABC):
    """Supplies a frame of real meter readings for a given sim time."""

    name: str = "telemetry"

    @abstractmethod
    def poll(self, sim_time: datetime) -> Frame:
        """Return the readings that apply at ``sim_time`` (may be empty)."""

    def close(self) -> None:  # pragma: no cover - default no-op
        """Release any underlying resources (streams, connections)."""


class SyntheticSource(TelemetrySource):
    """No real data — meters fall back to synthetic device models. Default."""

    name = "synthetic"

    def poll(self, sim_time: datetime) -> Frame:
        return {}


def _to_utc(ts: datetime) -> datetime:
    return ts if ts.tzinfo else ts.replace(tzinfo=timezone.utc)


def _num(row: Dict[str, str], *names: str) -> Optional[float]:
    for name in names:
        if name in row and row[name] not in (None, ""):
            try:
                return float(row[name])
            except (TypeError, ValueError):
                return None
    return None


class ReplaySource(TelemetrySource):
    """Replay timestamped meter readings from a CSV with hold-last-value alignment.

    Columns (case-sensitive, all but ``meter_id`` optional):
      - ``meter_id`` — required.
      - ``timestamp`` — ISO-8601. If absent, all rows form one constant frame.
      - consumption: ``consumption_kw``/``power_consumed`` (kW) **or**
        ``energy_consumed``/``energy_consumed_kwh`` (kWh per interval).
      - generation: ``generation_kw``/``power_generated`` (kW) **or**
        ``energy_generated``/``energy_generated_kwh`` (kWh per interval).
      - reactive power: ``reactive_power_kvar``/``reactive_kvar``/``q_kvar``.
      - ``voltage``, ``frequency`` — optional pass-through.

    Energy columns are converted to kW using ``interval_seconds`` so they round-trip
    through ``generate_reading`` back to the same kWh.
    """

    name = "replay"

    def __init__(self, path: str | Path, interval_seconds: int = 15) -> None:
        self.path = Path(path)
        self.interval_seconds = max(1, int(interval_seconds))
        # Ordered list of (timestamp_or_None, frame); static sources have one entry.
        self._frames: List[Tuple[Optional[datetime], Frame]] = self._load()
        if not self._frames:
            logger.warning("ReplaySource loaded no rows from %s", self.path)

    def _energy_to_kw(self, kwh: float) -> float:
        return kwh / (self.interval_seconds / 3600.0)

    def _row_to_telemetry(self, row: Dict[str, str]) -> Optional[MeterTelemetry]:
        meter_id = (row.get("meter_id") or row.get("meter_serial") or "").strip()
        if not meter_id:
            return None
        cons_kw = _num(row, "consumption_kw", "cons_kw", "power_consumed")
        if cons_kw is None:
            kwh = _num(row, "energy_consumed", "energy_consumed_kwh", "consumption_kwh")
            cons_kw = self._energy_to_kw(kwh) if kwh is not None else None
        gen_kw = _num(row, "generation_kw", "gen_kw", "power_generated")
        if gen_kw is None:
            kwh = _num(
                row, "energy_generated", "energy_generated_kwh", "generation_kwh"
            )
            gen_kw = self._energy_to_kw(kwh) if kwh is not None else None
        return MeterTelemetry(
            meter_id=meter_id,
            cons_kw=cons_kw,
            gen_kw=gen_kw,
            reactive_kvar=_num(row, "reactive_power_kvar", "reactive_kvar", "q_kvar"),
            voltage=_num(row, "voltage"),
            frequency_hz=_num(row, "frequency", "frequency_hz"),
        )

    def _load(self) -> List[Tuple[Optional[datetime], Frame]]:
        if not self.path.exists():
            raise FileNotFoundError(f"Replay telemetry file not found: {self.path}")

        grouped: Dict[Optional[datetime], Frame] = {}
        with self.path.open(newline="", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            for row in reader:
                telemetry = self._row_to_telemetry(row)
                if telemetry is None:
                    continue
                ts_raw = (row.get("timestamp") or "").strip()
                ts: Optional[datetime] = None
                if ts_raw:
                    try:
                        ts = _to_utc(datetime.fromisoformat(ts_raw))
                    except ValueError:
                        logger.warning("Skipping unparsable timestamp %r", ts_raw)
                        continue
                telemetry.timestamp = ts
                grouped.setdefault(ts, {})[telemetry.meter_id] = telemetry

        # None-keyed (timestamp-less) frames collapse to a single constant frame.
        frames = [(ts, frame) for ts, frame in grouped.items()]
        frames.sort(
            key=lambda item: (item[0] is not None, item[0] or _to_utc(datetime.min))
        )
        return frames

    def poll(self, sim_time: datetime) -> Frame:
        if not self._frames:
            return {}
        sim_time = _to_utc(sim_time)
        # Constant (timestamp-less) source: always return the single frame.
        if len(self._frames) == 1 and self._frames[0][0] is None:
            return self._frames[0][1]

        # Hold-last-value: latest frame whose timestamp <= sim_time.
        chosen: Optional[Frame] = None
        for ts, frame in self._frames:
            if ts is None:
                continue
            if ts <= sim_time:
                chosen = frame
            else:
                break
        # Before the first sample: use the earliest timestamped frame.
        if chosen is None:
            for ts, frame in self._frames:
                if ts is not None:
                    return frame
            return {}
        return chosen


class ReferenceGridReplaySource(TelemetrySource):
    """Replay a CINELDI/MATPOWER reference-grid folder directly.

    ``p_load.csv`` and ``q_load.csv`` are wide hourly files with one column per
    load bus. Values are interpreted as MW and MVAr and exposed as kW/kVAr.
    Meter ids follow the topology convention: ``ref_lv_bus_<bus_i>``.
    """

    name = "reference-grid"

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self._frames_by_timestamp: Dict[datetime, Frame] = {}
        self._frames_by_calendar_hour: Dict[Tuple[int, int, int], Frame] = {}
        self._load()
        if not self._frames_by_timestamp:
            logger.warning(
                "ReferenceGridReplaySource loaded no rows from %s", self.path
            )

    def _load(self) -> None:
        if not self.path.exists():
            raise FileNotFoundError(
                f"Reference grid telemetry path not found: {self.path}"
            )
        p_path = self.path / "p_load.csv"
        q_path = self.path / "q_load.csv"
        if not p_path.exists():
            raise FileNotFoundError(f"Reference grid p_load.csv not found: {p_path}")

        q_by_timestamp = self._load_q_rows(q_path) if q_path.exists() else {}
        with p_path.open(newline="", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            for row in reader:
                ts = self._parse_timestamp(row.get("Date", ""))
                if ts is None:
                    continue
                q_row = q_by_timestamp.get(ts, {})
                frame: Frame = {}
                for bus_id, value in row.items():
                    if bus_id == "Date" or value in (None, ""):
                        continue
                    meter_id = self._meter_id(bus_id)
                    frame[meter_id] = MeterTelemetry(
                        meter_id=meter_id,
                        cons_kw=float(value) * 1000.0,
                        gen_kw=None,
                        reactive_kvar=float(q_row.get(bus_id) or 0.0) * 1000.0,
                        timestamp=ts,
                    )
                self._frames_by_timestamp[ts] = frame
                self._frames_by_calendar_hour[(ts.month, ts.day, ts.hour)] = frame

    def _load_q_rows(self, q_path: Path) -> Dict[datetime, Dict[str, str]]:
        rows: Dict[datetime, Dict[str, str]] = {}
        with q_path.open(newline="", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            for row in reader:
                ts = self._parse_timestamp(row.get("Date", ""))
                if ts is not None:
                    rows[ts] = row
        return rows

    def _parse_timestamp(self, value: str) -> Optional[datetime]:
        text = (value or "").strip()
        if not text:
            return None
        try:
            return _to_utc(datetime.fromisoformat(text))
        except ValueError:
            logger.warning("Skipping unparsable reference-grid timestamp %r", value)
            return None

    def _meter_id(self, bus_id: str) -> str:
        from smart_meter_simulator.adapters.reference_grid_loader import (
            reference_meter_id,
        )

        return reference_meter_id(bus_id)

    def poll(self, sim_time: datetime) -> Frame:
        if not self._frames_by_timestamp:
            return {}
        sim_time = _to_utc(sim_time).replace(minute=0, second=0, microsecond=0)
        exact = self._frames_by_timestamp.get(sim_time)
        if exact is not None:
            return exact
        calendar = self._frames_by_calendar_hour.get(
            (sim_time.month, sim_time.day, sim_time.hour)
        )
        if calendar is not None:
            return calendar
        ordered = sorted(self._frames_by_timestamp)
        idx = (sim_time.timetuple().tm_yday - 1) * 24 + sim_time.hour
        return self._frames_by_timestamp[ordered[idx % len(ordered)]]


def parse_telemetry_spec(spec: str) -> Tuple[str, str]:
    """Parse a telemetry source spec into ``(source, value)``.

    Supported: ``synthetic``, ``replay:<path>``,
    ``reference-grid:<folder>``. A plain ``.csv`` path is treated as
    ``replay:<path>``.
    """
    text = (spec or "").strip()
    if not text or text.lower() == "synthetic":
        return "synthetic", ""
    if ":" not in text:
        if text.lower().endswith(".csv"):
            return "replay", text
        raise ValueError(f"Unsupported telemetry spec: {spec}")
    source, value = text.split(":", 1)
    return source.strip().lower(), value.strip()


def build_telemetry_source(spec: str, interval_seconds: int = 15) -> TelemetrySource:
    """Build a telemetry source from a ``TELEMETRY_SOURCE`` spec."""
    source, value = parse_telemetry_spec(spec)
    if source == "synthetic":
        return SyntheticSource()
    if source == "replay":
        return ReplaySource(value, interval_seconds=interval_seconds)
    if source in {"reference-grid", "reference_grid", "matpower"}:
        return ReferenceGridReplaySource(value)
    raise ValueError(f"Unsupported telemetry source: {source}")
