"""
Thai Electrical Grid Data Generator

Generates realistic sample data for Thai distribution network based on:
- EGAT transmission system (500kV, 230kV, 115kV)
- MEA/PEA distribution system (22kV, 0.4kV)
- Real Thai provincial coordinates
- Standard transformer ratios and line configurations

Usage:
    uv run python examples/generate_thai_grid.py --region bangkok --meters 1000
    uv run python examples/generate_thai_grid.py --region chiang_mai --export
"""

import asyncio
import argparse
import json
import random
from typing import Dict, List, Tuple
from decimal import Decimal
from datetime import datetime

# Import from project
from smart_meter_simulator.database.repository import PostGISRepository


# =============================================================================
# Thai Grid Configuration
# =============================================================================

# Provincial coordinates (longitude, latitude)
THAI_PROVINCES = {
    # Central Region
    "bangkok": {"lon": 100.5018, "lat": 13.7563, "area": "Bangkok Metropolitan"},
    "samut_prakan": {"lon": 100.5998, "lat": 13.5990, "area": "Central"},
    "nonthaburi": {"lon": 100.5231, "lat": 13.8621, "area": "Central"},
    "pathum_thani": {"lon": 100.5250, "lat": 14.0208, "area": "Central"},
    "ayutthaya": {"lon": 100.5696, "lat": 14.3692, "area": "Central"},
    
    # Northern Region
    "chiang_mai": {"lon": 98.9853, "lat": 18.7883, "area": "Northern"},
    "chiang_rai": {"lon": 99.8325, "lat": 19.9105, "area": "Northern"},
    "lamphun": {"lon": 99.0087, "lat": 18.5744, "area": "Northern"},
    "lampang": {"lon": 99.4918, "lat": 18.2888, "area": "Northern"},
    
    # Northeastern Region (Isan)
    "nakhon_ratchasima": {"lon": 102.0977, "lat": 14.9799, "area": "Northeastern"},
    "khon_kaen": {"lon": 102.8236, "lat": 16.4322, "area": "Northeastern"},
    "udon_thani": {"lon": 102.7879, "lat": 17.4138, "area": "Northeastern"},
    "ubon_ratchathani": {"lon": 104.8472, "lat": 15.2286, "area": "Northeastern"},
    
    # Southern Region
    "phuket": {"lon": 98.3981, "lat": 7.8804, "area": "Southern"},
    "surat_thani": {"lon": 99.3331, "lat": 9.1382, "area": "Southern"},
    "nakhon_si_thammarat": {"lon": 99.9661, "lat": 8.4304, "area": "Southern"},
    "songkhla": {"lon": 100.5951, "lat": 7.1756, "area": "Southern"},
}

# EGAT Voltage Hierarchy
VOLTAGE_LEVELS = {
    "transmission": [500.0, 230.0, 115.0],
    "distribution": [22.0, 0.4],
}

# Transformer ratios (primary/secondary kV)
TRANSFORMER_RATIOS = [
    (500.0, 230.0),   # EHV transmission
    (230.0, 115.0),   # HV transmission
    (115.0, 22.0),    # Sub-transmission to MV
    (22.0, 0.4),      # MV to LV (distribution)
]

# Line configurations (Thai standard)
LINE_CONFIGS = {
    500.0: {
        "type": "overhead",
        "conductor": "ACSR 460 mm² (TACSR 460)",
        "circuits": 2,
    },
    230.0: {
        "type": "overhead",
        "conductor": "ACSR 300 mm² (TACSR 300)",
        "circuits": 2,
    },
    115.0: {
        "type": "overhead",
        "conductor": "ACSR 185 mm² (TACSR 185)",
        "circuits": 1,
    },
    22.0: {
        "type": "overhead",
        "conductor": "NA2XS2Y 1x185 RM/25 12/20 kV",
        "circuits": 1,
    },
    0.4: {
        "type": "underground",
        "conductor": "NYY 4x185 mm²",
        "circuits": 1,
    },
}

# Meter type distribution (Thai market)
METER_DISTRIBUTION = {
    "solar_prosumer": 0.35,      # 35% - Rooftop solar
    "grid_consumer": 0.40,       # 40% - Pure consumers
    "hybrid_prosumer": 0.15,     # 15% - Solar + battery
    "battery": 0.05,             # 5% - Battery storage
    "ev_charger": 0.05,          # 5% - EV charging
}

# Operators
OPERATORS = {
    500.0: "EGAT",
    230.0: "EGAT",
    115.0: "EGAT",
    22.0: "MEA",    # Metropolitan Electricity Authority
    0.4: "MEA",
}


# =============================================================================
# Grid Generator
# =============================================================================

class ThaiGridGenerator:
    """Generate realistic Thai electrical grid data"""
    
    def __init__(self, repo: PostGISRepository, region: str):
        self.repo = repo
        self.region = region
        self.province_config = THAI_PROVINCES.get(region, THAI_PROVINCES["bangkok"])
        
        # Generated assets tracking
        self.substations = []
        self.transformers = []
        self.power_lines = []
        self.meters = []
    
    def _random_offset(self, base_lon: float, base_lat: float, km_range: float) -> Tuple[float, float]:
        """Generate random coordinates within km range"""
        # Approximate: 1 degree ≈ 111 km
        deg_range = km_range / 111.0
        lon = base_lon + random.uniform(-deg_range, deg_range)
        lat = base_lat + random.uniform(-deg_range, deg_range)
        return lon, lat
    
    async def generate_transmission_network(self, num_substations: int = 5):
        """Generate EGAT transmission network (500kV, 230kV, 115kV)"""
        print(f"  Generating {num_substations} transmission substations...")
        
        base_lon = self.province_config["lon"]
        base_lat = self.province_config["lat"]
        
        # Create 500kV main substation
        sub_500 = await self.repo.create_substation(
            name=f"500kV {self.province_config['area']} Main",
            code=f"SUB-500-{self.region.upper()[:3]}-001",
            voltage_level_kv=500.0,
            operator="EGAT",
            type="transmission",
            capacity_mva=Decimal("300.0"),
            longitude=base_lon,
            latitude=base_lat,
            province=self.province_config["area"]
        )
        self.substations.append(sub_500)
        
        # Create 230kV substations
        for i in range(max(1, num_substations // 3)):
            lon, lat = self._random_offset(base_lon, base_lat, 30)  # 30km radius
            sub_230 = await self.repo.create_substation(
                name=f"230kV {self.province_config['area']} {i+1}",
                code=f"SUB-230-{self.region.upper()[:3]}-{i+1:03d}",
                voltage_level_kv=230.0,
                operator="EGAT",
                type="transmission",
                capacity_mva=Decimal("150.0"),
                longitude=lon,
                latitude=lat,
                province=self.province_config["area"]
            )
            self.substations.append(sub_230)
            
            # Connect to 500kV substation
            line = await self.repo.create_power_line(
                code=f"LINE-500-{i+1:03d}",
                voltage_level_kv=500.0,
                coordinates=[(base_lon, base_lat), (lon, lat)],
                line_type="overhead",
                conductor_type="ACSR 460 mm² (TACSR 460)"
            )
            self.power_lines.append(line)
        
        # Create 115kV substations
        for i in range(max(2, num_substations // 2)):
            lon, lat = self._random_offset(base_lon, base_lat, 50)  # 50km radius
            sub_115 = await self.repo.create_substation(
                name=f"115kV {self.province_config['area']} {i+1}",
                code=f"SUB-115-{self.region.upper()[:3]}-{i+1:03d}",
                voltage_level_kv=115.0,
                operator="EGAT",
                type="sub_transmission",
                capacity_mva=Decimal("60.0"),
                longitude=lon,
                latitude=lat,
                province=self.province_config["area"]
            )
            self.substations.append(sub_115)
            
            # Connect to nearest 230kV substation
            line = await self.repo.create_power_line(
                code=f"LINE-230-{i+1:03d}",
                voltage_level_kv=230.0,
                coordinates=[(self.substations[i % len(self.substations)].get_coordinates()[0],
                             self.substations[i % len(self.substations)].get_coordinates()[1]),
                            (lon, lat)],
                line_type="overhead",
                conductor_type="ACSR 300 mm² (TACSR 300)"
            )
            self.power_lines.append(line)
        
        print(f"    ✓ Created {len(self.substations)} transmission substations")
        print(f"    ✓ Created {len(self.power_lines)} transmission lines")
    
    async def generate_distribution_network(self, num_transformers: int = 20):
        """Generate MEA/PEA distribution network (22kV, 0.4kV)"""
        print(f"  Generating {num_transformers} distribution transformers...")
        
        base_lon = self.province_config["lon"]
        base_lat = self.province_config["lat"]
        
        # Create 22kV distribution substations
        num_22kv = max(3, num_transformers // 5)
        for i in range(num_22kv):
            lon, lat = self._random_offset(base_lon, base_lat, 20)  # 20km radius
            sub_22 = await self.repo.create_substation(
                name=f"22kV Distribution {self.province_config['area']} {i+1}",
                code=f"SUB-22-{self.region.upper()[:3]}-{i+1:03d}",
                voltage_level_kv=22.0,
                operator="MEA",
                type="distribution",
                capacity_mva=Decimal("20.0"),
                longitude=lon,
                latitude=lat,
                province=self.province_config["area"]
            )
            self.substations.append(sub_22)
        
        # Create distribution transformers (22kV/0.4kV)
        for i in range(num_transformers):
            # Distribute around 22kV substations
            sub_22 = self.substations[-(i % num_22kv)] if num_22kv > 0 else None
            if sub_22:
                base = sub_22.get_coordinates()
                lon, lat = self._random_offset(base[0], base[1], 5)  # 5km radius
            else:
                lon, lat = self._random_offset(base_lon, base_lat, 15)
            
            txn = await self.repo.create_transformer(
                code=f"TXN-22-{self.region.upper()[:3]}-{i+1:04d}",
                voltage_primary_kv=22.0,
                voltage_secondary_kv=0.4,
                capacity_kva=random.choice([315, 400, 500, 630, 800, 1000]),
                longitude=lon,
                latitude=lat,
                substation_id=sub_22.id if sub_22 else None
            )
            self.transformers.append(txn)
        
        # Create 22kV distribution lines
        for i in range(min(num_transformers, 30)):
            if i < len(self.transformers) - 1:
                coord1 = self.transformers[i].get_coordinates()
                coord2 = self.transformers[i + 1].get_coordinates()
                
                # Add intermediate poles
                num_poles = random.randint(2, 5)
                coords = [coord1]
                for j in range(num_poles):
                    t = (j + 1) / (num_poles + 1)
                    mid_lon = coord1[0] + t * (coord2[0] - coord1[0])
                    mid_lat = coord1[1] + t * (coord2[1] - coord1[1])
                    coords.append((mid_lon, mid_lat))
                coords.append(coord2)
                
                line = await self.repo.create_power_line(
                    code=f"LINE-22-{self.region.upper()[:3]}-{i+1:04d}",
                    voltage_level_kv=22.0,
                    coordinates=coords,
                    line_type="overhead",
                    conductor_type="NA2XS2Y 1x185 RM/25 12/20 kV"
                )
                self.power_lines.append(line)
        
        print(f"    ✓ Created {len(self.transformers)} distribution transformers")
        print(f"    ✓ Created {len(self.power_lines)} distribution lines")
    
    async def generate_meters(self, num_meters: int = 500):
        """Generate smart meters with Thai market distribution"""
        print(f"  Generating {num_meters} smart meters...")
        
        meter_types = list(METER_DISTRIBUTION.keys())
        weights = list(METER_DISTRIBUTION.values())
        
        for i in range(num_meters):
            # Select meter type based on distribution
            meter_type = random.choices(meter_types, weights=weights)[0]
            
            # Assign to nearest transformer
            if self.transformers:
                txn = self.transformers[i % len(self.transformers)]
                base_lon, base_lat = txn.get_coordinates()
                # Distribute within 500m of transformer
                lon, lat = self._random_offset(base_lon, base_lat, 0.5)
            else:
                lon, lat = self._random_offset(
                    self.province_config["lon"],
                    self.province_config["lat"],
                    10
                )
            
            # Generate meter ID
            prefix = {
                "solar_prosumer": "SOL",
                "grid_consumer": "GRD",
                "hybrid_prosumer": "HYB",
                "battery": "BAT",
                "ev_charger": "EV",
            }[meter_type]
            
            meter_id = f"METER-{prefix}-{self.region.upper()[:3]}-{i+1:06d}"
            serial_number = f"SN{datetime.now().year}{i+1:012d}"
            
            # Find nearest transformer
            nearest_txn = None
            if self.transformers:
                # Simple assignment (in production, use spatial query)
                nearest_txn = self.transformers[i % len(self.transformers)].id
            
            meter = await self.repo.create_meter(
                meter_id=meter_id,
                meter_type=meter_type,
                serial_number=serial_number,
                longitude=lon,
                latitude=lat,
                province=self.province_config["area"],
                transformer_id=nearest_txn
            )
            self.meters.append(meter)
            
            if (i + 1) % 100 == 0:
                print(f"    Generated {i + 1}/{num_meters} meters...")
        
        print(f"    ✓ Created {len(self.meters)} meters")
    
    async def generate_all(self, num_meters: int = 500):
        """Generate complete grid network"""
        print(f"\n{'='*60}")
        print(f"Thai Grid Generator - {self.province_config['area']}")
        print(f"{'='*60}")
        
        # Calculate infrastructure based on meter count
        num_transformers = max(20, num_meters // 25)  # 1 transformer per ~25 meters
        num_substations = max(5, num_meters // 100)   # 1 substation per ~100 meters
        
        await self.generate_transmission_network(num_substations)
        await self.generate_distribution_network(num_transformers)
        await self.generate_meters(num_meters)
        
        print(f"\n{'='*60}")
        print(f"Generation Complete!")
        print(f"{'='*60}")
        print(f"  Substations: {len(self.substations)}")
        print(f"  Transformers: {len(self.transformers)}")
        print(f"  Power Lines: {len(self.power_lines)}")
        print(f"  Meters: {len(self.meters)}")
        print(f"{'='*60}\n")
        
        return {
            "substations": len(self.substations),
            "transformers": len(self.transformers),
            "power_lines": len(self.power_lines),
            "meters": len(self.meters),
        }


# =============================================================================
# CLI
# =============================================================================

async def main():
    parser = argparse.ArgumentParser(description="Generate Thai electrical grid data")
    parser.add_argument(
        "--region",
        type=str,
        default="bangkok",
        choices=list(THAI_PROVINCES.keys()),
        help="Province/region to generate data for"
    )
    parser.add_argument(
        "--meters",
        type=int,
        default=500,
        help="Number of meters to generate"
    )
    parser.add_argument(
        "--database-url",
        type=str,
        default="postgresql+asyncpg://gridtokenx:gridtokenx_password@localhost:5433/gridtokenx_gis",
        help="PostgreSQL database URL"
    )
    parser.add_argument(
        "--export",
        action="store_true",
        help="Export generated data as GeoJSON"
    )
    
    args = parser.parse_args()
    
    # Initialize repository
    print(f"\nConnecting to database...")
    repo = PostGISRepository(args.database_url)
    
    connected = await repo.check_connection()
    if not connected:
        print("❌ Failed to connect to database")
        return
    
    print("✓ Connected to PostGIS database\n")
    
    try:
        # Generate grid
        generator = ThaiGridGenerator(repo, args.region)
        stats = await generator.generate_all(num_meters=args.meters)
        
        # Export if requested
        if args.export:
            print("Exporting network as GeoJSON...")
            geojson = await repo.export_network_geojson()
            
            filename = f"thai_grid_{args.region}.geojson"
            with open(filename, "w") as f:
                json.dump(geojson, f, indent=2)
            
            print(f"✓ Exported to {filename}")
        
        # Print summary
        print("\n✅ Grid generation successful!")
        print(f"\nTo view on map:")
        print(f"  1. Start simulator: docker-compose up -d simulator")
        print(f"  2. Open: http://localhost:5173/thai-grid-map")
        print(f"  3. Select region: {args.region}")
        
    finally:
        await repo.close()


if __name__ == "__main__":
    asyncio.run(main())
