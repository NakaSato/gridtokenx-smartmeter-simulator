"""
Shared grid topology model.

This is the neutral shape consumed by the simulator core.  Adapters may still
expose legacy structures, but topology source parsing should land here first.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import networkx as nx


@dataclass(frozen=True)
class GridBus:
    """A named electrical connection point."""

    name: str
    phases: str = ""
    nominal_voltage: float = 0.0
    source_type: str = "node"
    properties: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class GridLine:
    """A directed topology edge between two buses."""

    name: str
    from_bus: str
    to_bus: str
    length: float = 0.0
    length_unit: str = ""
    resistance_ohm_per_km: float = 0.0
    reactance_ohm_per_km: float = 0.0
    capacity_kw: float = 0.0
    phases: str = ""
    source_type: str = "overhead_line"
    properties: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class GridLoad:
    """A static load attached to a bus."""

    name: str
    parent: str
    constant_power: complex = 0j
    phases: str = ""
    nominal_voltage: float = 0.0
    source_type: str = "load"
    properties: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class GridPV:
    """A PV resource attached to a bus through an inverter."""

    name: str
    parent: str
    bus: str
    capacity_kw: float = 0.0
    inverter_name: str = ""
    phases: str = ""
    properties: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TopologyValidationResult:
    """Validation output for a topology source."""

    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return not self.errors

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_valid": self.is_valid,
            "errors": self.errors,
            "warnings": self.warnings,
        }


@dataclass
class GridTopology:
    """Core topology representation for grid simulation."""

    source: str = "unknown"
    source_path: Optional[str] = None
    buses: List[GridBus] = field(default_factory=list)
    lines: List[GridLine] = field(default_factory=list)
    loads: List[GridLoad] = field(default_factory=list)
    pvs: List[GridPV] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def bus_names(self) -> List[str]:
        return [bus.name for bus in self.buses if bus.name]

    @property
    def bus_index(self) -> Dict[str, int]:
        return {name: idx for idx, name in enumerate(self.bus_names)}

    def get_substation_bus(self) -> str:
        """Return the preferred slack/substation bus name."""
        names = self.bus_names
        for preferred in ("ref_lv_bus_1", "sourcebus", "swing_bus"):
            if preferred in names:
                return preferred
        for bus in self.buses:
            bustype = str(bus.properties.get("bustype", "")).upper()
            if bustype == "SWING":
                return bus.name
        return names[0] if names else ""

    def to_networkx(self) -> nx.DiGraph:
        """Build a NetworkX graph used by the approximate solver."""
        graph = nx.DiGraph()
        for bus in self.buses:
            graph.add_node(
                bus.name,
                nominal_voltage=bus.nominal_voltage,
                phases=bus.phases,
                source_type=bus.source_type,
            )
        for line in self.lines:
            if line.from_bus and line.to_bus:
                graph.add_edge(
                    line.from_bus,
                    line.to_bus,
                    weight=line.length,
                    name=line.name,
                    length_unit=line.length_unit,
                    resistance_ohm_per_km=line.resistance_ohm_per_km,
                    reactance_ohm_per_km=line.reactance_ohm_per_km,
                    capacity_kw=line.capacity_kw,
                    phases=line.phases,
                    source_type=line.source_type,
                    properties=line.properties,
                )
        return graph

    def to_legacy_net(self) -> Dict[str, list]:
        """Return the historical adapter dict shape."""
        return {
            "buses": [
                {
                    **bus.properties,
                    "name": bus.name,
                    "phases": bus.phases,
                    "nominal_voltage": bus.nominal_voltage,
                    "source_type": bus.source_type,
                }
                for bus in self.buses
            ],
            "lines": [
                {
                    **line.properties,
                    "name": line.name,
                    "from": line.from_bus,
                    "to": line.to_bus,
                    "length": line.length,
                    "length_unit": line.length_unit,
                    "resistance_ohm_per_km": line.resistance_ohm_per_km,
                    "reactance_ohm_per_km": line.reactance_ohm_per_km,
                    "capacity_kw": line.capacity_kw,
                    "phases": line.phases,
                    "source_type": line.source_type,
                }
                for line in self.lines
            ],
            "loads": [
                {
                    **load.properties,
                    "name": load.name,
                    "parent": load.parent,
                    "constant_power_A": load.constant_power,
                    "phases": load.phases,
                    "nominal_voltage": load.nominal_voltage,
                    "source_type": load.source_type,
                }
                for load in self.loads
            ],
            "pvs": [
                {
                    **pv.properties,
                    "name": pv.name,
                    "parent": pv.parent,
                    "bus": pv.bus,
                    "capacity_kw": pv.capacity_kw,
                    "inverter_name": pv.inverter_name,
                    "phases": pv.phases,
                }
                for pv in self.pvs
            ],
        }

    def load_at_bus(self) -> Dict[str, complex]:
        """Aggregate static GLM load by parent bus."""
        result: Dict[str, complex] = {}
        for load in self.loads:
            if load.parent:
                result[load.parent] = result.get(load.parent, 0j) + load.constant_power
        return result

    def validate(self) -> TopologyValidationResult:
        """Validate structural consistency without requiring a solver."""
        result = TopologyValidationResult()
        names = self.bus_names
        name_set = set(names)

        if not names:
            result.errors.append("Topology has no buses.")

        duplicates = sorted({name for name in names if names.count(name) > 1})
        for name in duplicates:
            result.errors.append(f"Duplicate bus name: {name}")

        line_names = [line.name for line in self.lines if line.name]
        duplicate_lines = sorted(
            {name for name in line_names if line_names.count(name) > 1}
        )
        for name in duplicate_lines:
            result.warnings.append(f"Duplicate line name: {name}")

        for line in self.lines:
            if not line.from_bus or not line.to_bus:
                result.errors.append(
                    f"Line {line.name or '<unnamed>'} has missing endpoint."
                )
                continue
            if line.from_bus not in name_set:
                result.errors.append(
                    f"Line {line.name or '<unnamed>'} references missing from bus: {line.from_bus}"
                )
            if line.to_bus not in name_set:
                result.errors.append(
                    f"Line {line.name or '<unnamed>'} references missing to bus: {line.to_bus}"
                )

        for load in self.loads:
            if not load.parent:
                result.errors.append(
                    f"Load {load.name or '<unnamed>'} has no parent bus."
                )
            elif load.parent not in name_set:
                result.errors.append(
                    f"Load {load.name or '<unnamed>'} references missing parent bus: {load.parent}"
                )

        for pv in self.pvs:
            if not pv.bus:
                result.errors.append(f"PV {pv.name or '<unnamed>'} has no bus.")
            elif pv.bus not in name_set:
                result.errors.append(
                    f"PV {pv.name or '<unnamed>'} references missing bus: {pv.bus}"
                )

        substation = self.get_substation_bus()
        if not substation:
            result.warnings.append("No substation/slack bus could be inferred.")

        graph = self.to_networkx()
        if graph.number_of_nodes() > 1 and not nx.is_weakly_connected(graph):
            result.warnings.append("Topology graph is disconnected.")

        return result

    def summary(self, include_validation: bool = False) -> Dict[str, Any]:
        """Return an API-friendly summary."""
        static_load_va = sum((load.constant_power for load in self.loads), 0j)
        data: Dict[str, Any] = {
            "source": self.source,
            "source_path": str(Path(self.source_path)) if self.source_path else None,
            "num_buses": len(self.buses),
            "num_lines": len(self.lines),
            "num_static_loads": len(self.loads),
            "num_pv": len(self.pvs),
            "pv_capacity_kw": sum(pv.capacity_kw for pv in self.pvs),
            "static_load_kw": static_load_va.real / 1000.0,
            "static_load_kvar": static_load_va.imag / 1000.0,
            "substation": self.get_substation_bus(),
        }
        if include_validation:
            data["validation"] = self.validate().to_dict()
        return data
