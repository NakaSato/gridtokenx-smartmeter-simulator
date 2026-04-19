"""
Edge-Optimized Forecasting Engine

Implements decentralized, resource-constrained forecasting using quantized 
sequence models (blueprint for TCN/LightGBM deployment on substations).
Target: <10% MAPE for 24-hour lookahead.
"""

import numpy as np
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from ..services.strategy_service import StrategyService

logger = logging.getLogger(__name__)

class EdgeForecastingEngine:
    """
    Decentralized forecasting engine designed for substation controllers.
    Utilizes historical patterns, real-time weather feeds, and temporal features.
    """
    
    def __init__(self, node_id: str):
        self.node_id = node_id
        # Weights for the simulated model (represents a trained TCN/LightGBM)
        self.weights = {
            "load_base": 0.7,
            "temp_sensitivity": 0.15,
            "cloud_sensitivity": 0.1,
            "temporal_noise": 0.05
        }
        self.history = []
        self.last_mape = 0.0

    def generate_24h_forecast(
        self, 
        current_load_mw: float, 
        weather_data: Dict[str, Any],
        timestamp: Optional[datetime] = None
    ) -> np.ndarray:
        """
        Generate a 24-step hourly forecast vector.
        
        Args:
            current_load_mw: Latest SCADA load measurement
            weather_data: {temp, irradiance, cloud_cover}
            timestamp: Start time for the forecast
        """
        ts = timestamp or datetime.now()
        forecast = []
        
        # Base daily profile (Double peak: noon tourism/solar, evening residential)
        # 00:00 - 23:00
        base_profile = [
            0.6, 0.5, 0.45, 0.4, 0.45, 0.6,  # Night/Early morning
            0.8, 1.2, 1.5, 1.8, 2.0, 2.1,  # Morning/Noon (Tourism AC + PV interaction)
            2.0, 1.9, 1.8, 1.7, 1.9, 2.3,  # Afternoon/Evening ramp
            2.5, 2.4, 2.2, 1.8, 1.2, 0.8   # Peak/Night ramp down
        ]
        
        temp_factor = weather_data.get("temp_c", 30.0) / 30.0
        cloud_factor = weather_data.get("cloud_cover", 0.0) / 100.0
        
        for i in range(24):
            hour = (ts.hour + i) % 24
            
            # 1. Base Load
            val = base_profile[hour] * current_load_mw
            
            # 2. Weather Adjustment (AC load sensitivity)
            val *= (1.0 + (temp_factor - 1.0) * self.weights["temp_sensitivity"])
            
            # 3. Cloud/Solar Adjustment (PV generation deficit increases net load)
            val *= (1.0 + cloud_factor * self.weights["cloud_sensitivity"])
            
            # 4. Temporal Features (Weekend/Holiday boost)
            if (ts + timedelta(hours=i)).weekday() >= 5:
                val *= 1.15 # 15% boost for tourism peak
                
            # 5. Quantized Noise (Representing model uncertainty)
            noise = np.random.normal(0, val * 0.03)
            forecast.append(max(0, val + noise))
            
        return np.array(forecast)

    def calculate_mape(self, forecast: np.ndarray, actual: np.ndarray) -> float:
        """Calculate Mean Absolute Percentage Error."""
        if len(forecast) == 0 or len(actual) == 0: return 0.0
        
        # Match lengths
        n = min(len(forecast), len(actual))
        f = forecast[:n]
        a = actual[:n]
        
        # Avoid division by zero
        a_safe = np.where(a == 0, 1e-6, a)
        mape = np.mean(np.abs((a - f) / a_safe)) * 100.0
        self.last_mape = mape
        
        if mape < 10.0:
            logger.info(f"FORECAST VALID: {self.node_id} MAPE = {mape:.2f}% (<10% Target Met)")
        else:
            logger.warning(f"FORECAST ALERT: {self.node_id} MAPE = {mape:.2f}% exceeds threshold")
            
        return mape

    def get_recommended_schedule(self, forecast: np.ndarray, capacity_mw: float) -> List[Dict[str, Any]]:
        """
        Generate the 'Recommended Schedule' based on forecasted bottlenecks using StrategyService.
        """
        # We reuse the logic from StrategyService for consistency
        strategy_service = StrategyService()
        # EdgeForecastingEngine's forecast is current_load + PV interaction.
        # We can treat pv_forecast as zeros since current_load_mw already accounts for it in EdgeForecastingEngine.
        pv_zeros = [0.0] * len(forecast)
        return strategy_service.calculate_optimal_dispatch_schedule(
            forecast.tolist(),
            pv_zeros,
            capacity_mw
        )
