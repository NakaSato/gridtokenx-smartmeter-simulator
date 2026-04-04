#!/usr/bin/env python3
"""
Thai Grid Data Importer

Import grid topology data from GeoJSON files or generate sample data
for the PostGIS database.

Usage:
    # Import from GeoJSON file
    uv run python examples/import_grid_data.py --input data/bangkok_urban.geojson
    
    # Generate sample data for Bangkok
    uv run python examples/import_grid_data.py --generate --region bangkok --meters 500
    
    # Generate sample data for Central Thailand
    uv run python examples/import_grid_data.py --generate --region central --meters 1000
    
    # Import and validate
    uv run python examples/import_grid_data.py --input data/grid.geojson --validate
"""

import asyncio
import argparse
import json
import logging
import random
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from smart_meter_simulator.database.repository import PostGISRepository
from smart_meter_simulator.database.models import Substation, Transformer, PowerLine, Meter

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ThaiGridImporter:
    """
    Import Thai grid data from GeoJSON files or generate sample data.
    
    Supports:
    - Import from GeoJSON FeatureCollection
    - Generate realistic Thai grid topology
    - Validate data integrity
    - Batch insert for performance
    """
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.repo = PostGISRepository(database_url)
        self.stats = {
            'substations': 0,
            'transformers': 0,
            'power_lines': 0,
            'meters': 0,
            'errors': 0
        }
    
    async def initialize(self):
        """Initialize database connection"""
        logger.info("Connecting to database...")
        connected = await self.repo.check_connection()
        if not connected:
            raise ConnectionError("Failed to connect to database")
        
        version = await self.repo.get_postgis_version()
        logger.info(f"Connected to PostGIS: {version}")
    
    async def close(self):
        """Close database connection"""
        await self.repo.engine.dispose()
        logger.info("Database connection closed")
    
    # =========================================================================
    # Import from GeoJSON
    # =========================================================================
    
    async def import_geojson(self, filepath: str, validate: bool = True) -> Dict[str, int]:
        """
        Import grid data from GeoJSON file.
        
        Args:
            filepath: Path to GeoJSON file
            validate: Validate data before import
        
        Returns:
            Dictionary with import statistics
        """
        logger.info(f"Importing GeoJSON from: {filepath}")
        
        # Load GeoJSON
        with open(filepath, 'r') as f:
            geojson = json.load(f)
        
        if geojson.get('type') != 'FeatureCollection':
            raise ValueError("Invalid GeoJSON: Expected FeatureCollection")
        
        features = geojson.get('features', [])
        logger.info(f"Found {len(features)} features")
        
        # Group features by type
        by_type = {}
        for feature in features:
            ftype = feature['properties'].get('type', 'unknown')
            if ftype not in by_type:
                by_type[ftype] = []
            by_type[ftype].append(feature)
        
        # Import each type
        if 'substation' in by_type:
            await self._import_substations_geojson(by_type['substation'], validate)
        
        if 'line' in by_type:
            await self._import_lines_geojson(by_type['line'], validate)
        
        if 'transformer' in by_type:
            await self._import_transformers_geojson(by_type['transformer'], validate)
        
        if 'meter' in by_type:
            await self._import_meters_geojson(by_type['meter'], validate)
        
        logger.info(f"Import complete: {self.stats}")
        return self.stats
    
    async def _import_substations_geojson(self, features: List[Dict], validate: bool):
        """Import substations from GeoJSON"""
        logger.info(f"Importing {len(features)} substations")
        
        for i, feature in enumerate(features):
            try:
                props = feature['properties']
                coords = feature['geometry']['coordinates']
                
                if validate:
                    self._validate_substation(props)
                
                await self.repo.create_substation(
                    name=props.get('name', f'Substation_{i}'),
                    code=props.get('code', f'SUB_{i:04d}'),
                    voltage_level_kv=props.get('voltage_level_kv', 22.0),
                    operator=props.get('operator', 'MEA'),
                    type=props.get('type', 'distribution'),
                    capacity_mva=props.get('capacity_mva'),
                    longitude=coords[0],
                    latitude=coords[1],
                    province=props.get('province', 'Bangkok'),
                    status=props.get('status', 'in_service')
                )
                
                self.stats['substations'] += 1
                
                if (i + 1) % 100 == 0:
                    logger.info(f"  Imported {i + 1}/{len(features)} substations")
            
            except Exception as e:
                logger.error(f"Error importing substation {i}: {e}")
                self.stats['errors'] += 1
    
    async def _import_lines_geojson(self, features: List[Dict], validate: bool):
        """Import power lines from GeoJSON"""
        logger.info(f"Importing {len(features)} power lines")
        
        for i, feature in enumerate(features):
            try:
                props = feature['properties']
                coords = feature['geometry']['coordinates']
                
                if validate:
                    self._validate_line(props)
                
                await self.repo.create_power_line(
                    code=props.get('code', f'LINE_{i:04d}'),
                    voltage_level_kv=props.get('voltage_level_kv', 22.0),
                    coordinates=[(c[0], c[1]) for c in coords],
                    line_type=props.get('line_type', 'overhead'),
                    conductor_type=props.get('conductor_type'),
                    status=props.get('status', 'in_service')
                )
                
                self.stats['power_lines'] += 1
                
                if (i + 1) % 100 == 0:
                    logger.info(f"  Imported {i + 1}/{len(features)} lines")
            
            except Exception as e:
                logger.error(f"Error importing line {i}: {e}")
                self.stats['errors'] += 1
    
    async def _import_transformers_geojson(self, features: List[Dict], validate: bool):
        """Import transformers from GeoJSON"""
        logger.info(f"Importing {len(features)} transformers")
        
        for i, feature in enumerate(features):
            try:
                props = feature['properties']
                coords = feature['geometry']['coordinates']
                
                if validate:
                    self._validate_transformer(props)
                
                await self.repo.create_transformer(
                    code=props.get('code', f'TXN_{i:04d}'),
                    voltage_primary_kv=props.get('voltage_primary_kv', 22.0),
                    voltage_secondary_kv=props.get('voltage_secondary_kv', 0.4),
                    capacity_kva=props.get('capacity_kva', 500),
                    longitude=coords[0],
                    latitude=coords[1],
                    status=props.get('status', 'in_service')
                )
                
                self.stats['transformers'] += 1
                
                if (i + 1) % 100 == 0:
                    logger.info(f"  Imported {i + 1}/{len(features)} transformers")
            
            except Exception as e:
                logger.error(f"Error importing transformer {i}: {e}")
                self.stats['errors'] += 1
    
    async def _import_meters_geojson(self, features: List[Dict], validate: bool):
        """Import meters from GeoJSON"""
        logger.info(f"Importing {len(features)} meters")
        
        for i, feature in enumerate(features):
            try:
                props = feature['properties']
                coords = feature['geometry']['coordinates']
                
                if validate:
                    self._validate_meter(props)
                
                await self.repo.create_meter(
                    meter_id=props.get('meter_id', f'METER_{i:06d}'),
                    meter_type=props.get('meter_type', 'grid_consumer'),
                    serial_number=props.get('serial_number'),
                    longitude=coords[0],
                    latitude=coords[1],
                    province=props.get('province', 'Bangkok')
                )
                
                self.stats['meters'] += 1
                
                if (i + 1) % 500 == 0:
                    logger.info(f"  Imported {i + 1}/{len(features)} meters")
            
            except Exception as e:
                logger.error(f"Error importing meter {i}: {e}")
                self.stats['errors'] += 1
    
    # =========================================================================
    # Generate Sample Data
    # =========================================================================
    
    async def generate_sample_data(
        self,
        region: str = 'bangkok',
        num_meters: int = 500,
        num_substations: int = 5
    ):
        """
        Generate realistic sample grid data.
        
        Args:
            region: Region name (bangkok, central, chiang_mai, phuket)
            num_meters: Number of smart meters to generate
            num_substations: Number of substations
        
        Returns:
            Dictionary with generation statistics
        """
        logger.info(f"Generating sample data for {region} ({num_meters} meters)")
        
        # Get region configuration
        config = self._get_region_config(region)
        
        # Generate substations
        logger.info("Generating substations...")
        substations = await self._generate_substations(
            num_substations,
            config['center'],
            config['bounds']
        )
        
        # Generate transformers
        logger.info("Generating transformers...")
        transformers = await self._generate_transformers(
            num_substations * 10,
            substations,
            config['bounds']
        )
        
        # Generate power lines
        logger.info("Generating power lines...")
        await self._generate_power_lines(substations, transformers, config)
        
        # Generate meters
        logger.info("Generating meters...")
        await self._generate_meters(
            num_meters,
            transformers,
            config
        )
        
        logger.info(f"Generation complete: {self.stats}")
        return self.stats
    
    def _get_region_config(self, region: str) -> Dict:
        """Get region configuration"""
        configs = {
            'bangkok': {
                'center': (100.5018, 13.7563),
                'bounds': {
                    'min_lat': 13.6000,
                    'max_lat': 13.9500,
                    'min_lon': 100.3000,
                    'max_lon': 100.9000
                },
                'voltage_levels': [500, 230, 115, 22, 0.4],
                'meter_types': {
                    'solar_prosumer': 0.40,
                    'grid_consumer': 0.35,
                    'hybrid_prosumer': 0.15,
                    'battery': 0.05,
                    'ev_charger': 0.05
                }
            },
            'central': {
                'center': (100.2000, 14.0000),
                'bounds': {
                    'min_lat': 13.5000,
                    'max_lat': 15.0000,
                    'min_lon': 99.5000,
                    'max_lon': 101.0000
                },
                'voltage_levels': [500, 230, 115, 22, 0.4],
                'meter_types': {
                    'solar_prosumer': 0.45,
                    'grid_consumer': 0.30,
                    'hybrid_prosumer': 0.15,
                    'battery': 0.05,
                    'ev_charger': 0.05
                }
            },
            'chiang_mai': {
                'center': (98.9853, 18.7883),
                'bounds': {
                    'min_lat': 18.5000,
                    'max_lat': 19.1000,
                    'min_lon': 98.7000,
                    'max_lon': 99.3000
                },
                'voltage_levels': [230, 115, 22, 0.4],
                'meter_types': {
                    'solar_prosumer': 0.35,
                    'grid_consumer': 0.40,
                    'hybrid_prosumer': 0.15,
                    'battery': 0.05,
                    'ev_charger': 0.05
                }
            },
            'phuket': {
                'center': (98.3923, 7.8804),
                'bounds': {
                    'min_lat': 7.7000,
                    'max_lat': 8.1000,
                    'min_lon': 98.2000,
                    'max_lon': 98.6000
                },
                'voltage_levels': [115, 22, 0.4],
                'meter_types': {
                    'solar_prosumer': 0.50,
                    'grid_consumer': 0.30,
                    'hybrid_prosumer': 0.10,
                    'battery': 0.05,
                    'ev_charger': 0.05
                }
            }
        }
        
        if region not in configs:
            logger.warning(f"Unknown region '{region}', using Bangkok config")
            return configs['bangkok']
        
        return configs[region]
    
    async def _generate_substations(
        self,
        num_substations: int,
        center: tuple,
        bounds: Dict
    ) -> List[Substation]:
        """Generate substations"""
        substations = []
        
        # Generate transmission substations (500kV, 230kV, 115kV)
        transmission_count = max(1, num_substations // 5)
        for i in range(transmission_count):
            voltage = random.choice([500, 230, 115])
            lon = random.uniform(bounds['min_lon'], bounds['max_lon'])
            lat = random.uniform(bounds['min_lat'], bounds['max_lat'])
            
            substation = await self.repo.create_substation(
                name=f"{voltage}kV Substation {i+1}",
                code=f"SUB-{voltage}-{i+1:03d}",
                voltage_level_kv=voltage,
                operator="EGAT" if voltage >= 230 else "MEA",
                type="transmission" if voltage >= 230 else "sub_transmission",
                capacity_mva=random.choice([100, 150, 200, 300]) if voltage >= 230 else random.choice([30, 50, 100]),
                longitude=lon,
                latitude=lat,
                province="Bangkok"
            )
            substations.append(substation)
            self.stats['substations'] += 1
        
        # Generate distribution substations (22kV)
        distribution_count = num_substations - transmission_count
        for i in range(distribution_count):
            lon = random.uniform(bounds['min_lon'], bounds['max_lon'])
            lat = random.uniform(bounds['min_lat'], bounds['max_lat'])
            
            substation = await self.repo.create_substation(
                name=f"22kV Distribution Substation {i+1}",
                code=f"SUB-22-{i+1:04d}",
                voltage_level_kv=22.0,
                operator="MEA",
                type="distribution",
                capacity_mva=random.choice([10, 16, 20, 25]),
                longitude=lon,
                latitude=lat,
                province="Bangkok"
            )
            substations.append(substation)
            self.stats['substations'] += 1
        
        logger.info(f"Generated {len(substations)} substations")
        return substations
    
    async def _generate_transformers(
        self,
        num_transformers: int,
        substations: List[Substation],
        bounds: Dict
    ) -> List[Transformer]:
        """Generate distribution transformers"""
        transformers = []
        
        for i in range(num_transformers):
            # Pick a random substation or generate near one
            if substations and random.random() < 0.7:
                # Near existing substation
                substation = random.choice(substations)
                sub_lon, sub_lat = substation.get_coordinates()
                # Random offset 0-2km
                lon_offset = random.uniform(-0.02, 0.02)
                lat_offset = random.uniform(-0.02, 0.02)
                lon = sub_lon + lon_offset
                lat = sub_lat + lat_offset
            else:
                # Random location
                lon = random.uniform(bounds['min_lon'], bounds['max_lon'])
                lat = random.uniform(bounds['min_lat'], bounds['max_lat'])
            
            transformer = await self.repo.create_transformer(
                code=f"TXN-{i+1:05d}",
                voltage_primary_kv=22.0,
                voltage_secondary_kv=0.4,
                capacity_kva=random.choice([160, 250, 315, 400, 500, 630]),
                longitude=lon,
                latitude=lat
            )
            transformers.append(transformer)
            self.stats['transformers'] += 1
        
        logger.info(f"Generated {len(transformers)} transformers")
        return transformers
    
    async def _generate_power_lines(
        self,
        substations: List[Substation],
        transformers: List[Transformer],
        config: Dict
    ):
        """Generate power lines between substations"""
        line_count = 0
        
        # Connect transmission substations
        transmission_subs = [s for s in substations if s.voltage_level_kv >= 115]
        for i, sub in enumerate(transmission_subs):
            if i > 0:
                prev_sub = transmission_subs[i-1]
                sub_lon, sub_lat = sub.get_coordinates()
                prev_lon, prev_lat = prev_sub.get_coordinates()
                
                await self.repo.create_power_line(
                    code=f"LINE-TX-{i:03d}",
                    voltage_level_kv=sub.voltage_level_kv,
                    coordinates=[(prev_lon, prev_lat), (sub_lon, sub_lat)],
                    line_type="overhead",
                    conductor_type="ACSR 184-AL1/30-ST1A",
                    from_substation_id=prev_sub.id,
                    to_substation_id=sub.id
                )
                line_count += 1
                self.stats['power_lines'] += 1
        
        # Connect distribution substations to transmission
        distribution_subs = [s for s in substations if s.voltage_level_kv == 22]
        for sub in distribution_subs:
            if transmission_subs:
                nearest_tx = random.choice(transmission_subs)
                sub_lon, sub_lat = sub.get_coordinates()
                tx_lon, tx_lat = nearest_tx.get_coordinates()
                
                # Add intermediate points for realistic line
                mid_lon = (sub_lon + tx_lon) / 2 + random.uniform(-0.01, 0.01)
                mid_lat = (sub_lat + tx_lat) / 2 + random.uniform(-0.01, 0.01)
                
                await self.repo.create_power_line(
                    code=f"LINE-DIST-{sub.code}",
                    voltage_level_kv=22.0,
                    coordinates=[(tx_lon, tx_lat), (mid_lon, mid_lat), (sub_lon, sub_lat)],
                    line_type="overhead",
                    conductor_type="NA2XS2Y 1x185 RM/25 12/20 kV",
                    from_substation_id=nearest_tx.id,
                    to_substation_id=sub.id
                )
                line_count += 1
                self.stats['power_lines'] += 1
        
        logger.info(f"Generated {line_count} power lines")
    
    async def _generate_meters(
        self,
        num_meters: int,
        transformers: List[Transformer],
        config: Dict
    ):
        """Generate smart meters near transformers"""
        meter_count = 0
        
        # Meter type distribution
        meter_types = config['meter_types']
        type_choices = list(meter_types.keys())
        type_weights = list(meter_types.values())
        
        for i in range(num_meters):
            # Pick random transformer
            transformer = random.choice(transformers)
            tx_lon, tx_lat = transformer.get_coordinates()
            
            # Random offset 0-200m from transformer
            lon_offset = random.uniform(-0.002, 0.002)
            lat_offset = random.uniform(-0.002, 0.002)
            lon = tx_lon + lon_offset
            lat = tx_lat + lat_offset
            
            # Pick meter type
            meter_type = random.choices(type_choices, weights=type_weights)[0]
            
            # Generate meter ID
            meter_id = f"METER-{meter_type[:3].upper()}-{i+1:06d}"
            
            await self.repo.create_meter(
                meter_id=meter_id,
                meter_type=meter_type,
                serial_number=f"SN{i+1:012d}",
                longitude=lon,
                latitude=lat,
                transformer_id=transformer.id,
                province="Bangkok"
            )
            meter_count += 1
            self.stats['meters'] += 1
            
            if (i + 1) % 500 == 0:
                logger.info(f"Generated {i + 1}/{num_meters} meters")
        
        logger.info(f"Generated {meter_count} meters")
    
    # =========================================================================
    # Validation
    # =========================================================================
    
    def _validate_substation(self, props: Dict):
        """Validate substation properties"""
        required = ['name', 'voltage_level_kv']
        for field in required:
            if field not in props:
                raise ValueError(f"Missing required field: {field}")
        
        voltage = props.get('voltage_level_kv')
        if voltage not in [500, 230, 115, 22, 0.4]:
            logger.warning(f"Unusual voltage level: {voltage}")
    
    def _validate_line(self, props: Dict):
        """Validate power line properties"""
        required = ['voltage_level_kv']
        for field in required:
            if field not in props:
                raise ValueError(f"Missing required field: {field}")
    
    def _validate_transformer(self, props: Dict):
        """Validate transformer properties"""
        pass  # All fields optional
    
    def _validate_meter(self, props: Dict):
        """Validate meter properties"""
        if 'meter_id' not in props:
            raise ValueError("Missing required field: meter_id")
    
    # =========================================================================
    # Statistics
    # =========================================================================
    
    async def print_statistics(self):
        """Print database statistics"""
        stats = await self.repo.get_network_stats()
        
        print("\n" + "="*60)
        print("DATABASE STATISTICS")
        print("="*60)
        
        print(f"\nSubstations by Voltage:")
        for voltage, count in sorted(stats['substations_by_voltage'].items(), reverse=True):
            print(f"  {voltage:>6.1f} kV: {count:>6}")
        
        print(f"\nPower Lines by Voltage:")
        for voltage, length in sorted(stats['lines_by_voltage_km'].items(), reverse=True):
            print(f"  {voltage:>6.1f} kV: {length:>10.2f} km")
        
        print(f"\nMeters by Type:")
        for meter_type, count in sorted(stats['meters_by_type'].items()):
            print(f"  {meter_type:>20}: {count:>6}")
        
        print(f"\nTotals:")
        print(f"  Total Substations: {stats['total_substations']}")
        print(f"  Total Lines: {stats['total_lines_km']:.2f} km")
        print(f"  Total Meters: {stats['total_meters']}")
        print("="*60 + "\n")


# =============================================================================
# Main Entry Point
# =============================================================================

async def main():
    parser = argparse.ArgumentParser(
        description="Import Thai grid data into PostGIS database"
    )
    
    parser.add_argument(
        "--input", "-i",
        type=str,
        help="Path to GeoJSON input file"
    )
    
    parser.add_argument(
        "--generate", "-g",
        action="store_true",
        help="Generate sample data instead of importing"
    )
    
    parser.add_argument(
        "--region", "-r",
        type=str,
        default="bangkok",
        choices=["bangkok", "central", "chiang_mai", "phuket"],
        help="Region for sample data generation"
    )
    
    parser.add_argument(
        "--meters", "-m",
        type=int,
        default=500,
        help="Number of meters to generate"
    )
    
    parser.add_argument(
        "--substations", "-s",
        type=int,
        default=5,
        help="Number of substations to generate"
    )
    
    parser.add_argument(
        "--validate", "-v",
        action="store_true",
        help="Validate data before import"
    )
    
    parser.add_argument(
        "--database-url", "-d",
        type=str,
        default="postgresql+asyncpg://gridtokenx:gridtokenx_password@localhost:5432/gridtokenx",
        help="Database connection URL"
    )
    
    args = parser.parse_args()
    
    # Create importer
    importer = ThaiGridImporter(args.database_url)
    
    try:
        # Initialize connection
        await importer.initialize()
        
        if args.generate:
            # Generate sample data
            await importer.generate_sample_data(
                region=args.region,
                num_meters=args.meters,
                num_substations=args.substations
            )
        elif args.input:
            # Import from file
            await importer.import_geojson(args.input, validate=args.validate)
        else:
            parser.print_help()
            sys.exit(1)
        
        # Print statistics
        await importer.print_statistics()
        
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)
    
    finally:
        await importer.close()


if __name__ == "__main__":
    asyncio.run(main())
