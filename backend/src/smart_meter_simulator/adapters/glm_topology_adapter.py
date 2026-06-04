import logging
import os
from typing import Any, Dict, List, Optional

import networkx as nx

from smart_meter_simulator.core.topology import GridTopology, TopologyValidationResult

from .glm_topology_loader import load_glm_topology

logger = logging.getLogger(__name__)


class GlmTopologyAdapter:
    """Compatibility adapter for GLM topology loading.

    The simulator core now consumes ``GridTopology`` directly.  This adapter is
    kept for callers that still expect legacy adapter attributes such as
    ``net``, ``graph``, ``bus_index``, and ``load_at_bus``.
    """

    def __init__(self, glm_path: str | None = None) -> None:
        self.glm_path: Optional[str] = glm_path
        self.topology: Optional[GridTopology] = None
        self.validation: TopologyValidationResult = TopologyValidationResult()

        self.net: Dict[str, list] = {"buses": [], "lines": [], "loads": []}
        self.graph: nx.DiGraph = nx.DiGraph()
        self.bus_index: Dict[str, int] = {}
        self.load_at_bus: Dict[str, complex] = {}

        if glm_path and os.path.exists(glm_path):
            self._load_topology(glm_path)
        elif glm_path:
            self.validation.errors.append(f"GLM file not found: {glm_path}")
            logger.warning("GLM file not found: %s", glm_path)

    def _load_topology(self, glm_path: str) -> None:
        """Load GLM topology into shared and legacy adapter structures."""
        logger.info("Loading GLM topology from %s", glm_path)
        try:
            topology = load_glm_topology(glm_path)
        except Exception as exc:
            self.validation.errors.append(f"Failed to parse GLM file: {exc}")
            logger.error(
                "Failed to parse GLM file %s: %s", glm_path, exc, exc_info=True
            )
            return

        self.topology = topology
        self.validation = topology.validate()
        for warning in self.validation.warnings:
            logger.warning("GLM topology warning: %s", warning)
        for error in self.validation.errors:
            logger.error("GLM topology error: %s", error)

        self.net = topology.to_legacy_net()
        self.graph = topology.to_networkx()
        self.bus_index = topology.bus_index
        self.load_at_bus = topology.load_at_bus()

        logger.info(
            "GLM topology loaded: %d buses, %d lines, %d loads",
            len(self.net["buses"]),
            len(self.net["lines"]),
            len(self.net["loads"]),
        )

    def get_bus_voltage(self, bus_name: str) -> float:
        """Return the nominal voltage (V) for a bus."""
        if bus_name not in self.bus_index:
            raise KeyError(f"Bus '{bus_name}' not found in parsed model")
        bus = self.net["buses"][self.bus_index[bus_name]]
        return float(bus.get("nominal_voltage", 0.0))

    def get_bus_load(self, bus_name: str) -> complex:
        """Return the static complex load (P + jQ) at a bus."""
        return self.load_at_bus.get(bus_name, 0j)

    def get_line_length(self, from_bus: str, to_bus: str) -> float:
        """Return the line length between two directly-connected buses."""
        if not self.graph.has_edge(from_bus, to_bus):
            raise KeyError(f"No line from '{from_bus}' to '{to_bus}'")
        return float(self.graph[from_bus][to_bus]["weight"])

    def get_neighbors(self, bus_name: str) -> List[str]:
        """Return adjacent bus names (successors + predecessors)."""
        succs = (
            set(self.graph.successors(bus_name))
            if self.graph.has_node(bus_name)
            else set()
        )
        preds = (
            set(self.graph.predecessors(bus_name))
            if self.graph.has_node(bus_name)
            else set()
        )
        return sorted(succs | preds)

    def get_substation_bus(self) -> str:
        """Return the inferred slack/substation bus."""
        if self.topology:
            return self.topology.get_substation_bus()
        if self.net["buses"]:
            return self.net["buses"][0].get("name", "")
        return ""

    def get_bus_count(self) -> int:
        return len(self.net["buses"])

    def get_line_count(self) -> int:
        return len(self.net["lines"])

    def get_load_count(self) -> int:
        return len(self.net["loads"])

    def get_topology_summary(self) -> Dict[str, Any]:
        """Return a source-level topology summary."""
        if not self.topology:
            return {
                "source": "glm",
                "source_path": self.glm_path,
                "num_buses": 0,
                "num_lines": 0,
                "num_static_loads": 0,
                "substation": "",
                "validation": self.validation.to_dict(),
            }
        return self.topology.summary(include_validation=True)

    def build_legacy_net(self) -> Dict[str, list]:
        """Return the legacy net shape for callers that expect an adapter."""
        return self.net

    def map_meters_to_buses_direct(self, meters: List[Any]) -> Dict[str, Any]:
        """Map meter objects to bus names using ``bus_idx`` from meter config."""
        mapping: Dict[str, Any] = {}
        buses = self.net["buses"]
        if not buses:
            return mapping

        for meter in meters:
            raw_idx = getattr(meter, "config", {}).get("bus_idx", 0)
            try:
                idx = int(raw_idx)
            except (TypeError, ValueError):
                idx = 0
            bus = buses[idx] if 0 <= idx < len(buses) else buses[0]
            mapping[meter.meter_id] = bus.get("name", "0")
        return mapping

    def update_measurements(self, readings: List[Any]) -> None:
        """Placeholder for future GLM mutation or external solver publication."""
        return None

    def run_power_flow(self) -> None:
        """No-op; core GLM mode uses GridManager's approximate topology solver."""
        if not self.glm_path or not os.path.exists(self.glm_path):
            logger.debug("No GLM path configured; skipping adapter power flow")
            return
        logger.debug("Adapter power flow disabled; using approximate core solver")
