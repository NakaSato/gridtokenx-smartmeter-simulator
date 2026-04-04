# PostGIS Integration for Thai Electrical Grid

Complete guide for setting up and using PostGIS spatial database with the GridTokenX Smart Meter Simulator.

## Overview

This integration adds **PostGIS** (PostgreSQL + GIS extensions) to the GridTokenX platform for:

- 🗺️ **Spatial Storage**: Persistent storage of grid topology with geographic coordinates
- 🔍 **Spatial Queries**: Nearest transformer, meters in radius, bounding box searches
- 📤 **GeoJSON Export**: Direct database-to-map export for visualization
- 📊 **Network Analysis**: Graph-based power flow analysis
- 📈 **Time-Series Data**: Meter readings with temporal partitioning

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    GridTokenX Platform                       │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐   │
│  │   React UI   │───▶│  FastAPI     │───▶│  PostGIS     │   │
│  │  (Leaflet)   │◀───│  (REST API)  │◀───│  Database    │   │
│  └──────────────┘    └──────────────┘    └──────────────┘   │
│         │                   │                   │            │
│         │                   │                   │            │
│  ┌──────▼──────┐    ┌──────▼──────┐    ┌──────▼──────┐      │
│  │  Map Tiles  │    │  GeoJSON    │    │  Spatial    │      │
│  │  (OSM/Sat)  │    │  Export     │    │  Queries    │      │
│  └─────────────┘    └─────────────┘    └─────────────┘      │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

## Quick Start

### 1. Start Database Services

```bash
# Start PostgreSQL + PostGIS
docker-compose up -d postgres pgadmin

# Wait for database to be ready (check logs)
docker-compose logs -f postgres

# Verify PostGIS is installed
docker exec -it gridtokenx-postgres psql -U gridtokenx -d gridtokenx -c "SELECT PostGIS_Version();"
```

### 2. Run Migrations

```bash
# Migrations auto-run on first startup
# Or manually:
docker exec -it gridtokenx-postgres psql -U gridtokenx -d gridtokenx -f /docker-entrypoint-initdb.d/001_postgis_grid_schema.sql
```

### 3. Configure Application

Update `.env`:

```bash
# Database
DATABASE_URL=postgresql+asyncpg://gridtokenx:gridtokenx_password@localhost:5432/gridtokenx

# Redis (optional)
REDIS_URL=redis://localhost:6379

# InfluxDB (optional)
INFLUXDB_URL=http://localhost:8086
INFLUXDB_TOKEN=admin_token
INFLUXDB_ORG=gridtokenx
INFLUXDB_BUCKET=meter_readings
```

### 4. Start Simulator

```bash
# With Docker Compose
docker-compose up -d simulator

# Or locally
uv run start-simulator --mode server --port 8082
```

### 5. Verify Connection

```bash
# Check PostGIS status
curl http://localhost:8082/api/grid/postgis/status

# Get network statistics
curl http://localhost:8082/api/grid/postgis/statistics
```

## Database Schema

### Core Tables

| Table | Description | Spatial Type |
|-------|-------------|--------------|
| `grid.substations` | HV/MV substations (EGAT, MEA, PEA) | `POINT` |
| `grid.transformers` | Distribution transformers (MV/LV) | `POINT` |
| `grid.power_lines` | Transmission & distribution lines | `LINESTRING` |
| `grid.meters` | Smart meters (AMI) | `POINT` |
| `grid.meter_readings` | Time-series readings (partitioned) | - |
| `grid.zones` | Service area boundaries | `POLYGON` |
| `grid.network_topology` | Graph representation | - |

### Voltage Levels

| Voltage | Operator | Usage |
|---------|----------|-------|
| 500 kV | EGAT | Transmission |
| 230 kV | EGAT | Transmission |
| 115 kV | EGAT/MEA | Sub-transmission |
| 22 kV | MEA/PEA | Distribution (MV) |
| 0.4 kV | MEA/PEA | Distribution (LV) |

## API Endpoints

### Database Status

```bash
GET /api/grid/postgis/status
```

**Response:**
```json
{
  "connected": true,
  "postgis_version": "3.3.2 r17448",
  "statistics": {
    "substations_by_voltage": {
      "500": 2,
      "230": 5,
      "115": 15,
      "22": 120,
      "0.4": 450
    },
    "lines_by_voltage_km": {
      "500": 245.6,
      "230": 189.3,
      "115": 456.8,
      "22": 1250.4,
      "0.4": 890.2
    },
    "meters_by_type": {
      "solar_prosumer": 350,
      "grid_consumer": 890,
      "battery": 45,
      "ev_charger": 78
    }
  }
}
```

### Get Network GeoJSON

```bash
GET /api/grid/postgis/network/geojson?voltage_min=0&voltage_max=500
```

**Query Parameters:**
- `voltage_min` (default: 0): Minimum voltage level (kV)
- `voltage_max` (default: 500): Maximum voltage level (kV)

**Response:** GeoJSON FeatureCollection

### Get Substations

```bash
# All substations
GET /api/grid/postgis/substations

# Filter by voltage
GET /api/grid/postgis/substations?voltage=22

# Filter by province
GET /api/grid/postgis/substations?province=Bangkok

# Bounding box query
GET /api/grid/postgis/substations?min_lon=100.5&min_lat=13.7&max_lon=100.6&max_lat=13.8
```

### Find Nearest Transformer

```bash
GET /api/grid/postgis/transformers/nearest?longitude=100.5018&latitude=13.7563&max_distance_m=500
```

**Response:**
```json
{
  "transformer_id": 123,
  "code": "TXN-BKK-001",
  "distance_m": 125.4,
  "capacity_kva": 500
}
```

### Get Nearby Meters

```bash
GET /api/grid/postgis/meters/nearby?longitude=100.5018&latitude=13.7563&radius_m=1000&meter_type=solar_prosumer
```

**Query Parameters:**
- `longitude` (required): Search center longitude
- `latitude` (required): Search center latitude
- `radius_m` (default: 1000): Search radius in meters
- `meter_type` (optional): Filter by meter type

### Register New Meter

```bash
POST /api/grid/postgis/meters?meter_id=METER_001&meter_type=solar_prosumer&longitude=100.5018&latitude=13.7563&serial_number=SN123456
```

### Get Network Statistics

```bash
GET /api/grid/postgis/statistics
```

## Spatial Queries

### Nearest Neighbor

```sql
-- Find nearest transformer to a point
SELECT * FROM grid.find_nearest_transformer(
    100.5018,  -- longitude
    13.7563,   -- latitude
    500        -- max distance (meters)
);
```

### Radius Search

```sql
-- Get all meters within 1km radius
SELECT * FROM grid.get_meters_in_radius(
    100.5018,  -- longitude
    13.7563,   -- latitude
    1000,      -- radius (meters)
    NULL       -- meter_type (NULL = all types)
);
```

### Bounding Box

```sql
-- Get assets within bounding box
SELECT * FROM grid.substations
WHERE ST_Intersects(
    location,
    ST_MakeEnvelope(100.5, 13.7, 100.6, 13.8, 4326)
);
```

### Distance Calculation

```sql
-- Calculate distance between two points
SELECT ST_Distance(
    (SELECT location FROM grid.substations WHERE code = 'SUB_001'),
    (SELECT location FROM grid.substations WHERE code = 'SUB_002')
)::geography as distance_meters;
```

### GeoJSON Export

```sql
-- Export entire network as GeoJSON
SELECT grid.export_network_geojson(0, 500);

-- Export specific voltage level
SELECT grid.export_network_geojson(22, 22);
```

## Python Usage

### Initialize Repository

```python
from smart_meter_simulator.database.repository import PostGISRepository

# Initialize
repo = PostGISRepository(
    "postgresql+asyncpg://gridtokenx:gridtokenx_password@localhost:5432/gridtokenx"
)

# Check connection
connected = await repo.check_connection()
print(f"Connected: {connected}")

# Get PostGIS version
version = await repo.get_postgis_version()
print(f"PostGIS version: {version}")
```

### Query Substations

```python
# Get by voltage level
substations = await repo.get_substations_by_voltage(22.0, province="Bangkok")

for sub in substations:
    print(f"{sub.name}: {sub.voltage_level_kv}kV")
    lon, lat = sub.get_coordinates()
    print(f"  Location: {lon}, {lat}")
```

### Find Nearest Transformer

```python
nearest = await repo.find_nearest_transformer(
    longitude=100.5018,
    latitude=13.7563,
    max_distance_m=500
)

if nearest:
    print(f"Nearest transformer: {nearest['code']}")
    print(f"Distance: {nearest['distance_m']:.1f}m")
    print(f"Capacity: {nearest['capacity_kva']}kVA")
```

### Export GeoJSON

```python
# Export network for map visualization
geojson = await repo.export_network_geojson(
    voltage_min=0,
    voltage_max=500
)

# Save to file
import json
with open('network.geojson', 'w') as f:
    json.dump(geojson, f, indent=2)
```

### Create New Assets

```python
# Create substation
substation = await repo.create_substation(
    name="Bangkok Main",
    code="SUB-BKK-001",
    voltage_level_kv=115,
    operator="MEA",
    type="sub_transmission",
    capacity_mva=100,
    longitude=100.5018,
    latitude=13.7563,
    province="Bangkok"
)

# Create transformer
transformer = await repo.create_transformer(
    code="TXN-001",
    voltage_primary_kv=22.0,
    voltage_secondary_kv=0.4,
    capacity_kva=500,
    substation_id=substation.id,
    longitude=100.5025,
    latitude=13.7570
)

# Create power line
line = await repo.create_power_line(
    code="LINE-001",
    voltage_level_kv=22.0,
    coordinates=[
        (100.5018, 13.7563),
        (100.5025, 13.7570),
        (100.5030, 13.7580)
    ],
    from_substation_id=substation.id,
    line_type="overhead",
    conductor_type="NA2XS2Y 1x185 RM/25 12/20 kV"
)
```

### Store Meter Readings

```python
from datetime import datetime

# Store reading
reading = await repo.store_reading(
    meter_id="METER_001",
    timestamp=datetime.utcnow(),
    energy_generated_kwh=5.234,
    energy_consumed_kwh=2.145,
    voltage_v=239.8,
    current_a=12.3,
    frequency_hz=50.02,
    signature="base64-encoded-signature"
)
```

## pgAdmin Usage

Access pgAdmin at: `http://localhost:5050`

**Login:**
- Email: `admin@gridtokenx.local`
- Password: `admin_password`

**Add Server:**
1. Right-click "Servers" → Register → Server
2. Name: `GridTokenX PostGIS`
3. Host: `postgres` (or `localhost` if connecting externally)
4. Port: `5432`
5. Username: `gridtokenx`
6. Password: `gridtokenx_password`

**View Spatial Data:**
1. Navigate to: Databases → gridtokenx → Schemas → grid → Tables
2. Right-click table → View/Edit Data → All Rows
3. Click geometry column to view map preview

## Docker Commands

```bash
# Start all services
docker-compose up -d

# Stop all services
docker-compose down

# View logs
docker-compose logs -f postgres
docker-compose logs -f simulator

# Restart specific service
docker-compose restart simulator

# Database backup
docker exec gridtokenx-postgres pg_dump -U gridtokenx gridtokenx > backup.sql

# Database restore
docker exec -i gridtokenx-postgres psql -U gridtokenx gridtokenx < backup.sql

# Run SQL query
docker exec -it gridtokenx-postgres psql -U gridtokenx -d gridtokenx -c "SELECT COUNT(*) FROM grid.substations;"

# Shell access
docker exec -it gridtokenx-postgres bash
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | - | PostgreSQL connection URL |
| `REDIS_URL` | `redis://localhost:6379` | Redis connection URL |
| `INFLUXDB_URL` | `http://localhost:8086` | InfluxDB URL |
| `INFLUXDB_TOKEN` | - | InfluxDB API token |
| `INFLUXDB_ORG` | `gridtokenx` | InfluxDB organization |
| `INFLUXDB_BUCKET` | `meter_readings` | InfluxDB bucket name |
| `SIMULATION_INTERVAL` | `15` | Simulation interval (seconds) |
| `NUM_METERS` | `100` | Number of meters to simulate |

## Troubleshooting

### Connection Issues

```bash
# Check if PostgreSQL is running
docker-compose ps postgres

# View PostgreSQL logs
docker-compose logs postgres

# Test connection
docker exec -it gridtokenx-postgres psql -U gridtokenx -d gridtokenx -c "SELECT 1;"
```

### PostGIS Not Enabled

```sql
-- Enable PostGIS manually
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;
```

### Permission Errors

```sql
-- Grant permissions
GRANT USAGE ON SCHEMA grid TO gridtokenx;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA grid TO gridtokenx;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA grid TO gridtokenx;
```

### Slow Queries

```sql
-- Check index usage
EXPLAIN ANALYZE SELECT * FROM grid.substations
WHERE ST_DWithin(
    location,
    ST_SetSRID(ST_MakePoint(100.5, 13.7), 4326),
    1000
);

-- Add index if missing
CREATE INDEX idx_substations_location ON grid.substations USING GIST (location);
```

## Performance Tips

1. **Use Spatial Indexes**: Always use `ST_DWithin` instead of `ST_Distance` for radius searches
2. **Partition Tables**: Meter readings are partitioned by timestamp
3. **Connection Pooling**: Use asyncpg with connection pool (default: 10 connections)
4. **Batch Inserts**: Insert meter readings in batches of 1000
5. **GeoJSON Caching**: Cache GeoJSON exports in Redis for frequently accessed areas

## Next Steps

- [ ] Import existing grid data from GeoJSON files
- [ ] Set up automatic meter registration
- [ ] Configure real-time data streaming to InfluxDB
- [ ] Enable SSL/TLS for database connections
- [ ] Set up database replication for high availability

## References

- [PostGIS Documentation](https://postgis.net/documentation/)
- [GeoAlchemy2 Documentation](https://geoalchemy-2.readthedocs.io/)
- [SQLAlchemy Core](https://docs.sqlalchemy.org/en/20/core/)
- [Thai Grid Standards (MEA/PEA)](../../../docs/THAI_GRID_TOPOLOGY.md)

---

**Part of the GridTokenX Platform**

For more information:
- `docs/THAI_GRID_TOPOLOGY.md` - Thai grid topology guide
- `docs/GRID_MAP_VIEWER.md` - Map viewer documentation
- `docs/THAI_INFRASTRUCTURE_MAP_INTEGRATION.md` - React integration guide
