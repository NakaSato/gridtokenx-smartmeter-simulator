#!/usr/bin/env python3
"""
Generate Sample Thailand Power Plants Data

Creates realistic power plant data for Thailand including:
- Thermal power plants (EGAT)
- Combined cycle plants
- Gas turbines
- Solar farms
- Hydroelectric plants
- Biomass plants

Similar to Open Infrastructure Map's Thailand power plants data.
"""

import asyncio
import argparse
import random
from typing import List, Dict
from datetime import datetime

# Sample Thailand power plant data based on real facilities
THAILAND_POWER_PLANTS = [
    # === Major Thermal Power Plants (EGAT) ===
    {
        "name": "Bang Pakong Power Plant",
        "type": "combined_cycle",
        "voltage_kv": 500,
        "capacity_mva": 3000,
        "latitude": 13.5394,
        "longitude": 100.9847,
        "region": "Central",
        "province": "Chachoengsao",
        "status": "operational"
    },
    {
        "name": "Map Ta Phut Power Plant",
        "type": "thermal",
        "voltage_kv": 500,
        "capacity_mva": 2750,
        "latitude": 12.6458,
        "longitude": 101.1642,
        "region": "Eastern",
        "province": "Rayong",
        "status": "operational"
    },
    {
        "name": "South Bangkok Power Plant",
        "type": "combined_cycle",
        "voltage_kv": 230,
        "capacity_mva": 1750,
        "latitude": 13.6578,
        "longitude": 100.5236,
        "region": "Central",
        "province": "Samut Prakan",
        "status": "operational"
    },
    {
        "name": "North Bangkok Power Plant",
        "type": "combined_cycle",
        "voltage_kv": 230,
        "capacity_mva": 1400,
        "latitude": 13.9583,
        "longitude": 100.6167,
        "region": "Central",
        "province": "Pathum Thani",
        "status": "operational"
    },
    {
        "name": "Ratchaburi Power Plant",
        "type": "thermal",
        "voltage_kv": 500,
        "capacity_mva": 2200,
        "latitude": 13.5269,
        "longitude": 99.7856,
        "region": "Central",
        "province": "Ratchaburi",
        "status": "operational"
    },
    
    # === Gas Turbine Plants ===
    {
        "name": "Chana Power Plant",
        "type": "gas_turbine",
        "voltage_kv": 230,
        "capacity_mva": 800,
        "latitude": 7.1167,
        "longitude": 100.6833,
        "region": "Southern",
        "province": "Songkhla",
        "status": "operational"
    },
    {
        "name": "Lan Krabue Power Plant",
        "type": "gas_turbine",
        "voltage_kv": 115,
        "capacity_mva": 600,
        "latitude": 16.8167,
        "longitude": 99.1833,
        "region": "Northern",
        "province": "Kamphaeng Phet",
        "status": "operational"
    },
    
    # === Hydroelectric Plants ===
    {
        "name": "Bhumibol Dam Power Plant",
        "type": "hydro",
        "voltage_kv": 230,
        "capacity_mva": 500,
        "latitude": 17.2167,
        "longitude": 98.9833,
        "region": "Northern",
        "province": "Tak",
        "status": "operational"
    },
    {
        "name": "Sirikit Dam Power Plant",
        "type": "hydro",
        "voltage_kv": 230,
        "capacity_mva": 450,
        "latitude": 18.2833,
        "longitude": 100.7167,
        "region": "Northern",
        "province": "Uttaradit",
        "status": "operational"
    },
    {
        "name": "Srinagarind Dam Power Plant",
        "type": "hydro",
        "voltage_kv": 230,
        "capacity_mva": 300,
        "latitude": 14.3167,
        "longitude": 99.2833,
        "region": "Central",
        "province": "Kanchanaburi",
        "status": "operational"
    },
    {
        "name": "Vajiralongkorn Dam Power Plant",
        "type": "hydro",
        "voltage_kv": 115,
        "capacity_mva": 240,
        "latitude": 14.7667,
        "longitude": 99.1833,
        "region": "Central",
        "province": "Kanchanaburi",
        "status": "operational"
    },
    
    # === Solar Farms (Large-Scale) ===
    {
        "name": "Lopburi Solar Farm",
        "type": "solar",
        "voltage_kv": 115,
        "capacity_mva": 73,
        "latitude": 14.8069,
        "longitude": 100.6167,
        "region": "Central",
        "province": "Lopburi",
        "status": "operational"
    },
    {
        "name": "Nakhon Ratchasima Solar Park",
        "type": "solar",
        "voltage_kv": 115,
        "capacity_mva": 84,
        "latitude": 14.9769,
        "longitude": 102.0978,
        "region": "Northeastern",
        "province": "Nakhon Ratchasima",
        "status": "operational"
    },
    {
        "name": "Udon Thani Solar Plant",
        "type": "solar",
        "voltage_kv": 115,
        "capacity_mva": 60,
        "latitude": 17.4139,
        "longitude": 102.7878,
        "region": "Northeastern",
        "province": "Udon Thani",
        "status": "operational"
    },
    {
        "name": "Khon Kaen Solar Farm",
        "type": "solar",
        "voltage_kv": 115,
        "capacity_mva": 55,
        "latitude": 16.4322,
        "longitude": 102.8236,
        "region": "Northeastern",
        "province": "Khon Kaen",
        "status": "operational"
    },
    {
        "name": "Suphan Buri Solar Power",
        "type": "solar",
        "voltage_kv": 115,
        "capacity_mva": 68,
        "latitude": 14.4745,
        "longitude": 100.1177,
        "region": "Central",
        "province": "Suphan Buri",
        "status": "operational"
    },
    {
        "name": "Phitsanulok Solar Farm",
        "type": "solar",
        "voltage_kv": 115,
        "capacity_mva": 50,
        "latitude": 16.8211,
        "longitude": 100.2658,
        "region": "Northern",
        "province": "Phitsanulok",
        "status": "operational"
    },
    {
        "name": "Nakhon Sawan Solar Plant",
        "type": "solar",
        "voltage_kv": 115,
        "capacity_mva": 45,
        "latitude": 15.7047,
        "longitude": 100.1372,
        "region": "Central",
        "province": "Nakhon Sawan",
        "status": "operational"
    },
    {
        "name": "Ubon Ratchathani Solar Farm",
        "type": "solar",
        "voltage_kv": 115,
        "capacity_mva": 52,
        "latitude": 15.2286,
        "longitude": 104.8569,
        "region": "Northeastern",
        "province": "Ubon Ratchathani",
        "status": "operational"
    },
    {
        "name": "Kanchanaburi Solar Power",
        "type": "solar",
        "voltage_kv": 115,
        "capacity_mva": 48,
        "latitude": 14.0022,
        "longitude": 99.5453,
        "region": "Central",
        "province": "Kanchanaburi",
        "status": "operational"
    },
    {
        "name": "Surin Solar Farm",
        "type": "solar",
        "voltage_kv": 115,
        "capacity_mva": 42,
        "latitude": 14.8828,
        "longitude": 103.4936,
        "region": "Northeastern",
        "province": "Surin",
        "status": "operational"
    },
    {
        "name": "Buriram Solar Plant",
        "type": "solar",
        "voltage_kv": 115,
        "capacity_mva": 38,
        "latitude": 15.0000,
        "longitude": 103.1028,
        "region": "Northeastern",
        "province": "Buriram",
        "status": "operational"
    },
    {
        "name": "Sisaket Solar Farm",
        "type": "solar",
        "voltage_kv": 115,
        "capacity_mva": 35,
        "latitude": 15.1186,
        "longitude": 104.3222,
        "region": "Northeastern",
        "province": "Sisaket",
        "status": "operational"
    },
    {
        "name": "Nong Khai Solar Power",
        "type": "solar",
        "voltage_kv": 115,
        "capacity_mva": 30,
        "latitude": 17.8783,
        "longitude": 102.7419,
        "region": "Northeastern",
        "province": "Nong Khai",
        "status": "operational"
    },
    {
        "name": "Phetchabun Solar Farm",
        "type": "solar",
        "voltage_kv": 115,
        "capacity_mva": 40,
        "latitude": 16.4167,
        "longitude": 101.1667,
        "region": "Northern",
        "province": "Phetchabun",
        "status": "operational"
    },
    {
        "name": "Prachuap Khiri Khan Solar",
        "type": "solar",
        "voltage_kv": 115,
        "capacity_mva": 36,
        "latitude": 11.8103,
        "longitude": 99.7972,
        "region": "Southern",
        "province": "Prachuap Khiri Khan",
        "status": "operational"
    },
    
    # === Biomass Plants ===
    {
        "name": "Phrae Biomass Power Plant",
        "type": "biomass",
        "voltage_kv": 22,
        "capacity_mva": 25,
        "latitude": 18.1447,
        "longitude": 100.1403,
        "region": "Northern",
        "province": "Phrae",
        "status": "operational"
    },
    {
        "name": "Surat Thani Biomass Plant",
        "type": "biomass",
        "voltage_kv": 22,
        "capacity_mva": 20,
        "latitude": 9.1386,
        "longitude": 99.3331,
        "region": "Southern",
        "province": "Surat Thani",
        "status": "operational"
    },
    
    # === Wind Farms ===
   
    {
        "name": "Nakhon Ratchasima Wind Farm",
        "type": "wind",
        "voltage_kv": 22,
        "capacity_mva": 30,
        "latitude": 14.5708,
        "longitude": 101.9758,
        "region": "Northeastern",
        "province": "Nakhon Ratchasima",
        "status": "operational"
    },
    {
        "name": "Phetchabun Wind Power",
        "type": "wind",
        "voltage_kv": 22,
        "capacity_mva": 25,
        "latitude": 16.4167,
        "longitude": 101.1667,
        "region": "Northern",
        "province": "Phetchabun",
        "status": "operational"
    },
]


async def generate_power_plants(repo, plants_data: List[Dict]):
    """Insert power plants into database as substations"""
    
    from sqlalchemy import text
    
    for plant in plants_data:
        # First check if plant already exists
        check_query = text("""
            SELECT id FROM grid.substations WHERE name = :name
        """)
        result = await repo.session.execute(check_query, {"name": plant["name"]})
        exists = result.fetchone()
        
        if exists:
            # Update existing
            query = text("""
                UPDATE grid.substations SET
                    type = :type,
                    voltage_level_kv = :voltage_level_kv,
                    capacity_mva = :capacity_mva,
                    province = :province,
                    district = :district,
                    location = ST_SetSRID(ST_MakePoint(:longitude, :latitude), 4326),
                    status = :status,
                    address = :address,
                    updated_at = NOW()
                WHERE name = :name
            """)
        else:
            # Insert new
            query = text("""
                INSERT INTO grid.substations (
                    name,
                    type,
                    voltage_level_kv,
                    capacity_mva,
                    province,
                    district,
                    location,
                    status,
                    created_at,
                    address
                ) VALUES (
                    :name,
                    :type,
                    :voltage_level_kv,
                    :capacity_mva,
                    :province,
                    :district,
                    ST_SetSRID(ST_MakePoint(:longitude, :latitude), 4326),
                    :status,
                    NOW(),
                    :address
                )
            """)
        
        await repo.session.execute(query, {
            "name": plant["name"],
            "type": plant["type"],
            "voltage_level_kv": plant["voltage_kv"],
            "capacity_mva": plant["capacity_mva"],
            "province": plant["province"],
            "district": plant["region"],
            "longitude": plant["longitude"],
            "latitude": plant["latitude"],
            "status": plant["status"],
            "address": f"{plant['region']} Region, {plant['province']}, Thailand"
        })
    
    await repo.session.commit()


async def main():
    parser = argparse.ArgumentParser(description='Generate Thailand power plants data')
    parser.add_argument('--all', action='store_true', help='Generate all power plants')
    parser.add_argument('--type', choices=['thermal', 'solar', 'hydro', 'wind', 'biomass', 'all'],
                       default='all', help='Filter by plant type')
    args = parser.parse_args()
    
    # Import repository
    try:
        from smart_meter_simulator.database.repository import PostGISRepository
        from smart_meter_simulator.config import get_config
    except ImportError:
        print("Error: Smart Meter Simulator package not found")
        return
    
    # Get configuration
    config = get_config()
    db_url = config.gis_database_url
    
    if not db_url:
        print("Error: GIS_DATABASE_URL not configured")
        return
    
    # Convert to asyncpg format if needed
    if db_url.startswith("postgresql://"):
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    
    print(f"Connecting to GIS database: {db_url.split('@')[-1]}")

    # Create repository
    repo = PostGISRepository(db_url)

    # Filter plants
    if args.type != 'all':
        plants_to_generate = [p for p in THAILAND_POWER_PLANTS if p['type'] == args.type]
    else:
        plants_to_generate = THAILAND_POWER_PLANTS

    print(f"\n🇹🇭 Generating {len(plants_to_generate)} Thailand power plants...")
    print("=" * 60)

    # Generate plants using async context manager
    async for session in repo.get_session():
        repo.session = session
        await generate_power_plants(repo, plants_to_generate)
        break
    
    # Print summary
    print("\n✅ Power plants generated successfully!")
    print("\nSummary by type:")
    type_counts = {}
    capacity_by_type = {}
    for plant in plants_to_generate:
        ptype = plant['type']
        type_counts[ptype] = type_counts.get(ptype, 0) + 1
        capacity_by_type[ptype] = capacity_by_type.get(ptype, 0) + plant['capacity_mva']
    
    for ptype, count in type_counts.items():
        print(f"  {ptype.capitalize():15} {count:3} plants, {capacity_by_type[ptype]:6.0f} MVA")
    
    total_capacity = sum(capacity_by_type.values())
    print(f"\n  {'Total':15} {len(plants_to_generate):3} plants, {total_capacity:6.0f} MVA")
    
    print("\n📊 View statistics at:")
    print("   http://localhost:8082/api/thailand/power-plants")
    print("   http://localhost:8082/api/thailand/power-plants/statistics")


if __name__ == "__main__":
    asyncio.run(main())
