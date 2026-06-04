"""Topology loading entry points for the simulator core."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from .topology import GridTopology


def parse_topology_spec(topology_spec: str | Path) -> tuple[str, str]:
    """Parse a topology spec into ``(source, value)``.

    Supported source:
    - ``glm:<path>`` for simulator-native GLM topology files.

    A plain path ending in ``.glm`` is accepted as compatibility sugar.
    """
    spec = str(topology_spec).strip()
    if not spec:
        raise ValueError("Topology spec is empty.")

    if ":" not in spec:
        if spec.lower().endswith(".glm"):
            return "glm", spec
        raise ValueError(f"Unsupported topology spec: {spec}")

    source, value = spec.split(":", 1)
    source = source.strip().lower()
    value = value.strip()
    if not source or not value:
        raise ValueError(f"Invalid topology spec: {spec}")
    return source, value


def load_glm_core_topology(glm_path: str | Path) -> GridTopology:
    """Load the simulator's core topology model from a GLM file."""
    from smart_meter_simulator.adapters.glm_topology_loader import load_glm_topology

    return load_glm_topology(glm_path)


def load_topology_spec(topology_spec: str | Path) -> GridTopology:
    """Load a core topology model from a topology source spec."""
    source, value = parse_topology_spec(topology_spec)
    if source == "glm":
        return load_glm_core_topology(value)
    raise ValueError(f"Unsupported topology source: {source}")


def load_configured_topology(topology_spec: Optional[str] = None) -> GridTopology:
    """Load core topology from a topology spec or configured GRID_TOPOLOGY."""
    if topology_spec is None:
        from smart_meter_simulator.config import get_config

        topology_spec = get_config().grid_topology
    return load_topology_spec(topology_spec)
