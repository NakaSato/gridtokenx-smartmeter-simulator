import pandas as pd
import numpy as np

def create_thai_daily_profiles(num_steps=96):
    """
    Generates representative daily load/generation profiles for Thailand.
    Resolution: 15-minute intervals (96 steps per day).
    
    Returns a DataFrame with columns:
    - irregular_residential (p.u.)
    - commercial (p.u.)
    - solar (p.u.)
    - ev_fast_charge (p.u.)
    """
    
    # Use integer index for simpler compatibility with pandapower run_timeseries(range(96))
    idx = range(num_steps)
    df = pd.DataFrame(index=idx)
    
    # helper for approximate time
    # 96 steps. 0 = 00:00, 48 = 12:00
    # Create an array of hours for calculation
    times = np.linspace(0, 24, num_steps, endpoint=False)
    
    # 1. Residential: Double Peak (Morning small, Evening dominant)
    # 06:00-08:00 small peak
    # 19:00-22:00 large peak (AC, lighting)
    # Base load ~ 0.2
    
    res_base = 0.2
    # Morning peak: Gaussian around 7am
    res_morning = 0.3 * np.exp(-0.5 * ((times - 7.0) / 1.5)**2)
    # Evening peak: Gaussian around 20pm (8pm)
    res_evening = 0.8 * np.exp(-0.5 * ((times - 20.0) / 2.5)**2)
    
    df['residential'] = res_base + res_morning + res_evening
    
    # 2. Commercial: Daytime Peak (10:00-16:00)
    # Matches business hours + AC cooling load
    # Base ~ 0.1
    comm_base = 0.1
    # Plateau-ish from 9am to 6pm
    # Using a super-gaussian or sum of gaussians for a blocky shape
    comm_day = 0.9 * np.exp(-0.5 * ((times - 13.0) / 4.0)**4)
    
    df['commercial'] = comm_base + comm_day
    
    # 3. Solar PV: Bell curve
    # 06:00 - 18:00
    # Peak at 12:00
    solar_vals = 1.0 * np.exp(-0.5 * ((times - 12.0) / 2.5)**2) - 0.01
    # Use numpy maximum to clip, ensuring we work with values
    solar_gen = np.maximum(0, solar_vals)
    df['solar'] = solar_gen
    
    # 4. EV Fast Charging (Stochastic/Bursty)
    # Randomly introduce high power draws to simulate 120kW chargers being used.
    # Probability higher during day/evening.
    # For a deterministic profile useful in basic testing, we'll create a "stress test" profile.
    # e.g., coincident charging at peak time (19:00) + some random day charging.
    
    ev_load = np.zeros(num_steps)
    # Add a burst at 19:00 (Step ~ 76)
    # 1.0 p.u. means FULL power of the charger
    
    # Random see for reproducibility
    np.random.seed(42)
    
    for i in range(num_steps):
        # Base probability related to traffic (8am - 8pm high)
        prob = 0.0
        if 8 <= times[i] <= 20: 
            prob = 0.1
        
        # Roll dice
        if np.random.rand() < prob:
            ev_load[i] = np.random.uniform(0.5, 1.0) # 50% to 100% capacity
            
    df['ev_fast_charge'] = ev_load
    
    return df
