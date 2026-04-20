import numpy as np
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class GridAnomalyAutoencoder:
    """
    AI-driven Anomaly Detection using Reconstruction Error.
    Simulates a Temporal Autoencoder that 'learns' healthy grid behaviors.
    """
    
    def __init__(self, input_dim: int = 24):
        self.input_dim = input_dim
        # Initialize as Identity: Healthy data reconstructs perfectly (MSE ~ 0)
        self.reconstruction_threshold = 2.0 
        
    def _reconstruct(self, x: np.ndarray, is_sag: bool = False) -> np.ndarray:
        """
        Learned Reconstruction logic.
        If healthy: x_hat ~= x
        If anomaly (Voltage Sag): Reconstruction fails, error spikes.
        """
        if is_sag:
            # Simulate reconstruction failure for anomalous inputs
            return x * 0.1 
        return x + np.random.normal(0, 0.05, self.input_dim) # Add small 'healthy' noise

    def predict_incident(self, telemetry: Dict[str, Any]) -> Dict[str, Any]:
        """
        AI Inference: Compares reality against 'learned' grid model.
        """
        p_reading = telemetry.get("power_kw", 0.0)
        v_reading = telemetry.get("voltage_v", 230.0)
        
        # Prepare context (current window)
        context = np.array([p_reading] * self.input_dim)
        
        # Determine if we simulate an anomaly for this input
        is_sag = v_reading < 210.0
        
        # Inference
        x_hat = self._reconstruct(context, is_sag=is_sag)
        error = np.mean((context - x_hat)**2)
        
        is_anomaly = error > self.reconstruction_threshold
        
        return {
            "is_anomaly": is_anomaly,
            "reconstruction_error": round(float(error), 4),
            "threshold": self.reconstruction_threshold,
            "confidence_pct": round(min(99.9, (error / self.reconstruction_threshold) * 50), 1) if is_anomaly else 0.0
        }

class GridRecommendationEngine:
    """
    Rule-Based Expert System for Anomaly Response.
    Translates AI detections into actionable grid operations.
    """
    
    @staticmethod
    def get_recommendation(anomaly_type: str, severity: str) -> str:
        logic_tree = {
            "VOLTAGE_SAG": "Main Grid deficit detected. Discharge BESS at 10 MW and initiate 5 MW Diesel backup.",
            "CAPACITY_DROP": "Submarine cable bottleneck detected. Activate Demand Response (Load Shedding) for Tier 3 customers.",
            "OVERLOAD": "Transformer thermal limit reached. Initiate preemptive peak shaving via BESS.",
            "HEALTHY": "Grid operating within normal parameters. Continue optimized MILP dispatch."
        }
        return logic_tree.get(anomaly_type, "Monitor grid stability and prepare standby generation.")
