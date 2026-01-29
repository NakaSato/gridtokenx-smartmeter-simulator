"""
pandapower integration bridge.

This module handles all pandapower-specific operations since pandapower
is a Python-only library that cannot be ported to Rust.

The Rust core handles all simulation calculations, while this bridge
provides power flow analysis using pandapower.
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
import logging
import math

logger = logging.getLogger(__name__)

# Try to import pandapower
_PANDAPOWER_AVAILABLE = False
try:
    import pandapower as pp
    import pandas as pd
    _PANDAPOWER_AVAILABLE = True
    logger.info("pandapower loaded for power flow analysis")
except ImportError as e:
    logger.warning(f"pandapower not available: {e}")


def is_pandapower_available() -> bool:
    """Check if pandapower is available."""
    return _PANDAPOWER_AVAILABLE


@dataclass
class PowerFlowResult:
    """Result from power flow analysis."""
    converged: bool = False
    iterations: int = 0
    
    # Bus results
    bus_voltages_pu: Dict[int, float] = field(default_factory=dict)
    bus_voltages_kv: Dict[int, float] = field(default_factory=dict)
    bus_angles_deg: Dict[int, float] = field(default_factory=dict)
    
    # Load results
    load_p_mw: Dict[int, float] = field(default_factory=dict)
    load_q_mvar: Dict[int, float] = field(default_factory=dict)
    
    # Generator results
    gen_p_mw: Dict[int, float] = field(default_factory=dict)
    gen_q_mvar: Dict[int, float] = field(default_factory=dict)
    
    # Line results
    line_loading_pct: Dict[int, float] = field(default_factory=dict)
    line_current_ka: Dict[int, float] = field(default_factory=dict)
    line_losses_mw: Dict[int, float] = field(default_factory=dict)
    
    # Transformer results
    trafo_loading_pct: Dict[int, float] = field(default_factory=dict)
    
    # Summary
    total_load_mw: float = 0.0
    total_gen_mw: float = 0.0
    total_losses_mw: float = 0.0
    min_voltage_pu: float = 1.0
    max_voltage_pu: float = 1.0
    max_line_loading_pct: float = 0.0
    max_trafo_loading_pct: float = 0.0
    
    # Violations
    voltage_violations: List[int] = field(default_factory=list)
    overloaded_lines: List[int] = field(default_factory=list)
    overloaded_trafos: List[int] = field(default_factory=list)


class PandapowerNetwork:
    """
    Wrapper around pandapower network for smart grid simulation.
    
    Provides methods to:
    - Create network from zone/transformer configuration
    - Update loads and generation from Rust simulation
    - Run power flow analysis
    - Extract results back to Rust core
    """
    
    def __init__(self, name: str = "SmartGrid"):
        self.name = name
        self.net = None
        self._meter_to_load: Dict[str, int] = {}  # meter_id -> load index
        self._meter_to_sgen: Dict[str, int] = {}  # meter_id -> sgen index
        self._zone_to_bus: Dict[int, int] = {}    # zone_id -> bus index
        self._trafo_indices: Dict[str, int] = {}  # trafo_name -> trafo index
        
        if _PANDAPOWER_AVAILABLE:
            self._create_empty_network()
    
    def _create_empty_network(self):
        """Create empty pandapower network."""
        self.net = pp.create_empty_network(name=self.name)
    
    def create_from_zones(
        self,
        zones: List[Dict[str, Any]],
        nominal_voltage_kv: float = 0.4,
        grid_voltage_kv: float = 22.0
    ):
        """
        Create network from zone configuration.
        
        Args:
            zones: List of zone configs with keys:
                - zone_id: int
                - transformer_name: str
                - capacity_kva: float
                - meters: List of meter dicts with meter_id, base_load_kw, has_solar, solar_capacity_kw
            nominal_voltage_kv: LV nominal voltage (default 0.4 kV = 400V)
            grid_voltage_kv: Grid connection voltage (default 22 kV)
        """
        if not _PANDAPOWER_AVAILABLE:
            logger.warning("pandapower not available, cannot create network")
            return
        
        self._create_empty_network()
        
        # Create external grid bus (slack)
        slack_bus = pp.create_bus(self.net, vn_kv=grid_voltage_kv, name="Grid_Connection")
        pp.create_ext_grid(self.net, bus=slack_bus, vm_pu=1.0, name="External_Grid")
        
        for zone in zones:
            zone_id = zone["zone_id"]
            trafo_name = zone.get("transformer_name", f"Trafo_{zone_id}")
            capacity_kva = zone.get("capacity_kva", 500.0)
            
            # Create MV bus (medium voltage side of transformer)
            mv_bus = pp.create_bus(self.net, vn_kv=grid_voltage_kv, name=f"MV_Bus_{zone_id}")
            
            # Create LV bus (low voltage side where meters connect)
            lv_bus = pp.create_bus(self.net, vn_kv=nominal_voltage_kv, name=f"LV_Bus_{zone_id}")
            self._zone_to_bus[zone_id] = lv_bus
            
            # Create line from grid to MV bus (simplified)
            pp.create_line_from_parameters(
                self.net,
                from_bus=slack_bus,
                to_bus=mv_bus,
                length_km=1.0,
                r_ohm_per_km=0.1,
                x_ohm_per_km=0.1,
                c_nf_per_km=0.0,
                max_i_ka=1.0,
                name=f"Line_Grid_Zone{zone_id}"
            )
            
            # Create transformer
            trafo_idx = pp.create_transformer_from_parameters(
                self.net,
                hv_bus=mv_bus,
                lv_bus=lv_bus,
                sn_mva=capacity_kva / 1000.0,
                vn_hv_kv=grid_voltage_kv,
                vn_lv_kv=nominal_voltage_kv,
                vkr_percent=1.0,
                vk_percent=5.0,
                pfe_kw=0.5,
                i0_percent=0.2,
                name=trafo_name
            )
            self._trafo_indices[trafo_name] = trafo_idx
            
            # Create loads and static generators for each meter
            for meter in zone.get("meters", []):
                meter_id = meter["meter_id"]
                base_load_kw = meter.get("base_load_kw", 1.0)
                
                # Create load for this meter
                load_idx = pp.create_load(
                    self.net,
                    bus=lv_bus,
                    p_mw=base_load_kw / 1000.0,
                    q_mvar=base_load_kw * 0.1 / 1000.0,  # Assume 0.1 power factor lagging
                    name=f"Load_{meter_id}"
                )
                self._meter_to_load[meter_id] = load_idx
                
                # Create static generator if meter has solar
                if meter.get("has_solar", False):
                    solar_capacity_kw = meter.get("solar_capacity_kw", 0.0)
                    if solar_capacity_kw > 0:
                        sgen_idx = pp.create_sgen(
                            self.net,
                            bus=lv_bus,
                            p_mw=0.0,  # Will be updated during simulation
                            q_mvar=0.0,
                            name=f"Solar_{meter_id}"
                        )
                        self._meter_to_sgen[meter_id] = sgen_idx
        
        logger.info(f"Created pandapower network with {len(zones)} zones, "
                   f"{len(self._meter_to_load)} loads, {len(self._meter_to_sgen)} solar generators")
    
    def update_load(self, meter_id: str, load_kw: float, reactive_kvar: Optional[float] = None):
        """Update load for a specific meter."""
        if not _PANDAPOWER_AVAILABLE or self.net is None:
            return
        
        load_idx = self._meter_to_load.get(meter_id)
        if load_idx is not None:
            self.net.load.at[load_idx, "p_mw"] = load_kw / 1000.0
            if reactive_kvar is not None:
                self.net.load.at[load_idx, "q_mvar"] = reactive_kvar / 1000.0
            else:
                self.net.load.at[load_idx, "q_mvar"] = load_kw * 0.1 / 1000.0
    
    def update_generation(self, meter_id: str, generation_kw: float):
        """Update solar generation for a specific meter."""
        if not _PANDAPOWER_AVAILABLE or self.net is None:
            return
        
        sgen_idx = self._meter_to_sgen.get(meter_id)
        if sgen_idx is not None:
            self.net.sgen.at[sgen_idx, "p_mw"] = generation_kw / 1000.0
    
    def batch_update(
        self,
        loads: Dict[str, float],
        generations: Dict[str, float],
        reactive_powers: Optional[Dict[str, float]] = None
    ):
        """
        Batch update all loads and generations.
        
        Args:
            loads: Dict of meter_id -> load_kw
            generations: Dict of meter_id -> generation_kw
            reactive_powers: Optional dict of meter_id -> reactive_kvar
        """
        for meter_id, load_kw in loads.items():
            reactive_kvar = reactive_powers.get(meter_id) if reactive_powers else None
            self.update_load(meter_id, load_kw, reactive_kvar)
        
        for meter_id, gen_kw in generations.items():
            self.update_generation(meter_id, gen_kw)
    
    def run_power_flow(self, algorithm: str = "nr") -> PowerFlowResult:
        """
        Run power flow analysis.
        
        Args:
            algorithm: Power flow algorithm ('nr' = Newton-Raphson, 'bfsw' = backward/forward sweep)
        
        Returns:
            PowerFlowResult with all analysis results
        """
        result = PowerFlowResult()
        
        if not _PANDAPOWER_AVAILABLE or self.net is None:
            logger.warning("pandapower not available or network not created")
            return result
        
        try:
            pp.runpp(self.net, algorithm=algorithm, numba=True)
            result.converged = self.net.converged
            result.iterations = self.net._ppc.get("iterations", 0) if hasattr(self.net, "_ppc") else 0
            
            if result.converged:
                # Extract bus results
                for idx in self.net.res_bus.index:
                    result.bus_voltages_pu[idx] = self.net.res_bus.at[idx, "vm_pu"]
                    result.bus_angles_deg[idx] = self.net.res_bus.at[idx, "va_degree"]
                
                # Extract load results
                for idx in self.net.res_load.index:
                    result.load_p_mw[idx] = self.net.res_load.at[idx, "p_mw"]
                    result.load_q_mvar[idx] = self.net.res_load.at[idx, "q_mvar"]
                
                # Extract generator results
                for idx in self.net.res_sgen.index:
                    result.gen_p_mw[idx] = self.net.res_sgen.at[idx, "p_mw"]
                    result.gen_q_mvar[idx] = self.net.res_sgen.at[idx, "q_mvar"]
                
                # Extract line results
                for idx in self.net.res_line.index:
                    result.line_loading_pct[idx] = self.net.res_line.at[idx, "loading_percent"]
                    result.line_current_ka[idx] = self.net.res_line.at[idx, "i_ka"]
                    result.line_losses_mw[idx] = self.net.res_line.at[idx, "pl_mw"]
                
                # Extract transformer results
                for idx in self.net.res_trafo.index:
                    result.trafo_loading_pct[idx] = self.net.res_trafo.at[idx, "loading_percent"]
                
                # Calculate summary
                result.total_load_mw = self.net.res_load["p_mw"].sum()
                result.total_gen_mw = self.net.res_ext_grid["p_mw"].sum() + self.net.res_sgen["p_mw"].sum()
                result.total_losses_mw = self.net.res_line["pl_mw"].sum()
                result.min_voltage_pu = self.net.res_bus["vm_pu"].min()
                result.max_voltage_pu = self.net.res_bus["vm_pu"].max()
                result.max_line_loading_pct = self.net.res_line["loading_percent"].max() if len(self.net.res_line) > 0 else 0.0
                result.max_trafo_loading_pct = self.net.res_trafo["loading_percent"].max() if len(self.net.res_trafo) > 0 else 0.0
                
                # Find violations
                result.voltage_violations = list(self.net.res_bus[
                    (self.net.res_bus["vm_pu"] < 0.95) | (self.net.res_bus["vm_pu"] > 1.05)
                ].index)
                
                if len(self.net.res_line) > 0:
                    result.overloaded_lines = list(self.net.res_line[
                        self.net.res_line["loading_percent"] > 80
                    ].index)
                
                if len(self.net.res_trafo) > 0:
                    result.overloaded_trafos = list(self.net.res_trafo[
                        self.net.res_trafo["loading_percent"] > 80
                    ].index)
                
        except Exception as e:
            logger.error(f"Power flow failed: {e}")
            result.converged = False
        
        return result
    
    def get_bus_voltage_pu(self, zone_id: int) -> float:
        """Get voltage at zone bus in per-unit."""
        if not _PANDAPOWER_AVAILABLE or self.net is None:
            return 1.0
        
        bus_idx = self._zone_to_bus.get(zone_id)
        if bus_idx is not None and hasattr(self.net, "res_bus"):
            try:
                return self.net.res_bus.at[bus_idx, "vm_pu"]
            except:
                pass
        return 1.0
    
    def get_trafo_loading_pct(self, trafo_name: str) -> float:
        """Get transformer loading percentage."""
        if not _PANDAPOWER_AVAILABLE or self.net is None:
            return 0.0
        
        trafo_idx = self._trafo_indices.get(trafo_name)
        if trafo_idx is not None and hasattr(self.net, "res_trafo"):
            try:
                return self.net.res_trafo.at[trafo_idx, "loading_percent"]
            except:
                pass
        return 0.0
    
    def get_meter_voltage_pu(self, meter_id: str) -> float:
        """Get voltage at meter's connection point."""
        # Find which zone/bus this meter is connected to
        load_idx = self._meter_to_load.get(meter_id)
        if load_idx is not None and self.net is not None:
            bus_idx = self.net.load.at[load_idx, "bus"]
            if hasattr(self.net, "res_bus"):
                try:
                    return self.net.res_bus.at[bus_idx, "vm_pu"]
                except:
                    pass
        return 1.0
    
    def export_results_to_dict(self) -> Dict[str, Any]:
        """Export all results as dictionary for JSON serialization."""
        result = self.run_power_flow()
        return {
            "converged": result.converged,
            "iterations": result.iterations,
            "total_load_mw": result.total_load_mw,
            "total_gen_mw": result.total_gen_mw,
            "total_losses_mw": result.total_losses_mw,
            "min_voltage_pu": result.min_voltage_pu,
            "max_voltage_pu": result.max_voltage_pu,
            "max_line_loading_pct": result.max_line_loading_pct,
            "max_trafo_loading_pct": result.max_trafo_loading_pct,
            "voltage_violations_count": len(result.voltage_violations),
            "overloaded_lines_count": len(result.overloaded_lines),
            "overloaded_trafos_count": len(result.overloaded_trafos),
        }


# Simplified power flow without pandapower
class SimplePowerFlow:
    """
    Simple power flow approximation for when pandapower is not available.
    Uses basic circuit equations for approximate results.
    """
    
    def __init__(self, nominal_voltage: float = 400.0):
        self.nominal_voltage = nominal_voltage
    
    def calculate_voltage_drop(
        self,
        load_kw: float,
        generation_kw: float,
        impedance_pu: float = 0.05
    ) -> float:
        """Calculate approximate voltage in per-unit."""
        net_load = load_kw - generation_kw
        voltage_drop_pu = net_load * impedance_pu / 100.0
        return max(0.9, min(1.1, 1.0 - voltage_drop_pu))
    
    def calculate_trafo_loading(
        self,
        total_load_kw: float,
        trafo_capacity_kva: float
    ) -> float:
        """Calculate transformer loading percentage."""
        if trafo_capacity_kva <= 0:
            return 0.0
        return min(150.0, total_load_kw / trafo_capacity_kva * 100.0)


__all__ = [
    "is_pandapower_available",
    "PowerFlowResult",
    "PandapowerNetwork",
    "SimplePowerFlow",
]
