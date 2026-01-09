"""
Grid State Models for Microgrid Optimization.

This module defines the data structures that represent the physical state
of the grid at any given moment. These are used by the simulation engine
for physics-based calculations and optimization algorithms.

The key focus is on:
1. Voltage stability analysis
2. Power quality monitoring (THD)
3. Load/generation balance
4. Congestion detection
"""

from dataclasses import dataclass, field
from typing import Dict, Optional, List
from datetime import datetime


@dataclass
class GridState:
    """
    Represents the current physical state of a grid node or zone.
    
    Used for:
    - Voltage regulation analysis
    - Power quality assessment
    - Microgrid optimization decisions
    """
    voltage_pu: float = 1.0       # Per-unit voltage at connection point (1.0 = nominal)
    frequency_hz: float = 50.0    # Grid frequency (Thailand standard: 50 Hz)
    thd_voltage: float = 0.0      # THD-V at connection point (%)
    thd_current: float = 0.0      # THD-I at connection point (%)
    is_on_peak: bool = False      # Time-of-Use on-peak flag
    congestion_factor: float = 0.0  # 0-1, higher = more congested transformer/line
    power_factor: float = 1.0     # Power factor at the node
    temperature_c: float = 25.0   # Ambient temperature (°C)


@dataclass
class ZoneState:
    """
    Aggregated state for a microgrid zone (transformer service area).
    
    Used for zone-level optimization and load balancing decisions.
    """
    zone_id: int
    avg_voltage_pu: float = 1.0
    min_voltage_pu: float = 1.0
    max_voltage_pu: float = 1.0
    total_load_kw: float = 0.0
    total_generation_kw: float = 0.0
    net_power_kw: float = 0.0     # Negative = exporting, Positive = importing
    meter_count: int = 0
    transformer_loading_pct: float = 0.0  # Transformer capacity utilization
    has_voltage_violation: bool = False
    has_overload: bool = False


@dataclass
class GridAnalysisResult:
    """
    Result of a complete grid analysis run.
    
    Contains all relevant metrics for microgrid optimization.
    """
    timestamp: datetime = field(default_factory=datetime.now)
    power_flow_converged: bool = True
    total_load_mw: float = 0.0
    total_generation_mw: float = 0.0
    total_loss_mw: float = 0.0
    loss_percentage: float = 0.0
    zone_states: Dict[int, ZoneState] = field(default_factory=dict)
    voltage_violations: List[str] = field(default_factory=list)  # List of bus names
    overloaded_elements: List[str] = field(default_factory=list)  # List of line/trafo names
    recommendations: List[str] = field(default_factory=list)  # Optimization suggestions


@dataclass 
class OptimizationTarget:
    """
    Defines optimization objectives for microgrid control.
    
    Used by optimization algorithms to determine control actions
    for batteries, flexible loads, and DER dispatch.
    """
    minimize_losses: bool = True
    minimize_voltage_deviation: bool = True
    maximize_self_consumption: bool = True
    peak_shaving_enabled: bool = False
    peak_threshold_kw: Optional[float] = None
    target_voltage_pu: float = 1.0
    voltage_tolerance_pu: float = 0.05  # ±5% tolerance band
