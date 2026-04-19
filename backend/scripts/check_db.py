import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def check():
    db_url = os.environ.get("GIS_DATABASE_URL", "postgresql+asyncpg://gridtokenx:gridtokenx_password@localhost:5433/gridtokenx_gis")
    engine = create_async_engine(db_url)
    async with engine.connect() as conn:
        res = await conn.execute(text("SELECT plant_id, name FROM grid.power_plants LIMIT 20"))
        for r in res:
            print(f" - {r[0]}: {r[1]}")
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(check())
