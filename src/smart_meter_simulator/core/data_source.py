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
        
    def preprocess_profile(
        self, 
        df: pd.DataFrame, 
        freq: str = "15T", 
        convert_kw_to_mw: bool = True
    ) -> pd.DataFrame:
        """
        Preprocess a profile: resample, fill gaps, and convert units.
        """
        # 1. Resample to standard frequency and interpolate
        df = df.resample(freq).mean().interpolate(method='linear')
        
        # 2. Convert kW to MW if needed
        if convert_kw_to_mw:
            df = df / 1000.0
            
        return df

    def load_profile(self, profile_name: str, preprocess: bool = True) -> bool:
        """
        Load a profile from the profiles directory using Polars for high performance.
        
        Args:
            profile_name: Name of the profile file (without extension)
            preprocess: If True, applies standard pre-processing (alignment/unit conversion)
            
        Returns:
            True if loaded successfully, False otherwise
        """
        import polars as pl
        
        # Supported extensions
        csv_path = os.path.join(self.profiles_dir, f"{profile_name}.csv")
        json_path = os.path.join(self.profiles_dir, f"{profile_name}.json")
        parquet_path = os.path.join(self.profiles_dir, f"{profile_name}.parquet")
        pqt_path = os.path.join(self.profiles_dir, f"{profile_name}.pqt")
        
        try:
            df_pl = None
            if os.path.exists(parquet_path) or os.path.exists(pqt_path):
                path = parquet_path if os.path.exists(parquet_path) else pqt_path
                df_pl = pl.read_parquet(path)
            elif os.path.exists(csv_path):
                df_pl = pl.read_csv(csv_path)
            elif os.path.exists(json_path):
                # Polars can read JSON, but if it fails we fallback to pandas
                try:
                    df_pl = pl.read_json(json_path)
                except Exception:
                    df = pd.read_json(json_path)
                    df_pl = pl.from_pandas(df)
            else:
                # Fallback to existing pandas implementation for HDF5
                return self._load_profile_pandas_fallback(profile_name, preprocess)
                
            if df_pl is None:
                logger.error(f"Profile file not found: {profile_name}")
                return False
                
            # For compatibility with the pandas-based rest of the codebase, 
            # we convert the ultra-fast Polars ingest back to a Pandas DataFrame
            # with proper datetime index for the resampling methods
            df = df_pl.to_pandas()
                
            if 'timestamp' in df.columns:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                df.set_index('timestamp', inplace=True)
            elif not isinstance(df.index, pd.DatetimeIndex):
                logger.error(f"Profile {profile_name} missing 'timestamp' column or index")
                return False
            
            if preprocess:
                df = self.preprocess_profile(df)
                
            self.profiles[profile_name] = df
            logger.info(f"[Polars Fast-Load] Loaded profile: {profile_name} with {len(df)} rows")
            return True
                
        except Exception as e:
            logger.error(f"Error loading profile {profile_name} via Polars: {e}")
            return self._load_profile_pandas_fallback(profile_name, preprocess)

    def _load_profile_pandas_fallback(self, profile_name: str, preprocess: bool = True) -> bool:
        """Legacy Pandas fallback loader for HDF5 or failed Polars loads"""
        csv_path = os.path.join(self.profiles_dir, f"{profile_name}.csv")
        json_path = os.path.join(self.profiles_dir, f"{profile_name}.json")
        h5_path = os.path.join(self.profiles_dir, f"{profile_name}.h5")
        hdf_path = os.path.join(self.profiles_dir, f"{profile_name}.hdf")
        
        try:
            df = None
            if os.path.exists(h5_path) or os.path.exists(hdf_path):
                path = h5_path if os.path.exists(h5_path) else hdf_path
                df = pd.read_hdf(path)
            elif os.path.exists(csv_path):
                df = pd.read_csv(csv_path)
            elif os.path.exists(json_path):
                with open(json_path, 'r') as f:
                    data = json.load(f)
                df = pd.DataFrame(data)
                
            if df is None: return False
                
            if 'timestamp' in df.columns:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                df.set_index('timestamp', inplace=True)
                
            if preprocess:
                df = self.preprocess_profile(df)
                
            self.profiles[profile_name] = df
            return True
        except Exception as e:
            logger.error(f"Fallback loader failed for {profile_name}: {e}")
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

    def get_values_batch(self, profile_name: str, timestamp: datetime) -> Dict[str, float]:
        """
        Efficiently get all meter values for a specific timestamp in one operation.
        """
        if profile_name not in self.profiles:
            if not self.load_profile(profile_name):
                return {}
        
        df = self.profiles[profile_name]
        try:
            idx = df.index.get_indexer([timestamp], method='nearest')[0]
            row = df.iloc[idx]
            # Convert row to dictionary focusing on numeric columns (meters)
            return row.to_dict()
        except Exception as e:
            logger.error(f"Error in batch fetch for {profile_name} at {timestamp}: {e}")
            return {}

    def list_profiles(self) -> List[str]:
        """List available profiles in the directory."""
        files = os.listdir(self.profiles_dir)
        return [os.path.splitext(f)[0] for f in files if f.endswith(('.csv', '.json', '.parquet', '.pqt', '.h5', '.hdf'))]

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
        meter_ids: List[str] = None,
        randomness: float = 0.1,  # Individual meter variation factor
        noise: float = 0.05       # Timestep noise factor
    ) -> bool:
        """
        Generate synthetic Standard Load Profile (SLP) data.
        """
        import numpy as np
        
        if not start_date:
            start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        if not meter_ids:
            meter_ids = ["M1"]
            
        # Standard daily weighting (96 samples for 15-min intervals)
        if profile_type.upper() == "H0":
            base_curve = np.array([
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
            ])
        else:
            base_curve = np.array([
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
            ])

        daily_kwh = annual_kwh / 365.0
        sum_weights = base_curve.sum()
        scaling_factor = daily_kwh / (sum_weights * 0.25)
        
        timestamps = [start_date + timedelta(minutes=15 * i) for i in range(96 * days)]
        data = {"timestamp": timestamps}
        
        for mid in meter_ids:
            # Add meter-specific variation
            meter_scaling = scaling_factor * (1.0 + (np.random.rand() - 0.5) * randomness)
            
            # Generate daily cycles with timestep noise
            full_values = []
            for d in range(days):
                daily_v = base_curve * meter_scaling
                # Add gaussian noise
                daily_v = daily_v * (1.0 + (np.random.randn(96) * noise))
                full_values.extend(daily_v.clip(min=0).tolist())
            
            data[mid] = full_values
            
        df = pd.DataFrame(data)
        df.set_index('timestamp', inplace=True)
        self.profiles[name] = df
        
        # Save as CSV for compatibility by default
        self.save_profile(name, df.reset_index().to_dict(orient='records'), format='csv')
        return True
