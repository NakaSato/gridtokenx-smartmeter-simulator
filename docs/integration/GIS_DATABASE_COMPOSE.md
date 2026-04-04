# GIS PostgreSQL Database - Docker Compose Setup

## Overview

The GridTokenX Smart Meter Simulator now includes **two PostgreSQL databases**:

1. **Primary Database** (`postgres`) - Main application data on port 5432
2. **GIS Database** (`gis-postgres`) - Spatial/GIS data on port 5433

---

## 📦 Services

### Primary Database (postgres)

| Property | Value |
|----------|-------|
| **Container** | `gridtokenx-postgres` |
| **Port** | 5432 |
| **Database** | `gridtokenx` |
| **Image** | `postgis/postgis:15-3.3` |
| **Use Case** | Application data, user accounts, trading data |

### GIS Database (gis-postgres) ✨ NEW

| Property | Value |
|----------|-------|
| **Container** | `gridtokenx-gis-postgres` |
| **Port** | 5433 |
| **Database** | `gridtokenx_gis` |
| **Image** | `postgis/postgis:17-3.4` |
| **Use Case** | Spatial data, grid topology, geographic queries |

---

## 🚀 Quick Start

### Start All Services

```bash
# Start everything
docker-compose up -d

# Or start specific service
docker-compose up -d gis-postgres
```

### Check Status

```bash
# List all services
docker-compose ps

# View GIS database logs
docker-compose logs -f gis-postgres
```

### Stop Services

```bash
# Stop everything
docker-compose down

# Or stop specific service
docker-compose stop gis-postgres
```

---

## 🔗 Connection Strings

### Primary Database (Port 5432)

```
# Async (asyncpg)
postgresql+asyncpg://gridtokenx:gridtokenx_password@localhost:5432/gridtokenx

# Sync (psycopg2)
postgresql://gridtokenx:gridtokenx_password@localhost:5432/gridtokenx

# Docker internal
postgresql+asyncpg://gridtokenx:gridtokenx_password@postgres:5432/gridtokenx
```

### GIS Database (Port 5433)

```
# Async (asyncpg)
postgresql+asyncpg://gridtokenx:gridtokenx_password@localhost:5433/gridtokenx_gis

# Sync (psycopg2)
postgresql://gridtokenx:gridtokenx_password@localhost:5433/gridtokenx_gis

# Docker internal
postgresql+asyncpg://gridtokenx:gridtokenx_password@gis-postgres:5432/gridtokenx_gis
```

---

## 🗺️ GIS Database Schema

The GIS database includes:

### Tables (grid schema)

- `grid.substations` - Electrical substations with location
- `grid.transformers` - Distribution transformers
- `grid.power_lines` - Transmission/distribution lines
- `grid.meters` - Smart meters with geographic position
- `grid.meter_readings` - Time-series meter data

### Spatial Functions

- `grid.find_nearest_transformer(lon, lat, max_distance)` - Find closest transformer
- `grid.get_meters_in_radius(lon, lat, radius, type)` - Search meters by location
- `grid.export_network_geojson(voltage_min, voltage_max)` - Export as GeoJSON
- `grid.get_network_stats()` - Network statistics

### Extensions

- ✅ PostGIS 3.4 - Spatial types and functions
- ✅ postgis_topology - Topology support

---

## 🛠️ Management Commands

### Run Migrations

```bash
# Primary database (auto-runs on first start)
docker-compose exec postgres psql -U gridtokenx -d gridtokenx -f /docker-entrypoint-initdb.d/001_postgis_grid_schema.sql

# GIS database
docker-compose exec gis-postgres psql -U gridtokenx -d gridtokenx_gis -f /docker-entrypoint-initdb.d/002_postgis_simple.sql
```

### Backup

```bash
# Primary database
docker-compose exec postgres pg_dump -U gridtokenx gridtokenx > backup.sql

# GIS database
docker-compose exec gis-postgres pg_dump -U gridtokenx gridtokenx_gis > gis_backup.sql
```

### Restore

```bash
# Primary database
cat backup.sql | docker-compose exec -T postgres psql -U gridtokenx gridtokenx

# GIS database
cat gis_backup.sql | docker-compose exec -T gis-postgres psql -U gridtokenx gridtokenx_gis
```

### Direct SQL Access

```bash
# Primary database
docker-compose exec postgres psql -U gridtokenx -d gridtokenx

# GIS database
docker-compose exec gis-postgres psql -U gridtokenx -d gridtokenx_gis
```

---

## 📊 pgAdmin Access

Access pgAdmin at: **http://localhost:5050**

**Login:**
- Email: `admin@gridtokenx.local`
- Password: `admin_password`

**Add Servers:**

1. **Primary Database:**
   - Name: `GridTokenX Primary`
   - Host: `postgres`
   - Port: `5432`
   - Database: `gridtokenx`
   - Username: `gridtokenx`
   - Password: `gridtokenx_password`

2. **GIS Database:**
   - Name: `GridTokenX GIS`
   - Host: `gis-postgres`
   - Port: `5432` (internal) or `5433` (external)
   - Database: `gridtokenx_gis`
   - Username: `gridtokenx`
   - Password: `gridtokenx_password`

---

## 🔍 Testing the GIS Database

### 1. Check PostGIS Version

```bash
docker-compose exec gis-postgres psql -U gridtokenx -d gridtokenx_gis -c "SELECT PostGIS_Version();"
```

### 2. List Extensions

```bash
docker-compose exec gis-postgres psql -U gridtokenx -d gridtokenx_gis -c "\dx"
```

### 3. List Tables

```bash
docker-compose exec gis-postgres psql -U gridtokenx -d gridtokenx_gis -c "\dt grid.*"
```

### 4. Test Spatial Query

```sql
-- Find distance between two points (in meters)
SELECT ST_Distance(
  ST_MakePoint(100.5018, 13.7563)::geography,
  ST_MakePoint(100.5100, 13.7600)::geography
) as distance_meters;
```

---

## 📝 Environment Variables

### Simulator Service

```yaml
environment:
  # Primary Database
  DATABASE_URL: postgresql+asyncpg://gridtokenx:gridtokenx_password@postgres:5432/gridtokenx
  
  # GIS Database
  GIS_DATABASE_URL: postgresql+asyncpg://gridtokenx:gridtokenx_password@gis-postgres:5432/gridtokenx_gis
  
  # Redis
  REDIS_URL: redis://redis:6379
  
  # InfluxDB
  INFLUXDB_URL: http://influxdb:8086
  INFLUXDB_TOKEN: admin_token
  INFLUXDB_ORG: gridtokenx
  INFLUXDB_BUCKET: meter_readings
```

---

## 🐛 Troubleshooting

### GIS Database Not Starting

```bash
# Check logs
docker-compose logs gis-postgres

# Restart service
docker-compose restart gis-postgres

# Remove and recreate
docker-compose down gis-postgres
docker-compose up -d gis-postgres
```

### Connection Refused

```bash
# Check if service is running
docker-compose ps gis-postgres

# Verify port is open
docker port gridtokenx-gis-postgres

# Should show: 5432/tcp -> 0.0.0.0:5433
```

### PostGIS Not Available

```bash
# Enable PostGIS manually
docker-compose exec gis-postgres psql -U gridtokenx -d gridtokenx_gis <<EOF
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;
EOF
```

---

## 📚 Resources

- **PostGIS Documentation:** https://postgis.net/documentation/
- **PostGIS Docker:** https://github.com/postgis/docker-postgis
- **GridTokenX Docs:** `docs/POSTGIS_INTEGRATION.md`

---

**Part of the GridTokenX Platform**
