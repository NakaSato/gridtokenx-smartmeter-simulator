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
        
        # 4. Anomaly Detection (Cyber-security Analysis)
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

        report = GridHealthReport(
            timestamp=datetime.now(),
            total_loss_mw=float(total_loss_mw),
            avg_voltage_pu=float(res_bus.vm_pu.mean()),
            max_voltage_pu=float(res_bus.vm_pu.max()),
            min_voltage_pu=float(res_bus.vm_pu.min()),
            num_violations=len(violations),
            violations=violations,
            loss_percentage=float(loss_pct),
            health_score=self._calculate_health_score(len(violations), loss_pct, anomaly_score),
            is_under_attack=len(attack_alerts) > 0,
            anomaly_score=float(anomaly_score),
            attack_alerts=attack_alerts
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
            # History stats
            "history_stats": {
                "size": int(len(self.history)),
                "total_violations": int(sum(int(r.num_violations) for r in self.history)),
                "max_loss_mw": float(max(float(r.total_loss_mw) for r in self.history))
            }
        }
