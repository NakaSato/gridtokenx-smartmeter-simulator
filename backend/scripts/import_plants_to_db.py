"""
Import Thailand Power Plants into PostGIS Database

Loads GeoJSON power plant data into the grid.power_plants table
via the PostGIS repository.

Usage:
    # From file path
    uv run python scripts/import_plants_to_db.py data/thailand_power_plants.geojson
    
    # With custom database URL
    DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/gridtokenx \
    uv run python scripts/import_plants_to_db.py data/thailand_power_plants.geojson
"""

import json
import asyncio
import logging
import sys
from pathlib import Path
from typing import Dict, Any, List

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from smart_meter_simulator.database.repository import PostGISRepository
from smart_meter_simulator.config import get_config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def geojson_to_plant_data(geojson_file: str) -> List[Dict[str, Any]]:
    """
    Convert GeoJSON file to list of plant data dictionaries.
    
    Handles the Thailand power plant GeoJSON format:
    {
      "type": "FeatureCollection",
      "features": [{
        "type": "Feature",
        "geometry": {"type": "Point", "coordinates": [lon, lat]},
        "properties": {
          "Type": "hydropower",
          "Plant / Project name": "Bhumibol",
          "Capacity (MW)": 779.0,
          ...
        }
      }]
    }
    """
    logger.info(f"Loading GeoJSON from {geojson_file}")
    
    with open(geojson_file, 'r') as f:
        geojson = json.load(f)
    
    if geojson.get('type') != 'FeatureCollection':
        raise ValueError("Expected GeoJSON FeatureCollection")
    
    plants_data = []
    
    for idx, feature in enumerate(geojson.get('features', [])):
        props = feature.get('properties', {})
        coords = feature.get('geometry', {}).get('coordinates', [])
        
        if len(coords) < 2:
            logger.warning(f"Feature {idx} has invalid coordinates, skipping")
            continue
        
        longitude = coords[0]
        latitude = coords[1]
        
        # Parse plant type
        plant_type_raw = props.get('Type', 'unknown').lower()
        
        # Generate unique plant_id
        type_prefix = plant_type_raw.replace(' ', '_').replace('/', '_').upper()[:10]
        plant_id = f"TH_{type_prefix}_{idx:04d}"
        
        # Parse capacity
        capacity_mw = props.get('Capacity (MW)', 0)
        if capacity_mw == 0:
            logger.warning(f"Plant {plant_id} has 0 capacity")
        
        # Determine grid connection voltage based on capacity
        if capacity_mw > 100:
            voltage_level_kv = 500 if capacity_mw > 500 else 230
            grid_connection = "transmission"
        elif capacity_mw > 10:
            voltage_level_kv = 115
            grid_connection = "transmission"
        else:
            voltage_level_kv = 22
            grid_connection = "distribution"
        
        # Parse fuel type
        fuel_raw = props.get('Fuel')
        fuel_type = None
        if fuel_raw:
            fuel_type = fuel_raw.split(':')[0].strip() if ':' in fuel_raw else fuel_raw
        
        # Determine region from coordinates (simplified)
        region = estimate_region(latitude, longitude)
        
        plant_data = {
            'plant_id': plant_id,
            'name': props.get('Plant / Project name', f"Plant_{idx}"),
            'plant_type': plant_type_raw,
            'fuel_type': fuel_type,
            'technology': props.get('Technology'),
            'capacity_mw': capacity_mw,
            'units': 1,
            'status': props.get('Status', 'operating'),
            'start_year': props.get('Start year'),
            'operator': 'EGAT',
            'latitude': latitude,
            'longitude': longitude,
            'province': None,  # Could be geocoded later
            'region': region,
            'location_accuracy': props.get('Location accuracy', 'exact'),
            'voltage_level_kv': voltage_level_kv,
            'grid_connection_type': grid_connection,
            'carbon_intensity_gco2_kwh': get_carbon_intensity(plant_type_raw, fuel_type),
            'source': 'GeoJSON Import - Global Power Plant Tracker',
            'osm_id': None,
        }
        
        plants_data.append(plant_data)
    
    logger.info(f"Parsed {len(plants_data)} plants from GeoJSON")
    return plants_data


def estimate_region(lat: float, lon: float) -> str:
    """Estimate Thai region from coordinates (simplified)"""
    if lat > 16.5:
        return "north"
    elif lat > 14.5 and lon < 101:
        return "central"
    elif lat > 13.5 and lat <= 14.5 and lon >= 100.3 and lon <= 100.9:
        return "bangkok"
    elif lon >= 101:
        return "east"
    elif lat > 14 and lon < 101:
        return "central"
    elif lat <= 14 and lon < 101:
        return "south"
    else:
        return "northeast"


def get_carbon_intensity(plant_type: str, fuel_type: str = None) -> float:
    """Get carbon intensity in g CO2/kWh"""
    intensity_map = {
        'hydropower': 0,
        'solar': 0,
        'wind': 0,
        'bioenergy': 20,
        'oil/gas': 490,
        'coal': 820,
    }
    
    base = intensity_map.get(plant_type, 400)
    
    # Refine based on fuel type
    if fuel_type:
        if 'natural gas' in fuel_type.lower():
            base = 490
        elif 'lignite' in fuel_type.lower():
            base = 1000
        elif 'bituminous' in fuel_type.lower():
            base = 820
    
    return base


async def import_to_database(geojson_file: str, database_url: str = None):
    """Import power plants from GeoJSON to PostGIS database"""
    
    # Get database URL
    if not database_url:
        try:
            config = get_config()
            database_url = config.database_url
            logger.info(f"Using database URL from config: {database_url.split('@')[1]}")
        except Exception:
            database_url = "postgresql+asyncpg://gridtokenx:gridtokenx_password@localhost:5432/gridtokenx"
            logger.info(f"Using default database URL")
    
    # Parse GeoJSON
    plants_data = geojson_to_plant_data(geojson_file)
    
    if not plants_data:
        logger.error("No plants found in GeoJSON file")
        return
    
    # Initialize repository
    repo = PostGISRepository(database_url)
    
    # Check connection
    connected = await repo.check_connection()
    if not connected:
        logger.error("Cannot connect to database")
        return
    
    logger.info("Connected to PostGIS database")
    
    # Check if table exists
    try:
        stats = await repo.get_power_plant_stats()
        logger.info(f"Existing plants in database: {stats['total']['count']}")
    except Exception:
        logger.warning("power_plants table may not exist. Run migration 003_power_plants.sql first")
        raise
    
    # Batch import
    logger.info(f"Importing {len(plants_data)} plants...")
    result = await repo.create_power_plants_batch(plants_data)
    
    # Summary
    logger.info("="*60)
    logger.info("IMPORT SUMMARY")
    logger.info("="*60)
    logger.info(f"✅ Created: {result['created']} plants")
    logger.info(f"❌ Errors: {result['errors']}")
    
    if result['error_details']:
        logger.warning("Error details:")
        for error in result['error_details'][:5]:
            logger.warning(f"  - {error}")
    
    # Show stats after import
    try:
        stats = await repo.get_power_plant_stats()
        logger.info(f"\nDatabase now contains:")
        logger.info(f"  Total: {stats['total']['count']} plants, {stats['total']['capacity_mw']:.1f} MW")
        logger.info(f"  Renewable: {stats['renewable']['count']} plants, {stats['renewable']['capacity_mw']:.1f} MW ({stats['renewable']['percentage']}%)")
        
        logger.info(f"\nBy type:")
        for plant_type, type_stats in stats['by_type'].items():
            logger.info(f"  {plant_type:15s}: {type_stats['plant_count']:4d} plants, {type_stats['total_capacity_mw']:10.1f} MW")
    except Exception as e:
        logger.error(f"Failed to fetch stats: {e}")
    
    logger.info("="*60)


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Import Thailand Power Plants to PostGIS")
    parser.add_argument("geojson_file", help="Path to GeoJSON file")
    parser.add_argument("--database-url", help="Database URL (overrides config)")
    
    args = parser.parse_args()
    
    # Check file exists
    if not Path(args.geojson_file).exists():
        logger.error(f"File not found: {args.geojson_file}")
        sys.exit(1)
    
    # Run import
    asyncio.run(import_to_database(args.geojson_file, args.database_url))


if __name__ == "__main__":
    main()
