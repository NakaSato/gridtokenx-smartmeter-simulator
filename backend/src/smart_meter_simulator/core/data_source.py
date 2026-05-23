import json
import os
import random
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger(__name__)


class ProfileDataSource:
    """
    Manages historical AMI profiles for simulation playback (Simplified - No Pandas/NumPy).
    """

    def __init__(self, profiles_dir: str = "data/profiles"):
        self.profiles_dir = profiles_dir
        os.makedirs(self.profiles_dir, exist_ok=True)
        self.profiles: Dict[str, List[Dict[str, Any]]] = {}
        self.last_loaded_metadata: Dict[str, Any] = {}

    def load_profile(self, profile_name: str) -> bool:
        """
        Load a profile from the profiles directory.
        """
        csv_path = os.path.join(self.profiles_dir, f"{profile_name}.csv")
        json_path = os.path.join(self.profiles_dir, f"{profile_name}.json")

        try:
            data = None
            if os.path.exists(json_path):
                with open(json_path, "r") as f:
                    data = json.load(f)

                if isinstance(data, dict) and "locations" in data:
                    self.last_loaded_metadata = {
                        k: v for k, v in data.items() if k != "locations"
                    }
                    data = data["locations"]
            elif os.path.exists(csv_path):
                import csv

                with open(csv_path, "r") as f:
                    reader = csv.DictReader(f)
                    data = list(reader)

            if data is None:
                return False

            self.profiles[profile_name] = data
            return True
        except Exception as e:
            logger.error(f"Loader failed for {profile_name}: {e}")
            return False

    def get_value(
        self, profile_name: str, meter_id: str, timestamp: datetime
    ) -> Optional[float]:
        """
        Get value (Simple lookup).
        """
        if profile_name not in self.profiles:
            if not self.load_profile(profile_name):
                return None

        # Very inefficient linear search for simulation
        # In real microservice, we'd use a better structure
        for entry in self.profiles[profile_name]:
            ts_str = entry.get("timestamp")
            if ts_str:
                try:
                    entry_ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                    if abs((entry_ts - timestamp).total_seconds()) < 60:
                        val = entry.get(meter_id)
                        return float(val) if val is not None else None
                except Exception:
                    continue
        return None

    def generate_slp(
        self,
        name: str,
        profile_type: str = "H0",
        annual_kwh: float = 3500,
        start_date: datetime = None,
        days: int = 1,
        meter_ids: List[str] = None,
    ) -> bool:
        """
        Generate synthetic Standard Load Profile (SLP) data without NumPy.
        """
        if not start_date:
            start_date = datetime.now().replace(
                hour=0, minute=0, second=0, microsecond=0
            )
        if not meter_ids:
            meter_ids = ["M1"]

        if profile_type.upper() == "H0":
            base_curve = [
                0.3,
                0.25,
                0.2,
                0.2,
                0.2,
                0.2,
                0.2,
                0.25,
                0.3,
                0.4,
                0.5,
                0.6,
                0.7,
                0.8,
                0.9,
                1.0,
                1.1,
                1.2,
                1.3,
                1.2,
                1.1,
                1.0,
                0.9,
                0.8,
                0.8,
                0.9,
                1.0,
                1.1,
                1.2,
                1.3,
                1.4,
                1.5,
                1.3,
                1.2,
                1.1,
                1.0,
                0.9,
                0.8,
                0.8,
                0.9,
                1.0,
                1.1,
                1.2,
                1.3,
                1.4,
                1.5,
                1.6,
                1.7,
                1.8,
                1.9,
                2.0,
                2.1,
                2.2,
                2.3,
                2.4,
                2.5,
                2.6,
                2.7,
                2.6,
                2.5,
                2.4,
                2.3,
                2.2,
                2.1,
                2.0,
                2.2,
                2.5,
                3.0,
                3.5,
                4.0,
                4.5,
                5.0,
                5.5,
                6.0,
                5.8,
                5.5,
                5.0,
                4.5,
                4.0,
                3.5,
                3.0,
                2.5,
                2.0,
                1.5,
                1.2,
                1.0,
                0.8,
                0.6,
                0.5,
                0.45,
                0.4,
                0.35,
                0.3,
                0.25,
                0.2,
                0.1,
            ]
        else:
            base_curve = [0.2] * 96  # Simple default

        daily_kwh = annual_kwh / 365.0
        sum_weights = sum(base_curve)
        scaling_factor = daily_kwh / (sum_weights * 0.25)

        result_data = []
        for i in range(96 * days):
            ts = start_date + timedelta(minutes=15 * i)
            entry = {"timestamp": ts.isoformat()}
            curve_idx = i % 96

            for mid in meter_ids:
                meter_variation = 1.0 + (random.random() - 0.5) * 0.1
                val = base_curve[curve_idx] * scaling_factor * meter_variation
                entry[mid] = max(0, val + random.gauss(0, val * 0.05))

            result_data.append(entry)

        self.profiles[name] = result_data

        json_path = os.path.join(self.profiles_dir, f"{name}.json")
        with open(json_path, "w") as f:
            json.dump(result_data, f)

        return True
