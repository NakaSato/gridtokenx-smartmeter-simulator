import pytest
import os
import pandas as pd
import polars as pl
from datetime import datetime, timedelta
from smart_meter_simulator.core.data_source import ProfileDataSource

def test_timestamp_alignment_resampling():
    """
    Verify that loading a 15-minute resolution file and resampling it to 5-minute ticks works correctly.
    """
    profiles_dir = "/tmp/test_profiles_alignment"
    os.makedirs(profiles_dir, exist_ok=True)
    ds = ProfileDataSource(profiles_dir=profiles_dir)
    
    # Create a 15-minute resolution CSV
    start_time = datetime(2024, 1, 1, 0, 0, 0)
    data = {
        "timestamp": [start_time + timedelta(minutes=15 * i) for i in range(4)],
        "M1": [1.0, 2.0, 3.0, 4.0]
    }
    df = pd.DataFrame(data)
    csv_path = os.path.join(profiles_dir, "align_test.csv")
    df.to_csv(csv_path, index=False)
    
    # Load with 5-minute resampling (5T)
    # The default in preprocess_profile is 15T, but we can call it with 5T
    # Actually, load_profile calls preprocess_profile(df) which uses default 15T.
    # Let's modify ProfileDataSource or call preprocess manually.
    
    success = ds.load_profile("align_test", preprocess=False)
    assert success
    
    raw_df = ds.profiles["align_test"]
    assert len(raw_df) == 4
    
    # Manually preprocess to 5T
    processed_df = ds.preprocess_profile(raw_df, freq="5T", convert_kw_to_mw=False)
    
    # 3 periods of 15 min = 45 min. 4 timestamps.
    # 0:00 (1.0), 0:15 (2.0), 0:30 (3.0), 0:45 (4.0)
    # 5T resampling should give:
    # 0:00 (1.0), 0:05 (1.33), 0:10 (1.66), 0:15 (2.0) ...
    assert len(processed_df) == 10 # (45 / 5) + 1 = 10
    assert processed_df.iloc[0]["M1"] == 1.0
    assert abs(processed_df.loc[start_time + timedelta(minutes=5), "M1"] - 1.333333) < 0.001
    assert processed_df.loc[start_time + timedelta(minutes=15), "M1"] == 2.0

def test_unit_conversion_kw_to_mw():
    """
    Verify kW to MW conversion.
    """
    profiles_dir = "/tmp/test_profiles_units"
    os.makedirs(profiles_dir, exist_ok=True)
    ds = ProfileDataSource(profiles_dir=profiles_dir)
    
    data = {
        "timestamp": [datetime(2024, 1, 1, 0, 0)],
        "M1": [2500.0] # 2500 kW
    }
    df = pd.DataFrame(data)
    df.set_index("timestamp", inplace=True)
    
    processed = ds.preprocess_profile(df, convert_kw_to_mw=True)
    assert processed.iloc[0]["M1"] == 2.5 # 2.5 MW

def test_slp_generation_high_precision():
    """
    Ensure SLP generation mathematically scales strictly proportionally to annual consumption.
    """
    ds = ProfileDataSource(profiles_dir="/tmp/test_slp_precision")
    annual_kwh = 10000
    days = 1
    
    success = ds.generate_slp(
        "precision_h0", 
        profile_type="H0", 
        annual_kwh=annual_kwh, 
        days=days, 
        meter_ids=["M1"], 
        randomness=0.0, 
        noise=0.0
    )
    assert success
    
    df = ds.profiles["precision_h0"]
    # Sum of 15-min kW values / 4 = kWh
    actual_daily_kwh = df["M1"].sum() / 4.0
    expected_daily_kwh = annual_kwh / 365.0
    
    # Tolerance should be extremely low for zero noise/randomness
    assert abs(actual_daily_kwh - expected_daily_kwh) < 0.0001

def test_polars_loading_csv():
    """
    Verify polars-based loading for CSV.
    """
    profiles_dir = "/tmp/test_profiles_polars"
    os.makedirs(profiles_dir, exist_ok=True)
    ds = ProfileDataSource(profiles_dir=profiles_dir)
    
    csv_path = os.path.join(profiles_dir, "polars_test.csv")
    with open(csv_path, "w") as f:
        f.write("timestamp,M1\n")
        f.write("2024-01-01T00:00:00,10.5\n")
        f.write("2024-01-01T00:15:00,20.5\n")
        
    success = ds.load_profile("polars_test", preprocess=False)
    assert success
    assert "polars_test" in ds.profiles
    assert ds.profiles["polars_test"].iloc[0]["M1"] == 10.5

def test_polars_loading_parquet():
    """
    Verify polars-based loading for Parquet.
    """
    profiles_dir = "/tmp/test_profiles_parquet"
    os.makedirs(profiles_dir, exist_ok=True)
    ds = ProfileDataSource(profiles_dir=profiles_dir)
    
    start_time = datetime(2024, 1, 1, 0, 0, 0)
    data = {
        "timestamp": [start_time, start_time + timedelta(minutes=15)],
        "M1": [50.0, 60.0]
    }
    df = pd.DataFrame(data)
    parquet_path = os.path.join(profiles_dir, "polars_pqt.parquet")
    df.to_parquet(parquet_path, index=False)
    
    success = ds.load_profile("polars_pqt", preprocess=False)
    assert success
    assert "polars_pqt" in ds.profiles
    assert ds.profiles["polars_pqt"].iloc[0]["M1"] == 50.0
