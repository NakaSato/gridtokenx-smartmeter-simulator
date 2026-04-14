"""
Load Thailand power plant GeoJSON data and integrate with GridTokenX simulator.

Creates generator/solar/battery configurations based on real power plant locations
and capacities from Thai energy infrastructure data.

Usage:
    uv run python scripts/load_thailand_power_plants.py --input th_plants.geojson
    uv run python scripts/load_thailand_power_plants.py --input th_plants.geojson --mode meters
"""

import json
import geopandas as gpd
import pandas as pd
import argparse
import os
from pathlib import Path


def load_power_plants(geojson_file: str) -> gpd.GeoDataFrame:
    """Load Thailand power plant GeoJSON data."""
    print(f"Loading power plants from {geojson_file}...")
    
    gdf = gpd.read_file(geojson_file)
    
    print(f"Loaded {len(gdf)} power plant entries")
    print(f"\nColumns: {list(gdf.columns)}")
    
    return gdf


def analyze_plants(gdf: gpd.GeoDataFrame):
    """Analyze power plant distribution by type, status, capacity."""
    print("\n" + "="*60)
    print("THAILAND POWER PLANT ANALYSIS")
    print("="*60)
    
    # By type
    print("\n📊 Plant Types:")
    type_counts = gdf["Type"].value_counts()
    for plant_type, count in type_counts.items():
        print(f"  {plant_type:15s}: {count:4d} plants")
    
    # By status
    print("\n📈 Status:")
    status_counts = gdf["Status"].value_counts()
    for status, count in status_counts.items():
        print(f"  {status:15s}: {count:4d} plants")
    
    # By capacity
    if "Capacity (MW)" in gdf.columns:
        print("\n⚡ Capacity by Type:")
        operating = gdf[gdf["Status"] == "operating"].copy()
        capacity_by_type = operating.groupby("Type")["Capacity (MW)"].sum().sort_values(ascending=False)
        
        total_capacity = capacity_by_type.sum()
        for plant_type, capacity in capacity_by_type.items():
            pct = capacity / total_capacity * 100
            print(f"  {plant_type:15s}: {capacity:8.1f} MW ({pct:5.1f}%)")
        
        print(f"\n  {'TOTAL':15s}: {total_capacity:8.1f} MW")
    
    # By fuel (for oil/gas plants)
    if "Fuel" in gdf.columns:
        oil_gas = gdf[gdf["Type"] == "oil/gas"]
        if len(oil_gas) > 0 and oil_gas["Fuel"].notna().any():
            print("\n🔥 Oil/Gas Fuel Types:")
            fuel_counts = oil_gas["Fuel"].value_counts().head(10)
            for fuel, count in fuel_counts.items():
                print(f"  {fuel:60s}: {count}")


def create_simulator_meters(gdf: gpd.GeoDataFrame, output_file: str, max_plants: int = 50):
    """
    Create smart meter configurations based on real power plants.
    
    Maps power plants to simulator meter types:
    - Solar farms → Solar Prosumer meters
    - Oil/gas plants → Grid Consumer (with backup generation)
    - Wind farms → Hybrid Prosumer
    - Hydro → Battery Storage (grid stabilization)
    """
    print(f"\n🔧 Creating simulator meters from {len(gdf)} power plants...")
    
    # Filter operating plants only
    operating = gdf[gdf["Status"] == "operating"].copy()
    
    # Remove duplicates by plant name (keep largest capacity)
    if "Plant / Project name" in operating.columns:
        operating = operating.sort_values("Capacity (MW)", ascending=False)
        operating = operating.drop_duplicates(subset=["Plant / Project name"], keep="first")
    
    # Limit to max_plants
    if len(operating) > max_plants:
        operating = operating.head(max_plants)
    
    print(f"Using {len(operating)} unique operating plants")
    
    # Map plant types to meter types
    meter_mapping = {
        "solar": "solar_prosumer",
        "wind": "hybrid_prosumer",
        "hydro": "battery_storage",
        "oil/gas": "grid_consumer",
        "coal": "grid_consumer",
        "bioenergy": "hybrid_prosumer",
    }
    
    meters = []
    
    for idx, plant in operating.iterrows():
        plant_type = plant.get("Type", "unknown").lower()
        meter_type = meter_mapping.get(plant_type, "grid_consumer")
        
        capacity_mw = plant.get("Capacity (MW)", 0)
        capacity_kw = capacity_mw * 1000  # Convert MW to kW
        
        # Scale capacity for simulator (real plants are too large)
        scale_factor = 0.001  # 1 MW plant → 1 kW simulated
        sim_capacity = max(capacity_kw * scale_factor, 1.0)  # Minimum 1 kW
        
        meter_config = {
            "meter_id": f"TH_{plant_type.upper()[:3]}_{idx:04d}",
            "meter_type": meter_type,
            "location": {
                "latitude": plant.geometry.y,
                "longitude": plant.geometry.x,
            },
            "plant_info": {
                "name": plant.get("Plant / Project name", "Unknown"),
                "type": plant_type,
                "capacity_mw": capacity_mw,
                "start_year": plant.get("Start year", None),
                "technology": plant.get("Technology", None),
                "fuel": plant.get("Fuel", None),
            },
            "simulation_params": {
                "base_generation_kw": sim_capacity,
                "base_consumption_kw": sim_capacity * 0.3,  # 30% self-consumption
                "battery_capacity_kwh": sim_capacity * 2 if meter_type == "battery_storage" else sim_capacity,
            },
            "grid_connection": {
                "voltage_level": "transmission" if capacity_mw > 100 else "distribution",
                "operator": "EGAT" if capacity_mw > 50 else "PEA/MEA",
            }
        }
        
        meters.append(meter_config)
    
    # Save to JSON
    os.makedirs(os.path.dirname(os.path.abspath(output_file)), exist_ok=True)
    with open(output_file, "w") as f:
        json.dump(meters, f, indent=2)
    
    print(f"\n✅ Created {len(meters)} meter configurations")
    print(f"📁 Saved to {output_file}")
    
    # Summary
    print("\n📊 Meter Type Distribution:")
    meter_types = pd.DataFrame(meters)
    type_counts = meter_types["meter_type"].value_counts()
    for mtype, count in type_counts.items():
        print(f"  {mtype:25s}: {count:4d} meters")
    
    return meters


def create_pandapower_generators(gdf: gpd.GeoDataFrame, output_file: str):
    """
    Create pandapower generator configurations from power plants.
    
    Output: JSON file with generator specs for pandapower network
    """
    print(f"\n⚡ Creating pandapower generators from {len(gdf)} power plants...")
    
    operating = gdf[gdf["Status"] == "operating"].copy()
    
    # Group by plant name (handle multiple entries per plant)
    if "Plant / Project name" in operating.columns:
        plants = operating.groupby("Plant / Project name").agg({
            "Capacity (MW)": "sum",
            "geometry": "first",
            "Type": "first",
            "Technology": "first",
            "Fuel": "first",
            "Start year": "min",
        }).reset_index()
    else:
        plants = operating
    
    generators = []
    
    for idx, plant in plants.iterrows():
        capacity_mw = plant.get("Capacity (MW)", 0)
        plant_type = plant.get("Type", "unknown")
        
        # Pandapower generator spec
        gen_config = {
            "name": plant.get("Plant / Project name", f"plant_{idx}"),
            "type": plant_type,
            "location": {
                "latitude": plant.geometry.y,
                "longitude": plant.geometry.x,
            },
            "electrical": {
                "p_mw": capacity_mw,
                "vm_pu": 1.0,
                "slack": False,
                "controllable": True,
            },
            "metadata": {
                "technology": plant.get("Technology", None),
                "fuel": plant.get("Fuel", None),
                "start_year": plant.get("Start year", None),
            }
        }
        
        generators.append(gen_config)
    
    # Save
    os.makedirs(os.path.dirname(os.path.abspath(output_file)), exist_ok=True)
    with open(output_file, "w") as f:
        json.dump(generators, f, indent=2)
    
    print(f"✅ Created {len(generators)} generator configurations")
    print(f"📁 Saved to {output_file}")
    
    # Summary by type
    print("\n⚡ Generator Capacity by Type:")
    gen_df = pd.DataFrame(generators)
    for gen_type in gen_df["type"].unique():
        type_gens = gen_df[gen_df["type"] == gen_type]
        total_cap = type_gens["electrical"].apply(lambda x: x["p_mw"]).sum()
        count = len(type_gens)
        print(f"  {gen_type:15s}: {total_cap:8.1f} MW ({count} plants)")
    
    return generators


def main():
    parser = argparse.ArgumentParser(
        description="Load Thailand Power Plant Data for GridTokenX Simulator"
    )
    parser.add_argument("--input", type=str, required=True, help="Input GeoJSON file")
    parser.add_argument(
        "--mode",
        choices=["analyze", "meters", "generators", "all"],
        default="all",
        help="Operation mode",
    )
    parser.add_argument("--max-plants", type=int, default=50, help="Max plants for meter generation")
    parser.add_argument(
        "--output-meters",
        type=str,
        default="data/thailand_simulator_meters.json",
        help="Output meter config file",
    )
    parser.add_argument(
        "--output-generators",
        type=str,
        default="data/thailand_pandapower_generators.json",
        help="Output generator config file",
    )
    
    args = parser.parse_args()
    
    # Load data
    gdf = load_power_plants(args.input)
    
    # Analyze
    if args.mode in ["analyze", "all"]:
        analyze_plants(gdf)
    
    # Create simulator meters
    if args.mode in ["meters", "all"]:
        create_simulator_meters(gdf, args.output_meters, args.max_plants)
    
    # Create pandapower generators
    if args.mode in ["generators", "all"]:
        create_pandapower_generators(gdf, args.output_generators)
    
    print("\n" + "="*60)
    print("✅ DONE!")
    print("="*60)


if __name__ == "__main__":
    main()
