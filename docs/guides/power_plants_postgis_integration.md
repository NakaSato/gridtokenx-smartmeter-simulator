# Thailand Power Plants - PostGIS Integration

Complete integration for loading Thailand power plant data into your PostGIS database with REST API access.

---

## Quick Start

### 1. Run Database Migration

```bash
cd backend

# Apply migration to create power_plants table
psql -h localhost -p 5432 -U gridtokenx -d gridtokenx -f database/migrations/003_power_plants.sql

# Or via Docker
docker exec -i postgres psql -U gridtokenx -d gridtokenx < database/migrations/003_power_plants.sql
```

### 2. Save Your GeoJSON Data

Save your Thailand power plant GeoJSON to:
```
backend/data/thailand_power_plants.geojson
```

### 3. Import to Database

```bash
cd backend

# Import from GeoJSON file
uv run python scripts/import_plants_to_db.py data/thailand_power_plants.geojson

# With custom database URL
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/gridtokenx \
uv run python scripts/import_plants_to_db.py data/thailand_power_plants.geojson
```

### 4. Query via API

```bash
# Start the server
uv run uvicorn smart_meter_simulator.app:app --host 0.0.0.0 --port 8082

# List all plants
curl http://localhost:8082/api/v1/power-plants/

# Get statistics
curl http://localhost:8082/api/v1/power-plants/stats

# Filter by type
curl "http://localhost:8082/api/v1/power-plants/?plant_type=solar&limit=10"

# Nearby search
curl "http://localhost:8082/api/v1/power-plants/search/nearby?lat=13.75&lon=100.5&radius_km=100"
```

---

## What Was Created

### 1. Database Table (`grid.power_plants`)

**Location:** `backend/database/migrations/003_power_plants.sql`

**Schema:**
```sql
CREATE TABLE grid.power_plants (
    id SERIAL PRIMARY KEY,
    plant_id VARCHAR(100) UNIQUE NOT NULL,
    name VARCHAR(500) NOT NULL,
    plant_type VARCHAR(50) NOT NULL,          -- hydropower, solar, wind, oil/gas, coal, bioenergy
    fuel_type VARCHAR(100),                   -- natural_gas, lignite, etc.
    technology VARCHAR(100),                  -- combined_cycle, PV, CFB, etc.
    capacity_mw NUMERIC(10,2) NOT NULL,
    status VARCHAR(50) DEFAULT 'operating',
    start_year INTEGER,
    operator VARCHAR(255) DEFAULT 'EGAT',
    location GEOGRAPHY(POINT, 4326) NOT NULL, -- PostGIS spatial column
    latitude DOUBLE PRECISION GENERATED ALWAYS AS (ST_Y(location::geometry)) STORED,
    longitude DOUBLE PRECISION GENERATED ALWAYS AS (ST_X(location::geometry)) STORED,
    province VARCHAR(100),
    region VARCHAR(50),                       -- bangkok, central, north, northeast, south, east
    voltage_level_kv NUMERIC(6,1),            -- 500, 230, 115, 22
    is_renewable BOOLEAN GENERATED ALWAYS AS (...) STORED,
    carbon_intensity_gco2_kwh NUMERIC(10,2),
    source VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

**Spatial Indexes:**
- `idx_power_plants_location` - GIST index for spatial queries
- `idx_power_plants_type` - Filter by plant type
- `idx_power_plants_status` - Filter by operational status
- `idx_power_plants_capacity` - Sort/filter by capacity
- `idx_power_plants_renewable` - Quick renewable energy queries
- `idx_power_plants_region` - Regional filtering

**Views:**
- `grid.vw_plants_by_type` - Capacity breakdown by plant type
- `grid.vw_plants_by_region` - Regional distribution
- `grid.vw_renewable_summary` - Renewable energy statistics
- `grid.vw_plants_near_substations` - Plants near grid substations

**Functions:**
- `grid.find_plants_in_radius(lat, lon, radius_km)` - Spatial search
- `grid.get_plant_capacity_stats()` - Aggregate statistics

### 2. SQLAlchemy ORM Model

**Location:** `backend/src/smart_meter_simulator/database/models.py`

```python
class PowerPlant(Base):
    __tablename__ = 'power_plants'
    __table_args__ = {'schema': 'grid'}
    
    id: Mapped[int]
    plant_id: Mapped[str]
    name: Mapped[str]
    plant_type: Mapped[str]
    capacity_mw: Mapped[Decimal]
    location: Mapped[Geography]  # PostGIS POINT
    
    # Methods
    def get_coordinates(self) -> tuple[float, float]
    def set_coordinates(self, longitude: float, latitude: float)
    @property
    def is_renewable(self) -> bool
```

### 3. Repository Methods

**Location:** `backend/src/smart_meter_simulator/database/repository.py`

```python
# Single plant
await repo.create_power_plant(plant_data)
await repo.get_power_plant(plant_id)
await repo.delete_power_plant(plant_id)

# Batch import
await repo.create_power_plants_batch(plants_data)

# Queries
await repo.get_power_plants(
    plant_type="solar",
    status="operating",
    region="bangkok",
    renewable_only=True,
    limit=100,
    offset=0
)

# Spatial search (uses PostGIS ST_DWithin)
await repo.get_power_plants_near(lat=13.75, lon=100.5, radius_km=50)

# Statistics
await repo.get_power_plant_stats()
```

### 4. REST API Endpoints

**Location:** `backend/src/smart_meter_simulator/routers/power_plants_v1.py`

| Method | Endpoint | Description |
|--------|----------|-------------|
| **POST** | `/api/v1/power-plants/import` | Import from GeoJSON file (multipart/form-data) |
| **POST** | `/api/v1/power-plants/` | Create single plant |
| **GET** | `/api/v1/power-plants/` | List plants (with filters) |
| **GET** | `/api/v1/power-plants/{plant_id}` | Get plant details |
| **GET** | `/api/v1/power-plants/search/nearby` | Spatial search (lat, lon, radius) |
| **GET** | `/api/v1/power-plants/stats` | Aggregate statistics |
| **DELETE** | `/api/v1/power-plants/{plant_id}` | Delete plant |

### 5. Import Script

**Location:** `backend/scripts/import_plants_to_db.py`

**Features:**
- Parses GeoJSON FeatureCollection format
- Auto-generates plant IDs
- Estimates region from coordinates
- Determines grid voltage based on capacity
- Calculates carbon intensity
- Batch inserts with error handling

---

## API Examples

### Import GeoJSON via API

```bash
curl -X POST http://localhost:8082/api/v1/power-plants/import \
  -F "file=@data/thailand_power_plants.geojson"
```

**Response:**
```json
{
  "created": 547,
  "errors": 0,
  "error_details": []
}
```

### List Plants with Filters

```bash
# Solar plants only
curl "http://localhost:8082/api/v1/power-plants/?plant_type=solar&limit=10"

# Renewable energy only
curl "http://localhost:8082/api/v1/power-plants/?renewable_only=true"

# By operator
curl "http://localhost:8082/api/v1/power-plants/?operator=GLOW"

# Paginated
curl "http://localhost:8082/api/v1/power-plants/?limit=50&offset=100"
```

**Response:**
```json
{
  "plants": [
    {
      "id": 1,
      "plant_id": "TH_HYDRO_0001",
      "name": "Bhumibol hydroelectric plant",
      "plant_type": "hydropower",
      "capacity_mw": 779.0,
      "status": "operating",
      "latitude": 17.2414,
      "longitude": 98.9732,
      "is_renewable": true
    }
  ],
  "total": 547,
  "limit": 10,
  "offset": 0,
  "has_more": true
}
```

### Get Plant Details

```bash
curl http://localhost:8082/api/v1/power-plants/TH_HYDRO_0001
```

**Response:**
```json
{
  "id": 1,
  "plant_id": "TH_HYDRO_0001",
  "name": "Bhumibol hydroelectric plant",
  "name_th": null,
  "plant_type": "hydropower",
  "fuel_type": null,
  "technology": "conventional storage",
  "capacity_mw": 779.0,
  "units": 1,
  "status": "operating",
  "start_year": 1964,
  "operator": "EGAT",
  "latitude": 17.2414,
  "longitude": 98.9732,
  "province": null,
  "region": "north",
  "voltage_level_kv": 500,
  "grid_connection_type": "transmission",
  "is_renewable": true,
  "carbon_intensity_gco2_kwh": 0,
  "source": "GeoJSON Import - Global Power Plant Tracker",
  "created_at": "2026-04-13T15:30:00Z"
}
```

### Spatial Search

```bash
# Find plants within 100km of Bangkok
curl "http://localhost:8082/api/v1/power-plants/search/nearby?lat=13.75&lon=100.5&radius_km=100"
```

**Response:**
```json
{
  "center": {"lat": 13.75, "lon": 100.5},
  "radius_km": 100,
  "count": 45,
  "plants": [
    {
      "plant_id": "TH_OIL_GAS_0025",
      "name": "Bang Pakong power station",
      "plant_type": "oil/gas",
      "capacity_mw": 704.0,
      "status": "operating",
      "latitude": 13.501,
      "longitude": 101.0253,
      "distance_km": 42.3
    }
  ]
}
```

### Statistics

```bash
curl http://localhost:8082/api/v1/power-plants/stats
```

**Response:**
```json
{
  "by_type": {
    "oil/gas": {
      "plant_type": "oil/gas",
      "plant_count": 85,
      "total_capacity_mw": 45230.0,
      "avg_capacity_mw": 532.12
    },
    "solar": {
      "plant_type": "solar",
      "plant_count": 234,
      "total_capacity_mw": 3456.5,
      "avg_capacity_mw": 14.77
    },
    "hydropower": {
      "plant_type": "hydropower",
      "plant_count": 9,
      "total_capacity_mw": 3170.0,
      "avg_capacity_mw": 352.22
    }
  },
  "renewable": {
    "count": 267,
    "capacity_mw": 7892.3,
    "percentage": 18.45
  },
  "total": {
    "count": 547,
    "capacity_mw": 42780.5
  }
}
```

---

## Direct SQL Queries

### Total Capacity by Type

```sql
SELECT 
    plant_type,
    COUNT(*) as plants,
    SUM(capacity_mw) as total_mw,
    ROUND(AVG(capacity_mw), 2) as avg_mw
FROM grid.power_plants
WHERE status = 'operating'
GROUP BY plant_type
ORDER BY total_mw DESC;
```

### Renewable Energy Percentage

```sql
SELECT 
    COUNT(*) FILTER (WHERE is_renewable) as renewable_plants,
    SUM(capacity_mw) FILTER (WHERE is_renewable) as renewable_mw,
    ROUND(
        SUM(capacity_mw) FILTER (WHERE is_renewable) / 
        SUM(capacity_mw) * 100, 2
    ) as renewable_pct
FROM grid.power_plants
WHERE status = 'operating';
```

### Plants Near Location (50km)

```sql
SELECT 
    name,
    plant_type,
    capacity_mw,
    ST_Distance(
        location,
        ST_SetSRID(ST_MakePoint(100.5, 13.75), 4326)::geography
    ) / 1000 as distance_km
FROM grid.power_plants
WHERE ST_DWithin(
    location,
    ST_SetSRID(ST_MakePoint(100.5, 13.75), 4326)::geography,
    50000
)
AND status = 'operating'
ORDER BY distance_km
LIMIT 10;
```

---

## Integration with Simulator

### Use Plants as External Grid Sources

```python
from smart_meter_simulator.database.repository import PostGISRepository
import pandapower as pp

# Load plants from database
repo = PostGISRepository("postgresql+asyncpg://...")
plants, _ = await repo.get_power_plants(status="operating", limit=50)

# Create pandapower network
net = pp.create_empty_network()

# Add plants as external grids or generators
for plant in plants:
    if plant['capacity_mw'] > 100:
        # Large plants = external grid connection
        pp.create_ext_grid(
            net,
            bus=bus_idx,
            vm_pu=1.0,
            s_sc_max_mva=plant['capacity_mw'],
        )
    else:
        # Smaller plants = generators
        pp.create_gen(
            net,
            bus=bus_idx,
            p_mw=plant['capacity_mw'],
            vm_pu=1.0,
        )
```

### Map Plants to Meters

```python
# Find meters near power plants
nearby = await repo.get_power_plants_near(lat=13.75, lon=100.5, radius_km=10)

for plant in nearby:
    # Create meters for plant distribution
    meter_config = {
        "meter_type": "solar_prosumer" if plant['is_renewable'] else "grid_consumer",
        "location": {
            "latitude": plant['latitude'],
            "longitude": plant['longitude'],
        },
        "base_generation_kw": plant['capacity_mw'] * 0.001,  # Scale down
    }
```

---

## Troubleshooting

### Migration Fails

```bash
# Check PostGIS is enabled
psql -h localhost -p 5432 -U gridtokenx -d gridtokenx -c "SELECT PostGIS_Version();"

# Manually create extension
psql -h localhost -p 5432 -U gridtokenx -d gridtokenx -c "CREATE EXTENSION IF NOT EXISTS postgis;"
```

### Import Fails

```bash
# Check file format
jq '.type' data/thailand_power_plants.geojson
# Should output: "FeatureCollection"

# Check first feature
jq '.features[0]' data/thailand_power_plants.geojson

# Test with small subset
jq '{type: .type, features: .features[:10]}' data/thailand_power_plants.geojson > test.geojson
uv run python scripts/import_plants_to_db.py test.geojson
```

### API Returns 500

```bash
# Check database connection
curl http://localhost:8082/api/v1/grid/status

# Check logs
tail -f logs/app.log | grep -i "power.plant"

# Verify table exists
psql -h localhost -p 5432 -U gridtokenx -d gridtokenx -c "\dt grid.power_plants"
```

---

## Next Steps

1. **Geocode provinces** - Add province/district from coordinates
2. **Link to substations** - Map plants to nearest grid substation
3. **Time-series data** - Track plant output over time
4. **Carbon tracking** - Calculate emissions by fuel type
5. **Forecasting** - Predict renewable output (solar/wind)
6. **VPP integration** - Aggregate plants into virtual power plants

---

**Database Schema:** Migration `003_power_plants.sql`  
**ORM Model:** `database/models.py:PowerPlant`  
**Repository:** `database/repository.py` (PowerPlant methods)  
**API Router:** `routers/power_plants_v1.py`  
**Import Script:** `scripts/import_plants_to_db.py`
