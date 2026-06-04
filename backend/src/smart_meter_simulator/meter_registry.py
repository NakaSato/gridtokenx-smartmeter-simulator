"""Meter registry: pin real meters to physical buses.

A registry maps each real meter (by ``meter_id``) to a bus name in the active GLM
topology, plus the metadata needed to build a :class:`SmartMeter` config. This is the
identity layer that turns the randomly-placed synthetic fleet into a model of a *known*
physical fleet — the prerequisite for driving the simulator with real telemetry
(see ``core/telemetry_source.py`` and ``docs/realtime-telemetry.md``).

Supported formats: CSV (operator-friendly) and JSON. Resolve a registry with
``load_meter_registry(path)`` and turn it into meter configs with
``build_meter_configs(entries, topology)``.
"""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from smart_meter_simulator.config import MeterType

_TRUE = {"1", "true", "yes", "y", "t", "on"}


def _as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in _TRUE


def _as_float(value: Any) -> Optional[float]:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


@dataclass
class MeterRegistryEntry:
    """One real meter pinned to a physical bus."""

    meter_id: str
    bus: str
    meter_type: str = "grid_consumer"
    has_solar: bool = False
    solar_capacity_kw: float = 0.0
    phase: str = "A"
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    serial_number: Optional[str] = None

    @classmethod
    def from_mapping(cls, row: Dict[str, Any]) -> "MeterRegistryEntry":
        meter_id = str(row.get("meter_id") or row.get("meter_serial") or "").strip()
        bus = str(
            row.get("bus") or row.get("bus_name") or row.get("node_id") or ""
        ).strip()
        if not meter_id:
            raise ValueError(f"Registry row missing meter_id: {row!r}")
        if not bus:
            raise ValueError(f"Registry row for {meter_id} missing bus: {row!r}")
        cap = _as_float(row.get("solar_capacity_kw")) or 0.0
        return cls(
            meter_id=meter_id,
            bus=bus,
            meter_type=str(row.get("meter_type") or "grid_consumer").strip(),
            has_solar=_as_bool(row.get("has_solar")) or cap > 0,
            solar_capacity_kw=cap,
            phase=str(row.get("phase") or "A").strip() or "A",
            latitude=_as_float(row.get("latitude") or row.get("lat")),
            longitude=_as_float(row.get("longitude") or row.get("lon")),
            serial_number=(
                str(row["serial_number"]).strip() if row.get("serial_number") else None
            ),
        )


def load_meter_registry(path: str | Path) -> List[MeterRegistryEntry]:
    """Load a meter registry from a ``.csv`` or ``.json`` file."""
    reference_grid_dir = _reference_grid_spec_value(path)
    if reference_grid_dir:
        return _load_reference_grid_meter_registry(reference_grid_dir)

    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Meter registry not found: {p}")

    if p.suffix.lower() == ".json":
        data = json.loads(p.read_text(encoding="utf-8"))
        rows = data["meters"] if isinstance(data, dict) and "meters" in data else data
        if not isinstance(rows, list):
            raise ValueError(
                f"JSON registry must be a list (or {{'meters': [...]}}): {p}"
            )
        return [MeterRegistryEntry.from_mapping(r) for r in rows]

    with p.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        return [MeterRegistryEntry.from_mapping(row) for row in reader]


def _reference_grid_spec_value(path: str | Path) -> str:
    text = str(path).strip()
    for prefix in ("reference-grid:", "reference_grid:", "matpower:"):
        if text.lower().startswith(prefix):
            return text.split(":", 1)[1].strip()
    return ""


def _load_reference_grid_meter_registry(
    grid_dir: str | Path,
) -> List[MeterRegistryEntry]:
    from smart_meter_simulator.adapters.reference_grid_loader import (
        load_reference_grid_load_buses,
    )

    entries: List[MeterRegistryEntry] = []
    for row in load_reference_grid_load_buses(grid_dir):
        entries.append(
            MeterRegistryEntry(
                meter_id=row["meter_id"],
                bus=row["bus"],
                meter_type="grid_consumer",
                has_solar=False,
                solar_capacity_kw=0.0,
                phase="A",
            )
        )
    return entries


def build_meter_configs(
    entries: List[MeterRegistryEntry], topology: Optional[Any] = None
) -> List[Dict[str, Any]]:
    """Turn registry entries into SmartMeter config dicts pinned to topology buses.

    Resolves each entry's ``bus`` name to its index in ``topology.buses`` so the grid
    mapper can pin the meter to the real bus. Unknown bus names leave ``bus_idx`` unset
    (the mapper then falls back to enumeration order).
    """
    from smart_meter_simulator.meter_generator import MeterGenerator

    bus_index: Dict[str, int] = {}
    if topology is not None and getattr(topology, "buses", None):
        bus_index = {bus.name: idx for idx, bus in enumerate(topology.buses)}

    generator = MeterGenerator(max(1, len(entries)))
    configs: List[Dict[str, Any]] = []
    for seq, entry in enumerate(entries, start=1):
        location_data = {
            "meter_id": entry.meter_id,
            "serial_number": entry.serial_number or f"SN-{entry.meter_id}",
            "name": f"{entry.bus}_{entry.meter_id}",
            "zone": entry.bus,
            "node_id": entry.bus,
            "bus_name": entry.bus,
            "bus_idx": bus_index.get(entry.bus),
            "phase": entry.phase,
            "latitude": entry.latitude,
            "longitude": entry.longitude,
            "has_solar": entry.has_solar,
            "solar_capacity": entry.solar_capacity_kw,
        }
        try:
            meter_type = MeterType(entry.meter_type)
        except ValueError:
            meter_type = MeterType.GRID_CONSUMER
        configs.append(generator.create_meter_config(seq, meter_type, location_data))
    return configs
