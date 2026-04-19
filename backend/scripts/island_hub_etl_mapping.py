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
        transformed["NODE_2"]['local_load_mw'] = raw_df['total_island_load'] * 0.25
        
        # Node 3: Tao
        transformed["NODE_3"] = raw_df[['timestamp']].copy()
        transformed["NODE_3"]['local_load_mw'] = raw_df['total_island_load'] * 0.10
        transformed["NODE_3"]['diesel_gen_mw'] = 0.0 # Backup state
        
        return transformed

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
