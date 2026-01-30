import pandas as pd
import json
import os
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger(__name__)

class ProfileDataSource:
    """
    Manages historical AMI profiles for simulation playback.
    Supports CSV, JSON and Parquet formats with resampling and interpolation.
    Includes Standard Load Profile (SLP) generation for H0 and G0 profiles.
    """
    
    def __init__(self, profiles_dir: str = "data/profiles"):
        self.profiles_dir = profiles_dir
        os.makedirs(self.profiles_dir, exist_ok=True)
        self.profiles: Dict[str, pd.DataFrame] = {}
        self.metadata: Dict[str, Any] = {}
        
    def load_profile(self, profile_name: str) -> bool:
        """
        Load a profile from the profiles directory.
        
        Args:
            profile_name: Name of the profile file (without extension)
            
        Returns:
            True if loaded successfully, False otherwise
        """
        # Try CSV first
        csv_path = os.path.join(self.profiles_dir, f"{profile_name}.csv")
        json_path = os.path.join(self.profiles_dir, f"{profile_name}.json")
        parquet_path = os.path.join(self.profiles_dir, f"{profile_name}.parquet")
        pqt_path = os.path.join(self.profiles_dir, f"{profile_name}.pqt")
        
        try:
            if os.path.exists(csv_path):
                df = pd.read_csv(csv_path)
                if 'timestamp' not in df.columns:
                    logger.error(f"Profile {profile_name} missing 'timestamp' column")
                    return False
                
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                df.set_index('timestamp', inplace=True)
                self.profiles[profile_name] = df
                logger.info(f"Loaded CSV profile: {profile_name} with {len(df)} rows")
                return True
            
            elif os.path.exists(json_path):
                with open(json_path, 'r') as f:
                    data = json.load(f)
                df = pd.DataFrame(data)
                if 'timestamp' not in df.columns:
                    logger.error(f"Profile {profile_name} missing 'timestamp' column")
                    return False
                
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                df.set_index('timestamp', inplace=True)
                self.profiles[profile_name] = df
                logger.info(f"Loaded JSON profile: {profile_name} with {len(df)} rows")
                return True

            elif os.path.exists(parquet_path) or os.path.exists(pqt_path):
                path = parquet_path if os.path.exists(parquet_path) else pqt_path
                df = pd.read_parquet(path)
                if 'timestamp' not in df.columns and not isinstance(df.index, pd.DatetimeIndex):
                    logger.error(f"Profile {profile_name} missing 'timestamp' column or index")
                    return False
                if 'timestamp' in df.columns:
                    df['timestamp'] = pd.to_datetime(df['timestamp'])
                    df.set_index('timestamp', inplace=True)
                self.profiles[profile_name] = df
                logger.info(f"Loaded Parquet profile: {profile_name} with {len(df)} rows")
                return True
            
            else:
                logger.error(f"Profile file not found: {profile_name}")
                return False
                
        except Exception as e:
            logger.error(f"Error loading profile {profile_name}: {e}")
            return False

    def get_value(self, profile_name: str, meter_id: str, timestamp: datetime) -> Optional[float]:
        """
        Get the value for a specific meter at a given timestamp.
        """
        if profile_name not in self.profiles:
            if not self.load_profile(profile_name):
                return None
        
        df = self.profiles[profile_name]
        if meter_id not in df.columns:
            return None
            
        try:
            idx = df.index.get_indexer([timestamp], method='nearest')[0]
            return float(df.iloc[idx][meter_id])
        except Exception:
            return None

    def list_profiles(self) -> List[str]:
        """List available profiles in the directory."""
        files = os.listdir(self.profiles_dir)
        return [os.path.splitext(f)[0] for f in files if f.endswith(('.csv', '.json', '.parquet', '.pqt'))]

    def save_profile(self, name: str, data: List[Dict[str, Any]], format: str = "csv"):
        """Save a new profile to disk."""
        path = os.path.join(self.profiles_dir, f"{name}.{format}")
        df = pd.DataFrame(data)
        if format == "csv":
            df.to_csv(path, index=False)
        elif format in ("parquet", "pqt"):
            df.to_parquet(path, index=False)
        else:
            df.to_json(path, orient='records')
        logger.info(f"Saved new profile: {name} in {format} format")
        return path

    def generate_slp(
        self, 
        name: str, 
        profile_type: str = "H0", 
        annual_kwh: float = 3500,
        start_date: datetime = None,
        days: int = 1,
        meter_ids: List[str] = None
    ) -> bool:
        """
        Generate synthetic Standard Load Profile (SLP) data.
        """
        if not start_date:
            start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        if not meter_ids:
            meter_ids = ["M1"]
            
        # Standard daily weighting (96 samples for 15-min intervals)
        if profile_type.upper() == "H0":
            base_curve = [
                0.3, 0.25, 0.2, 0.2, 0.2, 0.2, 0.2, 0.25,
                0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0,
                1.1, 1.2, 1.3, 1.2, 1.1, 1.0, 0.9, 0.8,
                0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.4, 1.5,
                1.3, 1.2, 1.1, 1.0, 0.9, 0.8, 0.8, 0.9,
                1.0, 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7,
                1.8, 1.9, 2.0, 2.1, 2.2, 2.3, 2.4, 2.5,
                2.6, 2.7, 2.6, 2.5, 2.4, 2.3, 2.2, 2.1,
                2.0, 2.2, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0,
                5.5, 6.0, 5.8, 5.5, 5.0, 4.5, 4.0, 3.5,
                3.0, 2.5, 2.0, 1.5, 1.2, 1.0, 0.8, 0.6,
                0.5, 0.45, 0.4, 0.35, 0.3, 0.25, 0.2, 0.1
            ]
        else:
            base_curve = [
                0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2,
                0.2, 0.2, 0.3, 0.4, 0.6, 0.8, 1.0, 1.2,
                1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0,
                5.5, 6.0, 6.5, 7.0, 7.5, 8.0, 8.5, 9.0,
                9.5, 10.0, 10.0, 10.0, 10.0, 9.8, 9.5, 9.0,
                8.5, 8.0, 7.5, 7.0, 6.5, 6.0, 5.5, 5.0,
                5.0, 5.5, 6.0, 6.5, 7.0, 7.5, 8.0, 8.5,
                9.0, 9.5, 9.8, 10.0, 10.0, 10.0, 10.0, 9.5,
                9.0, 8.5, 8.0, 7.5, 7.0, 6.5, 6.0, 5.5,
                5.0, 4.0, 3.0, 2.0, 1.5, 1.0, 0.8, 0.6,
                0.5, 0.4, 0.3, 0.3, 0.2, 0.2, 0.2, 0.2,
                0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2 
            ]

        # Annual to Daily total
        daily_kwh = annual_kwh / 365.0
        # Power (kW) = Energy (kWh) / Time (h)
        # For 15-min intervals (0.25h), P = E / 0.25 = E * 4
        # We want the SUM of (P * 0.25) over the day to equal daily_kwh
        # Sum(weights * factor * 0.25) = daily_kwh
        # factor = daily_kwh / (Sum(weights) * 0.25)
        sum_weights = sum(base_curve)
        scaling_factor = daily_kwh / (sum_weights * 0.25)
        
        timestamps = [start_date + timedelta(minutes=15 * i) for i in range(96 * days)]
        data = {"timestamp": timestamps}
        for mid in meter_ids:
            values = []
            for d in range(days):
                values.extend([v * scaling_factor for v in base_curve])
            data[mid] = values
            
        df = pd.DataFrame(data)
        df.set_index('timestamp', inplace=True)
        self.profiles[name] = df
        
        self.save_profile(name, df.reset_index().to_dict(orient='records'), format='csv')
        return True
