import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
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
    reputation_score: float = 1.0 # 0.0 to 1.0
    history: List[Dict[str, Any]] = field(default_factory=list)
    priority: int = 2 # Phase 19: 1=Critical, 2=Normal, 3=Sheddable
    is_shed: bool = False # Phase 19

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

    def calculate_health_score(self) -> float:
        """
        Calculate health score (0-100) based on resource availability and SOC diversity.
        A healthy cluster has many controllable resources and balanced SOC.
        """
        if not self.resources:
            return 0.0
            
        controllables = [r for r in self.resources.values() if r.is_controllable]
        if not controllables:
            return 10.0 # Very low if no control
            
        # 1. Controllability Ratio (40%)
        avail_ratio = len(controllables) / len(self.resources)
        
        # 2. SOC Balance (30%) - Prefer SOCs not at extreme limits
        socs = [r.current_soc / r.capacity_kwh for r in controllables if r.capacity_kwh > 0]
        if not socs:
            soc_score = 0
        else:
            # Score higher if average SOC is in the middle (sweet spot 20-80%)
            avg_soc = sum(socs) / len(socs)
            soc_score = 1.0 - 2.0 * abs(avg_soc - 0.5) # 1.0 at 50%, 0.4 at 20%/80%
            
        # 3. Capacity Diversity (30%) - Higher score if many small assets vs one big one (resilience)
        total_cap = sum(r.capacity_kwh for r in controllables)
        if total_cap == 0:
            div_score = 0
        else:
            # Herfindahl-Hirschman Index inspired
            hhi = sum((r.capacity_kwh / total_cap)**2 for r in controllables)
            div_score = 1.0 - hhi # 0 if one big asset, near 1 if many small ones
            
        score = (avail_ratio * 40) + (soc_score * 30) + (div_score * 30)
        
        # 4. Security Factor (Penalty for low reputation)
        avg_reputation = sum(r.reputation_score for r in controllables) / len(controllables)
        if avg_reputation < 0.8:
            penalty = (0.8 - avg_reputation) * 100
            score -= penalty
            
        return round(max(0, min(100, score)), 1)

    def generate_cluster_bid(self) -> Optional[Dict[str, Any]]:
        """
        Generate an aggregate market bid for the cluster.
        """
        up_flex = self.max_flexibility_up_kw
        down_flex = self.max_flexibility_down_kw
        
        if up_flex > 0.1:
            return {
                "cluster_id": self.cluster_id,
                "is_buy": False, # Sell surplus (discharging)
                "amount": up_flex,
                "type": "VPP_AGGREGATE"
            }
        elif down_flex > 0.1:
            return {
                "cluster_id": self.cluster_id,
                "is_buy": True, # Buy to charge
                "amount": down_flex,
                "type": "VPP_AGGREGATE"
            }
        return None

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
            is_controllable=config.get('is_controllable', True),
            priority=config.get('priority', 2)
        )
        
        self.clusters[feeder_id].resources[meter_id] = resource
        self.meter_map[meter_id] = feeder_id
        
    def update_meter_state(self, meter_id: str, battery_level: float):
        """
        Update dynamic state of a registered meter and detect anomalies.
        """
        cluster_id = self.meter_map.get(meter_id)
        if cluster_id and cluster_id in self.clusters:
            res = self.clusters[cluster_id].resources.get(meter_id)
            if res:
                # Security Check (Phase 16)
                self._detect_resource_anomalies(res, battery_level)
                res.current_soc = battery_level
                
                # Maintain short history
                res.history.append({"timestamp": datetime.now(), "soc": battery_level})
                if len(res.history) > 50:
                    res.history.pop(0)

    def _detect_resource_anomalies(self, resource: DERResource, new_soc: float):
        """
        Detect False Data Injection (FDI) on SOC reporting.
        Flags impossible SOC jumps based on battery physics.
        """
        if not resource.history:
            return

        last_soc = resource.history[-1]["soc"]
        # Max change per cycle (assume 15min tick, max power kw)
        # Change in kWh = (MaxPower * 0.25)
        # We allow a 20% margin for noise/sim variations
        max_delta_kwh = resource.max_charge_kw * 0.25 * 1.2
        actual_delta_kwh = abs(new_soc - last_soc)

        if actual_delta_kwh > max_delta_kwh and resource.capacity_kwh > 0:
            logger.warning(f"VPP SECURITY ALERT: Physical impossibility detected for meter {resource.meter_id}. Delta {actual_delta_kwh:.2f}kWh > Max {max_delta_kwh:.2f}kWh")
            self.update_reputation(resource.meter_id, -0.2) # Significant penalty

    def update_reputation(self, meter_id: str, delta: float):
        """Update reputation score of a meter."""
        cluster_id = self.meter_map.get(meter_id)
        if cluster_id:
            res = self.clusters[cluster_id].resources.get(meter_id)
            if res:
                res.reputation_score = max(0.0, min(1.0, res.reputation_score + delta))
                if res.reputation_score < 0.5:
                    logger.warning(f"VPP TRUST BREACH: Meter {meter_id} reputation dropped to {res.reputation_score:.2f}")

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
            "soc_percentage": (cluster.current_stored_kwh / cluster.total_capacity_kwh * 100) if cluster.total_capacity_kwh > 0 else 0,
            "health_score": cluster.calculate_health_score()
        }

    def get_all_cluster_statuses(self) -> List[Dict[str, Any]]:
        """
        Get aggregated status for all clusters.
        """
        return [self.get_cluster_status(cid) for cid in self.clusters.keys()]

    def calculate_afrr_response(self, cluster_id: str, frequency_hz: float) -> float:
        """
        Calculate the required POWER (kW) adjustment to restore frequency to 50Hz.
        Uses a standard frequency-watt droop characteristic.
        """
        cluster = self.clusters.get(cluster_id)
        if not cluster:
            return 0.0
            
        f_delta = frequency_hz - 50.0
        # Deadband +/- 0.02 Hz
        if abs(f_delta) < 0.02:
            return 0.0
            
        # Droop setting K = 5% (0.05). Means 1Hz delta (2%) causes ~40% power change.
        # Target (kW) = - (Delta_f / 50) * (Total_Flexibility / Droop_Gain)
        # We simplify: adjust based on available flexibility up/down
        
        if f_delta < 0:
            # Under-frequency: Need to INJECT (Discharge)
            max_up = cluster.max_flexibility_up_kw
            response = min(max_up, abs(f_delta) * (max_up / 0.5)) # Full response at 0.5Hz delta
            return response
        else:
            # Over-frequency: Need to ABSORB (Charge)
            max_down = cluster.max_flexibility_down_kw
            response = min(max_down, f_delta * (max_down / 0.5))
            return -response

    def orchestrate_microgrid_stability(self, cluster_id: str, freq: float, total_cons: float, total_gen: float) -> Dict[str, float]:
        """
        Phase 19: Advanced Microgrid Stability Orchestration.
        Calculates required load shedding and secondary battery response.
        """
        cluster = self.clusters.get(cluster_id)
        if not cluster: return {}

        dispatches = {}
        
        # 1. Frequency Control (Secondary Response)
        target_afrr = self.calculate_afrr_response(cluster_id, freq)
        if target_afrr != 0:
            dispatches.update(self.dispatch_cluster(cluster_id, target_afrr))

        # 2. Energy Balance & Load Shedding
        imbalance = total_gen - total_cons
        current_batt = sum(v for v in dispatches.values())
        net_imbalance = imbalance + current_batt
        
        if net_imbalance < -0.1: # Deficit
            shortfall = abs(net_imbalance)
            for priority in [3, 2]: # Shed priority 3 then 2
                sheddable = [r for r in cluster.resources.values() if r.priority == priority and not r.is_shed]
                for r in sheddable:
                    if shortfall <= 0: break
                    r.is_shed = True
                    logger.warning(f"VPP HEALING: Dynamic Shedding {r.meter_id} (P{priority}) to balance {shortfall:.2f}kW deficit")
                    shortfall -= 3.0 # Approx gain
        return dispatches

    def reset_shedding(self, cluster_id: str):
        """Phase 19: Restore all shedded loads (e.g., after reconnection)."""
        cluster = self.clusters.get(cluster_id)
        if cluster:
            for r in cluster.resources.values():
                if r.is_shed:
                    r.is_shed = False
                    logger.info(f"VPP HEALING: Restoring load for {r.meter_id}")

    def dispatch_cluster(self, cluster_id: str, target_kw: float, nodal_prices: Optional[Dict[str, float]] = None, carbon_intensity: Optional[float] = None) -> Dict[str, float]:
        """
        Dispatch a target power to the cluster resources, respecting constraints and optimizing for:
        1. State of Charge (SOC) - Keep batteries healthy
        2. Nodal Prices (Congestion) - Discharge at high price, Charge at low price
        3. Carbon Intensity (Environment) - Discharge at high carbon, Charge at low carbon
        4. Reputation (Trust) - Prefer reliable assets
        5. Priority (Sheddability) - Respect load priorities
        """
        if cluster_id not in self.clusters:
            return {}
            
        cluster = self.clusters[cluster_id]
        return self._optimize_dispatch(cluster, target_kw, nodal_prices, carbon_intensity)

    def _optimize_dispatch(self, cluster: VPPCluster, target_kw: float, nodal_prices: Optional[Dict[str, float]] = None, carbon_intensity: Optional[float] = None) -> Dict[str, float]:
        # Filter: Only use resources with healthy reputation (> 0.4)
        # Low trust resources are excluded entirely if they are too low, otherwise weighted down
        controllables = [r for r in cluster.resources.values() if r.is_controllable and r.reputation_score > 0.4]
        
        if not controllables:
            logger.warning(f"VPP DISPATCH FAILED: No trusted controllable resources in cluster {cluster.cluster_id}")
            return {}
            
        if abs(target_kw) < 0.001:
            return {r.meter_id: 0.0 for r in controllables}

        # Weighted Dispatch Logic
        weights = {}
        total_weight = 0.0
        
        is_discharging = target_kw > 0
        
        # Phase 22+: Multi-Factor Weighting
        carbon_factor = 1.0
        if carbon_intensity is not None:
             if is_discharging:
                 # Discharging relieves grid. Valuable when carbon is HIGH.
                 carbon_factor = 0.5 + (carbon_intensity / 500.0)
             else:
                 # Charging adds load. Good when carbon is LOW.
                 carbon_factor = max(0.5, 1.6 - (carbon_intensity / 500.0))
        
        for r in controllables:
            soc_ratio = r.current_soc / r.capacity_kwh if r.capacity_kwh > 0 else 0
            
            # 1. Price Factor (Phase 21)
            price_factor = 1.0
            if nodal_prices:
                price = nodal_prices.get(r.meter_id, 0.25)
                price_factor = price / 0.25 # Relative to base
            
            # 2. Reputation Weight (New Optimization)
            # Reliable assets get higher priority for dispatch commands
            rep_weight = r.reputation_score ** 2

            # 3. Priority Weight (New Optimization)
            # Critical loads (priority 1) are harder to shed/use for charging
            # Non-critical loads (priority 3) are used first
            p_weight = 1.0
            if not is_discharging: # Charging (Absorb surplus)
                if r.priority == 1: p_weight = 0.5
                if r.priority == 3: p_weight = 1.5

            if is_discharging:
                # Discharging: Prefer High SOC, High Price, High Carbon, High Reputation
                if soc_ratio > 0.15:
                    w = r.max_discharge_kw * (soc_ratio - 0.1) ** 2 * price_factor * carbon_factor * rep_weight * p_weight
                    weights[r.meter_id] = w
                    total_weight += w
            else:
                # Charging: Prefer Low SOC, Low Price, Low Carbon, High Reputation
                if soc_ratio < 0.95:
                    w = r.max_charge_kw * (0.98 - soc_ratio) ** 2 / max(0.1, price_factor) * carbon_factor * rep_weight * p_weight
                    weights[r.meter_id] = w
                    total_weight += w

        if total_weight == 0:
            # Fallback to simple proportional if all factors zeroed out but capacity remains
            for r in controllables:
                if (is_discharging and r.current_soc > 0) or (not is_discharging and r.current_soc < r.capacity_kwh):
                    weights[r.meter_id] = 1.0
                    total_weight += 1.0

        if total_weight == 0: return {}

        # Distribute target based on weights
        abs_target = abs(target_kw)
        actual_total = 0.0
        dispatches = {}
        
        for r in controllables:
            w = weights.get(r.meter_id, 0.0)
            if w > 0:
                share = (w / total_weight) * abs_target
                limit = r.max_discharge_kw if is_discharging else r.max_charge_kw
                # Also limit by SOC ceiling/floor to avoid over-discharge in a single tick
                if is_discharging:
                    soc_kwh = r.current_soc
                    limit = min(limit, soc_kwh * 4.0) # Assume 15min tick (factor 4)
                else:
                    headroom = r.capacity_kwh - r.current_soc
                    limit = min(limit, headroom * 4.0)
                
                dispatch = min(share, limit)
                dispatches[r.meter_id] = dispatch if is_discharging else -dispatch
                actual_total += dispatch
            else:
                dispatches[r.meter_id] = 0.0

        # Redistribution layer for remainder
        remainder = abs_target - actual_total
        if remainder > 0.01:
            for r in controllables:
                if remainder <= 0: break
                limit = r.max_discharge_kw if is_discharging else r.max_charge_kw
                current = abs(dispatches.get(r.meter_id, 0.0))
                space = limit - current
                if space > 0:
                    add = min(space, remainder)
                    dispatches[r.meter_id] = (current + add) * (1 if is_discharging else -1)
                    remainder -= add

        return dispatches
