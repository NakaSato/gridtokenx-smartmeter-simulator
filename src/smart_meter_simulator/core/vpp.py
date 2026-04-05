"""
Virtual Power Plant (VPP) Manager

This module handles aggregation of Distributed Energy Resources (DERs)
and coordinates their dispatch for grid services like frequency response (aFRR)
and carbon-aware peak shaving.
"""

import logging
import math
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class DERResource:
    """
    Distributed Energy Resource representation.
    """
    meter_id: str
    feeder_id: str
    type: str = "battery"
    capacity_kw: float = 0.0
    capacity_kwh: float = 0.0
    current_soc_kwh: float = 0.0
    max_charge_kw: float = 0.0
    max_discharge_kw: float = 0.0
    is_controllable: bool = True
    enabled: bool = True
    reputation_score: float = 1.0
    priority: int = 2  # 1=Critical, 2=Normal, 3=Sheddable
    is_shed: bool = False  # Load shedding state
    current_cons_kw: float = 0.0
    current_gen_kw: float = 0.0
    history: List[Dict[str, Any]] = field(default_factory=list)
    
    @property
    def soc_percent(self) -> float:
        if self.capacity_kwh <= 0: return 0.0
        return (self.current_soc_kwh / self.capacity_kwh) * 100.0

    @property
    def max_flexibility_up_kw(self) -> float:
        """Max upward flexibility (discharge / injection)."""
        if not self.enabled or not self.is_controllable: return 0.0
        # Simple limit check: can't discharge more than remaining energy (15-min approx)
        energy_limited = self.current_soc_kwh / 0.25 
        return min(self.max_discharge_kw, energy_limited)
    
    @property
    def max_flexibility_down_kw(self) -> float:
        """Max downward flexibility (charge / absorption)."""
        if not self.enabled or not self.is_controllable: return 0.0
        # Space left in battery
        space_kwh = self.capacity_kwh - self.current_soc_kwh
        energy_limited = space_kwh / 0.25
        return min(self.max_charge_kw, energy_limited)

@dataclass
class VPPCluster:
    """
    Aggregates multiple DER resources for coordinated dispatch.
    """
    cluster_id: str
    resources: Dict[str, DERResource] = field(default_factory=dict)
    target_kw: float = 0.0
    current_kw: float = 0.0
    
    @property
    def total_capacity_kwh(self) -> float:
        return sum(r.capacity_kwh for r in self.resources.values())
    
    @property
    def current_stored_kwh(self) -> float:
        return sum(r.current_soc_kwh for r in self.resources.values())
    
    @property
    def max_flexibility_up_kw(self) -> float:
        return sum(r.max_flexibility_up_kw for r in self.resources.values())
    
    @property
    def max_flexibility_down_kw(self) -> float:
        return sum(r.max_flexibility_down_kw for r in self.resources.values())

    @property
    def total_cons_kw(self) -> float:
        return sum(r.current_cons_kw for r in self.resources.values() if not r.is_shed)

    @property
    def total_gen_kw(self) -> float:
        return sum(r.current_gen_kw for r in self.resources.values())
    
    def calculate_health_score(self) -> float:
        """Calculate cluster health score (0-100) based on SOC and reputation."""
        if not self.resources: return 0.0
        avg_rep = sum(r.reputation_score for r in self.resources.values()) / len(self.resources)
        avg_soc = sum(r.soc_percent for r in self.resources.values()) / len(self.resources)
        # Health is high if resources are reliable and have balanced SOC
        score = (avg_rep * 0.7 + (avg_soc / 100.0) * 0.3) * 100.0
        return min(100.0, max(0.0, score))

class VPPManager:
    """
    Orchestrates VPP clusters and optimizes resource dispatch.
    """
    
    def __init__(self):
        self.clusters: Dict[str, VPPCluster] = {}
        self.meter_map: Dict[str, str] = {} # meter_id -> cluster_id
        self.cumulative_carbon_saved_g = 0.0
    
    def register_meter(self, meter_id: str, config: Dict[str, Any], state: Dict[str, Any]):
        """Register a meter with VPP based on its capabilities."""
        feeder_id = config.get("feeder_id", "Default_VPP")
        if not config.get("has_battery"): return
        
        resource = DERResource(
            meter_id=meter_id,
            feeder_id=feeder_id,
            capacity_kw=config.get("max_power_kw", 5.0),
            capacity_kwh=config.get("battery_capacity", 10.0),
            current_soc_kwh=state.get("battery_level", 0.0),
            max_charge_kw=config.get("max_power_kw", 5.0),
            max_discharge_kw=config.get("max_power_kw", 5.0),
            priority=config.get("priority", 2)
        )
        
        if feeder_id not in self.clusters:
            self.clusters[feeder_id] = VPPCluster(cluster_id=feeder_id)
            
        self.clusters[feeder_id].resources[meter_id] = resource
        self.meter_map[meter_id] = feeder_id
        logger.info(f"Registered meter {meter_id} to VPP cluster {feeder_id}")
    
    def update_meter_state(self, meter_id: str, battery_level: float, p_cons: float = 0.0, p_gen: float = 0.0):
        """Update DER resource state and perform security monitoring."""
        if meter_id not in self.meter_map: return
        cid = self.meter_map[meter_id]
        resource = self.clusters[cid].resources[meter_id]
        
        # Security: Detect impossible SOC jumps (indicative of sensor tampering/attack)
        prev_soc = resource.current_soc_kwh
        # Max change in 15 mins (approx interval)
        max_delta = resource.capacity_kw * 0.25 * 1.5 # 50% buffer
        delta = abs(battery_level - prev_soc)
        
        if delta > max_delta and len(resource.history) > 0:
            logger.warning(f"VPP SECURITY ALERT: Impossible SOC jump for meter {meter_id} ({prev_soc:.2f} -> {battery_level:.2f})")
            resource.reputation_score *= 0.8 # Penalty
            
        resource.current_soc_kwh = battery_level
        resource.current_cons_kw = p_cons
        resource.current_gen_kw = p_gen
        
        resource.history.append({"ts": datetime.now(), "soc": battery_level})
        if len(resource.history) > 100: resource.history.pop(0)
    
    def calculate_afrr_response(self, cluster_id: str, freq: float) -> float:
        """
        Calculate required power adjustment based on frequency deviation.
        Standard FCR/aFRR logic with 20mHz deadband.
        """
        deadband = 0.02 # Hz
        deviation = freq - 50.0
        
        if abs(deviation) < deadband: return 0.0
        
        # Standard droop (e.g., 5%)
        # K = 1 / 0.05 = 20 pu/pu
        # For simplicity, target = -deviation * Cluster_Capacity * Gain
        cluster = self.clusters.get(cluster_id)
        if not cluster: return 0.0
        
        gain = 10.0 # MW / Hz (scaled for this simulation)
        target = -deviation * gain
        
        # Clip to cluster limits
        if target > 0:
            return min(target, cluster.max_flexibility_up_kw)
        else:
            return max(target, -cluster.max_flexibility_down_kw)

    def dispatch_cluster(
        self,
        cluster_id: str,
        target_kw: float,
        nodal_prices: Optional[Dict[str, float]] = None,
        carbon_intensity: Optional[float] = None
    ) -> Dict[str, float]:
        """
        Optimized multi-objective dispatch.
        Weights: SOC balance (30%), Nodal Price (40%), Carbon Sensitivity (30%).
        """
        cluster = self.clusters.get(cluster_id)
        if not cluster or target_kw == 0: return {}
        
        resources = list(cluster.resources.values())
        if not resources: return {}
        
        # Calculate weights for each resource
        weights = {}
        for r in resources:
            # 1. SOC Weight
            # If discharging (target > 0), prefer high SOC
            # If charging (target < 0), prefer low SOC
            soc_w = r.soc_percent / 100.0 if target_kw > 0 else (100.0 - r.soc_percent) / 100.0
            
            # 2. Price Weight
            price = nodal_prices.get(r.meter_id, 0.25) if nodal_prices else 0.25
            # If discharging, prefer high price nodes
            # If charging, prefer low price nodes
            price_w = (price / 0.5) if target_kw > 0 else (1.0 - (price / 0.5))
            
            # 3. Carbon Weight
            # intensity is usually 0-500 g/kWh
            c_intensity = carbon_intensity if carbon_intensity is not None else 250.0
            # If discharging, prefer high intensity periods (displace dirty grid power)
            # If charging, prefer low intensity periods (soak up clean power)
            carbon_w = (c_intensity / 500.0) if target_kw > 0 else (1.0 - (c_intensity / 500.0))
            
            # Combined Weight
            weights[r.meter_id] = (soc_w * 0.3 + price_w * 0.4 + carbon_w * 0.3) * r.reputation_score
            
        # Normalize weights and allocate
        total_w = sum(weights.values())
        if total_w <= 0: return {r.meter_id: target_kw / len(resources) for r in resources}
        
        dispatches = {}
        for mid, w in weights.items():
            raw_dispatch = (w / total_w) * target_kw
            r = cluster.resources[mid]
            # Clip to physical limits
            if target_kw > 0:
                dispatches[mid] = min(raw_dispatch, r.max_flexibility_up_kw)
            else:
                dispatches[mid] = max(raw_dispatch, -r.max_flexibility_down_kw)
                
        # Calculate Carbon Savings (Estimate)
        # If target_kw > 0 (Discharge), we are displacing grid power
        if target_kw > 0 and carbon_intensity is not None:
            # interval_h = 15 mins / 60 = 0.25h (In actual engine, we use its interval)
            # For simplicity, we'll assume a 15-min interval for this calculation or pass it
            interval_h = 0.25 # Default 15 mins
            savings = target_kw * interval_h * carbon_intensity
            self.cumulative_carbon_saved_g += savings
            logger.info(f"VPP: Saved {savings:.2f}g CO2 by displacing {target_kw:.2f}kW grid power")

        return dispatches

    def get_cluster_status(self, cluster_id: str) -> Dict[str, Any]:
        cluster = self.clusters.get(cluster_id)
        if not cluster: return {"status": "Not Found"}
        
        return {
            "cluster_id": cluster_id,
            "num_resources": len(cluster.resources),
            "total_capacity_kwh": cluster.total_capacity_kwh,
            "current_soc_percent": (cluster.current_stored_kwh / cluster.total_capacity_kwh * 100) if cluster.total_capacity_kwh > 0 else 0,
            "flexibility_up_kw": cluster.max_flexibility_up_kw,
            "flexibility_down_kw": cluster.max_flexibility_down_kw,
            "total_cons_kw": cluster.total_cons_kw,
            "total_gen_kw": cluster.total_gen_kw,
            "carbon_saved_g": self.cumulative_carbon_saved_g, # Aggregate for now
            "health_score": cluster.calculate_health_score()
        }

    def get_all_cluster_statuses(self) -> Dict[str, Any]:
        """Return status for all registered VPP clusters."""
        return {cid: self.get_cluster_status(cid) for cid in self.clusters}

    def reset_shedding(self, cluster_id: str):
        """Restore all shedded resources in the cluster."""
        cluster = self.clusters.get(cluster_id)
        if not cluster: return
        
        for r in cluster.resources.values():
            if r.is_shed:
                r.is_shed = False
                logger.info(f"VPP: Restored shedded resource {r.meter_id}")

    def orchestrate_microgrid_stability(
        self, 
        cluster_id: str, 
        freq: float, 
        total_cons: float, 
        total_gen: float
    ):
        """
        Maintain stability in island mode.
        Implements emergency load shedding and battery support.
        """
        cluster = self.clusters.get(cluster_id)
        if not cluster: return
        
        # 1. Frequency-based Emergency Response
        # If freq < 49.0Hz, we must shed load
        if freq < 49.5:
            # Sort resources by priority (highest priority value = lowest importance)
            # We shed priority 3 first, then 2. Priority 1 is critical.
            resources = sorted(cluster.resources.values(), key=lambda x: x.priority, reverse=True)
            
            imbalance = total_cons - total_gen
            if imbalance <= 0: return # Already stable
            
            shed_total = 0.0
            for r in resources:
                if r.priority > 1 and not r.is_shed:
                    r.is_shed = True
                    shed_total += r.current_cons_kw
                    logger.warning(f"VPP EMERGENCY: Shedding load {r.meter_id} (Priority {r.priority}) to stabilize grid.")
                    if (total_cons - shed_total) <= total_gen:
                        break # We've shed enough
        
        # 2. Battery Support (Coordinated Dispatch)
        # In island mode, we want to maintain SOC balance while matching load
        target = total_cons - total_gen
        if abs(target) > 1.0: # Only dispatch if significant imbalance
            dispatches = self.dispatch_cluster(cluster_id, target)
            # These will be applied by the engine in the next tick
            # Or we can return them? engine.py expects orchestrate to just update state
            # but actually engine.py calls dispatch_cluster separately for aFRR.
            # In island mode, orchestrate_microgrid_stability is the primary loop.
            return dispatches
        
        return {}
