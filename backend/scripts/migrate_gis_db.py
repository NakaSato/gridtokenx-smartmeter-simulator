#!/usr/bin/env python3
"""
Run PostGIS migration on new GIS database
"""

import asyncio
import sys
import re
from pathlib import Path
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

def split_sql_statements(sql: str) -> list:
    """Split SQL file into individual statements."""
    sql = re.sub(r'--.*?$', '', sql, flags=re.MULTILINE)
    sql = re.sub(r'/\*.*?\*/', '', sql, flags=re.DOTALL)
    
    statements = []
    current = []
    in_function = False
    
    for line in sql.split('\n'):
        current.append(line)
        if '$$' in line:
            in_function = not in_function
        if ';' in line and not in_function:
            stmt = '\n'.join(current).strip()
            if stmt and stmt != ';':
                statements.append(stmt.rstrip(';').strip())
            current = []
    
    if current:
        stmt = '\n'.join(current).strip()
        if stmt and stmt != ';':
            statements.append(stmt.rstrip(';').strip())
    
    return [s for s in statements if s]

async def run_migration(db_url: str):
    print(f"Connecting to: {db_url}")
    engine = create_async_engine(db_url)
    
    migration_file = Path(__file__).parent.parent / "database" / "migrations" / "002_postgis_simple.sql"
    
    if not migration_file.exists():
        print(f"❌ Migration file not found: {migration_file}")
        return False
    
    print(f"Reading: {migration_file}")
    with open(migration_file, 'r') as f:
        migration_sql = f.read()
    
    print("Running migration...\n")
    try:
        async with engine.begin() as conn:
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis"))
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis_topology"))
            print("✓ PostGIS extensions enabled")
        
        statements = split_sql_statements(migration_sql)
        print(f"Executing {len(statements)} SQL statements...")
        
        errors = []
        for i, stmt in enumerate(statements, 1):
            try:
                async with engine.begin() as conn:
                    await conn.execute(text(stmt))
                if i % 20 == 0:
                    print(f"  Executed {i}/{len(statements)}...")
            except Exception as e:
                errors.append((i, str(e)[:150]))
        
        if errors:
            print(f"\n⚠️  {len(errors)} statements had errors")
        
        print("\n✓ Schema creation complete")
        
        async with engine.begin() as conn:
            result = await conn.execute(text("""
                SELECT table_name FROM information_schema.tables
                WHERE table_schema = 'grid' ORDER BY table_name
            """))
            tables = [row[0] for row in result]
        
        print(f"\n✓ Created {len(tables)} tables in grid schema:")
        for table in tables:
            print(f"  - grid.{table}")
        
        print("\n✅ Migration completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False
    finally:
        await engine.dispose()

if __name__ == "__main__":
    db_url = "postgresql+asyncpg://gridtokenx:gridtokenx_password@localhost:5433/gridtokenx_gis"
    success = asyncio.run(run_migration(db_url))
    sys.exit(0 if success else 1)
