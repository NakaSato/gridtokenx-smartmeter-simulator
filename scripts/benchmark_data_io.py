import time
import os
import pandas as pd
import numpy as np
from datetime import datetime
from smart_meter_simulator.core.data_source import ProfileDataSource

def benchmark_io():
    ds = ProfileDataSource(profiles_dir="data/benchmarks")
    os.makedirs("data/benchmarks", exist_ok=True)
    
    num_meters = 1000
    num_steps = 96 * 7 # One week of 15m data
    meter_ids = [f"METER_{i}" for i in range(num_meters)]
    
    print(f"Generating benchmark data for {num_meters} meters and {num_steps} steps...")
    ds.generate_slp("benchmark_slp", annual_kwh=3500, days=7, meter_ids=meter_ids)
    
    # Path for formats
    csv_path = "data/benchmarks/benchmark_slp.csv"
    parquet_path = "data/benchmarks/benchmark_slp.parquet"
    hdf_path = "data/benchmarks/benchmark_slp.h5"
    
    # Save in all formats
    df = ds.profiles["benchmark_slp"]
    df.to_csv(csv_path)
    df.to_parquet(parquet_path)
    df.to_hdf(hdf_path, key='data', mode='w')
    
    formats = [
        ("CSV", csv_path),
        ("Parquet", parquet_path),
        ("HDF5", hdf_path)
    ]
    
    print("\n--- Load Performance ---")
    for name, path in formats:
        start = time.time()
        # Clear cache
        if "benchmark_slp" in ds.profiles:
            del ds.profiles["benchmark_slp"]
        
        # We need to rename file to match load_profile expectation if we want to test load_profile
        base_name = f"test_{name}"
        ext = os.path.splitext(path)[1]
        test_path = os.path.join("data/benchmarks", f"{base_name}{ext}")
        import shutil
        shutil.copy(path, test_path)
        
        ds.load_profile(base_name, preprocess=False)
        end = time.time()
        print(f"{name:10}: {end-start:.4f}s")

    print("\n--- Fetch Performance (1000 steps) ---")
    ts = df.index[0]
    
    # Test individual fetch
    start = time.time()
    for _ in range(100):
        for mid in meter_ids[:10]: # Just 10 meters to avoid taking too long
            ds.get_value("test_Parquet", mid, ts)
    end = time.time()
    print(f"Individual Fetch (100x10): {end-start:.4f}s")
    
    # Test batch fetch
    start = time.time()
    for _ in range(100):
        ds.get_values_batch("test_Parquet", ts)
    end = time.time()
    print(f"Batch Fetch (100xAll):     {end-start:.4f}s")

if __name__ == "__main__":
    benchmark_io()
