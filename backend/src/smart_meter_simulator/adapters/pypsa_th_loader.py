"""
PyPSA-TH Data Loader Module

Integration module for the PyPSA-TH (PyPSA-Earth Thailand) power system model.
Loads, converts, and integrates PyPSA-TH network data into the pandapower-based
simulator.

PyPSA-TH Repository: https://github.com/FiruzAhamed/PyPSA-TH
Based on: PyPSA-Earth v0.3.0

Key Features:
- Loads PyPSA network files (NetCDF .nc format)
- Converts PyPSA components to pandapower network
- Integrates with EGAT transmission builder for hybrid modeling
- Supports snapshots for time-series power flow analysis

References:
- PyPSA-Earth Documentation: https://pypsa-earth.readthedocs.io/
- Thailand config: voltages = [69, 115, 132, 230, 300, 500] kV
- Cost data: 2019, 2030, 2037, 2045, 2050 scenarios
"""

from typing import List, Dict, Any, Optional, Tuple, Union
from pathlib import Path
from dataclasses import dataclass
import logging

import pandas as pd
import numpy as np

try:
    import pandapower as pp
    PANDAPOWER_AVAILABLE = True
except ImportError:
    PANDAPOWER_AVAILABLE = False

try:
    import pypsa
    PYPSA_AVAILABLE = True
except ImportError:
    PYPSA_AVAILABLE = False

from .topology_builder import (
    TopologyBuilder,
    BusConfig,
    LineConfig,
    TransformerConfig,
    VoltageLevel,
)
from .egat_transmission import EGATTransmissionBuilder

logger = logging.getLogger(__name__)


# Default path to cloned PyPSA-TH repository
DEFAULT_PYPSA_TH_PATH = Path(__file__).parent.parent.parent.parent / "data" / "pypsa-th"


@dataclass
class PyPSATHConfig:
    """Configuration for PyPSA-TH data loading."""
    pypsa_th_path: Path = DEFAULT_PYPSA_TH_PATH
    use_prebuilt_network: bool = True
    fallback_to_egat: bool = True
    include_generators: bool = True
    include_loads: bool = True
    include_storage: bool = False
    voltage_filter_kv: Optional[List[float]] = None
    region_filter: Optional[str] = None


class PyPSATHLoader:
    """
    Loads and converts PyPSA-TH network data to pandapower format.

    PyPSA Network Components:
    - Bus: Nodes in the power system (substations)
    - Line: AC transmission lines
    - Link: DC links and converters
    - Transformer: Voltage transformation
    - Generator: Power plants
    - Load: Demand profiles
    - StorageUnit: Energy storage

    Example:
        loader = PyPSATHLoader()
        net = loader.load_to_pandapower()

        # Or load PyPSA network directly
        n = loader.load_pypsa_network()
        print(n.buses)  # All buses in the Thailand network
    """

    # PyPSA-Earth voltage to pandapower conductor mapping
    # Uses pandapower's built-in standard types
    VOLTAGE_CONDUCTOR_MAP = {
        69.0: "94-AL1/15-ST1A 110.0",
        115.0: "243-AL1/39-ST1A 110.0",
        132.0: "243-AL1/39-ST1A 110.0",
        230.0: "490-AL1/64-ST1A 220.0",
        300.0: "490-AL1/64-ST1A 380.0",
        500.0: "679-AL1/86-ST1A 380.0",
    }

    # Generator carrier to pandapower generator type mapping
    GENERATOR_TYPE_MAP = {
        "solar": "Solar",
        "onwind": "Wind",
        "offwind-ac": "Wind Offshore",
        "offwind-dc": "Wind Offshore",
        "hydro": "Hydro",
        "OCGT": "Gas",
        "CCGT": "Gas",
        "coal": "Coal",
        "lignite": "Lignite",
        "oil": "Oil",
        "nuclear": "Nuclear",
        "biomass": "Biomass",
        "geothermal": "Geothermal",
    }

    def __init__(self, config: Optional[PyPSATHConfig] = None):
        """
        Initialize PyPSA-TH loader.

        Args:
            config: Loading configuration (uses defaults if None)
        """
        self.config = config or PyPSATHConfig()
        self.pypsa_network: Optional[pypsa.Network] = None
        self._validate_paths()

    def _validate_paths(self):
        """Validate that PyPSA-TH repository path exists."""
        if not self.config.pypsa_th_path.exists():
            logger.warning(
                f"PyPSA-TH path not found: {self.config.pypsa_th_path}. "
                f"Clone with: git clone https://github.com/FiruzAhamed/PyPSA-TH "
                f"{self.config.pypsa_th_path}"
            )

    def load_pypsa_network(
        self,
        network_path: Optional[Path] = None,
    ) -> Optional[pypsa.Network]:
        """
        Load PyPSA network from NetCDF file.

        Args:
            network_path: Path to .nc file. If None, searches common locations.

        Returns:
            PyPSA Network object or None if not found
        """
        if not PYPSA_AVAILABLE:
            logger.error("PyPSA not installed. Install with: pip install pypsa")
            return None

        # Search for pre-built network files
        candidates = []
        if network_path:
            candidates.append(network_path)
        else:
            base = self.config.pypsa_th_path
            # Common PyPSA-Earth output locations
            candidates.extend([
                base / "networks" / "base.nc",
                base / "networks" / "elec_s.nc",
                base / "networks" / "elec_c.nc",
                base / "networks" / "test.nc",
            ])

        for path in candidates:
            if path.exists():
                logger.info(f"Loading PyPSA network from: {path}")
                self.pypsa_network = pypsa.Network(path)
                logger.info(
                    f"Loaded: {len(self.pypsa_network.buses)} buses, "
                    f"{len(self.pypsa_network.lines)} lines, "
                    f"{len(self.pypsa_network.generators)} generators"
                )
                return self.pypsa_network

        logger.warning(
            f"No pre-built PyPSA network found. "
            f"Run the Snakemake pipeline in {self.config.pypsa_th_path} "
            f"or use fallback_to_egat=True."
        )
        return None

    def load_pypsa_from_scratch(self) -> Optional[pypsa.Network]:
        """
        Build PyPSA-TH network from scratch using config and Snakemake.

        This runs the full PyPSA-Earth workflow:
        1. Download OSM data
        2. Build network topology
        3. Add electricity components
        4. Solve network (optional)

        Note: This requires additional dependencies (Gurobi, ERA5 data, etc.)
        and may take significant time.

        Returns:
            PyPSA Network object or None if build failed
        """
        if not PYPSA_AVAILABLE:
            logger.error("PyPSA not installed.")
            return None

        pypsa_path = self.config.pypsa_th_path

        # Check if Snakefile exists
        snakefile = pypsa_path / "Snakefile"
        if not snakefile.exists():
            logger.error(f"Snakefile not found at {pypsa_path}")
            return None

        logger.info(
            "PyPSA-TH build from scratch requires Snakemake pipeline. "
            "Consider using load_pypsa_network() with pre-built data instead."
        )
        return None

    def get_network_summary(self) -> Dict[str, Any]:
        """
        Get summary of loaded PyPSA network.

        Returns:
            Dictionary with network statistics
        """
        if self.pypsa_network is None:
            return {"error": "No PyPSA network loaded"}

        n = self.pypsa_network

        return {
            "buses": len(n.buses),
            "lines": len(n.lines),
            "links": len(n.links),
            "transformers": len(n.transformers),
            "generators": len(n.generators),
            "loads": len(n.loads),
            "storage_units": len(n.storage_units),
            "stores": len(n.stores),
            "snapshots": len(n.snapshots),
            "voltage_levels_kV": sorted(n.buses.v_nom.unique().tolist()),
            "carriers": sorted(n.generators.carrier.unique().tolist()),
            "total_generation_capacity_MW": n.generators.p_nom.sum(),
            "total_line_length_km": n.lines.length.sum() if "length" in n.lines.columns else None,
        }

    def convert_to_pandapower(
        self,
        network: Optional[pypsa.Network] = None,
    ) -> Optional[pp.pandapowerNet]:
        """
        Convert PyPSA network to pandapower format.

        Conversion mapping:
        - PyPSA Bus -> pandapower Bus
        - PyPSA Line -> pandapower Line
        - PyPSA Transformer -> pandapower Transformer
        - PyPSA Generator -> pandapower Static Generator (sgen)
        - PyPSA Load -> pandapower Load

        Args:
            network: PyPSA network (uses loaded network if None)

        Returns:
            pandapower network or None if conversion failed
        """
        if not PANDAPOWER_AVAILABLE:
            logger.error("pandapower not installed.")
            return None

        n = network or self.pypsa_network
        if n is None:
            logger.error("No PyPSA network available.")
            return None

        # Create empty pandapower network
        pandanet = pp.create_empty_network(name="PyPSA-TH Thailand Network")
        bus_map_pypsa_to_pp = {}  # PyPSA bus index -> pandapower bus index

        # Convert buses
        for bus_idx, bus_row in n.buses.iterrows():
            v_nom = bus_row.get("v_nom", 230.0)

            # Apply voltage filter if specified
            if self.config.voltage_filter_kv:
                if v_nom not in self.config.voltage_filter_kv:
                    continue

            # Apply region filter if specified
            if self.config.region_filter:
                country = bus_row.get("country", "")
                if country != "TH":
                    continue

            # Determine voltage level
            if v_nom >= 110:
                vlevel = VoltageLevel.HV
            elif v_nom >= 1:
                vlevel = VoltageLevel.MV
            else:
                vlevel = VoltageLevel.LV

            bus_name = bus_row.get("v_nom", str(bus_idx))
            if "carrier" in bus_row.index and bus_row["carrier"] is not None:
                bus_name = f"{bus_idx} ({bus_row['carrier']})"

            pp_bus_idx = pp.create_bus(
                pandanet,
                vn_kv=v_nom,
                name=str(bus_idx),
                geodata=(bus_row.get("x", 0), bus_row.get("y", 0)),
            )
            bus_map_pypsa_to_pp[bus_idx] = pp_bus_idx

        # Convert lines
        for line_idx, line_row in n.lines.iterrows():
            bus0 = line_row["bus0"]
            bus1 = line_row["bus1"]

            if bus0 not in bus_map_pypsa_to_pp or bus1 not in bus_map_pypsa_to_pp:
                continue

            # Get voltage level to select conductor type
            v_nom = n.buses.loc[bus0, "v_nom"]
            conductor = self.VOLTAGE_CONDUCTOR_MAP.get(
                v_nom, "Al/St 240/40 2-bundle 220.0"
            )

            length_km = line_row.get("length", 1.0)
            s_nom = line_row.get("s_nom", 1000)

            pp.create_line(
                pandanet,
                from_bus=bus_map_pypsa_to_pp[bus0],
                to_bus=bus_map_pypsa_to_pp[bus1],
                length_km=length_km,
                std_type=conductor,
                name=str(line_idx),
                parallel=line_row.get("num_parallel", 1),
            )

        # Convert transformers
        if hasattr(n, "transformers") and len(n.transformers) > 0:
            for trafo_idx, trafo_row in n.transformers.iterrows():
                bus0 = trafo_row["bus0"]
                bus1 = trafo_row["bus1"]

                if bus0 not in bus_map_pypsa_to_pp or bus1 not in bus_map_pypsa_to_pp:
                    continue

                sn_mva = trafo_row.get("sn_mva", 100)
                vn_hv = n.buses.loc[bus0, "v_nom"]
                vn_lv = n.buses.loc[bus1, "v_nom"]

                try:
                    pp.create_transformer(
                        pandanet,
                        hv_bus=bus_map_pypsa_to_pp[bus0],
                        lv_bus=bus_map_pypsa_to_pp[bus1],
                        sn_mva=sn_mva / 1000,  # Convert MVA
                        vn_hv_kv=vn_hv,
                        vn_lv_kv=vn_lv,
                        vk_percent=trafo_row.get("vk_percent", 10),
                        vkr_percent=trafo_row.get("vkr_percent", 0.5),
                        pfe_kw=trafo_row.get("pfe_kw", 0),
                        name=str(trafo_idx),
                    )
                except Exception as e:
                    logger.warning(f"Failed to create transformer {trafo_idx}: {e}")

        # Convert generators to static generators
        if self.config.include_generators:
            for gen_idx, gen_row in n.generators.iterrows():
                bus = gen_row["bus"]
                if bus not in bus_map_pypsa_to_pp:
                    continue

                p_mw = gen_row.get("p_nom", 0) / 1000  # Convert to MW
                vm_pu = gen_row.get("vm_pu_set", 1.0)

                try:
                    pp.create_sgen(
                        pandanet,
                        bus=bus_map_pypsa_to_pp[bus],
                        p_mw=p_mw,
                        q_mvar=0,
                        name=f"{gen_idx} ({gen_row.get('carrier', 'unknown')})",
                    )
                except Exception as e:
                    logger.warning(f"Failed to create generator {gen_idx}: {e}")

        # Convert loads
        if self.config.include_loads and hasattr(n, "loads") and len(n.loads) > 0:
            for load_idx, load_row in n.loads.iterrows():
                bus = load_row["bus"]
                if bus not in bus_map_pypsa_to_pp:
                    continue

                p_mw = load_row.get("p_set", 0)
                q_mvar = load_row.get("q_set", 0)

                try:
                    pp.create_load(
                        pandanet,
                        bus=bus_map_pypsa_to_pp[bus],
                        p_mw=p_mw,
                        q_mvar=q_mvar,
                        name=str(load_idx),
                    )
                except Exception as e:
                    logger.warning(f"Failed to create load {load_idx}: {e}")

        logger.info(
            f"Converted to pandapower: {len(pandanet.bus)} buses, "
            f"{len(pandanet.line)} lines, {len(pandanet.trafo)} transformers, "
            f"{len(pandanet.sgen)} generators, {len(pandanet.load)} loads"
        )

        return pandanet

    def load_to_pandapower(
        self,
        network_path: Optional[Path] = None,
    ) -> Optional[pp.pandapowerNet]:
        """
        Load PyPSA-TH data and convert to pandapower.

        Tries in order:
        1. Load pre-built PyPSA network and convert
        2. Fall back to EGAT transmission builder (if configured)

        Args:
            network_path: Path to .nc file

        Returns:
            pandapower network or None
        """
        # Try loading PyPSA network
        self.load_pypsa_network(network_path)

        if self.pypsa_network is not None:
            return self.convert_to_pandapower()

        # Fallback to EGAT data
        if self.config.fallback_to_egat:
            logger.info("Falling back to EGAT transmission data")
            egat_builder = EGATTransmissionBuilder()
            return egat_builder.build_full_network()

        return None

    def get_generators_by_carrier(self, carrier: str) -> pd.DataFrame:
        """
        Get all generators of a specific carrier type.

        Args:
            carrier: Generator carrier (solar, onwind, hydro, OCGT, etc.)

        Returns:
            DataFrame with generator data
        """
        if self.pypsa_network is None:
            return pd.DataFrame()

        gens = self.pypsa_network.generators
        return gens[gens.carrier == carrier]

    def get_load_profiles(self) -> Optional[pd.DataFrame]:
        """
        Get load time series profiles from PyPSA network.

        Returns:
            DataFrame with load profiles indexed by snapshots
        """
        if self.pypsa_network is None:
            return None

        n = self.pypsa_network

        if not hasattr(n, "loads_t") or not hasattr(n.loads_t, "p"):
            return None

        return n.loads_t.p

    def get_generator_profiles(self) -> Optional[pd.DataFrame]:
        """
        Get generator capacity profiles from PyPSA network.

        Returns:
            DataFrame with generator profiles indexed by snapshots
        """
        if self.pypsa_network is None:
            return None

        n = self.pypsa_network

        if not hasattr(n, "generators_t") or not hasattr(n.generators_t, "p_max_pu"):
            return None

        return n.generators_t.p_max_pu


def load_pypsa_th(
    pypsa_th_path: Optional[Path] = None,
    fallback_to_egat: bool = True,
) -> Optional[pp.pandapowerNet]:
    """
    Convenience function: Load PyPSA-TH data to pandapower.

    Args:
        pypsa_th_path: Path to PyPSA-TH repository
        fallback_to_egat: Fall back to EGAT data if PyPSA not available

    Returns:
        pandapower network
    """
    config = PyPSATHConfig(
        pypsa_th_path=pypsa_th_path or DEFAULT_PYPSA_TH_PATH,
        fallback_to_egat=fallback_to_egat,
    )
    loader = PyPSATHLoader(config)
    return loader.load_to_pandapower()


def get_pypsa_th_summary(pypsa_th_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Convenience function: Get PyPSA-TH network summary.

    Args:
        pypsa_th_path: Path to PyPSA-TH repository

    Returns:
        Dictionary with network statistics
    """
    config = PyPSATHConfig(
        pypsa_th_path=pypsa_th_path or DEFAULT_PYPSA_TH_PATH,
        fallback_to_egat=False,
    )
    loader = PyPSATHLoader(config)
    loader.load_pypsa_network()
    return loader.get_network_summary()


def convert_pypsa_to_pandapower(
    pypsa_network: pypsa.Network,
) -> pp.pandapowerNet:
    """
    Convenience function: Convert PyPSA network to pandapower.

    Args:
        pypsa_network: PyPSA Network object

    Returns:
        pandapower network
    """
    loader = PyPSATHLoader()
    return loader.convert_to_pandapower(pypsa_network)
