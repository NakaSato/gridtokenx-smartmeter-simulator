import math
from datetime import datetime
from typing import Dict, Any, List

class FeaturePipeline:
    """
    Feature Engineering Pipeline for AI Load Forecasting.
    Extracts temporal, weather, and historical load features.
    """

    @staticmethod
    def extract_temporal_features(target_time: datetime) -> Dict[str, float]:
        """
        Extract cyclical time-of-day and day-of-week features.
        """
        hour = target_time.hour + target_time.minute / 60.0
        day_of_week = target_time.weekday()

        # Cyclical encoding for hour (0-24)
        hour_sin = math.sin(2 * math.pi * hour / 24.0)
        hour_cos = math.cos(2 * math.pi * hour / 24.0)

        # Cyclical encoding for day of week (0-7)
        dow_sin = math.sin(2 * math.pi * day_of_week / 7.0)
        dow_cos = math.cos(2 * math.pi * day_of_week / 7.0)

        return {
            "hour_sin": hour_sin,
            "hour_cos": hour_cos,
            "dow_sin": dow_sin,
            "dow_cos": dow_cos,
            "is_weekend": 1.0 if day_of_week >= 5 else 0.0
        }

    @staticmethod
    def get_weather_features(target_time: datetime) -> Dict[str, float]:
        """
        Mock weather data ingestion.
        In a real scenario, this fetches from an API (e.g., OpenWeatherMap)
        Temperature spikes typically occur between 13:00 - 15:00.
        """
        hour = target_time.hour + target_time.minute / 60.0
        # Base temp 26C, peak temp 34C around 14:00
        base_temp = 26.0
        peak_offset = 8.0 * math.exp(-((hour - 14.0) ** 2) / 10.0)
        
        # Add a bit of randomness or weekend spikes if needed
        temperature_c = base_temp + peak_offset
        
        return {
            "temperature_c": round(temperature_c, 2),
            "humidity_percent": 75.0,  # Mock static humidity
        }

    @staticmethod
    def prepare_inference_vector(target_time: datetime, current_load_kw: float) -> List[float]:
        """
        Assemble the final feature vector for LightGBM / TCN inference.
        """
        temporal = FeaturePipeline.extract_temporal_features(target_time)
        weather = FeaturePipeline.get_weather_features(target_time)
        
        # Ordering is critical for tabular ML models
        vector = [
            current_load_kw,
            temporal["hour_sin"],
            temporal["hour_cos"],
            temporal["dow_sin"],
            temporal["dow_cos"],
            temporal["is_weekend"],
            weather["temperature_c"],
            weather["humidity_percent"]
        ]
        return vector
