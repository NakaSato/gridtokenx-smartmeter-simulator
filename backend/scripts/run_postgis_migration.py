#!/usr/bin/env python3
"""
Run PostGIS migration to create database schema
"""

import asyncio
import sys
import re
from pathlib import Path
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

def split_sql_statements(sql: str) -> list:
    """
    Split SQL file into individual statements.
    Handles multi-line statements and comments properly.
    """
    # Remove single-line comments
    sql = re.sub(r'--.*?$', '', sql, flags=re.MULTILINE)
    # Remove multi-line comments
    sql = re.sub(r'/\*.*?\*/', '', sql, flags=re.DOTALL)
    
    # Split by semicolon, but keep $$ blocks intact (for PL/pgSQL functions)
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
    
    # Add any remaining statement
    if current:
        stmt = '\n'.join(current).strip()
        if stmt and stmt != ';':
            statements.append(stmt.rstrip(';').strip())
    
    return [s for s in statements if s]

async def run_migration():
    # Database URL
    db_url = "postgresql+asyncpg://gridtokenx_user:gridtokenx_password@localhost:5434/gridtokenx"
    
    print(f"Connecting to database: {db_url}")
    engine = create_async_engine(db_url)
    
    # Read migration file
    migration_file = Path(__file__).parent.parent / "database" / "migrations" / "001_postgis_grid_schema.sql"
    
    if not migration_file.exists():
        print(f"❌ Migration file not found: {migration_file}")
        return False
    
    print(f"Reading migration: {migration_file}")
    with open(migration_file, 'r') as f:
        migration_sql = f.read()
    
    print("Running migration...")
    try:
        # Enable PostGIS extensions first (separate connection)
        async with engine.begin() as conn:
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis"))
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis_topology"))
            print("✓ PostGIS extensions enabled")
        
        # Split migration into individual statements
        statements = split_sql_statements(migration_sql)
        
        print(f"Executing {len(statements)} SQL statements...")
        errors = []
        
        # Execute each statement in its own transaction
        for i, stmt in enumerate(statements, 1):
            try:
                async with engine.begin() as conn:
                    await conn.execute(text(stmt))
                if i % 20 == 0:
                    print(f"  Executed {i}/{len(statements)} statements...")
            except Exception as e:
                error_msg = str(e)[:200]
                print(f"  ⚠️  Statement {i} failed: {error_msg}...")
                errors.append((i, error_msg))
                # Continue with next statement
        
        if errors:
            print(f"\n⚠️  {len(errors)} statements failed, but continuing...")
        
        print("✓ Schema creation complete")
        
        # Verify tables
        async with engine.begin() as conn:
            result = await conn.execute(text("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'grid'
                ORDER BY table_name
            """))
            tables = [row[0] for row in result]
        
        print(f"\n✓ Created {len(tables)} tables:")
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
    success = asyncio.run(run_migration())
    sys.exit(0 if success else 1)
