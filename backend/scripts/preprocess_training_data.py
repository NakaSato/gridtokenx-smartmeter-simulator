import pandas as pd
import numpy as np
from pathlib import Path
import os

DATA_DIR = Path(__file__).parent.parent / "data"

def load_grid_data():
    """Load and resample grid data (hourly)"""
    files = [DATA_DIR / "system_2023.csv", DATA_DIR / "system_2024.csv"]
    dfs = []
    
    for f in files:
        if not f.exists():
            continue
        print(f"Loading grid data: {f}")
        df = pd.read_csv(f)
        # Handle datetime parsing (Day/Month/Year Hour:Minute)
        df['datetime'] = pd.to_datetime(df['datetime'], format='%d/%m/%Y %H:%M')
        df = df.set_index('datetime')
        
        # Resample to hourly and take the mean (ensure regularity)
        # Note: resample then mean() handles the 0:05 rows
        df_hourly = df[['south_generation', 'south_demand']].resample('h').mean()
        dfs.append(df_hourly)
        
    return pd.concat(dfs).sort_index()

def load_weather_data():
    """Load weather data for Koh Tao"""
    files = [DATA_DIR / "koh_tao_weather_2023.csv", DATA_DIR / "koh_tao_weather_2024.csv"]
    dfs = []
    
    for f in files:
        if not f.exists():
            continue
        print(f"Loading weather data: {f}")
        # Find where header ends (NASA format)
        with open(f, 'r') as file:
            lines = file.readlines()
            header_end = 0
            for i, line in enumerate(lines):
                if "-END HEADER-" in line:
                    header_end = i + 1
                    break
        
        df = pd.read_csv(f, skiprows=header_end)
        
        # Parse dates (YEAR,MO,DY,HR)
        df['datetime'] = pd.to_datetime({
            'year': df['YEAR'],
            'month': df['MO'],
            'day': df['DY'],
            'hour': df['HR']
        })
        
        df = df.set_index('datetime')
        # Clean specific columns
        df = df[['ALLSKY_SFC_SW_DWN', 'T2M', 'RH2M']]
        df = df.rename(columns={
            'ALLSKY_SFC_SW_DWN': 'irradiance',
            'T2M': 'temp_c',
            'RH2M': 'humidity'
        })
        dfs.append(df)
        
    return pd.concat(dfs).sort_index()

def add_features(df):
    """Add temporal and cyclical features for LightGBM"""
    print("Adding features...")
    df['hour'] = df.index.hour
    df['day_of_week'] = df.index.dayofweek
    df['month'] = df.index.month
    df['is_weekend'] = df['day_of_week'].isin([5, 6]).astype(int)
    
    # Cyclical hour encoding
    df['hour_sin'] = np.sin(2 * np.pi * df['hour'] / 24)
    df['hour_cos'] = np.cos(2 * np.pi * df['hour'] / 24)
    
    # Lagged features (South Demand)
    df['load_lag_1h'] = df['south_demand'].shift(1)
    df['load_lag_2h'] = df['south_demand'].shift(2)
    df['load_lag_24h'] = df['south_demand'].shift(24)
    
    # Drop rows with NaN from lags
    df = df.dropna()
    return df

def main():
    grid_df = load_grid_data()
    weather_df = load_weather_data()
    
    print(f"Grid data range: {grid_df.index.min()} to {grid_df.index.max()}")
    print(f"Weather data range: {weather_df.index.min()} to {weather_df.index.max()}")
    
    # Join on timestamp
    combined_df = grid_df.join(weather_df, how='inner')
    
    if combined_df.empty:
        print("❌ ERROR: No overlap found between grid and weather data.")
        return
        
    # Feature Engineering
    final_df = add_features(combined_df)
    
    # Export
    output_path = DATA_DIR / "training_set.csv"
    final_df.to_csv(output_path)
    print(f"✅ Success! Preprocessed dataset saved to {output_path}")
    print(f"📊 Final Rows: {len(final_df)}")
    print(f"Columns: {list(final_df.columns)}")

if __name__ == "__main__":
    main()
