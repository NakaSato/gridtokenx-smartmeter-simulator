"""
EGAT Dashboard Data Scraper & Importer

This tool helps extract data from the EGAT dashboard (sothailand.com/sysgen/egat/)
and import it into the PostGIS database.

Usage:
    1. Manually copy data from the EGAT dashboard
    2. Save as JSON/CSV/Excel file
    3. Run this importer

    uv run python examples/scrape_egat_dashboard.py --input egat_data.json --type substations
"""

import asyncio
import argparse
import json
import csv
from typing import Dict, List, Optional
from pathlib import Path
from datetime import datetime

from smart_meter_simulator.database.repository import PostGISRepository


# =============================================================================
# Data Parsers
# =============================================================================

class EGATDataParser:
    """Parse data from EGAT dashboard exports"""
    
    @staticmethod
    def parse_json(filepath: str) -> Dict:
        """Parse JSON export"""
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    @staticmethod
    def parse_csv(filepath: str) -> List[Dict]:
        """Parse CSV export"""
        data = []
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                data.append(row)
        return data
    
    @staticmethod
    def parse_excel(filepath: str) -> List[Dict]:
        """Parse Excel export (requires openpyxl)"""
        try:
            import pandas as pd
            df = pd.read_excel(filepath)
            return df.to_dict('records')
        except ImportError:
            print("❌ pandas/openpyxl not installed")
            print("Install with: uv add pandas openpyxl")
            return []
    
    @staticmethod
    def parse_manual_input(filepath: str) -> Dict:
        """Parse manually structured data"""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data


# =============================================================================
# EGAT Data Importer
# =============================================================================

class EGATDataImporter:
    """Import EGAT data into PostGIS"""
    
    def __init__(self, repo: PostGISRepository):
        self.repo = repo
        self.stats = {
            'substations': 0,
            'transformers': 0,
            'power_lines': 0,
            'meters': 0,
            'errors': 0
        }
    
    async def import_substations(self, substations: List[Dict]) -> int:
        """Import EGAT substations"""
        print(f"\n{'='*60}")
        print(f"Importing {len(substations)} substations...")
        print(f"{'='*60}")
        
        for i, sub in enumerate(substations, 1):
            try:
                # Map EGAT dashboard fields to database fields
                name = sub.get('name', sub.get('Substation_Name', ''))
                code = sub.get('code', sub.get('Substation_Code', sub.get('id', f'SUB-{i:03d}')))
                voltage = float(sub.get('voltage', sub.get('voltage_kv', sub.get('Voltage_Level', 115))))
                operator = sub.get('operator', sub.get('Operator', 'EGAT'))
                sub_type = sub.get('type', sub.get('Type', 'transmission'))
                capacity = float(sub.get('capacity', sub.get('capacity_mva', 100)))
                
                # Handle coordinates
                if 'longitude' in sub and 'latitude' in sub:
                    lon = float(sub['longitude'])
                    lat = float(sub['latitude'])
                elif 'lon' in sub and 'lat' in sub:
                    lon = float(sub['lon'])
                    lat = float(sub['lat'])
                elif 'coordinates' in sub:
                    coords = sub['coordinates']
                    lon = float(coords[0]) if isinstance(coords, list) else float(coords.split(',')[0])
                    lat = float(coords[1]) if isinstance(coords, list) else float(coords.split(',')[1])
                else:
                    print(f"  ⚠️  Substation {code}: Missing coordinates, skipping")
                    self.stats['errors'] += 1
                    continue
                
                # Create substation
                await self.repo.create_substation(
                    name=name,
                    code=code,
                    voltage_level_kv=voltage,
                    operator=operator,
                    type=sub_type,
                    capacity_mva=capacity,
                    longitude=lon,
                    latitude=lat,
                    province=sub.get('province', sub.get('Province', 'Unknown'))
                )
                
                self.stats['substations'] += 1
                
                if i % 10 == 0:
                    print(f"  Imported {i}/{len(substations)} substations...")
                    
            except Exception as e:
                print(f"  ❌ Error importing substation {sub.get('code', i)}: {e}")
                self.stats['errors'] += 1
        
        print(f"  ✓ Imported {self.stats['substations']} substations")
        if self.stats['errors'] > 0:
            print(f"  ⚠️  {self.stats['errors']} errors")
        
        return self.stats['substations']
    
    async def import_transformers(self, transformers: List[Dict]) -> int:
        """Import EGAT transformers"""
        print(f"\n{'='*60}")
        print(f"Importing {len(transformers)} transformers...")
        print(f"{'='*60}")
        
        for i, txn in enumerate(transformers, 1):
            try:
                code = txn.get('code', txn.get('Transformer_Code', f'TXN-{i:04d}'))
                v_primary = float(txn.get('voltage_primary', txn.get('Primary_kV', 22)))
                v_secondary = float(txn.get('voltage_secondary', txn.get('Secondary_kV', 0.4)))
                capacity = float(txn.get('capacity', txn.get('Capacity_kVA', 500)))
                
                # Handle coordinates
                if 'longitude' in txn and 'latitude' in txn:
                    lon = float(txn['longitude'])
                    lat = float(txn['latitude'])
                elif 'lon' in txn and 'lat' in txn:
                    lon = float(txn['lon'])
                    lat = float(txn['lat'])
                elif 'coordinates' in txn:
                    coords = txn['coordinates']
                    lon = float(coords[0])
                    lat = float(coords[1])
                else:
                    print(f"  ⚠️  Transformer {code}: Missing coordinates, skipping")
                    self.stats['errors'] += 1
                    continue
                
                await self.repo.create_transformer(
                    code=code,
                    voltage_primary_kv=v_primary,
                    voltage_secondary_kv=v_secondary,
                    capacity_kva=capacity,
                    longitude=lon,
                    latitude=lat
                )
                
                self.stats['transformers'] += 1
                
                if i % 20 == 0:
                    print(f"  Imported {i}/{len(transformers)} transformers...")
                    
            except Exception as e:
                print(f"  ❌ Error importing transformer {txn.get('code', i)}: {e}")
                self.stats['errors'] += 1
        
        print(f"  ✓ Imported {self.stats['transformers']} transformers")
        return self.stats['transformers']
    
    async def import_power_lines(self, power_lines: List[Dict]) -> int:
        """Import EGAT power lines"""
        print(f"\n{'='*60}")
        print(f"Importing {len(power_lines)} power lines...")
        print(f"{'='*60}")
        
        for i, line in enumerate(power_lines, 1):
            try:
                code = line.get('code', line.get('Line_Code', f'LINE-{i:04d}'))
                voltage = float(line.get('voltage', line.get('Voltage_kV', 22)))
                line_type = line.get('type', line.get('Line_Type', 'overhead'))
                conductor = line.get('conductor', line.get('Conductor_Type', 'ACSR 185'))
                
                # Handle coordinates (LineString)
                if 'coordinates' in line:
                    coords = line['coordinates']
                    if isinstance(coords, str):
                        # Parse "lon1,lat1;lon2,lat2;..." format
                        coord_list = []
                        for point in coords.split(';'):
                            lon, lat = point.split(',')
                            coord_list.append((float(lon), float(lat)))
                    elif isinstance(coords, list):
                        if isinstance(coords[0], list):
                            # [[lon1, lat1], [lon2, lat2], ...]
                            coord_list = [(float(c[0]), float(c[1])) for c in coords]
                        else:
                            # [lon1, lat1, lon2, lat2, ...]
                            coord_list = [(float(coords[i]), float(coords[i+1])) 
                                         for i in range(0, len(coords), 2)]
                    else:
                        print(f"  ⚠️  Line {code}: Invalid coordinates format, skipping")
                        self.stats['errors'] += 1
                        continue
                elif 'start_lon' in line and 'end_lon' in line:
                    # Simple start-end format
                    coord_list = [
                        (float(line['start_lon']), float(line['start_lat'])),
                        (float(line['end_lon']), float(line['end_lat']))
                    ]
                else:
                    print(f"  ⚠️  Line {code}: Missing coordinates, skipping")
                    self.stats['errors'] += 1
                    continue
                
                await self.repo.create_power_line(
                    code=code,
                    voltage_level_kv=voltage,
                    coordinates=coord_list,
                    line_type=line_type,
                    conductor_type=conductor
                )
                
                self.stats['power_lines'] += 1
                
                if i % 20 == 0:
                    print(f"  Imported {i}/{len(power_lines)} power lines...")
                    
            except Exception as e:
                print(f"  ❌ Error importing line {line.get('code', i)}: {e}")
                self.stats['errors'] += 1
        
        print(f"  ✓ Imported {self.stats['power_lines']} power lines")
        return self.stats['power_lines']
    
    async def import_meters(self, meters: List[Dict]) -> int:
        """Import smart meters"""
        print(f"\n{'='*60}")
        print(f"Importing {len(meters)} meters...")
        print(f"{'='*60}")
        
        for i, meter in enumerate(meters, 1):
            try:
                meter_id = meter.get('meter_id', meter.get('Meter_ID', f'METER-{i:06d}'))
                meter_type = meter.get('meter_type', meter.get('Type', 'grid_consumer'))
                serial = meter.get('serial', meter.get('Serial_Number', f'SN{i:012d}'))
                
                # Handle coordinates
                if 'longitude' in meter and 'latitude' in meter:
                    lon = float(meter['longitude'])
                    lat = float(meter['latitude'])
                elif 'lon' in meter and 'lat' in meter:
                    lon = float(meter['lon'])
                    lat = float(meter['lat'])
                else:
                    print(f"  ⚠️  Meter {meter_id}: Missing coordinates, skipping")
                    self.stats['errors'] += 1
                    continue
                
                await self.repo.create_meter(
                    meter_id=meter_id,
                    meter_type=meter_type,
                    serial_number=serial,
                    longitude=lon,
                    latitude=lat,
                    province=meter.get('province', 'Unknown')
                )
                
                self.stats['meters'] += 1
                
                if i % 50 == 0:
                    print(f"  Imported {i}/{len(meters)} meters...")
                    
            except Exception as e:
                print(f"  ❌ Error importing meter {meter.get('meter_id', i)}: {e}")
                self.stats['errors'] += 1
        
        print(f"  ✓ Imported {self.stats['meters']} meters")
        return self.stats['meters']
    
    def print_summary(self):
        """Print import summary"""
        print(f"\n{'='*60}")
        print(f"IMPORT SUMMARY")
        print(f"{'='*60}")
        print(f"  ✅ Substations:  {self.stats['substations']}")
        print(f"  ✅ Transformers: {self.stats['transformers']}")
        print(f"  ✅ Power Lines:  {self.stats['power_lines']}")
        print(f"  ✅ Meters:       {self.stats['meters']}")
        print(f"  ❌ Errors:       {self.stats['errors']}")
        print(f"{'='*60}\n")


# =============================================================================
# Template Generator
# =============================================================================

def generate_template(output_dir: str = '.'):
    """Generate template files for manual data entry"""
    
    templates = {
        'substations_template.json': {
            "description": "EGAT Substations - Copy data from sothailand.com/sysgen/egat/",
            "substations": [
                {
                    "name": "500kV Bangkok Main",
                    "code": "SUB-500-001",
                    "voltage": 500,
                    "operator": "EGAT",
                    "type": "transmission",
                    "capacity": 300,
                    "longitude": 100.5018,
                    "latitude": 13.7563,
                    "province": "Bangkok"
                }
            ]
        },
        'transformers_template.json': {
            "description": "EGAT Transformers",
            "transformers": [
                {
                    "code": "TXN-001",
                    "voltage_primary": 22,
                    "voltage_secondary": 0.4,
                    "capacity": 500,
                    "longitude": 100.5025,
                    "latitude": 13.7570
                }
            ]
        },
        'power_lines_template.json': {
            "description": "EGAT Power Lines",
            "power_lines": [
                {
                    "code": "LINE-001",
                    "voltage": 230,
                    "type": "overhead",
                    "conductor": "ACSR 300 mm²",
                    "coordinates": [
                        [100.5018, 13.7563],
                        [100.5100, 13.7600]
                    ]
                }
            ]
        },
        'meters_template.json': {
            "description": "Smart Meters",
            "meters": [
                {
                    "meter_id": "METER-SOL-000001",
                    "meter_type": "solar_prosumer",
                    "serial": "SN2024000001",
                    "longitude": 100.5020,
                    "latitude": 13.7565,
                    "province": "Bangkok"
                }
            ]
        }
    }
    
    for filename, content in templates.items():
        filepath = Path(output_dir) / filename
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(content, f, indent=2, ensure_ascii=False)
        print(f"✓ Created template: {filepath}")


# =============================================================================
# CLI
# =============================================================================

async def main():
    parser = argparse.ArgumentParser(
        description='Import EGAT dashboard data into PostGIS',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Import substations from JSON
  uv run python examples/scrape_egat_dashboard.py --input substations.json --type substations
  
  # Import transformers from CSV
  uv run python examples/scrape_egat_dashboard.py --input transformers.csv --type transformers
  
  # Import power lines from Excel
  uv run python examples/scrape_egat_dashboard.py --input egat_lines.xlsx --type lines
  
  # Generate templates for manual entry
  uv run python examples/scrape_egat_dashboard.py --generate-templates
        """
    )
    
    parser.add_argument(
        '--input', '-i',
        type=str,
        help='Input file (JSON, CSV, or Excel)'
    )
    parser.add_argument(
        '--type', '-t',
        type=str,
        choices=['substations', 'transformers', 'lines', 'meters', 'all'],
        help='Type of data to import'
    )
    parser.add_argument(
        '--database-url',
        type=str,
        default='postgresql+asyncpg://gridtokenx:gridtokenx_password@localhost:5432/gridtokenx',
        help='PostgreSQL database URL'
    )
    parser.add_argument(
        '--format', '-f',
        type=str,
        choices=['json', 'csv', 'excel', 'auto'],
        default='auto',
        help='Input file format'
    )
    parser.add_argument(
        '--generate-templates',
        action='store_true',
        help='Generate template files for manual data entry'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default='.',
        help='Output directory for templates'
    )
    
    args = parser.parse_args()
    
    # Generate templates if requested
    if args.generate_templates:
        generate_template(args.output_dir)
        print("\n✅ Templates generated!")
        print("\nInstructions:")
        print("1. Open the template files")
        print("2. Copy data from https://www.sothailand.com/sysgen/egat/")
        print("3. Fill in the template files")
        print("4. Run: uv run python examples/scrape_egat_dashboard.py --input <file> --type <type>")
        return
    
    # Validate input
    if not args.input:
        print("❌ Error: --input is required")
        parser.print_help()
        return
    
    # Check file exists
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"❌ Error: File not found: {input_path}")
        return
    
    # Determine format
    if args.format == 'auto':
        if input_path.suffix.lower() == '.json':
            file_format = 'json'
        elif input_path.suffix.lower() == '.csv':
            file_format = 'csv'
        elif input_path.suffix.lower() in ['.xlsx', '.xls']:
            file_format = 'excel'
        else:
            print(f"❌ Error: Unknown file format: {input_path.suffix}")
            return
    else:
        file_format = args.format
    
    # Parse input file
    print(f"\nParsing {file_format} file: {input_path}")
    parser_obj = EGATDataParser()
    
    if file_format == 'json':
        data = parser_obj.parse_json(str(input_path))
    elif file_format == 'csv':
        data = parser_obj.parse_csv(str(input_path))
    elif file_format == 'excel':
        data = parser_obj.parse_excel(str(input_path))
    else:
        print(f"❌ Error: Unsupported format: {file_format}")
        return
    
    # Connect to database
    print(f"\nConnecting to database...")
    repo = PostGISRepository(args.database_url)
    
    connected = await repo.check_connection()
    if not connected:
        print("❌ Failed to connect to database")
        return
    
    print("✓ Connected to PostGIS database\n")
    
    try:
        # Import data
        importer = EGATDataImporter(repo)
        
        if args.type == 'substations':
            substations = data.get('substations', data) if isinstance(data, dict) else data
            await importer.import_substations(substations)
        
        elif args.type == 'transformers':
            transformers = data.get('transformers', data) if isinstance(data, dict) else data
            await importer.import_transformers(transformers)
        
        elif args.type == 'lines':
            power_lines = data.get('power_lines', data) if isinstance(data, dict) else data
            await importer.import_power_lines(power_lines)
        
        elif args.type == 'meters':
            meters = data.get('meters', data) if isinstance(data, dict) else data
            await importer.import_meters(meters)
        
        elif args.type == 'all':
            if isinstance(data, dict):
                if 'substations' in data:
                    await importer.import_substations(data['substations'])
                if 'transformers' in data:
                    await importer.import_transformers(data['transformers'])
                if 'power_lines' in data:
                    await importer.import_power_lines(data['power_lines'])
                if 'meters' in data:
                    await importer.import_meters(data['meters'])
            else:
                print("❌ Error: 'all' type requires structured JSON with keys")
        
        # Print summary
        importer.print_summary()
        
    finally:
        await repo.close()


if __name__ == "__main__":
    asyncio.run(main())
