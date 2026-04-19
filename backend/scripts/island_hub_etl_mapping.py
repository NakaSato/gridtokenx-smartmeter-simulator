"""
Island Hub ETL Pipeline Mapping

This script demonstrates the "Post-Oil Futures Lab" data structure for the 
Khanom-Samui-Phangan-Tao island microgrid. It maps raw EGAT datasets 
into Node-based structures for ingestion into the simulation engine.
"""

import pandas as pd
import json
import os
from datetime import datetime
from typing import Dict, List, Any, Tuple
import calendar

class IslandHubETL:
    """
    Simulates the transformation of EGAT/Mainland data into Island-specific Node structures.
    """
    
    def __init__(self):
        self.nodes = {
            "NODE_0": {"name": "Khanom Substation", "type": "Reference Bus (EGAT)"},
            "NODE_1": {"name": "Koh Samui Hub", "type": "Primary Hub"},
            "NODE_2": {"name": "Koh Phangan", "type": "Transit Load"},
            "NODE_3": {"name": "Koh Tao", "type": "Constrained Edge"}
        }

    def transform_egat_to_node_data(self, raw_df: pd.DataFrame) -> Dict[str, pd.DataFrame]:
        """
        Splits a unified EGAT transmission dataset into individual island nodes.
        
        Logic:
        - Node 0 (Mainland): Exports via 115 kV Circuit 3.
        - Node 1 (Samui): Hub for BESS and local generation.
        - Node 2 (Phangan): Intermediate load.
        - Node 3 (Tao): Isolated edge with 10MW Diesel backup.
        """
        # Mock transformation logic
        transformed = {}
        
        # Node 1: Samui Hub
        # Includes Samui local load + exports to Phangan
        transformed["NODE_1"] = raw_df[['timestamp']].copy()
        transformed["NODE_1"]['local_load_mw'] = raw_df['total_island_load'] * 0.65
        transformed["NODE_1"]['bess_state_mwh'] = 50.0 # Initial
        
        # Node 2: Phangan
        transformed["NODE_2"] = raw_df[['timestamp']].copy()
        
        def get_phangan_dynamic_load(row):
            ts = row['timestamp']
            T_active, N_active, DAP_d, Load_d = self.calculate_phangan_demographic_load(ts)
            
            # Shape it with the mainland's temporal profile
            profile_scalar = row['total_island_load'] / 40.0
            return Load_d * profile_scalar
            
        transformed["NODE_2"]['local_load_mw'] = raw_df.apply(get_phangan_dynamic_load, axis=1)
        # Node 3: Tao
        transformed["NODE_3"] = raw_df[['timestamp']].copy()
        
        # Apply the 'New Assumption' demographic load model
        def get_tao_dynamic_load(row):
            ts = row['timestamp']
            T_active, DAP_d, Load_d = self.calculate_demographic_load(ts)
            
            # Use the demographic baseline and shape it with the mainland's temporal profile
            profile_scalar = row['total_island_load'] / 40.0 # normalize around average
            return Load_d * profile_scalar
            
        transformed["NODE_3"]['local_load_mw'] = raw_df.apply(get_tao_dynamic_load, axis=1)
        transformed["NODE_3"]['diesel_gen_mw'] = 0.0 # Backup state
        
        return transformed

    def calculate_phangan_demographic_load(self, date: datetime) -> Tuple[float, float, float, float]:
        """
        Calculates the dynamic daily load for Ko Pha-ngan based on its unique
        demographic split and lunar-cycle events.
        """
        # Population Metrics
        R_base = 25_000       # Actual resident population (expats, workforce)
        T_annual = 450_000    # Floating tourist population
        N_active = 5_000      # Estimated daily digital nomad population
        L = 4.0               # Average length of stay
        
        # Energy Intensity Multipliers (MW)
        EI_res = 0.0008       # 0.8 kW per resident
        EI_tourist = 0.002    # 2.0 kW per standard tourist
        EI_nomad = 0.0035     # 3.5 kW per digital nomad (continuous AC, servers)
        
        month = date.month
        D_m = calendar.monthrange(date.year, month)[1]
        
        # Monthly weights (same MOTS baseline)
        monthly_weights = {
            1: 0.12, 2: 0.11, 3: 0.10, 4: 0.10, 5: 0.06, 6: 0.06,
            7: 0.08, 8: 0.09, 9: 0.06, 10: 0.07, 11: 0.05, 12: 0.10
        }
        W_m = monthly_weights.get(month, 0.083)
        
        # Lunar Spike (S_lunar) in MW
        # For simulation simplicity, we assume if date is near April 23 (Full moon in April 2024), apply spike
        is_full_moon_window = date.day in [22, 23, 24]
        S_lunar = 8.0 if is_full_moon_window else 0.0 # 8 MW spike
        
        # Step 1: Active Tourists
        T_active = (T_annual * W_m / D_m) * L
        
        # Step 2: Daily Active Population (DAP)
        DAP_d = R_base + T_active + N_active
        
        # Step 3: Expanded Load Equation
        Load_d = (R_base * EI_res) + (T_active * EI_tourist) + (N_active * EI_nomad) + S_lunar
        
        return T_active, N_active, DAP_d, Load_d

    def calculate_demographic_load(self, date: datetime) -> Tuple[float, float, float]:
        """
        Calculates the dynamic daily load based on demographic 'New Assumptions'.
        Mathematically synthesizes tourist tiers into a single Daily Active Population (DAP).
        """
        # Constants
        T_annual = 400_000  # Total annual tourists
        R_base = 10_000     # Static base population (unregistered workers, locals, expats)
        L = 4.0             # Average length of stay in days
        
        # Energy Intensity (EI) Multipliers in MW
        EI_res = 0.0005     # 0.5 kW per resident
        EI_tourist = 0.0025 # 2.5 kW per tourist (AC 14h/day, desalinated water)
        C_base = 2.0        # 2.0 MW Fixed commercial baseloads (dive compressors, municipal)
        
        month = date.month
        D_m = calendar.monthrange(date.year, month)[1]
        
        # MOTS historical data weighting factors (W_m)
        monthly_weights = {
            1: 0.12, 2: 0.11, 3: 0.10, 4: 0.10, 5: 0.06, 6: 0.06,
            7: 0.08, 8: 0.09, 9: 0.06, 10: 0.07, 11: 0.05, 12: 0.10
        }
        W_m = monthly_weights.get(month, 0.083)
        
        # Step 1: Calculating the Daily Floating Population
        T_active = (T_annual * W_m / D_m) * L
        
        # Step 2: Formulating the Daily Active Population (DAP)
        DAP_d = R_base + T_active
        
        # Step 3: Assigning Energy Intensity (EI) Multipliers
        Load_d = (R_base * EI_res) + (T_active * EI_tourist) + C_base
        
        return T_active, DAP_d, Load_d

    def generate_simulation_profile(self, node_data: Dict[str, pd.DataFrame], output_path: str):
        """
        Converts the Node structure into a simulation-ready profile (smart meter readings).
        """
        profile_data = []
        
        # We simulate 24 hours of data
        for i, row in node_data["NODE_1"].iterrows():
            ts = row['timestamp']
            entry = {"timestamp": ts.isoformat()}
            
            # Map node loads to meter clusters
            # NODE_1 (Samui) -> SAMUI-DIST-001...035
            for m_idx in range(1, 36):
                # Distribute Samui load across meters with some randomness
                entry[f"SAMUI-DIST-{m_idx:03d}"] = row['local_load_mw'] / 35.0 * (1.0 + (i % 10 - 5) / 50.0)
                
            # NODE_2 (Phangan) -> KPG-DIST-301...320
            for m_idx in range(300, 320):
                entry[f"KPG-DIST-{m_idx:03d}"] = node_data["NODE_2"].iloc[i]['local_load_mw'] / 20.0
                
            # NODE_3 (Tao) -> TAO-DIST-501...510
            for m_idx in range(500, 510):
                entry[f"TAO-DIST-{m_idx:03d}"] = node_data["NODE_3"].iloc[i]['local_load_mw'] / 10.0
                
            profile_data.append(entry)
            
        # Save as CSV for the SimulationEngine's ProfileDataSource
        df = pd.DataFrame(profile_data)
        df.to_csv(output_path, index=False)
        print(f"✅ Generated Simulation Profile: {output_path}")

def main():
    etl = IslandHubETL()
    
    # Create mock raw EGAT data
    dates = pd.date_range(start="2024-04-22 00:00", periods=96, freq="15T")
    raw_egat = pd.DataFrame({
        "timestamp": dates,
        "total_island_load": [30.0 + 20.0 * (1.0 - abs(i-48)/48.0) for i in range(96)] # Peak at noon
    })
    
    print("🚀 Running Island Hub ETL Transformation...")
    node_data = etl.transform_egat_to_node_data(raw_egat)
    
    output_dir = "backend/data/profiles"
    os.makedirs(output_dir, exist_ok=True)
    
    etl.generate_simulation_profile(node_data, os.path.join(output_dir, "island_hub_peak_scenario.csv"))
    
    print("\nETL Node Mapping Summary:")
    for node_id, info in etl.nodes.items():
        print(f"- {node_id}: {info['name']} ({info['type']})")

if __name__ == "__main__":
    main()
