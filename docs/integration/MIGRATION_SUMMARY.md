# Smart Meter Simulator - Database Migration Summary

## ✅ Migration Complete

The Smart Meter Simulator codebase has been successfully migrated to use the **GIS Database (Port 5433)** for all spatial operations.

---

## 📊 Database Architecture

| Database | Port | Purpose | Service |
|----------|------|---------|---------|
| **GridTokenX API** | 5432 | Users, trading, orders, blockchain | `postgres` |
| **GIS (PostGIS)** | 5433 | Spatial data, grid topology, meters | `gis-postgres` |

---

## 🔄 Changes Made

### 1. Configuration (`src/smart_meter_simulator/config/settings.py`)

✅ Added `gis_database_url` field:
```python
# GIS Database Configuration (PostGIS for spatial data)
gis_database_url: str = Field(
    default="postgresql+asyncpg://gridtokenx:gridtokenx_password@localhost:5433/gridtokenx_gis",
    alias="GIS_DATABASE_URL"
)
```

### 2. Router (`src/smart_meter_simulator/routers/grid.py`)

✅ Updated `get_postgis_repo()` to use GIS database:
```python
async def get_postgis_repo() -> PostGISRepository:
    """Get PostGIS repository from GIS database settings"""
    config = get_config()
    
    # Use GIS database URL if available
    db_url = config.gis_database_url if config.gis_database_url else config.database_url
    
    return PostGISRepository(db_url)
```

### 3. Environment (`.env.example`)

✅ Updated database configuration:
```env
# Primary Database - GridTokenX API (users, trading, orders)
DATABASE_URL=postgresql+asyncpg://gridtokenx:gridtokenx_password@localhost:5432/gridtokenx

# GIS Database - Spatial Data (grid topology, meters, locations)
GIS_DATABASE_URL=postgresql+asyncpg://gridtokenx:gridtokenx_password@localhost:5433/gridtokenx_gis
```

### 4. Docker Compose (`docker-compose.yml`)

✅ Added GIS database service:
```yaml
gis-postgres:
  image: postgis/postgis:17-3.4
  container_name: gridtokenx-gis-postgres
  ports:
    - "5433:5432"
  environment:
    POSTGRES_USER: gridtokenx
    POSTGRES_PASSWORD: gridtokenx_password
    POSTGRES_DB: gridtokenx_gis
```

### 5. Documentation

✅ Created migration guides:
- `docs/DATABASE_MIGRATION_GUIDE.md` - Complete migration guide
- `docs/GIS_DATABASE_COMPOSE.md` - GIS database Docker setup
- `docs/POSTGIS_API_REFERENCE.md` - API reference

---

## 🚀 Usage

### Start Services

```bash
# Start GIS database
docker-compose up -d gis-postgres

# Start all services
docker-compose up -d
```

### Set Environment

```bash
# Copy example environment
cp .env.example .env

# The .env file should contain:
# DATABASE_URL=postgresql+asyncpg://gridtokenx:gridtokenx_password@localhost:5432/gridtokenx
# GIS_DATABASE_URL=postgresql+asyncpg://gridtokenx:gridtokenx_password@localhost:5433/gridtokenx_gis
```

### Run Migrations

```bash
# Migrate GIS database schema
uv run python scripts/migrate_gis_db.py
```

### Test API

```bash
# Check GIS database status
curl http://localhost:8082/api/grid/postgis/status

# Get network statistics
curl http://localhost:8082/api/grid/postgis/statistics

# Export grid as GeoJSON
curl http://localhost:8082/api/grid/postgis/network/geojson

# Find nearest transformer
curl "http://localhost:8082/api/grid/postgis/transformers/nearest?longitude=100.5018&latitude=13.7563&max_distance_m=500"
```

### Generate Sample Data

```bash
# Generate Thai grid data (stored in GIS database)
uv run python examples/generate_thai_grid.py \
  --region bangkok \
  --meters 100
```

---

## 📁 Modified Files

| File | Changes |
|------|---------|
| `config/settings.py` | Added `gis_database_url` field |
| `routers/grid.py` | Updated PostGIS repository to use GIS database |
| `.env.example` | Added `GIS_DATABASE_URL` configuration |
| `docker-compose.yml` | Added `gis-postgres` service |
| `docs/` | Added 3 new documentation files |

---

## 🔍 Database Separation

### What Goes Where

#### GridTokenX API Database (5432)
- User accounts
- Trading orders
- Market data
- Blockchain transactions
- REC (Renewable Energy Certificates)
- Wallet information

#### GIS Database (5433)
- Substations (location, voltage, capacity)
- Transformers (location, voltage ratio)
- Power lines (geometry, conductor type)
- Smart meters (location, type)
- Meter readings (time-series)
- Geographic zones
- Network topology

---

## ✅ Verification

### Check Services

```bash
# List running containers
docker-compose ps

# Should show:
# ✅ gridtokenx-postgres (5432)
# ✅ gridtokenx-gis-postgres (5433)
# ✅ gridtokenx-simulator (8082)
```

### Test Connections

```bash
# Primary database (5432)
docker exec gridtokenx-postgres psql -U gridtokenx -c "SELECT 1"

# GIS database (5433)
docker exec gridtokenx-gis-postgres psql -U gridtokenx -c "SELECT PostGIS_Version()"
```

### Test API

```bash
# Health check
curl http://localhost:8082/health

# GIS status
curl http://localhost:8082/api/grid/postgis/status
```

---

## 🎯 Benefits

| Benefit | Description |
|---------|-------------|
| **Performance** | Spatial queries don't impact trading operations |
| **Scalability** | Can scale databases independently |
| **Specialization** | Each DB optimized for its workload |
| **Maintenance** | Easier backup/restore per database |
| **Security** | Different access controls per database |

---

## 📚 Documentation

| Document | Description |
|----------|-------------|
| `docs/DATABASE_MIGRATION_GUIDE.md` | Complete migration guide |
| `docs/GIS_DATABASE_COMPOSE.md` | GIS database Docker setup |
| `docs/POSTGIS_API_REFERENCE.md` | API endpoints reference |
| `docs/POSTGIS_INTEGRATION.md` | PostGIS integration guide |
| `docs/THAI_GRID_INTEGRATION.md` | Thai grid modeling guide |

---

## 🐛 Troubleshooting

### GIS Database Not Connected

```bash
# Check if running
docker-compose ps gis-postgres

# View logs
docker-compose logs gis-postgres

# Restart
docker-compose restart gis-postgres
```

### Migration Failed

```bash
# Drop and recreate schema
docker exec gridtokenx-gis-postgres psql -U gridtokenx -d gridtokenx_gis \
  -c "DROP SCHEMA IF EXISTS grid CASCADE; CREATE SCHEMA grid;"

# Re-run migration
uv run python scripts/migrate_gis_db.py
```

### API Returns 503

```bash
# Check simulator logs
docker-compose logs simulator

# Verify environment
cat .env | grep GIS_DATABASE_URL
```

---

## 🎉 Migration Complete!

The Smart Meter Simulator now uses:
- ✅ **Port 5432** for GridTokenX API data
- ✅ **Port 5433** for GIS/spatial data

All PostGIS operations (spatial queries, grid topology, meter locations) are now stored and queried from the dedicated GIS database.

---

**Part of the GridTokenX Platform**
