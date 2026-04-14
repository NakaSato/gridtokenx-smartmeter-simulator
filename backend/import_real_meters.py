#!/usr/bin/env python3
"""Create grid.meters table and import real_location.json as smart meters."""

import asyncio
import re
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    db_url = "postgresql+asyncpg://gridtokenx:gridtokenx_password@localhost:5433/gridtokenx_gis"
    
    file_path = Path(__file__).parent / "real_location.json"
    with open(file_path) as f:
        content = f.read()
    
    coords_list = re.findall(r'"([^"]+,\s*[^"]+)"', content)
    logger.info(f"Found {len(coords_list)} coordinates")
    
    from sqlalchemy.ext.asyncio import create_async_engine
    from sqlalchemy import text
    
    engine = create_async_engine(db_url)
    
    try:
        async with engine.begin() as conn:
            # Create table
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS grid.meters (
                    id SERIAL PRIMARY KEY,
                    meter_id VARCHAR(100) UNIQUE NOT NULL,
                    meter_type VARCHAR(50),
                    accuracy_class VARCHAR(20),
                    rated_voltage_v NUMERIC(10,2) DEFAULT 230,
                    phase_count INTEGER DEFAULT 1,
                    status VARCHAR(20) DEFAULT 'active',
                    location GEOGRAPHY(POINT, 4326) NOT NULL,
                    province VARCHAR(100),
                    district VARCHAR(100),
                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW()
                )
            """))
            logger.info("✅ grid.meters table created")
            
            meter_types = ['solar_prosumer', 'grid_consumer', 'hybrid_prosumer']
            
            for idx, coord_str in enumerate(coords_list):
                lat, lon = [float(x.strip()) for x in coord_str.split(",")]
                meter_id = f"SM_{idx + 1:05d}"
                mtype = meter_types[idx % len(meter_types)]
                
                await conn.execute(text("""
                    INSERT INTO grid.meters (
                        meter_id, meter_type, accuracy_class,
                        rated_voltage_v, phase_count, status,
                        location, province, district
                    ) VALUES (
                        :meter_id, :meter_type, 'CLASS_1_0',
                        230, 1, 'active',
                        ST_SetSRID(ST_MakePoint(:lon, :lat), 4326),
                        'Bangkok', 'Lat Krabang'
                    )
                """), {
                    "meter_id": meter_id,
                    "meter_type": mtype,
                    "lat": lat,
                    "lon": lon,
                })
                
                if (idx + 1) % 10 == 0:
                    logger.info(f"  Inserted {idx + 1}/{len(coords_list)}")
            
            result = await conn.execute(text("SELECT COUNT(*) FROM grid.meters"))
            total = result.scalar()
            logger.info(f"✅ Imported {len(coords_list)} smart meters. Total: {total}")
            
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())
