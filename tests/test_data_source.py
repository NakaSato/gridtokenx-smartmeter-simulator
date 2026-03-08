import pytest
from datetime import datetime, timedelta
from smart_meter_simulator.core.data_source import ProfileDataSource
import pandas as pd

def test_slp_generation_and_scaling():
    ds = ProfileDataSource(profiles_dir="/tmp/test_profiles")
    
    # Generate H0 profile for 1 day, target 3500 kWh annually
    success = ds.generate_slp("test_h0", profile_type="H0", annual_kwh=3500, days=1, meter_ids=["M1", "M2"], randomness=0.0, noise=0.0)
    assert success
    
    df = ds.profiles["test_h0"]
    assert "M1" in df.columns
    assert "M2" in df.columns
    assert len(df) == 96 # 15-min intervals in a day
    
    # The sum of the 15-min power values (kW) divided by 4 gives kWh
    daily_kwh_m1 = df["M1"].sum() / 4.0
    
    # 3500 kWh / 365 = ~9.589 kWh/day
    expected_daily = 3500 / 365.0
    
    # Check if the generator scales correctly
    assert abs(daily_kwh_m1 - expected_daily) < 0.1
