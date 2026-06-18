"""Microgrid zone island/reconnect control for the GLM grid simulator.

A zone (``ZoneSpec`` in :mod:`core.topology`) is islanded by tripping its point
of common coupling — the PCC bus, i.e. the transformer LV terminal where the zone
meets the utility backbone. Tripping that bus removes the coupling, so the zone
and everything below it falls off the substation slack: the grid solver's
per-tick reachability sweep then reports those buses in ``islanded_buses``.

This is a **runtime control surface** like fault injection and demand response —
it adds/removes a bus fault on :class:`~core.grid_manager.GridManager`. No private
island state is kept: a zone reads islanded iff its PCC bus is currently faulted,
so the view stays consistent through resets and topology hot-swaps (both clear
faults) with nothing extra to reset.

Phase 2 semantics: islanding *disconnects* a zone from the grid. Without a local
slack to hold it (per-zone frequency / island DER balancing is Phase 4) an
islanded zone de-energizes — which is exactly what ``islanded_buses`` reflects.
"""

from __future__ import annotations

from typing import Any, Dict, List

from smart_meter_simulator.core.topology import ZoneSpec


class ZoneController:
    """Island/reconnect zones and report their live state via the grid faults.

    Holds only a reference to the :class:`GridManager`; zone definitions are read
    live from ``grid.topology.zones`` so a topology hot-swap is transparent.
    """

    def __init__(self, grid: Any) -> None:
        self._grid = grid

    @property
    def zones(self) -> Dict[int, ZoneSpec]:
        topology = getattr(self._grid, "topology", None)
        return topology.zones if topology and topology.zones else {}

    def get(self, code: int) -> ZoneSpec | None:
        return self.zones.get(code)

    def is_islanded(self, code: int) -> bool:
        """True when the zone's PCC bus is currently tripped (commanded island)."""
        spec = self.zones.get(code)
        return bool(spec and spec.pcc_bus and spec.pcc_bus in self._grid.faulted_buses)

    def island(self, code: int) -> ZoneSpec:
        """Disconnect a zone by tripping its PCC bus. Effective next solve.

        Raises ``KeyError`` for an unknown zone code and ``ValueError`` for a
        non-islandable zone (one with no PCC transformer).
        """
        spec = self.zones.get(code)
        if spec is None:
            raise KeyError(code)
        if not spec.islandable or not spec.pcc_bus:
            raise ValueError(f"zone {code} is not islandable (no PCC transformer)")
        self._grid.apply_fault("bus", spec.pcc_bus)
        return spec

    def reconnect(self, code: int) -> ZoneSpec:
        """Reconnect a zone by clearing its PCC bus fault. Effective next solve.

        Raises ``KeyError`` for an unknown zone code. Idempotent: reconnecting a
        zone that is already connected is a no-op (returns the spec).
        """
        spec = self.zones.get(code)
        if spec is None:
            raise KeyError(code)
        if spec.pcc_bus:
            self._grid.clear_fault("bus", spec.pcc_bus)
        return spec

    def _zone_status(self, spec: ZoneSpec) -> Dict[str, Any]:
        islanded_buses = self._grid.islanded_buses
        return {
            "zone_code": spec.code,
            "label": spec.label,
            "bus_count": len(spec.member_buses),
            "pcc_bus": spec.pcc_bus,
            "pcc_transformer": spec.pcc_transformer,
            "der_bus": spec.der_bus,
            "islandable": spec.islandable,
            # Self-supporting: can island AND hold its own voltage via local DER.
            "island_capable": bool(spec.islandable and spec.der_bus),
            # Commanded: operator tripped the PCC. Electrical: any member bus is
            # actually cut off from the slack this tick (the two agree once the
            # solve has run after an island command).
            "commanded_island": self.is_islanded(spec.code),
            "islanded": bool(set(spec.member_buses) & islanded_buses),
        }

    def status(self, code: int) -> Dict[str, Any]:
        spec = self.zones.get(code)
        if spec is None:
            raise KeyError(code)
        return self._zone_status(spec)

    def list_status(self) -> List[Dict[str, Any]]:
        """Live state of every zone, ordered by code."""
        return [self._zone_status(spec) for _, spec in sorted(self.zones.items())]
