"""
State Estimator - Phase 2 Implementation

Integrates pandapower state estimation for power system analysis.
Validates measurements against ANSI C12.20 accuracy standards.

References:
- meter_spec.md Section 5.3 (Measurement Accuracy & Validation)
- meter_spec.md Section 4.4 (State Estimation Integration)
"""

from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)

# Compatibility fix for some pandapower/numpy versions that might access np.linalg.linalg
if not hasattr(np.linalg, 'linalg'):
    np.linalg.linalg = np.linalg

try:
    import pandapower as pp
    from pandapower.estimation import estimate, remove_bad_data, chi2_analysis
    PANDAPOWER_AVAILABLE = True
except ImportError:
    PANDAPOWER_AVAILABLE = False


class EstimationAlgorithm(Enum):
    """Available state estimation algorithms."""
    WLS = "wls"          # Weighted Least Squares
    IRWLS = "irwls"      # Iteratively Reweighted Least Squares (Robust)
    LAV = "lav"          # Least Absolute Value (Robust)


class ValidationResult(Enum):
    """Measurement validation result."""
    VALID = "valid"
    OUTLIER = "outlier"
    BAD_DATA = "bad_data"
    MISSING = "missing"


@dataclass
class EstimationResults:
    """Results from state estimation."""
    converged: bool
    iterations: int
    residuals: pd.DataFrame
    estimated_voltages: pd.DataFrame
    bad_data_detected: List[str]
    num_measurements: int = 0  # Total number of measurements used
    chi2_statistic: Optional[float] = None
    mean_absolute_error: Optional[float] = None
    max_residual: Optional[float] = None
    v_deviation_avg: Optional[float] = None # Average voltage deviation from nominal
    total_losses_mw: Optional[float] = None # Total grid active power losses


@dataclass
class AccuracyMetrics:
    """ANSI C12.20 accuracy metrics."""
    measurement_name: str
    true_value: float
    estimated_value: float
    error_percent: float
    std_dev: float
    within_tolerance: bool
    tolerance_percent: float = 2.0  # ANSI C12.20 ±2% for residential


class StateEstimator:
    """
    Power system state estimator using pandapower.
    """
    
    def __init__(
        self,
        algorithm: EstimationAlgorithm = EstimationAlgorithm.WLS,
        tolerance: float = 1e-6,
        max_iterations: int = 10
    ):
        if not PANDAPOWER_AVAILABLE:
            raise ImportError(
                "pandapower is required for StateEstimator. "
                "Install with: pip install pandapower>=2.14.0"
            )
        
        self.algorithm = algorithm
        self.tolerance = tolerance
        self.max_iterations = max_iterations
        self.last_results: Optional[EstimationResults] = None
    
    def run_estimation(
        self,
        net: pp.pandapowerNet,
        init: str = "flat"
    ) -> EstimationResults:
        """
        Run state estimation on the network.
        """
        if len(net.measurement) == 0:
            raise ValueError("Network has no measurements. Add measurements first.")
        
        try:
            # Attempt initial estimation with configured algorithm
            res_raw = self._execute_estimate(net, self.algorithm.value, init)
            success, iterations = self._parse_estimate_result(res_raw)
            
            # Auto-Fallback: If WLS fails, retry with IRWLS (robust)
            if not success and self.algorithm == EstimationAlgorithm.WLS:
                logger.warning("WLS failed to converge, retrying with IRWLS robust estimator...")
                res_raw = self._execute_estimate(net, "irwls", init)
                success, iterations = self._parse_estimate_result(res_raw)
                
        except Exception as e:
            logger.error(f"Pandapower estimate() failed: {e}")
            success = False
            iterations = 0
            
        if not success:
            results = EstimationResults(
                converged=False,
                iterations=iterations,
                residuals=pd.DataFrame(),
                estimated_voltages=pd.DataFrame(),
                bad_data_detected=[],
                num_measurements=len(net.measurement)
            )
            self.last_results = results
            return results
        
        # Extract results
        residuals = self._calculate_residuals(net)
        estimated_voltages = net.res_bus[['vm_pu', 'va_degree']].copy() if hasattr(net, 'res_bus') else pd.DataFrame()
        
        # Calculate error metrics
        mae = residuals['residual'].abs().mean() if not residuals.empty else None
        max_res = residuals['residual'].abs().max() if not residuals.empty else None
        
        results = EstimationResults(
            converged=success,
            iterations=iterations,
            residuals=residuals,
            estimated_voltages=estimated_voltages,
            bad_data_detected=[],
            num_measurements=len(net.measurement),
            mean_absolute_error=mae,
            max_residual=max_res
        )
        
        self.last_results = results
        return results
    
    def detect_bad_data(
        self,
        net: pp.pandapowerNet,
        chi2_prob_false: float = 0.05,
        use_normalized_residuals: bool = True
    ) -> List[str]:
        """
        Detect bad data using Chi-squared and Normalized Residuals.
        """
        if len(net.measurement) == 0:
            return []
        
        bad_meter_names = set()
        
        # 1. Chi-squared test
        try:
            chi2_bad_indices = chi2_analysis(net, chi2_prob_false=chi2_prob_false)
            if chi2_bad_indices:
                for idx in chi2_bad_indices:
                    bad_meter_names.add(net.measurement.loc[idx, 'name'])
        except Exception:
            pass
            
        # 2. Normalized Residuals (Standard test: rN > 3.0)
        if use_normalized_residuals:
            try:
                rn_df = self.calculate_normalized_residuals(net)
                bad_local = rn_df[rn_df['norm_residual'] > 3.0]
                for _, row in bad_local.iterrows():
                    bad_meter_names.add(row['measurement'])
            except Exception:
                pass
        
        return list(bad_meter_names)
    
    def calculate_normalized_residuals(self, net: pp.pandapowerNet) -> pd.DataFrame:
        """Calculate |residual| / std_dev."""
        df = self._calculate_residuals(net)
        if df.empty:
            return df
        df['norm_residual'] = df['residual'].abs() / df['std_dev']
        return df

    def _execute_estimate(self, net: pp.pandapowerNet, algorithm: str, init: str):
        return estimate(net, algorithm=algorithm, init=init, tolerance=self.tolerance, maximum_iterations=self.max_iterations)

    def _parse_estimate_result(self, res_raw) -> Tuple[bool, int]:
        success = False
        iterations = 0
        if isinstance(res_raw, bool):
            success = res_raw
        elif hasattr(res_raw, 'success'):
            success = res_raw.success
            iterations = getattr(res_raw, 'num_iterations', 0)
        elif isinstance(res_raw, dict):
            success = res_raw.get('success', False)
            iterations = res_raw.get('num_iterations', 0)
        return success, iterations

    def _calculate_residuals(self, net: pp.pandapowerNet) -> pd.DataFrame:
        residuals = []
        meas_type_col = 'measurement_type' if 'measurement_type' in net.measurement.columns else 'meas_type'
        
        for idx, meas in net.measurement.iterrows():
            meas_name = meas['name']
            meas_type = meas[meas_type_col]
            measured_value = meas['value']
            estimated_value = measured_value # Fallback
            
            try:
                if meas_type == 'v':
                    bus_idx = meas['element']
                    if hasattr(net, 'res_bus') and bus_idx in net.res_bus.index:
                        estimated_value = net.res_bus.loc[bus_idx, 'vm_pu']
                elif meas_type == 'p':
                    estimated_value = 0.0 # Default for power injection
                    element_type = meas.get('element_type', 'load')
                    element_idx = meas['element']
                    if element_type == 'load' and hasattr(net, 'res_load') and element_idx in net.res_load.index:
                        estimated_value = net.res_load.loc[element_idx, 'p_mw']
                    elif element_type == 'sgen' and hasattr(net, 'res_sgen') and element_idx in net.res_sgen.index:
                        estimated_value = net.res_sgen.loc[element_idx, 'p_mw']
                elif meas_type == 'q':
                    estimated_value = 0.0
                    element_type = meas.get('element_type', 'load')
                    element_idx = meas['element']
                    if element_type == 'load' and hasattr(net, 'res_load') and element_idx in net.res_load.index:
                        estimated_value = net.res_load.loc[element_idx, 'q_mvar']
                    elif element_type == 'sgen' and hasattr(net, 'res_sgen') and element_idx in net.res_sgen.index:
                        estimated_value = net.res_sgen.loc[element_idx, 'q_mvar']
            except Exception:
                pass
            
            residuals.append({
                'measurement': meas_name,
                'type': meas_type,
                'measured': measured_value,
                'estimated': estimated_value,
                'residual': measured_value - estimated_value,
                'std_dev': meas['std_dev']
            })
        
        return pd.DataFrame(residuals)

    def validate_ansi_c12_20(
        self,
        net: pp.pandapowerNet,
        true_values: Optional[Dict[str, float]] = None,
        tolerance_percent: float = 2.0
    ) -> List[AccuracyMetrics]:
        if not hasattr(net, 'res_bus') or net.res_bus.empty:
            raise ValueError("Run state estimation first")
        
        metrics = []
        df_res = self._calculate_residuals(net)
        
        for _, row in df_res.iterrows():
            meas_name = row['measurement']
            true_value = true_values.get(meas_name, row['measured']) if true_values else row['measured']
            error_p = abs((row['estimated'] - true_value) / true_value * 100) if true_value != 0 else 0
            
            metrics.append(AccuracyMetrics(
                measurement_name=meas_name,
                true_value=true_value,
                estimated_value=row['estimated'],
                error_percent=error_p,
                std_dev=row['std_dev'],
                within_tolerance=error_p <= tolerance_percent,
                tolerance_percent=tolerance_percent
            ))
        return metrics

    def get_summary(self) -> Dict[str, Any]:
        if self.last_results is None:
            return {"error": "No results"}
        res = self.last_results
        return {
            "converged": res.converged,
            "iterations": res.iterations,
            "num_measurements": res.num_measurements,
            "mean_absolute_error": res.mean_absolute_error,
            "max_residual": res.max_residual
        }

class MeasurementValidator:
    def __init__(self):
        self.validation_history = []
    
    def validate_range(self, measurements: pd.DataFrame, limits: Optional[Dict[str, Tuple[float, float]]] = None) -> Dict[str, ValidationResult]:
        if limits is None:
            limits = {'v': (0.8, 1.2), 'p': (-100, 100), 'q': (-50, 50)}
        results = {}
        meas_type_col = 'measurement_type' if 'measurement_type' in measurements.columns else 'meas_type'
        for _, meas in measurements.iterrows():
            m_type = meas[meas_type_col]
            val = meas['value']
            if m_type in limits:
                mi, ma = limits[m_type]
                results[meas['name']] = ValidationResult.VALID if mi <= val <= ma else ValidationResult.OUTLIER
            else:
                results[meas['name']] = ValidationResult.VALID
        return results
