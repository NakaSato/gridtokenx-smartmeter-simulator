import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)

@dataclass
class GridHealthReport:
    timestamp: datetime
    total_loss_mw: float
    avg_voltage_pu: float
    max_voltage_pu: float
    min_voltage_pu: float
    num_violations: int
    violations: List[Dict[str, Any]] = field(default_factory=list)
    loss_percentage: float = 0.0
    health_score: float = 100.0
    is_under_attack: bool = False
    anomaly_score: float = 0.0
    attack_alerts: List[Dict[str, Any]] = field(default_factory=list)
    stealth_ratio: float = 0.0         # Phase 18: Bias that evaded detection
    detection_latency: int = 0         # Phase 18: Steps since attack start
    recovery_rate: float = 100.0       # Phase 19: % of non-shedded loads
    self_healing_active: bool = False  # Phase 19: True if load shedding is active
    avg_nodal_price: float = 0.25      # Phase 21: Average price across nodes
    carbon_intensity: float = 450.0    # Phase 21: gCO2/kWh
    nodal_prices: Dict[int, float] = field(default_factory=dict) # bus_idx -> price

class GridAnalytics:
    """
    Provides advanced grid analytics and health monitoring.
    Tracks voltage violations and technical losses over time.
    """
    
    def __init__(self, voltage_low: float = 0.95, voltage_high: float = 1.05):
        self.voltage_low = voltage_low
        self.voltage_high = voltage_high
        self.history: List[GridHealthReport] = []
        self.residual_ewma: Dict[str, float] = {} # meter_id -> EWMA of normalized residual
        self.ewma_alpha = 0.2 # Smoothing factor
        self.attack_start_step: Optional[int] = None # Phase 18: For latency tracking
        
    def analyze_step(self, net: any, estimation_results: any) -> GridHealthReport:
        """
        Analyze a single simulation step.
        
        Args:
            net: Pandapower network with results
            estimation_results: Results from StateEstimator
        """
        import pandapower as pp
        
        # 1. Voltage Violation Analysis
        res_bus = net.res_bus
        violations = []
        
        high_v = res_bus[res_bus.vm_pu > self.voltage_high]
        for idx, row in high_v.iterrows():
            violations.append({
                "bus_idx": int(idx),
                "bus_name": net.bus.at[idx, 'name'],
                "type": "overvoltage",
                "value": float(row.vm_pu),
                "limit": self.voltage_high
            })
            
        low_v = res_bus[res_bus.vm_pu < self.voltage_low]
        for idx, row in low_v.iterrows():
            violations.append({
                "bus_idx": int(idx),
                "bus_name": net.bus.at[idx, 'name'],
                "type": "undervoltage",
                "value": float(row.vm_pu),
                "limit": self.voltage_low
            })
            
        # 2. Loss Analysis
        total_loss_mw = pp.topology.excess_power(net) if hasattr(pp.topology, 'excess_power') else 0.0
        # Alternative: Sum of branch losses
        line_loss = net.res_line.pl_mw.sum() if hasattr(net, 'res_line') else 0.0
        trafo_loss = net.res_trafo.pl_mw.sum() if hasattr(net, 'res_trafo') else 0.0
        total_loss_mw = line_loss + trafo_loss
        
        # 3. Calculate Loss Percentage
        total_gen = net.res_sgen.p_mw.sum() + net.res_ext_grid.p_mw.sum()
        loss_pct = (total_loss_mw / total_gen * 100) if total_gen != 0 else 0.0
        
        # 4. Carbon Intensity Analysis (Phase 21)
        # Simplified model: 0g for solar/VPP, 500g for external grid (fossil-heavy)
        ext_grid_p = net.res_ext_grid.p_mw.sum() if hasattr(net, 'res_ext_grid') else 0.0
        total_p_cons = net.res_load.p_mw.sum() if hasattr(net, 'res_load') else 1.0
        carbon_intensity = (ext_grid_p / total_p_cons) * 500.0 if total_p_cons > 0 else 0.0
        
        # 5. Anomaly Detection (Cyber-security Analysis)
        attack_alerts = []
        anomaly_score = 0.0
        
        if estimation_results and not estimation_results.residuals.empty:
            # estimation_results.residuals has: measurement, norm_residual
            # (Note: calculate_normalized_residuals adds norm_residual)
            res_df = estimation_results.residuals
            if 'norm_residual' not in res_df.columns:
                res_df['norm_residual'] = res_df['residual'].abs() / res_df['std_dev']
            
            for _, row in res_df.iterrows():
                m_name = row['measurement']
                val = row['norm_residual']
                
                # Update EWMA
                prev = self.residual_ewma.get(m_name, 0.0)
                new_ewma = (1 - self.ewma_alpha) * prev + self.ewma_alpha * val
                self.residual_ewma[m_name] = new_ewma
                
                # Detect Anomaly:
                # 1. Instantaneous spike (rN > 4.0)
                # 2. Persistent bias (EWMA > 2.0) - catches stealthy attacks
                if val > 4.0 or new_ewma > 2.0:
                    alert_type = "persistent_bias" if new_ewma > 2.0 else "data_spike"
                    attack_alerts.append({
                        "meter_id": m_name,
                        "type": alert_type,
                        "severity": "high" if val > 5.0 else "medium",
                        "residual": float(val),
                        "ewma": float(new_ewma)
                    })
            
            # Global anomaly score: percentage of compromised sensors weighted by severity
            if len(self.residual_ewma) > 0:
                anomaly_score = min(100.0, (len(attack_alerts) / len(self.residual_ewma)) * 200.0)

        # Calculate health score after all relevant metrics are available
        health_score = self._calculate_health_score(len(violations), loss_pct, anomaly_score)

        # 5. Recovery Analytics (Phase 19)
        # We need to check the shedding status of resources
        # Since 'vpp' is not passed to analyze_step, we can infer it or pass it.
        # Alternatively, assume recovery_rate 100% and update it from engine if needed.
        # For consistency with the report structure:
        recovery_rate = 100.0 
        is_healing = False
        
        report = GridHealthReport(
            timestamp=datetime.now(),
            total_loss_mw=float(total_loss_mw),
            avg_voltage_pu=float(res_bus.vm_pu.mean()) if not res_bus.empty else 1.0,
            max_voltage_pu=float(res_bus.vm_pu.max()) if not res_bus.empty else 1.0,
            min_voltage_pu=float(res_bus.vm_pu.min()) if not res_bus.empty else 1.0,
            num_violations=len(violations),
            violations=violations,
            loss_percentage=float(loss_pct),
            health_score=health_score,
            is_under_attack=bool(anomaly_score > 0.1),
            anomaly_score=float(anomaly_score),
            attack_alerts=attack_alerts,
            stealth_ratio=self._calculate_stealth_ratio(len(attack_alerts)),
            detection_latency=self._update_detection_latency(bool(attack_alerts)),
            recovery_rate=recovery_rate,
            self_healing_active=is_healing,
            carbon_intensity=float(carbon_intensity),
            avg_nodal_price=float(net.avg_nodal_price if hasattr(net, 'avg_nodal_price') else 0.25),
            nodal_prices=dict(net.nodal_prices) if hasattr(net, 'nodal_prices') else {}
        )
        
        self.history.append(report)
        # Keep last 1000 steps
        if len(self.history) > 1000:
            self.history.pop(0)
            
        return report

    def _calculate_health_score(self, violations: int, loss_pct: float, anomaly_score: float = 0.0) -> float:
        """Calculate a health score from 0-100 based on grid state."""
        score = 100.0
        # Deduct for violations (penalty = 10 points each)
        score -= min(50.0, violations * 10.0)
        # Deduct for excessive losses (penalty = 5 points per % beyond 5%)
        if loss_pct > 5.0:
            score -= min(40.0, (loss_pct - 5.0) * 5.0)
        # Deduct for cyber anomalies
        score -= min(30.0, anomaly_score * 0.5)
        return max(0.0, score)

    def _calculate_stealth_ratio(self, detected_count: int) -> float:
        """Estimate of how much attack traffic is undetected."""
        if not self.residual_ewma: return 0.0
        # Placeholder: Ratio of suspected but not yet flagged as high-risk
        # In a real system, would use Ground Truth comparison
        return max(0.0, 1.0 - (detected_count / max(1, len(self.residual_ewma))))

    def _update_detection_latency(self, is_detected: bool) -> int:
        """Track how many steps pass between attack start and detection."""
        # This requires knowing when the attack started (mocked here or via internal state)
        if not is_detected:
            if self.attack_start_step is not None:
                self.attack_start_step += 1
                return 0
            return 0
        else:
            latency = self.attack_start_step if self.attack_start_step else 0
            self.attack_start_step = None # Reset
            return latency

    def get_summary(self) -> Dict[str, Any]:
        """Return a summary of grid health matching the WebSocket format."""
        if not self.history:
            return {}
            
        recent = self.history[-1]
        
        # Flattened structure matching engine.py broadcast and frontend GridHealth interface
        return {
            "timestamp": recent.timestamp.isoformat(),
            "total_loss_mw": float(recent.total_loss_mw),
            "avg_voltage_pu": float(recent.avg_voltage_pu),
            "max_voltage_pu": float(recent.max_voltage_pu),
            "min_voltage_pu": float(recent.min_voltage_pu),
            "num_violations": int(recent.num_violations),
            "loss_percentage": float(recent.loss_percentage),
            "health_score": float(recent.health_score),
            "is_under_attack": bool(recent.is_under_attack),
            "anomaly_score": float(recent.anomaly_score),
            "attack_alerts": recent.attack_alerts,
            "stealth_ratio": float(recent.stealth_ratio),
            "detection_latency": int(recent.detection_latency),
            "recovery_rate": float(recent.recovery_rate),
            "self_healing_active": bool(recent.self_healing_active),
            # History stats
            "history_stats": {
                "size": int(len(self.history)),
                "total_violations": int(sum(int(r.num_violations) for r in self.history)),
                "max_loss_mw": float(max(float(r.total_loss_mw) for r in self.history))
            }
        }
