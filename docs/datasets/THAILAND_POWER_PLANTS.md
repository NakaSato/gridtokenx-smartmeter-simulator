# Thailand Power Plants Statistics

A comprehensive power generation statistics and visualization feature for Thailand's electrical grid, similar to [Open Infrastructure Map](https://openinframap.org/stats/area/Thailand/plants).

---

## 🎯 Overview

This feature provides real-time statistics and interactive visualization of Thailand's power generation infrastructure, including:

- **Thermal power plants** (EGAT)
- **Combined cycle plants**
- **Gas turbines**
- **Hydroelectric dams**
- **Solar farms**
- **Wind farms**
- **Biomass plants**

---

## 📊 Features

### 1. Interactive Dashboard

**URL:** `http://localhost:8082/api/thailand/power-plants`

A beautiful, responsive web dashboard with:
- Summary statistics cards
- Capacity breakdown charts (by fuel type, by region)
- Interactive map with plant locations
- Detailed power plant table

![Dashboard Preview](https://via.placeholder.com/800x400?text=Thailand+Power+Plants+Dashboard)

### 2. REST API

**Base URL:** `http://localhost:8082/api/thailand/power-plants`

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/power-plants` | GET | HTML dashboard |
| `/power-plants/statistics` | GET | Comprehensive statistics |
| `/power-plants/by-fuel` | GET | Breakdown by fuel type |
| `/power-plants/by-region` | GET | Breakdown by region |
| `/power-plants/list` | GET | List of all power plants |

---

## 🚀 Quick Start

### 1. Generate Sample Data

```bash
# Generate 19 realistic Thailand power plants
uv run python examples/generate_thailand_power_plants.py
```

**Output:**
```
🇹🇭 Generating 19 Thailand power plants...
============================================================

✅ Power plants generated successfully!

Summary by type:
  Combined_cycle    3 plants,   6150 MVA
  Thermal           2 plants,   4950 MVA
  Gas_turbine       2 plants,   1400 MVA
  Hydro             4 plants,   1490 MVA
  Solar             4 plants,    198 MVA
  Biomass           2 plants,     45 MVA
  Wind              2 plants,     55 MVA

  Total            19 plants,  14288 MVA

📊 View statistics at:
   http://localhost:8082/api/thailand/power-plants
```

### 2. View Dashboard

Open in browser:
```
http://localhost:8082/api/thailand/power-plants
```

### 3. Query API

```bash
# Get comprehensive statistics
curl http://localhost:8082/api/thailand/power-plants/statistics | jq

# Get breakdown by fuel type
curl http://localhost:8082/api/thailand/power-plants/by-fuel | jq

# Get breakdown by region
curl http://localhost:8082/api/thailand/power-plants/by-region | jq

# Get list of all plants
curl http://localhost:8082/api/thailand/power-plants/list | jq
```

---

## 📈 API Response Examples

### Statistics Endpoint

```json
{
  "total_capacity_mw": 11430.4,
  "total_plants": 19,
  "solar_capacity_mw": 158.4,
  "renewable_percentage": 12.5,
  "by_fuel_type": {
    "combined_cycle": 4920.0,
    "thermal": 3960.0,
    "gas_turbine": 1120.0,
    "hydro": 1192.0,
    "solar": 158.4,
    "wind": 44.0,
    "biomass": 36.0
  },
  "by_region": {
    "Central": 7170.4,
    "Eastern": 2200.0,
    "Southern": 656.0,
    "Northern": 1280.0,
    "Northeastern": 124.0
  },
  "plants": [
    {
      "id": 1,
      "name": "Bang Pakong Power Plant",
      "plant_type": "combined_cycle",
      "capacity_mw": 2400.0,
      "region": "Central",
      "province": "Chachoengsao",
      "latitude": 13.5394,
      "longitude": 100.9847,
      "status": "operational",
      "voltage_kv": 500.0
    },
    // ... more plants
  ],
  "timestamp": "2026-03-29T22:46:30.960101Z"
}
```

---

## 🗺️ Included Power Plants

### Major Thermal Plants

| Name | Type | Capacity (MW) | Location |
|------|------|---------------|----------|
| Bang Pakong | Combined Cycle | 2,400 | Chachoengsao |
| Map Ta Phut | Thermal | 2,200 | Rayong |
| Ratchaburi | Thermal | 1,760 | Ratchaburi |
| South Bangkok | Combined Cycle | 1,400 | Samut Prakan |
| North Bangkok | Combined Cycle | 1,120 | Pathum Thani |

### Hydroelectric Dams

| Name | Capacity (MW) | Location |
|------|---------------|----------|
| Bhumibol Dam | 400 | Tak |
| Sirikit Dam | 360 | Uttaradit |
| Srinagarind Dam | 240 | Kanchanaburi |
| Vajiralongkorn Dam | 192 | Kanchanaburi |

### Renewable Energy

| Name | Type | Capacity (MW) | Location |
|------|------|---------------|----------|
| Lopburi Solar Farm | Solar | 58.4 | Lopburi |
| Nakhon Ratchasima Solar | Solar | 40.0 | Nakhon Ratchasima |
| Nakhon Ratchasima Wind | Wind | 24.0 | Nakhon Ratchasima |
| Phrae Biomass | Biomass | 20.0 | Phrae |

---

## 🛠️ Technical Details

### Database Schema

Power plants are stored in the `grid.substations` table:

```sql
CREATE TABLE grid.substations (
    id               SERIAL PRIMARY KEY,
    name             VARCHAR(255) NOT NULL,
    type             VARCHAR(50),
    voltage_level_kv NUMERIC(6,1),
    capacity_mva     NUMERIC(10,2),
    province         VARCHAR(100),
    district         VARCHAR(100),
    location         GEOGRAPHY(Point, 4326),
    status           VARCHAR(20),
    address          TEXT,
    created_at       TIMESTAMP DEFAULT NOW(),
    updated_at       TIMESTAMP DEFAULT NOW()
);
```

### Plant Type Mapping

| Voltage Level | Plant Type |
|---------------|------------|
| ≥ 500 kV | Thermal (Major stations) |
| ≥ 230 kV | Combined Cycle |
| ≥ 115 kV | Gas Turbine |
| < 115 kV | Solar/Distributed |

### Renewable Energy Calculation

Renewable types include:
- `solar`
- `wind`
- `hydro`
- `biomass`
- `geothermal`

**Formula:**
```
Renewable % = (Renewable Capacity / Total Capacity) × 100
```

---

## 🎨 Dashboard Features

### Summary Cards

- **Total Capacity** - Sum of all plant capacities in MW
- **Power Plants** - Count of all power plants
- **Solar Installations** - Count of solar plants
- **Renewable %** - Percentage of renewable capacity

### Charts

1. **Capacity by Fuel Type** (Doughnut Chart)
   - Visual breakdown of generation capacity by energy source
   - Color-coded by fuel type

2. **Capacity by Region** (Bar Chart)
   - Geographic distribution of power capacity
   - Shows regional energy infrastructure

### Interactive Map

- **Leaflet.js** powered map
- Markers for each power plant
- Click for details popup
- Auto-centered on Thailand

### Data Table

- Sortable list of all power plants
- Shows: Name, Type, Region, Capacity, Status
- Limited to first 50 plants for performance

---

## 📝 Customization

### Add Custom Power Plants

```python
from smart_meter_simulator.database.repository import PostGISRepository
from sqlalchemy import text
import asyncio

async def add_custom_plant():
    repo = PostGISRepository("postgresql+asyncpg://...")
    
    async for session in repo.get_session():
        await session.execute(text("""
            INSERT INTO grid.substations (
                name, type, voltage_level_kv, capacity_mva,
                province, district, location, status
            ) VALUES (
                'My Power Plant', 'solar', 22, 50,
                'Bangkok', 'Central',
                ST_SetSRID(ST_MakePoint(100.5018, 13.7563), 4326),
                'operational'
            )
        """))
        await session.commit()
        break

asyncio.run(add_custom_plant())
```

### Filter by Type

```bash
# Generate only solar plants
uv run python examples/generate_thailand_power_plants.py --type solar

# Generate only hydro plants
uv run python examples/generate_thailand_power_plants.py --type hydro
```

---

## 🔗 Integration

### GridTokenX Platform

This feature integrates with:
- **GIS Database** (Port 5433) - Spatial data storage
- **Smart Meter Simulator** - Real-time grid monitoring
- **Thai Infrastructure Map** - Frontend visualization

### External Systems

- **EGAT Data** - Can import from EGAT APIs
- **OpenStreetMap** - Map tiles for visualization
- **Chart.js** - Interactive charts

---

## 🐛 Troubleshooting

### No Data Showing

```bash
# Check if data exists
docker exec gridtokenx-gis-postgres psql -U gridtokenx -d gridtokenx_gis \
  -c "SELECT COUNT(*) FROM grid.substations;"

# If 0, generate sample data
uv run python examples/generate_thailand_power_plants.py
```

### API Returns 503

```bash
# Check GIS database is running
docker-compose ps gis-postgres

# Check simulator logs
docker-compose logs simulator | grep "power plants"
```

### Map Not Loading

- Ensure internet connection for OpenStreetMap tiles
- Check browser console for JavaScript errors
- Verify Leaflet.js CDN is accessible

---

## 📚 Related Documentation

- [`GIS_DATABASE_COMPOSE.md`](GIS_DATABASE_COMPOSE.md) - GIS database setup
- [`POSTGIS_INTEGRATION.md`](POSTGIS_INTEGRATION.md) - PostGIS integration
- [`THAI_GRID_INTEGRATION.md`](THAI_GRID_INTEGRATION.md) - Thai grid modeling
- [`DATABASE_MIGRATION_GUIDE.md`](DATABASE_MIGRATION_GUIDE.md) - Database migration

---

## 🎯 Future Enhancements

- [ ] Real-time generation data from smart meters
- [ ] Historical capacity trends
- [ ] CO₂ emissions calculations
- [ ] Grid stability metrics
- [ ] Export to various formats (CSV, GeoJSON, PDF)
- [ ] Comparison with regional neighbors
- [ ] Energy mix projections

---

**Part of the GridTokenX Smart Meter Simulator**

Inspired by [Open Infrastructure Map](https://openinframap.org/)
