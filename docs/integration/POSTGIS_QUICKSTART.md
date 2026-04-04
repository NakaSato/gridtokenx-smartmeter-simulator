# PostGIS Quick Start Guide

Get the Thai Infrastructure Map with PostGIS database up and running in 5 minutes!

## 🚀 Quick Start (5 Minutes)

### Step 1: Start PostGIS Database

```bash
# Start PostgreSQL + PostGIS
docker-compose up -d postgres

# Wait for database to be ready (check logs)
docker-compose logs -f postgres

# You should see: "database system is ready to accept connections"
```

### Step 2: Verify PostGIS Installation

```bash
# Check PostGIS version
docker exec -it gridtokenx-postgres psql -U gridtokenx -d gridtokenx \
  -c "SELECT PostGIS_Version();"
```

**Expected output:**
```
                postgis_version                
---------------------------------------------
 3.3.2 r17448 [EXT]
(1 row)
```

### Step 3: Generate Sample Data

```bash
# Generate realistic Thai grid data (500 meters, Bangkok)
uv run python examples/import_grid_data.py \
  --generate \
  --region bangkok \
  --meters 500 \
  --substations 5
```

**Expected output:**
```
2024-01-01 12:00:00 - INFO - Connecting to database...
2024-01-01 12:00:01 - INFO - Connected to PostGIS: 3.3.2 r17448
2024-01-01 12:00:01 - INFO - Generating sample data for bangkok (500 meters)
2024-01-01 12:00:01 - INFO - Generating substations...
2024-01-01 12:00:02 - INFO - Generated 5 substations
2024-01-01 12:00:02 - INFO - Generating transformers...
2024-01-01 12:00:03 - INFO - Generated 50 transformers
2024-01-01 12:00:03 - INFO - Generating power lines...
2024-01-01 12:00:04 - INFO - Generated 8 power lines
2024-01-01 12:00:04 - INFO - Generating meters...
2024-01-01 12:00:06 - INFO - Generated 500 meters
2024-01-01 12:00:06 - INFO - Generation complete: {...}

============================================================
DATABASE STATISTICS
============================================================

Substations by Voltage:
     500.0 kV:      1
     230.0 kV:      1
     115.0 kV:      1
      22.0 kV:      2

Power Lines by Voltage:
     500.0 kV:      12.45 km
     230.0 kV:       8.32 km
     115.0 kV:      15.67 km
      22.0 kV:      45.89 km

Meters by Type:
        solar_prosumer:    200
       grid_consumer:    175
     hybrid_prosumer:     75
              battery:     25
         ev_charger:     25

Totals:
  Total Substations: 5
  Total Lines: 82.33 km
  Total Meters: 500
============================================================
```

### Step 4: Start Simulator

```bash
# Start all services (simulator + database)
docker-compose up -d simulator

# Or run locally
uv run start-simulator --mode server --port 8082
```

### Step 5: Test API Endpoints

```bash
# Check database status
curl http://localhost:8082/api/grid/postgis/status

# Get network statistics
curl http://localhost:8082/api/grid/postgis/statistics

# Get network GeoJSON (for map)
curl http://localhost:8082/api/grid/postgis/network/geojson | head -50
```

**Expected response from `/status`:**
```json
{
  "connected": true,
  "postgis_version": "3.3.2 r17448",
  "statistics": {
    "substations_by_voltage": {
      "500": 1,
      "230": 1,
      "115": 1,
      "22": 2
    },
    "meters_by_type": {
      "solar_prosumer": 200,
      "grid_consumer": 175,
      ...
    }
  }
}
```

### Step 6: Open Thai Infrastructure Map

**Option A: With Frontend (Recommended)**

```bash
# Start frontend development server
cd ui
bun run dev

# Open browser to:
# http://localhost:5173/thai-grid-map
```

**Option B: Direct API Access**

Open in browser:
```
http://localhost:8082/api/grid/postgis/network/geojson?voltage_min=0&voltage_max=500
```

Or view the raw GeoJSON data to verify it's working.

---

## 🎯 What You Have Now

✅ **PostGIS Database** running with Thai grid topology  
✅ **500 Smart Meters** distributed across Bangkok  
✅ **5 Substations** (500kV, 230kV, 115kV, 22kV)  
✅ **50 Transformers** connecting MV/LV networks  
✅ **Power Lines** connecting all assets  
✅ **REST API** for spatial queries  
✅ **GeoJSON Export** for map visualization  

---

## 🔍 Test Spatial Queries

### Find Nearest Transformer

```bash
curl "http://localhost:8082/api/grid/postgis/transformers/nearest?longitude=100.5018&latitude=13.7563&max_distance_m=500"
```

**Response:**
```json
{
  "transformer_id": 12,
  "code": "TXN-00012",
  "distance_m": 125.4,
  "capacity_kva": 500
}
```

### Get Nearby Meters

```bash
curl "http://localhost:8082/api/grid/postgis/meters/nearby?longitude=100.5018&latitude=13.7563&radius_m=1000&meter_type=solar_prosumer"
```

**Response:**
```json
{
  "count": 45,
  "meters": [
    {
      "meter_id": "METER-SOL-000123",
      "meter_type": "solar_prosumer",
      "distance_m": 87.3,
      "location": "0101000020E6100000..."
    },
    ...
  ]
}
```

### Get Substations by Voltage

```bash
curl "http://localhost:8082/api/grid/postgis/substations?voltage=22"
```

### Bounding Box Query

```bash
curl "http://localhost:8082/api/grid/postgis/substations?min_lon=100.4&min_lat=13.7&max_lon=100.6&max_lat=13.8"
```

---

## 🗺️ View on Map

### Using the React Map Viewer

1. Navigate to: `http://localhost:5173/thai-grid-map`
2. The map will automatically load data from PostGIS
3. Use layer controls to toggle voltage levels
4. Click on elements to see details
5. Export data using the "Export" button

### Using pgAdmin (Database UI)

1. Open: `http://localhost:5050`
2. Login:
   - Email: `admin@gridtokenx.local`
   - Password: `admin_password`
3. Add Server:
   - Host: `postgres`
   - Username: `gridtokenx`
   - Password: `gridtokenx_password`
4. Navigate to: Databases → gridtokenx → Schemas → grid
5. Right-click table → View/Edit Data

---

## 📊 Database Schema Overview

```
grid.substations       (5 rows)
  ├─ id, name, code
  ├─ voltage_level_kv (500, 230, 115, 22)
  ├─ location (POINT)
  └─ operator (EGAT, MEA)

grid.transformers      (50 rows)
  ├─ id, code
  ├─ voltage_primary_kv (22kV)
  ├─ voltage_secondary_kv (0.4kV)
  ├─ capacity_kva (160-630 kVA)
  └─ location (POINT)

grid.power_lines       (8 rows)
  ├─ id, code
  ├─ voltage_level_kv
  ├─ geom (LINESTRING)
  └─ length_km (calculated)

grid.meters            (500 rows)
  ├─ id, meter_id
  ├─ meter_type (solar_prosumer, etc.)
  ├─ transformer_id (FK)
  └─ location (POINT)
```

---

## 🧹 Cleanup

```bash
# Stop all services
docker-compose down

# Remove volumes (delete all data)
docker-compose down -v

# Restart fresh
docker-compose up -d postgres
uv run python examples/import_grid_data.py --generate --region bangkok
```

---

## 🎨 Customize Sample Data

### Generate Different Regions

```bash
# Central Thailand (rural)
uv run python examples/import_grid_data.py \
  --generate --region central --meters 1000

# Chiang Mai
uv run python examples/import_grid_data.py \
  --generate --region chiang_mai --meters 300

# Phuket
uv run python examples/import_grid_data.py \
  --generate --region phuket --meters 400
```

### Generate More Data

```bash
# Large-scale test (10,000 meters)
uv run python examples/import_grid_data.py \
  --generate --region bangkok --meters 10000 --substations 20
```

### Import from GeoJSON

```bash
# Import existing grid data
uv run python examples/import_grid_data.py \
  --input data/bangkok_urban.geojson --validate
```

---

## 🐛 Troubleshooting

### Database Connection Failed

```bash
# Check if PostgreSQL is running
docker-compose ps postgres

# View logs
docker-compose logs postgres

# Restart database
docker-compose restart postgres
```

### PostGIS Not Enabled

```bash
# Enable PostGIS manually
docker exec -it gridtokenx-postgres psql -U gridtokenx -d gridtokenx <<EOF
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;
EOF
```

### No Data in Database

```bash
# Check table counts
docker exec -it gridtokenx-postgres psql -U gridtokenx -d gridtokenx <<EOF
SELECT 
  (SELECT COUNT(*) FROM grid.substations) as substations,
  (SELECT COUNT(*) FROM grid.transformers) as transformers,
  (SELECT COUNT(*) FROM grid.power_lines) as lines,
  (SELECT COUNT(*) FROM grid.meters) as meters;
EOF
```

### API Returns Empty GeoJSON

1. Verify database has data (see above)
2. Check API logs: `docker-compose logs simulator`
3. Test direct database query:
   ```bash
   docker exec -it gridtokenx-postgres psql -U gridtokenx -d gridtokenx \
     -c "SELECT grid.export_network_geojson(0, 500);"
   ```

---

## 📚 Next Steps

1. **Explore API Endpoints** - See [`docs/POSTGIS_INTEGRATION.md`](docs/POSTGIS_INTEGRATION.md)
2. **Customize Map Visualization** - See [`docs/THAI_INFRASTRUCTURE_MAP_INTEGRATION.md`](docs/THAI_INFRASTRUCTURE_MAP_INTEGRATION.md)
3. **Add Real-time Data** - Stream meter readings to InfluxDB
4. **Import Real Grid Data** - Use `examples/import_grid_data.py`
5. **Build Production Deployment** - Configure SSL, backups, monitoring

---

## 📞 Quick Reference

| Service | URL | Credentials |
|---------|-----|-------------|
| Simulator API | `http://localhost:8082` | - |
| Thai Infrastructure Map | `http://localhost:5173/thai-grid-map` | - |
| pgAdmin | `http://localhost:5050` | `admin@gridtokenx.local` / `admin_password` |
| PostgreSQL | `localhost:5432` | `gridtokenx` / `gridtokenx_password` |
| Redis | `localhost:6379` | - |
| InfluxDB | `http://localhost:8086` | `admin` / `admin_password` |

---

## 🎉 Success!

You now have a fully functional **PostGIS-backed Thai Infrastructure Map** with:

- ✅ Spatial database for grid topology
- ✅ 500+ simulated smart meters
- ✅ REST API for spatial queries
- ✅ Interactive map visualization
- ✅ GeoJSON export capabilities

**Ready to visualize your Thai electrical distribution network!** 🗺️⚡

---

**Part of the GridTokenX Platform**

For detailed documentation: [`docs/POSTGIS_INTEGRATION.md`](docs/POSTGIS_INTEGRATION.md)
