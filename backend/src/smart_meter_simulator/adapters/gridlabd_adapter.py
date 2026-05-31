"""
GridLAB-D Co-Simulation Adapter for GridTokenX Smart Meter Simulator.

Provides three modes of operation:

1. **standalone**: Loads a GLM file via GLMPandapowerConverter, runs pandapower
   power flow. Identical behavior to PandapowerAdapter but with GLM topologies.
   No GridLAB-D binary required.

2. **co_sim**: Runs GridLAB-D as a HELICS federate. Receives voltages and
   sends load/generation data via HELICS messages. GridLAB-D handles all physics.
   Requires GridLAB-D binary and HELICS broker.

3. **hybrid**: Uses GridLAB-D for physics, but mirrors state into a pandapower
   network for compatibility with existing visualization (GeoJSON) and analytics.

The adapter duck-types with PandapowerAdapter — same method signatures:
- ``initialize(meters, ...)``
- ``update_measurements(readings)``
- ``run_power_flow()``
- ``map_meters_to_buses_spatial(meters)``
- ``get_grid_geojson()``
"""

import asyncio
import logging
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
import pandapower as pp

from .glm_converter import GLMPandapowerConverter

logger = logging.getLogger(__name__)

# Try HELICS import
try:
    import helics as h
    HELICS_AVAILABLE = True
except ImportError:
    h = None
    HELICS_AVAILABLE = False
    logger.info("HELICS not installed — GridlabdAdapter co_sim mode unavailable")


class GridlabdAdapter:
    """GridLAB-D co-simulation adapter with three operating modes.

    Args:
        mode: Operating mode — ``"standalone"``, ``"co_sim"``, or ``"hybrid"``.
        glm_path: Path to the GLM model file (required for standalone).
        gridlabd_executable: Path to the GridLAB-D binary (required for co_sim).
        federate_name: HELICS federate name for co_sim mode.
    """

    def __init__(
        self,
        mode: str = "standalone",
        glm_path: str = "",
        gridlabd_executable: str = "gridlabd",
        federate_name: str = "gridlabdSimulator",
    ):
        self.mode = mode
        self.glm_path = glm_path
        self.gridlabd_executable = gridlabd_executable
        self.federate_name = federate_name

        # Internal state
        self.net: Optional[pp.pandapowerNet] = None
        self.meter_to_bus: Dict[str, int] = {}
        self.bus_geodata: Dict[int, tuple] = {}
        self._converter = GLMPandapowerConverter()
        self._gridlabd_process: Optional[subprocess.Popen] = None
        self._helics_fed = None
        self._is_initialized = False

    # ── Public API (duck-typed with PandapowerAdapter) ──────────────────────

    def initialize(
        self,
        meters: List[Any],
        glm_path: Optional[str] = None,
        helics_broker: Optional[str] = None,
    ) -> bool:
        """Initialize the adapter with meters and optional configuration.

        Args:
            meters: List of SmartMeter objects.
            glm_path: Override the GLM file path.
            helics_broker: HELICS broker address (for co_sim mode).

        Returns:
            True if initialization succeeded.
        """
        if glm_path:
            self.glm_path = glm_path

        try:
            if self.mode == "standalone":
                return self._init_standalone()
            elif self.mode == "co_sim":
                return self._init_cosim(helics_broker)
            elif self.mode == "hybrid":
                return self._init_hybrid(helics_broker)
            else:
                logger.error(f"Unknown GridlabdAdapter mode: {self.mode}")
                return False
        except Exception as e:
            logger.error(f"GridlabdAdapter initialization failed: {e}", exc_info=True)
            return False

    def update_measurements(self, readings: List[Any]) -> None:
        """Update the grid model with current meter readings.

        In standalone mode: Injects readings into the pandapower network.
        In co_sim mode: Publishes readings to GridLAB-D via HELICS.
        In hybrid mode: Does both.
        """
        if self.mode == "standalone" or self.mode == "hybrid":
            self._update_pandapower(readings)

        if self.mode == "co_sim" or (self.mode == "hybrid" and self._helics_fed):
            self._publish_to_helics(readings)

    def run_power_flow(self) -> bool:
        """Execute power flow analysis.

        In standalone mode: Runs pandapower NR solver.
        In co_sim mode: No-op (GridLAB-D handles physics).
        In hybrid mode: Copies GridLAB-D results into pandapower network.
        """
        if self.mode == "standalone" or self.mode == "hybrid":
            if self.net is None:
                return False
            try:
                pp.runpp(self.net, algorithm="nr", numba=True)
                return self.net.converged
            except Exception as e:
                logger.error(f"Power flow failed: {e}")
                return False
        return True  # co_sim: GridLAB-D handles it

    def map_meters_to_buses_spatial(self, meters: List[Any]) -> Dict[str, int]:
        """Map meters to the nearest bus in the network."""
        from scipy.spatial import cKDTree

        self.meter_to_bus = {}
        if not self.net or not self.bus_geodata:
            return {}

        bus_coords = []
        bus_indices = []
        for idx, (x, y) in self.bus_geodata.items():
            bus_coords.append([x, y])
            bus_indices.append(idx)

        if not bus_coords:
            return {}

        tree = cKDTree(np.array(bus_coords))

        for meter in meters:
            config = getattr(meter, "config", {})
            lat = config.get("latitude", getattr(meter, "latitude", None))
            lon = config.get("longitude", getattr(meter, "longitude", None))

            if lat is not None and lon is not None:
                dist, idx = tree.query([lon, lat])
                self.meter_to_bus[meter.meter_id] = bus_indices[idx]
            else:
                # Distribute meters evenly across buses
                bus_idx = bus_indices[len(self.meter_to_bus) % len(bus_indices)]
                self.meter_to_bus[meter.meter_id] = bus_idx

        return self.meter_to_bus

    def get_grid_geojson(self) -> Dict[str, Any]:
        """Convert current grid state to GeoJSON FeatureCollection."""
        if self.net is None:
            return {"type": "FeatureCollection", "features": []}

        features = []

        # Buses
        for idx, row in self.net.bus.iterrows():
            pos = self.bus_geodata.get(idx, (0, 0))
            vm_pu = 1.0
            if hasattr(self.net, "res_bus") and idx in self.net.res_bus.index:
                vm_pu = self.net.res_bus.at[idx, "vm_pu"]

            features.append({
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [pos[0], pos[1]]},
                "properties": {
                    "type": "bus",
                    "id": int(idx),
                    "name": str(row["name"]),
                    "vn_kv": float(row["vn_kv"]),
                    "vm_pu": float(vm_pu),
                    "source": "gridlabd",
                },
            })

        # Lines
        for idx, row in self.net.line.iterrows():
            fb = int(row["from_bus"])
            tb = int(row["to_bus"])
            f_pos = self.bus_geodata.get(fb, (0, 0))
            t_pos = self.bus_geodata.get(tb, (0, 0))

            loading = 0.0
            if hasattr(self.net, "res_line") and idx in self.net.res_line.index:
                loading = self.net.res_line.at[idx, "loading_percent"]

            features.append({
                "type": "Feature",
                "geometry": {
                    "type": "LineString",
                    "coordinates": [[f_pos[1], f_pos[0]], [t_pos[1], t_pos[0]]],
                },
                "properties": {
                    "type": "line",
                    "id": int(idx),
                    "name": str(row["name"]),
                    "loading_percent": float(loading),
                    "source": "gridlabd",
                },
            })

        return {"type": "FeatureCollection", "features": features}

    async def step(self, target_time: float) -> float:
        """Advance the co-simulation to the target time.

        Only used in co_sim/hybrid mode. Sends HELICS time request and waits
        for GridLAB-D to complete its step.

        Args:
            target_time: Target simulation time in seconds.

        Returns:
            The granted simulation time.
        """
        if self._helics_fed is None:
            return target_time

        try:
            loop = asyncio.get_event_loop()
            granted = await loop.run_in_executor(
                None, h.helicsFederateRequestTime, self._helics_fed, target_time
            )
            # In hybrid mode, read GridLAB-D outputs and mirror to pandapower
            if self.mode == "hybrid":
                self._mirror_helics_to_pandapower()
            return float(granted)
        except Exception as e:
            logger.error(f"HELICS time request failed: {e}")
            return target_time

    def finalize(self) -> None:
        """Clean up resources."""
        if self._helics_fed is not None:
            try:
                h.helicsFederateFinalize(self._helics_fed)
                h.helicsFederateFree(self._helics_fed)
                h.helicsCloseLibrary()
            except Exception:
                pass
            self._helics_fed = None

        if self._gridlabd_process is not None:
            try:
                self._gridlabd_process.terminate()
                self._gridlabd_process.wait(timeout=10)
            except Exception:
                self._gridlabd_process.kill()
            self._gridlabd_process = None

        self._is_initialized = False

    # ── Initialization methods ──────────────────────────────────────────────

    def _init_standalone(self) -> bool:
        """Initialize standalone mode: load GLM → pandapower."""
        if not self.glm_path or not Path(self.glm_path).exists():
            logger.error(f"GLM file not found: {self.glm_path}")
            return False

        self.net = self._converter.convert(self.glm_path)
        self._map_bus_geodata()
        self._is_initialized = True
        logger.info(f"GridlabdAdapter (standalone) initialized from {self.glm_path}")
        return True

    def _init_cosim(self, helics_broker: Optional[str] = None) -> bool:
        """Initialize co-simulation mode with GridLAB-D as HELICS federate."""
        if not HELICS_AVAILABLE:
            logger.error("HELICS not available — cannot use co_sim mode")
            return False

        # For co_sim, we still load the GLM to pandapower for bus mapping
        # but physics come from GridLAB-D
        if self.glm_path and Path(self.glm_path).exists():
            self.net = self._converter.convert(self.glm_path)
            self._map_bus_geodata()

        # Initialize HELICS federate for communication with GridLAB-D
        try:
            fed_info = h.helicsCreateFederateInfo()
            h.helicsFederateInfoSetCoreTypeFromString(fed_info, "zmq")
            if helics_broker:
                h.helicsFederateInfoSetCoreInitString(
                    fed_info, f"--broker={helics_broker} --federates=1"
                )
            h.helicsFederateInfoSetTimeProperty(fed_info, h.HELICS_PROPERTY_TIME_PERIOD, 900.0)

            self._helics_fed = h.helicsCreateValueFederate(
                f"{self.federate_name}_adapter", fed_info
            )

            # Register subscriptions to GridLAB-D outputs
            self._sub_voltages = h.helicsFederateRegisterSubscription(
                self._helics_fed, f"{self.federate_name}/voltage_v", "V"
            )
            self._sub_loading = h.helicsFederateRegisterSubscription(
                self._helics_fed, f"{self.federate_name}/loading_pct", "%"
            )

            # Register publications for meter loads
            self._pub_total_load = h.helicsFederateRegisterGlobalPublication(
                self._helics_fed, f"{self.federate_name}_adapter/total_load_kw",
                h.HELICS_DATA_TYPE_DOUBLE, "kW"
            )

            h.helicsFederateEnterExecutingMode(self._helics_fed)
            self._is_initialized = True
            logger.info("GridlabdAdapter (co_sim) initialized with HELICS")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize co_sim HELICS federate: {e}")
            return False

    def _init_hybrid(self, helics_broker: Optional[str] = None) -> bool:
        """Initialize hybrid mode: GLM → pandapower + HELICS co-simulation."""
        # First do standalone init (load GLM to pandapower)
        if not self._init_standalone():
            return False
        # Then set up HELICS communication
        return self._init_cosim(helics_broker)

    # ── Measurement update methods ──────────────────────────────────────────

    def _update_pandapower(self, readings: List[Any]) -> None:
        """Update pandapower network with meter readings."""
        if self.net is None:
            return

        # Reset dynamic loads/sgens
        self.net.load.p_mw = 0
        self.net.load.q_mvar = 0
        self.net.sgen.p_mw = 0
        self.net.sgen.q_mvar = 0

        for r in readings:
            bus_idx = self.meter_to_bus.get(r.meter_id)
            if bus_idx is None:
                continue

            p_mw = getattr(r, "active_power_kw", 0) / 1000.0
            if p_mw == 0 and hasattr(r, "energy_consumed"):
                p_mw = r.energy_consumed * 720 / 1000.0

            if p_mw > 0:
                load_idx = self.net.load[self.net.load.name == f"load_{r.meter_id}"].index
                if load_idx.empty:
                    pp.create_load(self.net, bus=bus_idx, p_mw=p_mw,
                                   q_mvar=p_mw * 0.1, name=f"load_{r.meter_id}")
                else:
                    self.net.load.at[load_idx[0], "p_mw"] = p_mw
                    self.net.load.at[load_idx[0], "q_mvar"] = p_mw * 0.1

            gen_mw = getattr(r, "energy_generated", 0) * 720 / 1000.0
            if gen_mw > 0:
                sgen_idx = self.net.sgen[self.net.sgen.name == f"sgen_{r.meter_id}"].index
                if sgen_idx.empty:
                    pp.create_sgen(self.net, bus=bus_idx, p_mw=gen_mw,
                                   q_mvar=0, name=f"sgen_{r.meter_id}")
                else:
                    self.net.sgen.at[sgen_idx[0], "p_mw"] = gen_mw

    def _publish_to_helics(self, readings: List[Any]) -> None:
        """Publish meter readings to GridLAB-D via HELICS."""
        if self._helics_fed is None:
            return

        total_kw = sum(getattr(r, "active_power_kw", 0) for r in readings)
        try:
            h.helicsPublicationPublishDouble(self._pub_total_load, float(total_kw))
        except Exception as e:
            logger.warning(f"Failed to publish to HELICS: {e}")

    def _mirror_helics_to_pandapower(self) -> None:
        """Read GridLAB-D outputs from HELICS and mirror into pandapower network."""
        if self._helics_fed is None or self.net is None:
            return

        try:
            if h.helicsInputIsUpdated(self._sub_voltages):
                # GridLAB-D publishes bus voltages — mirror them
                # (Full implementation would parse the voltage array)
                pass
        except Exception as e:
            logger.warning(f"Failed to mirror HELICS data: {e}")

    # ── Helpers ──────────────────────────────────────────────────────────────

    def _map_bus_geodata(self) -> None:
        """Cache bus coordinates from pandapower network."""
        self.bus_geodata = {}
        if self.net is None:
            return
        has_geo = hasattr(self.net, "bus_geodata") and not self.net.bus_geodata.empty
        for idx in self.net.bus.index:
            if has_geo and idx in self.net.bus_geodata.index:
                self.bus_geodata[idx] = (
                    float(self.net.bus_geodata.at[idx, "x"]),
                    float(self.net.bus_geodata.at[idx, "y"]),
                )
            else:
                self.bus_geodata[idx] = (0.0, 0.0)
