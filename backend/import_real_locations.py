#!/usr/bin/env python3
"""Import real_location.json coordinates into grid.power_plants table."""

import asyncio
import json
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    db_url = "postgresql+asyncpg://gridtokenx:gridtokenx_password@localhost:5433/gridtokenx_gis"
    
    # Read and parse the file - extract all quoted coordinate pairs
    file_path = Path(__file__).parent / "real_location.json"
    with open(file_path) as f:
        content = f.read()
    
    import re
    # Match all quoted "lat, lon" pairs
    coords_list = re.findall(r'"([^"]+,\s*[^"]+)"', content)
    logger.info(f"Found {len(coords_list)} coordinates")
    
    from sqlalchemy.ext.asyncio import create_async_engine
    from sqlalchemy import text
    
    engine = create_async_engine(db_url)
    
    try:
        async with engine.begin() as conn:
            # Check existing count
            result = await conn.execute(text("SELECT COUNT(*) FROM grid.power_plants"))
            existing_count = result.scalar()
            logger.info(f"Existing plants: {existing_count}")
            
            # Insert each coordinate as a micro-generator
            for idx, coord_str in enumerate(coords_list):
                lat, lon = [float(x.strip()) for x in coord_str.split(",")]
                plant_id = f"TH_MICRO_{existing_count + idx + 1:05d}"
                name = f"Micro Generator {existing_count + idx + 1}"
                
                await conn.execute(text("""
                    INSERT INTO grid.power_plants (
                        plant_id, name, name_th, plant_type, fuel_type, technology,
                        capacity_mw, units, status, operator,
                        location, latitude, longitude,
                        province, region, source
                    ) VALUES (
                        :plant_id, :name, :name_th, 'solar', 'solar', 'PV',
                        0.5, 1, 'operating', 'Local Micro-Grid',
                        ST_SetSRID(ST_MakePoint(:lon, :lat), 4326),
                        :lat, :lon,
                        'Bangkok', 'bangkok', 'real_location.json'
                    )
                """), {
                    "plant_id": plant_id,
                    "name": name,
                    "name_th": None,
                    "lat": lat,
                    "lon": lon,
                })
                
                if (idx + 1) % 10 == 0:
                    logger.info(f"  Inserted {idx + 1}/{len(coords_list)}")
            
            # Verify
            result = await conn.execute(text("SELECT COUNT(*) FROM grid.power_plants"))
            new_count = result.scalar()
            logger.info(f"✅ Imported {len(coords_list)} micro plants. Total: {new_count}")
            
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())
