import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
import numpy as np

logger = logging.getLogger(__name__)

@dataclass
class DERResource:
    meter_id: str
    feeder_id: str
    max_charge_kw: float
    max_discharge_kw: float
    current_soc: float
    capacity_kwh: float
    is_controllable: bool = False

@dataclass
class VPPCluster:
    cluster_id: str
    resources: Dict[str, DERResource] = field(default_factory=dict)
    
    @property
    def total_capacity_kwh(self) -> float:
        return sum(r.capacity_kwh for r in self.resources.values())

    @property
    def current_stored_kwh(self) -> float:
        return sum(r.current_soc for r in self.resources.values())

    @property
    def max_flexibility_up_kw(self) -> float:
        """Max power we can inject (Discharge)"""
        return sum(r.max_discharge_kw for r in self.resources.values() if r.is_controllable)

    @property
    def max_flexibility_down_kw(self) -> float:
        """Max power we can absorb (Charge)"""
        return sum(r.max_charge_kw for r in self.resources.values() if r.is_controllable)

class VPPManager:
    """
    Virtual Power Plant Manager.
    Aggregates individual meters into controllable clusters (VPPs) based on grid topology.
    """
    
    def __init__(self):
        self.clusters: Dict[str, VPPCluster] = {}
        self.meter_map: Dict[str, str] = {} # meter_id -> cluster_id
        
    def register_meter(self, meter_id: str, config: Dict[str, Any], state: Dict[str, Any]):
        """
        Register a meter as a DER resource.
        """
        feeder_id = config.get('feeder_id', 'Default_VPP')
        
        if feeder_id not in self.clusters:
            self.clusters[feeder_id] = VPPCluster(cluster_id=feeder_id)
            
        has_battery = config.get('has_battery', False)
        capacity = config.get('battery_capacity', 0.0) if has_battery else 0.0
        max_power = config.get('max_power_kw', 10.0) if has_battery else 0.0
        
        resource = DERResource(
            meter_id=meter_id,
            feeder_id=feeder_id,
            max_charge_kw=max_power,
            max_discharge_kw=max_power,
            current_soc=state.get('battery_level', 0.0),
            capacity_kwh=capacity,
            is_controllable=has_battery
        )
        
        self.clusters[feeder_id].resources[meter_id] = resource
        self.meter_map[meter_id] = feeder_id
        
    def update_meter_state(self, meter_id: str, battery_level: float):
        """
        Update dynamic state of a registered meter.
        """
        cluster_id = self.meter_map.get(meter_id)
        if cluster_id and cluster_id in self.clusters:
            res = self.clusters[cluster_id].resources.get(meter_id)
            if res:
                res.current_soc = battery_level

    def get_cluster_status(self, cluster_id: str) -> Dict[str, Any]:
        """
        Get aggregated status of a VPP cluster.
        """
        cluster = self.clusters.get(cluster_id)
        if not cluster:
            return {}
            
        return {
            "cluster_id": cluster_id,
            "resource_count": len(cluster.resources),
            "controllable_count": sum(1 for r in cluster.resources.values() if r.is_controllable),
            "total_capacity_kwh": cluster.total_capacity_kwh,
            "current_stored_kwh": cluster.current_stored_kwh,
            "flex_up_kw": cluster.max_flexibility_up_kw,
            "flex_down_kw": cluster.max_flexibility_down_kw,
            "soc_percentage": (cluster.current_stored_kwh / cluster.total_capacity_kwh * 100) if cluster.total_capacity_kwh > 0 else 0
        }

    def dispatch_cluster(self, cluster_id: str, target_dispatch_kw: float) -> Dict[str, float]:
        """
        Calculate dispatch setpoints for individual assets to meet a cluster target.
        Target > 0: Discharge (Inject)
        Target < 0: Charge (Absorb)
        
        Returns:
            Dict[meter_id, dispatch_kw]
        """
        cluster = self.clusters.get(cluster_id)
        if not cluster:
            return {}
            
        controllables = [r for r in cluster.resources.values() if r.is_controllable]
        if not controllables:
            return {}
            
        # Naive Proportional Dispatch
        # In a real system, we'd solve an optimization problem minimizing cost/degradation
        
        total_available = 0.0
        dispatches = {}
        
        if target_dispatch_kw > 0:
            # Discharging
            total_available = cluster.max_flexibility_up_kw
            if total_available == 0: return {}
            
            ratio = min(1.0, target_dispatch_kw / total_available)
            for r in controllables:
                # Check if we have juice
                if r.current_soc > 0.1 * r.capacity_kwh: # Min 10% reserve for example
                   dispatches[r.meter_id] = r.max_discharge_kw * ratio
                else:
                   dispatches[r.meter_id] = 0.0
                   
        else:
            # Charging
            total_available = cluster.max_flexibility_down_kw
            if total_available == 0: return {}
            
            # target is negative here, total_available is positive
            ratio = min(1.0, abs(target_dispatch_kw) / total_available)
            for r in controllables:
                # Check if full
                if r.current_soc < 0.95 * r.capacity_kwh:
                    dispatches[r.meter_id] = -1 * r.max_charge_kw * ratio
                else:
                    dispatches[r.meter_id] = 0.0
                    
        return dispatches
