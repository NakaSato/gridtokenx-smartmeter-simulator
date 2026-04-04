# Thai Electrical Grid (EGAT) Integration Guide

This guide explains how to model the **Thai electrical grid system** using the GridTokenX Smart Meter Simulator with PostGIS spatial database.

---

## 🇹🇭 Thai Grid Overview

### Grid Structure

Thailand's electrical grid is operated by three main utilities:

| Utility | Coverage Area | Voltage Levels |
|---------|---------------|----------------|
| **EGAT** (Electricity Generating Authority of Thailand) | Nationwide | 500kV, 230kV, 115kV (Transmission) |
| **MEA** (Metropolitan Electricity Authority) | Bangkok & vicinity | 22kV, 0.4kV (Distribution) |
| **PEA** (Provincial Electricity Authority) | Rest of Thailand | 22kV, 0.4kV (Distribution) |

### Voltage Hierarchy

```
500kV (EGAT Transmission) ─┬─> 230kV (EGAT Transmission) ─┬─> 115kV (EGAT Sub-transmission)
                           │                               │
                           │                               └─> 22kV (MEA/PEA Distribution)
                           │                                       │
                           └───────────────────────────────────────┘
                                                                   └─> 0.4kV (LV Consumer)
```

### Standard Equipment

**Transmission Lines (EGAT):**
| Voltage | Conductor Type | Configuration |
|---------|---------------|---------------|
| 500kV | ACSR 460 mm² (TACSR 460) | Double circuit |
| 230kV | ACSR 300 mm² (TACSR 300) | Double circuit |
| 115kV | ACSR 185 mm² (TACSR 185) | Single circuit |

**Distribution Lines (MEA/PEA):**
| Voltage | Conductor Type | Configuration |
|---------|---------------|---------------|
| 22kV | NA2XS2Y 1x185 RM/25 12/20 kV | Overhead/Underground |
| 0.4kV | NYY 4x185 mm² | Underground |

**Transformers:**
| Primary (kV) | Secondary (kV) | Capacity Range |
|--------------|----------------|----------------|
| 500 | 230 | 250-500 MVA |
| 230 | 115 | 100-250 MVA |
| 115 | 22 | 40-100 MVA |
| 22 | 0.4 | 315-1600 kVA |

---

## 📊 Grid Modeling with PostGIS

### Database Schema

The PostGIS schema models Thai grid assets with spatial accuracy:

```sql
-- Transmission substations (EGAT)
CREATE TABLE grid.substations (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200),
    code VARCHAR(50) UNIQUE,
    voltage_level_kv NUMERIC(10,2),  -- 500, 230, 115, 22, 0.4
    operator VARCHAR(50),             -- EGAT, MEA, PEA
    type VARCHAR(50),                 -- transmission, sub_transmission, distribution
    capacity_mva NUMERIC(10,2),
    location GEOGRAPHY(POINT, 4326)   -- WGS84 coordinates
);

-- Distribution transformers
CREATE TABLE grid.transformers (
    id SERIAL PRIMARY KEY,
    code VARCHAR(50) UNIQUE,
    voltage_primary_kv NUMERIC(10,2),
    voltage_secondary_kv NUMERIC(10,2),
    capacity_kva NUMERIC(10,2),
    location GEOGRAPHY(POINT, 4326)
);

-- Power lines (transmission & distribution)
CREATE TABLE grid.power_lines (
    id SERIAL PRIMARY KEY,
    code VARCHAR(50) UNIQUE,
    voltage_level_kv NUMERIC(10,2),
    geometry GEOGRAPHY(LINESTRING, 4326),
    line_type VARCHAR(50),            -- overhead, underground
    conductor_type VARCHAR(200)
);

-- Smart meters
CREATE TABLE grid.meters (
    id SERIAL PRIMARY KEY,
    meter_id VARCHAR(50) UNIQUE,
    meter_type VARCHAR(50),           -- solar_prosumer, grid_consumer, etc.
    location GEOGRAPHY(POINT, 4326),
    transformer_id INTEGER REFERENCES grid.transformers(id)
);
```

---

## 🛠️ Tools & Utilities

### 1. Thai Grid Generator

Generate realistic sample data for any Thai province:

```bash
# Generate Bangkok grid with 1000 meters
uv run python examples/generate_thai_grid.py \
  --region bangkok \
  --meters 1000 \
  --export

# Generate Chiang Mai grid
uv run python examples/generate_thai_grid.py \
  --region chiang_mai \
  --meters 500

# Generate Phuket grid (tourist area, high EV adoption)
uv run python examples/generate_thai_grid.py \
  --region phuket \
  --meters 300
```

**Supported Regions:**

| Region | Provinces |
|--------|-----------|
| **Central** | bangkok, samut_prakan, nonthaburi, pathum_thani, ayutthaya |
| **Northern** | chiang_mai, chiang_rai, lamphun, lampang |
| **Northeastern (Isan)** | nakhon_ratchasima, khon_kaen, udon_thani, ubon_ratchathani |
| **Southern** | phuket, surat_thani, nakhon_si_thammarat, songkhla |

**Output:**
- Transmission substations (500kV, 230kV, 115kV)
- Distribution substations (22kV)
- Distribution transformers (22kV/0.4kV)
- Power lines with realistic routing
- Smart meters with Thai market distribution

### 2. Import from External Data

Import grid data from CIM, GeoJSON, or other formats:

```bash
# Import from GeoJSON file
uv run python examples/import_grid_data.py \
  --input egat_transmission.geojson \
  --type transmission

# Import from CIM RDF/XML
uv run python examples/import_grid_data.py \
  --input thai_grid_cim.xml \
  --format cim
```

---

## 🔌 API Usage Examples

### Query Thai Grid Assets

**Get all 22kV substations in Bangkok:**

```bash
curl "http://localhost:8082/api/grid/postgis/substations?voltage=22&province=Bangkok"
```

**Find nearest transformer for new connection:**

```bash
curl "http://localhost:8082/api/grid/postgis/transformers/nearest?longitude=100.5018&latitude=13.7563&max_distance_m=500"
```

**Export distribution network (22kV only):**

```bash
curl "http://localhost:8082/api/grid/postgis/network/geojson?voltage_min=22&voltage_max=22" \
  -o bangkok_distribution.geojson
```

**Get network statistics:**

```bash
curl "http://localhost:8082/api/grid/postgis/statistics"
```

Response:
```json
{
  "substations_by_voltage": {
    "500": 2,
    "230": 5,
    "115": 15,
    "22": 120,
    "0.4": 450
  },
  "meters_by_type": {
    "solar_prosumer": 350,
    "grid_consumer": 890,
    "hybrid_prosumer": 145,
    "battery": 45,
    "ev_charger": 78
  },
  "total_meters": 1508
}
```

---

## 📈 Meter Type Distribution (Thai Market)

The simulator uses realistic Thai market distribution:

| Meter Type | Percentage | Description |
|------------|------------|-------------|
| **solar_prosumer** | 35% | Rooftop solar installations |
| **grid_consumer** | 40% | Pure consumers (no generation) |
| **hybrid_prosumer** | 15% | Solar + battery systems |
| **battery** | 5% | Standalone battery storage |
| **ev_charger** | 5% | EV charging stations |

**Adjust distribution for specific regions:**

```python
# Phuket: Higher EV adoption (tourist area)
PHUKET_DISTRIBUTION = {
    "solar_prosumer": 0.30,
    "grid_consumer": 0.35,
    "hybrid_prosumer": 0.15,
    "battery": 0.05,
    "ev_charger": 0.15,  # Higher EV adoption
}

# Bangkok: Higher solar adoption
BANGKOK_DISTRIBUTION = {
    "solar_prosumer": 0.45,  # Higher solar
    "grid_consumer": 0.35,
    "hybrid_prosumer": 0.10,
    "battery": 0.05,
    "ev_charger": 0.05,
}
```

---

## 🗺️ Visualization

### Interactive Map

Access the Thai Infrastructure Map:

```
http://localhost:5173/thai-grid-map
```

**Features:**
- Toggle voltage layers (500kV, 230kV, 115kV, 22kV, 0.4kV)
- Filter by operator (EGAT, MEA, PEA)
- Click assets for details
- Export as GeoJSON
- Real-time meter readings

### Layer Styling

Recommended map styling for Thai grid:

```javascript
const voltageStyles = {
  500: { color: '#FF0000', weight: 6 },  // Red (EGAT EHV)
  230: { color: '#FF6600', weight: 5 },  // Orange (EGAT HV)
  115: { color: '#FFCC00', weight: 4 },  // Yellow (EGAT MV)
  22:  { color: '#00AA00', weight: 3 },  // Green (MEA/PEA MV)
  0.4: { color: '#0066CC', weight: 2 },  // Blue (LV)
};

const operatorIcons = {
  'EGAT': '🏭',   // Transmission
  'MEA': '🏙️',    // Metropolitan
  'PEA': '🏘️',    // Provincial
};
```

---

## 📋 Use Cases

### 1. Grid Planning

**Scenario:** Plan new distribution network for expanding suburb

```python
# 1. Query existing infrastructure
response = requests.get(
    'http://localhost:8082/api/grid/postgis/substations?voltage=22'
)
substations = response.json()['substations']

# 2. Find load centers
response = requests.get(
    'http://localhost:8082/api/grid/postgis/meters/nearby',
    params={'longitude': 100.5, 'latitude': 13.75, 'radius_m': 5000}
)
meters = response.json()['meters']

# 3. Calculate optimal transformer location
# (Use clustering algorithm on meter locations)
```

### 2. Impact Assessment

**Scenario:** Assess impact of new industrial customer

```python
# 1. Find nearest transformer
response = requests.get(
    'http://localhost:8082/api/grid/postgis/transformers/nearest',
    params={'longitude': 100.52, 'latitude': 13.76, 'max_distance_m': 1000}
)
transformer = response.json()

# 2. Check capacity
if transformer['capacity_kva'] < required_load:
    print("Upgrade required!")
else:
    print("Existing infrastructure sufficient")
```

### 3. P2P Trading Analysis

**Scenario:** Identify potential P2P trading clusters

```python
# Find solar prosumers and consumers in same area
response = requests.get(
    'http://localhost:8082/api/grid/postgis/meters/nearby',
    params={
        'longitude': 100.5018,
        'latitude': 13.7563,
        'radius_m': 2000,
        'meter_type': 'solar_prosumer'
    }
)
prosumers = response.json()['meters']

# Match with nearby consumers
response = requests.get(
    'http://localhost:8082/api/grid/postgis/meters/nearby',
    params={
        'longitude': 100.5018,
        'latitude': 13.7563,
        'radius_m': 2000,
        'meter_type': 'grid_consumer'
    }
)
consumers = response.json()['meters']

# Calculate potential P2P matches
print(f"Potential P2P cluster: {len(prosumers)} prosumers, {len(consumers)} consumers")
```

---

## 🔧 Customization

### Add New Province

Edit `examples/generate_thai_grid.py`:

```python
THAI_PROVINCES = {
    # ... existing provinces ...
    "nakhon_pathom": {
        "lon": 100.0672,
        "lat": 13.8199,
        "area": "Central"
    },
}
```

### Custom Voltage Levels

For special industrial zones:

```python
# Add 33kV distribution (some industrial areas)
VOLTAGE_LEVELS["distribution"].append(33.0)

# Create custom transformer ratio
TRANSFORMER_RATIOS.append((115.0, 33.0))
TRANSFORMER_RATIOS.append((33.0, 22.0))
```

### Import Real Grid Data

**From CIM (IEC 61970):**

```python
from smart_meter_simulator.adapters.cim_adapter import CIMAdapter

adapter = CIMAdapter()
grid_data = adapter.import_from_xml("thai_grid_cim.xml")

# Convert to PostGIS
for substation in grid_data['substations']:
    await repo.create_substation(**substation)
```

**From GIS Shapefile:**

```bash
# Convert shapefile to GeoJSON
ogr2ogr -f GeoJSON egat_transmission.geojson egat_transmission.shp

# Import to PostGIS
uv run python examples/import_grid_data.py \
  --input egat_transmission.geojson \
  --type transmission
```

---

## 📊 Performance Benchmarks

**Query Performance (PostGIS with spatial indexes):**

| Query Type | Records | Latency |
|------------|---------|---------|
| Nearest transformer | 10,000 | < 5ms |
| Meters in radius (1km) | 10,000 | < 10ms |
| GeoJSON export (full network) | 50,000 | < 100ms |
| Bounding box query | 10,000 | < 15ms |
| Network statistics | All | < 50ms |

**Generation Performance:**

| Meters | Time | Assets Created |
|--------|------|----------------|
| 500 | ~5s | 5 substations, 20 transformers, 30 lines |
| 1,000 | ~10s | 10 substations, 40 transformers, 60 lines |
| 5,000 | ~45s | 50 substations, 200 transformers, 300 lines |
| 10,000 | ~90s | 100 substations, 400 transformers, 600 lines |

---

## 🎓 Best Practices

### 1. Data Quality

- ✅ Use accurate coordinates (WGS84)
- ✅ Follow EGAT/MEA/PEA naming conventions
- ✅ Include all voltage levels in hierarchy
- ✅ Validate transformer ratios match grid standards

### 2. Performance

- ✅ Create spatial indexes on location columns
- ✅ Use bounding box filters before distance calculations
- ✅ Batch insert operations (100-500 records per batch)
- ✅ Cache frequently accessed GeoJSON exports

### 3. Security

- ✅ Use read-only API keys for public endpoints
- ✅ Validate coordinate ranges (Thailand: 97°-106°E, 5°-21°N)
- ✅ Rate limit spatial queries (expensive operations)
- ✅ Audit meter registration (critical infrastructure)

---

## 🔍 Troubleshooting

### Issue: Coordinates appear in wrong location

**Solution:** Verify coordinate order (longitude, latitude)

```python
# Correct: (lon, lat)
location = (100.5018, 13.7563)  # Bangkok

# Wrong: (lat, lon)
location = (13.7563, 100.5018)  # Ocean west of Africa
```

### Issue: Slow spatial queries

**Solution:** Check spatial indexes exist

```sql
-- Verify indexes
SELECT indexname, indexdef
FROM pg_indexes
WHERE tablename IN ('substations', 'transformers', 'power_lines', 'meters');

-- Create missing indexes
CREATE INDEX idx_substations_location ON grid.substations USING GIST(location);
CREATE INDEX idx_transformers_location ON grid.transformers USING GIST(location);
CREATE INDEX idx_power_lines_geometry ON grid.power_lines USING GIST(geometry);
CREATE INDEX idx_meters_location ON grid.meters USING GIST(location);
```

### Issue: No data for region

**Solution:** Generate sample data

```bash
uv run python examples/generate_thai_grid.py \
  --region bangkok \
  --meters 1000 \
  --generate
```

---

## 📚 References

### Official Sources

- **EGAT:** https://www.egat.co.th
- **MEA:** https://www.mea.or.th
- **PEA:** https://www.pea.co.th
- **EPPO (Energy Policy and Planning Office):** https://www.eppo.go.th

### Technical Standards

- **IEC 61970:** Common Information Model (CIM)
- **IEC 61968:** CIM for Distribution
- **IEEE 1547:** Interconnection standards
- **ANSI C12.20:** Electricity metering accuracy

### Data Formats

- **CIM RDF/XML:** IEC 61970 grid model exchange
- **GeoJSON:** Spatial data format
- **PSS®E:** Power system simulation files
- **DYNAW:** Dynamic simulation format

---

## 🚀 Next Steps

1. **Generate sample data** for your region
   ```bash
   uv run python examples/generate_thai_grid.py --region bangkok --meters 1000
   ```

2. **View on map**
   ```
   http://localhost:5173/thai-grid-map
   ```

3. **Query via API**
   ```bash
   curl http://localhost:8082/api/grid/postgis/statistics
   ```

4. **Integrate with applications**
   - Use REST API for frontend apps
   - Direct PostgreSQL access for analytics
   - WebSocket for real-time meter readings

---

**Part of the GridTokenX Platform**

For more information:
- `docs/POSTGIS_INTEGRATION.md` - PostGIS setup guide
- `docs/POSTGIS_QUICKSTART.md` - Quick start
- `examples/import_grid_data.py` - Data import utility
- `tests/test_postgis/` - Test suite
