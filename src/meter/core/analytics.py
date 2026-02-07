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

class GridAnalytics:
    """
    Provides advanced grid analytics and health monitoring.
    Tracks voltage violations and technical losses over time.
    """
    
    def __init__(self, voltage_low: float = 0.95, voltage_high: float = 1.05):
        self.voltage_low = voltage_low
        self.voltage_high = voltage_high
        self.history: List[GridHealthReport] = []
        
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
        
        report = GridHealthReport(
            timestamp=datetime.now(),
            total_loss_mw=float(total_loss_mw),
            avg_voltage_pu=float(res_bus.vm_pu.mean()),
            max_voltage_pu=float(res_bus.vm_pu.max()),
            min_voltage_pu=float(res_bus.vm_pu.min()),
            num_violations=len(violations),
            violations=violations,
            loss_percentage=float(loss_pct)
        )
        
        self.history.append(report)
        # Keep last 1000 steps
        if len(self.history) > 1000:
            self.history.pop(0)
            
        return report

    def get_summary(self) -> Dict[str, Any]:
        """Return a summary of grid health over the recent history."""
        if not self.history:
            return {"status": "No data"}
            
        recent = self.history[-1]
        
        return {
            "latest": {
                "loss_mw": recent.total_loss_mw,
                "loss_pct": recent.loss_percentage,
                "avg_v": recent.avg_voltage_pu,
                "violations": recent.num_violations
            },
            "history_size": len(self.history),
            "total_violations_detected": sum(r.num_violations for r in self.history),
            "max_loss_observed": max(r.total_loss_mw for r in self.history),
            "min_v_observed": min(r.min_voltage_pu for r in self.history),
            "max_v_observed": max(r.max_voltage_pu for r in self.history)
        }
