from datetime import datetime, timedelta
from typing import Dict, Any, List
import math

from smart_meter_simulator.ai.feature_engineering import FeaturePipeline

class AIForecastingEngine:
    """
    AI Forecasting Engine using Gradient Boosting (Mocked LightGBM behavior).
    Predicts both the expected load on Koh Tao and the remaining capacity 
    of the 115kV submarine cable from Samui.
    """

    def __init__(self, model_path: str = None):
        """
        Initialize the forecasting engine.
        In production, this would load a pretrained LightGBM or TCN model.
        """
        self.model_loaded = True
        self.base_capacity_kw = 25000.0  # Total capacity of 115kV cable (25 MW)
        
    def _calculate_demographic_metrics(self, target_time: datetime) -> Dict[str, float]:
        """
        Calculate the Daily Active Population (DAP) and dynamic base load 
        based on the 'New Assumption' for Koh Tao.
        """
        import calendar
        T_annual = 400_000
        R_base = 10_000
        L = 4.0
        
        month = target_time.month
        D_m = calendar.monthrange(target_time.year, month)[1]
        
        monthly_weights = {
            1: 0.12, 2: 0.11, 3: 0.10, 4: 0.10, 5: 0.06, 6: 0.06,
            7: 0.08, 8: 0.09, 9: 0.06, 10: 0.07, 11: 0.05, 12: 0.10
        }
        W_m = monthly_weights.get(month, 0.083)
        
        # Calculate T_active and DAP
        T_active = (T_annual * W_m / D_m) * L
        DAP_d = R_base + T_active
        
        # Calculate dynamic base load in kW
        # EI_res = 0.5 kW, EI_tourist = 2.5 kW, C_base = 2000 kW
        Load_d_kw = (R_base * 0.5) + (T_active * 2.5) + 2000.0
        
        return {
            "T_active": T_active,
            "DAP_d": DAP_d,
            "Load_d_kw": Load_d_kw
        }
        
    def _calculate_phangan_demographic_metrics(self, target_time: datetime) -> Dict[str, float]:
        """
        Calculate the Daily Active Population and dynamic base load for Ko Pha-ngan,
        accounting for the digital nomad baseload and the Full Moon lunar spike.
        """
        import calendar
        R_base = 25_000
        T_annual = 450_000
        N_active = 5_000
        L = 4.0
        
        month = target_time.month
        D_m = calendar.monthrange(target_time.year, month)[1]
        
        monthly_weights = {
            1: 0.12, 2: 0.11, 3: 0.10, 4: 0.10, 5: 0.06, 6: 0.06,
            7: 0.08, 8: 0.09, 9: 0.06, 10: 0.07, 11: 0.05, 12: 0.10
        }
        W_m = monthly_weights.get(month, 0.083)
        
        is_full_moon_window = target_time.day in [22, 23, 24]
        S_lunar_kw = 8000.0 if is_full_moon_window else 0.0
        
        T_active = (T_annual * W_m / D_m) * L
        
        # Load_d = (R_base * EI_res) + (T_active * EI_tourist) + (N_active * EI_nomad) + S_lunar
        # EI_res = 0.8 kW, EI_tourist = 2.0 kW, EI_nomad = 3.5 kW
        Load_d_kw = (R_base * 0.8) + (T_active * 2.0) + (N_active * 3.5) + S_lunar_kw
        
        return {
            "T_active": T_active,
            "N_active": N_active,
            "Load_d_kw": Load_d_kw
        }
        
    def _mock_lightgbm_inference(self, features: List[float]) -> Dict[str, float]:
        """
        Simulate LightGBM prediction based on input features.
        features: [current_load_kw, hour_sin, hour_cos, dow_sin, dow_cos, is_weekend, temp, humidity]
        """
        # Unpack features for mock calculation
        _, hour_sin, hour_cos, dow_sin, dow_cos, is_weekend, temp, _ = features
        
        # 1. Predict Load_Tao (The Yellow Line)
        # Use dynamic base load from the New Assumption demographic metrics (passed via features or assumed context)
        # We will adjust this in forecast_next_24_hours by passing it in, but for mock inference, 
        # let's assume base_load_tao is passed as an extra feature or handled outside.
        # Actually, let's just let forecast_next_24_hours pass the base_load_tao to us.
        pass # Replaced below
        
        # 2. Predict Capacity_115kV (The Blue Line)
        # Capacity is drained by Koh Samui's AC usage before reaching Koh Tao.
        samui_base_load = 5000.0
        samui_temp_effect = max(0, temp - 26.0) * 1500.0 # Samui load highly sensitive to temp
        samui_time_effect = hour_sin * -3000.0
        samui_load = samui_base_load + samui_temp_effect + samui_time_effect
        
        # Phangan's load acts as a further drain on the 115kV capacity before it reaches Tao.
        # We will deduct it in `forecast_next_24_hours` where we calculate the Phangan demographic load.
        
        return {
            "temp_effect": max(0, temp - 26.0) * 500.0,
            "time_effect": hour_sin * -2000.0 + hour_cos * -1000.0,
            "weekend_effect": is_weekend * 2500.0,
            "samui_load": samui_load
        }

    def forecast_next_24_hours(self, start_time: datetime, current_load_kw: float) -> List[Dict[str, Any]]:
        """
        Run the AI pipeline to forecast the next 24 hours.
        Calculates the Delta = Capacity_115kV - Load_Tao.
        """
        forecasts = []
        
        # State variable to track cumulative thermal stress (heat buildup in the cable)
        thermal_accumulation = 0.0
        
        for i in range(24):
            target_time = start_time + timedelta(hours=i)
            
            # Step 1: Feature Engineering
            features = FeaturePipeline.prepare_inference_vector(target_time, current_load_kw)
            
            # Step 1.5: Demographic Metrics (New Assumption)
            tao_metrics = self._calculate_demographic_metrics(target_time)
            phangan_metrics = self._calculate_phangan_demographic_metrics(target_time)
            
            # Step 2: Model Inference
            predictions = self._mock_lightgbm_inference(features)
            
            # Combine dynamic base load with LightGBM effects
            load_tao = round(tao_metrics["Load_d_kw"] + predictions["temp_effect"] + predictions["time_effect"] + predictions["weekend_effect"], 2)
            
            # Remaining Capacity calculation: Base - Samui Load - Phangan Load
            # Phangan load has a time effect as well (assume similar AC usage shape but less extreme than Samui)
            _, hour_sin, _, _, _, _, temp, _ = features
            phangan_time_effect = hour_sin * -1500.0
            total_phangan_load = phangan_metrics["Load_d_kw"] + phangan_time_effect
            
            # Dynamic Line Rating (DLR) - Thermal Derating Simulation
            # The submarine cable heats up when upstream load is high and cools when low.
            # Base threshold for cooling vs heating is 18 MW (18000 kW)
            total_upstream_load = predictions["samui_load"] + total_phangan_load
            thermal_stress = (total_upstream_load - 18000.0) / 1000.0  # Heat generated/dissipated in MW
            
            # High ambient sea temperatures also prevent cooling
            ambient_temp_penalty = max(0, temp - 28.0) * 0.5 
            
            # Accumulate heat, bounded between 0 and a maximum heat index (e.g., 60.0)
            thermal_accumulation += (thermal_stress + ambient_temp_penalty)
            thermal_accumulation = max(0.0, min(60.0, thermal_accumulation))
            
            # Derate the cable's baseline capacity by 150 kW per unit of accumulated thermal stress
            thermal_derating_kw = thermal_accumulation * 150.0
            dynamic_base_capacity_kw = self.base_capacity_kw - thermal_derating_kw
            
            # The capacity actually reaching Koh Tao
            capacity_115kv = round(dynamic_base_capacity_kw - predictions["samui_load"] - total_phangan_load, 2)
            
            # Step 3: Delta Calculation (The constraint trigger)
            delta = round(capacity_115kv - load_tao, 2)
            
            forecasts.append({
                "timestamp": target_time.isoformat(),
                "hour_offset": i,
                "Load_Tao": load_tao,            # Yellow Line
                "Capacity_115kV": capacity_115kv,# Blue Line
                "delta": delta,
                "constraint_active": delta < 0,  # If True, BESS must be dispatched
                "DAP_d": int(tao_metrics["DAP_d"]),
                "T_active": int(tao_metrics["T_active"]),
                "thermal_derating_kw": round(thermal_derating_kw, 2)
            })
            
        return forecasts
