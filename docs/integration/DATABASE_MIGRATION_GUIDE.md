# Database Migration Guide - GIS Separation

## Overview

The Smart Meter Simulator has been migrated to use **separate databases**:

- **Port 5432**: GridTokenX API Database (users, trading, orders)
- **Port 5433**: GIS Database (spatial data, grid topology, meters)

---

## 🔄 Changes Made

### 1. Configuration (`config/settings.py`)

**Added:**
```python
# GIS Database Configuration (PostGIS for spatial data)
gis_database_url: str = Field(
    default="postgresql+asyncpg://gridtokenx:gridtokenx_password@localhost:5433/gridtokenx_gis",
    alias="GIS_DATABASE_URL"
)
```

### 2. Router (`routers/grid.py`)

**Updated PostGIS repository dependency:**
```python
async def get_postgis_repo() -> PostGISRepository:
    """Get PostGIS repository from GIS database settings"""
    config = get_config()
    
    # Use GIS database URL if available
    db_url = config.gis_database_url if config.gis_database_url else config.database_url
    
    # Convert to asyncpg format if needed
    if db_url.startswith("postgresql://"):
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    
    return PostGISRepository(db_url)
```

### 3. Environment (`.env.example`)

**Updated:**
```env
# Primary Database - GridTokenX API
DATABASE_URL=postgresql+asyncpg://gridtokenx:gridtokenx_password@localhost:5432/gridtokenx

# GIS Database - Spatial Data
GIS_DATABASE_URL=postgresql+asyncpg://gridtokenx:gridtokenx_password@localhost:5433/gridtokenx_gis
```

---

## 📊 Database Architecture

```
┌─────────────────────────┐
│  Smart Meter Simulator  │
│  (FastAPI/Python)       │
└────────┬────────────────┘
         │
         ├──► Primary DB (5432) ──► Application data
         │
         └──► GIS DB (5433) ──────► Spatial/Grid data
```

### Primary Database (Port 5432)

**Used for:**
- Application configuration
- User accounts (if applicable)
- Trading data
- Market orders
- Blockchain records

**Connection:**
```
postgresql+asyncpg://gridtokenx:gridtokenx_password@localhost:5432/gridtokenx
```

### GIS Database (Port 5433)

**Used for:**
- Substations (location, voltage, capacity)
- Transformers (location, voltage ratio)
- Power lines (geometry, voltage, conductor type)
- Smart meters (location, type, readings)
- Geographic queries
- Spatial analysis

**Connection:**
```
postgresql+asyncpg://gridtokenx:gridtokenx_password@localhost:5433/gridtokenx_gis
```

---

## 🚀 Migration Steps

### 1. Update Environment File

Create or update `.env`:

```bash
cp .env.example .env
```

Edit `.env`:
```env
DATABASE_URL=postgresql+asyncpg://gridtokenx:gridtokenx_password@localhost:5432/gridtokenx
GIS_DATABASE_URL=postgresql+asyncpg://gridtokenx:gridtokenx_password@localhost:5433/gridtokenx_gis
```

### 2. Start GIS Database

```bash
# Using docker-compose
docker-compose up -d gis-postgres

# Or manually
docker run -d \
  --name gridtokenx-gis-postgres \
  -e POSTGRES_USER=gridtokenx \
  -e POSTGRES_PASSWORD=gridtokenx_password \
  -e POSTGRES_DB=gridtokenx_gis \
  -p 5433:5432 \
  postgis/postgis:17-3.4
```

### 3. Run Migrations

```bash
# Run GIS schema migration
uv run python scripts/migrate_gis_db.py
```

### 4. Verify Connection

```bash
# Test GIS database
curl http://localhost:8082/api/grid/postgis/status

# Expected response:
{
  "connected": true,
  "postgis_version": "3.4 USE_GEOS=1 USE_PROJ=1 USE_STATS=1",
  "statistics": { ... }
}
```

---

## 🔍 Testing

### 1. Check API Endpoints

```bash
# GIS Database Status
curl http://localhost:8082/api/grid/postgis/status

# Network Statistics
curl http://localhost:8082/api/grid/postgis/statistics

# GeoJSON Export
curl http://localhost:8082/api/grid/postgis/network/geojson

# Find Nearest Transformer
curl "http://localhost:8082/api/grid/postgis/transformers/nearest?longitude=100.5018&latitude=13.7563&max_distance_m=500"
```

### 2. Generate Sample Data

```bash
# Generate Thai grid data (uses GIS database)
uv run python examples/generate_thai_grid.py \
  --region bangkok \
  --meters 100
```

### 3. Query GIS Database Directly

```bash
# Connect to GIS database
docker exec -it gridtokenx-gis-postgres psql -U gridtokenx -d gridtokenx_gis

# List tables
\dt grid.*

# Query substations
SELECT name, voltage_level_kv, ST_X(location) as lon, ST_Y(location) as lat
FROM grid.substations;

# Test spatial function
SELECT * FROM grid.find_nearest_transformer(100.5018, 13.7563, 500);
```

---

## 📝 Code Changes Required

### If You Have Custom Code

**Before:**
```python
from smart_meter_simulator.config import get_config

config = get_config()
db_url = config.database_url  # Used for everything
```

**After:**
```python
from smart_meter_simulator.config import get_config

config = get_config()

# For application data
app_db_url = config.database_url

# For spatial/GIS data
gis_db_url = config.gis_database_url
```

### Repository Pattern

```python
# For GIS operations
from smart_meter_simulator.database.repository import PostGISRepository

gis_repo = PostGISRepository(config.gis_database_url)

# For application operations
from sqlalchemy.ext.asyncio import create_async_engine

app_engine = create_async_engine(config.database_url)
```

---

## 🐛 Troubleshooting

### GIS Database Connection Failed

**Error:**
```
Database connection failed: Multiple exceptions: [Errno 61] Connect call failed
```

**Solution:**
```bash
# Check if GIS database is running
docker ps | grep gis-postgres

# Restart if needed
docker-compose restart gis-postgres

# Verify port is open
netstat -an | grep 5433
```

### PostGIS Extension Not Found

**Error:**
```
extension "postgis" does not exist
```

**Solution:**
```bash
# Install PostGIS in container
docker exec gridtokenx-gis-postgres psql -U gridtokenx -d gridtokenx_gis <<EOF
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;
EOF
```

### No Data in GIS Database

**Solution:**
```bash
# Run migration
uv run python scripts/migrate_gis_db.py

# Or generate sample data
uv run python examples/generate_thai_grid.py --region bangkok --meters 100
```

---

## 📚 Related Documentation

- `docs/GIS_DATABASE_COMPOSE.md` - GIS database Docker setup
- `docs/POSTGIS_INTEGRATION.md` - PostGIS integration guide
- `docs/POSTGIS_API_REFERENCE.md` - API endpoints reference
- `docs/THAI_GRID_INTEGRATION.md` - Thai grid modeling

---

## ✅ Verification Checklist

- [ ] `.env` file updated with `GIS_DATABASE_URL`
- [ ] GIS database container running (`docker-compose ps gis-postgres`)
- [ ] Migration completed successfully
- [ ] API endpoints responding (`/api/grid/postgis/status`)
- [ ] Sample data generated (optional)
- [ ] pgAdmin can connect to both databases
- [ ] No errors in simulator logs

---

**Migration Complete!** 🎉

The Smart Meter Simulator now uses:
- **Port 5432** for application data
- **Port 5433** for GIS/spatial data
