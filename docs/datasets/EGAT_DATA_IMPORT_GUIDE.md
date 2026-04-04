# EGAT Dashboard Data Import Guide

This guide explains how to extract data from the **EGAT Dashboard** (sothailand.com/sysgen/egat/) and import it into the PostGIS database.

---

## 📋 Overview

Since the EGAT dashboard cannot be scraped automatically, this tool provides a **semi-automated workflow**:

1. **Generate templates** for data entry
2. **Manually copy** data from the EGAT dashboard
3. **Fill in templates** with the copied data
4. **Import** into PostGIS database

---

## 🚀 Quick Start

### Step 1: Generate Templates

```bash
uv run python examples/scrape_egat_dashboard.py --generate-templates
```

This creates 4 template files:
- `substations_template.json`
- `transformers_template.json`
- `power_lines_template.json`
- `meters_template.json`

### Step 2: Copy Data from EGAT Dashboard

Visit: **https://www.sothailand.com/sysgen/egat/**

For each asset type (substations, transformers, power lines):

1. **Open the dashboard**
2. **Locate the data table** or list view
3. **Copy the data** (select all, copy)
4. **Paste into Excel/Google Sheets** (optional, for cleaning)

### Step 3: Fill in Templates

Open each template file and add the data:

**Example: `substations_template.json`**

```json
{
  "description": "EGAT Substations from sothailand.com/sysgen/egat/",
  "substations": [
    {
      "name": "500kV Bangkok Main",
      "code": "SUB-500-001",
      "voltage": 500,
      "operator": "EGAT",
      "type": "transmission",
      "capacity": 300,
      "longitude": 100.5018,
      "latitude": 13.7563,
      "province": "Bangkok"
    },
    {
      "name": "230kV Samut Prakan",
      "code": "SUB-230-001",
      "voltage": 230,
      "operator": "EGAT",
      "type": "transmission",
      "capacity": 150,
      "longitude": 100.5998,
      "latitude": 13.5990,
      "province": "Samut Prakan"
    }
  ]
}
```

### Step 4: Import into PostGIS

```bash
# Import substations
uv run python examples/scrape_egat_dashboard.py \
  --input substations_template.json \
  --type substations

# Import transformers
uv run python examples/scrape_egat_dashboard.py \
  --input transformers_template.json \
  --type transformers

# Import power lines
uv run python examples/scrape_egat_dashboard.py \
  --input power_lines_template.json \
  --type lines

# Import all at once (if using single JSON file)
uv run python examples/scrape_egat_dashboard.py \
  --input egat_complete.json \
  --type all
```

---

## 📁 Template Formats

### Substations Template

```json
{
  "substations": [
    {
      "name": "Substation Name",
      "code": "UNIQUE_CODE",
      "voltage": 500,
      "operator": "EGAT",
      "type": "transmission",
      "capacity": 300,
      "longitude": 100.5018,
      "latitude": 13.7563,
      "province": "Bangkok"
    }
  ]
}
```

**Fields:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Substation name |
| `code` | string | Yes | Unique identifier |
| `voltage` | float | Yes | Voltage level (kV) |
| `operator` | string | No | Operator (EGAT/MEA/PEA) |
| `type` | string | No | transmission/sub_transmission/distribution |
| `capacity` | float | No | Capacity (MVA) |
| `longitude` | float | **Yes** | WGS84 longitude |
| `latitude` | float | **Yes** | WGS84 latitude |
| `province` | string | No | Province name |

### Transformers Template

```json
{
  "transformers": [
    {
      "code": "TXN-001",
      "voltage_primary": 22,
      "voltage_secondary": 0.4,
      "capacity": 500,
      "longitude": 100.5025,
      "latitude": 13.7570
    }
  ]
}
```

**Fields:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `code` | string | Yes | Unique identifier |
| `voltage_primary` | float | Yes | Primary voltage (kV) |
| `voltage_secondary` | float | Yes | Secondary voltage (kV) |
| `capacity` | float | No | Capacity (kVA) |
| `longitude` | float | **Yes** | WGS84 longitude |
| `latitude` | float | **Yes** | WGS84 latitude |

### Power Lines Template

```json
{
  "power_lines": [
    {
      "code": "LINE-001",
      "voltage": 230,
      "type": "overhead",
      "conductor": "ACSR 300 mm²",
      "coordinates": [
        [100.5018, 13.7563],
        [100.5100, 13.7600],
        [100.5150, 13.7650]
      ]
    }
  ]
}
```

**Fields:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `code` | string | Yes | Unique identifier |
| `voltage` | float | Yes | Voltage level (kV) |
| `type` | string | No | overhead/underground |
| `conductor` | string | No | Conductor type |
| `coordinates` | array | **Yes** | LineString coordinates [[lon,lat],...] |

**Alternative coordinate formats:**

```json
// Format 1: Array of arrays
"coordinates": [[100.5, 13.75], [100.51, 13.76]]

// Format 2: Flat array
"coordinates": [100.5, 13.75, 100.51, 13.76]

// Format 3: Semicolon-separated string
"coordinates": "100.5,13.75;100.51,13.76"

// Format 4: Start-end points
"start_lon": 100.5,
"start_lat": 13.75,
"end_lon": 100.51,
"end_lat": 13.76
```

### Meters Template

```json
{
  "meters": [
    {
      "meter_id": "METER-SOL-000001",
      "meter_type": "solar_prosumer",
      "serial": "SN2024000001",
      "longitude": 100.5020,
      "latitude": 13.7565,
      "province": "Bangkok"
    }
  ]
}
```

**Fields:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `meter_id` | string | Yes | Unique meter ID |
| `meter_type` | string | Yes | solar_prosumer/grid_consumer/hybrid_prosumer/battery/ev_charger |
| `serial` | string | No | Serial number |
| `longitude` | float | **Yes** | WGS84 longitude |
| `latitude` | float | **Yes** | WGS84 latitude |
| `province` | string | No | Province name |

---

## 📊 Supported File Formats

### JSON (Recommended)

```bash
uv run python examples/scrape_egat_dashboard.py \
  --input data.json \
  --type substations
```

### CSV

Create CSV with headers:

```csv
name,code,voltage,operator,type,capacity,longitude,latitude,province
500kV Bangkok Main,SUB-500-001,500,EGAT,transmission,300,100.5018,13.7563,Bangkok
230kV Samut Prakan,SUB-230-001,230,EGAT,transmission,150,100.5998,13.5990,Samut Prakan
```

```bash
uv run python examples/scrape_egat_dashboard.py \
  --input substations.csv \
  --type substations
```

### Excel (.xlsx)

```bash
uv run python examples/scrape_egat_dashboard.py \
  --input egat_data.xlsx \
  --type substations
```

**Note:** Excel import requires `pandas` and `openpyxl`:

```bash
uv add pandas openpyxl
```

---

## 🔧 Advanced Usage

### Import from Multiple Files

```bash
# Import each type separately
uv run python examples/scrape_egat_dashboard.py -i substations.json -t substations
uv run python examples/scrape_egat_dashboard.py -i transformers.json -t transformers
uv run python examples/scrape_egat_dashboard.py -i lines.json -t lines
uv run python examples/scrape_egat_dashboard.py -i meters.json -t meters
```

### Import Complete Grid (Single File)

Create a single JSON file with all data:

```json
{
  "substations": [...],
  "transformers": [...],
  "power_lines": [...],
  "meters": [...]
}
```

```bash
uv run python examples/scrape_egat_dashboard.py \
  --input egat_complete.json \
  --type all
```

### Custom Database URL

```bash
uv run python examples/scrape_egat_dashboard.py \
  --input data.json \
  --type substations \
  --database-url postgresql+asyncpg://user:pass@host:5432/dbname
```

---

## 📝 Data Extraction Tips

### From HTML Tables

If the EGAT dashboard shows data in HTML tables:

1. **Browser Developer Tools:**
   - Right-click table → Inspect
   - Copy outer HTML
   - Use online HTML table to CSV converter

2. **Browser Extensions:**
   - Install "Table Capture" (Chrome/Edge)
   - Capture table as CSV/Excel
   - Clean data if needed

3. **Copy-Paste Method:**
   - Select entire table (Ctrl+A in table area)
   - Copy (Ctrl+C)
   - Paste into Excel/Google Sheets
   - Export as CSV

### Coordinate Extraction

If coordinates are not directly available:

1. **Google Maps:**
   - Right-click on substation location
   - First line shows coordinates (lat, lon)
   - Format: `13.7563, 100.5018`
   - Convert to: `"longitude": 100.5018, "latitude": 13.7563`

2. **Thai Grid Reference:**
   - Bangkok: ~13.75°N, 100.50°E
   - Chiang Mai: ~18.79°N, 98.99°E
   - Phuket: ~7.88°N, 98.40°E
   - Khon Kaen: ~16.43°N, 102.82°E

### Data Cleaning

Common issues and fixes:

```json
// ❌ Wrong: Coordinates as string
"coordinates": "100.5018, 13.7563"

// ✅ Correct: Separate fields
"longitude": 100.5018,
"latitude": 13.7563

// ❌ Wrong: Voltage with unit
"voltage": "500 kV"

// ✅ Correct: Numeric only
"voltage": 500

// ❌ Wrong: Capacity with unit
"capacity": "300 MVA"

// ✅ Correct: Numeric only
"capacity": 300
```

---

## ✅ Validation

After import, verify the data:

### 1. Check via API

```bash
# Get statistics
curl http://localhost:8082/api/grid/postgis/statistics

# Query substations
curl http://localhost:8082/api/grid/postgis/substations

# Export as GeoJSON
curl http://localhost:8082/api/grid/postgis/network/geojson
```

### 2. Check via Database

```sql
-- Count substations by voltage
SELECT voltage_level_kv, COUNT(*) 
FROM grid.substations 
GROUP BY voltage_level_kv 
ORDER BY voltage_level_kv DESC;

-- Count transformers
SELECT COUNT(*) FROM grid.transformers;

-- Count power lines by voltage
SELECT voltage_level_kv, COUNT(*) 
FROM grid.power_lines 
GROUP BY voltage_level_kv 
ORDER BY voltage_level_kv DESC;

-- Count meters by type
SELECT meter_type, COUNT(*) 
FROM grid.meters 
GROUP BY meter_type;
```

### 3. Visualize on Map

```
http://localhost:5173/thai-grid-map
```

---

## 🐛 Troubleshooting

### Error: "Missing coordinates"

**Problem:** Longitude/latitude not provided

**Solution:**
```json
// ❌ Wrong
{
  "name": "Substation A",
  "location": "Bangkok"
}

// ✅ Correct
{
  "name": "Substation A",
  "longitude": 100.5018,
  "latitude": 13.7563
}
```

### Error: "Invalid coordinates format"

**Problem:** Coordinates not in expected format

**Solution:**
```json
// ❌ Wrong: String
"coordinates": "100.5,13.75;100.51,13.76"

// ✅ Correct: Array of arrays
"coordinates": [[100.5, 13.75], [100.51, 13.76]]
```

### Error: "Duplicate key value violates unique constraint"

**Problem:** Code/ID already exists in database

**Solution:**
- Use unique codes for each asset
- Or delete existing data first:

```sql
-- WARNING: This deletes all data!
DELETE FROM grid.meters;
DELETE FROM grid.power_lines;
DELETE FROM grid.transformers;
DELETE FROM grid.substations;
```

### Error: "Column does not exist"

**Problem:** CSV/Excel headers don't match expected fields

**Solution:**
- Check field names in template files
- Use exact field names from templates

---

## 📚 Example Workflow

### Complete Example: Import Bangkok Grid

**Step 1: Generate templates**
```bash
uv run python examples/scrape_egat_dashboard.py --generate-templates
```

**Step 2: Copy data from EGAT dashboard**
- Visit: https://www.sothailand.com/sysgen/egat/
- Copy substation data
- Copy transformer data
- Copy power line data

**Step 3: Fill templates**

`substations_template.json`:
```json
{
  "substations": [
    {
      "name": "500kV Bangkok Main",
      "code": "SUB-500-BKK-001",
      "voltage": 500,
      "operator": "EGAT",
      "type": "transmission",
      "capacity": 300,
      "longitude": 100.5018,
      "latitude": 13.7563,
      "province": "Bangkok"
    },
    {
      "name": "230kV Samut Prakan",
      "code": "SUB-230-SP-001",
      "voltage": 230,
      "operator": "EGAT",
      "type": "transmission",
      "capacity": 150,
      "longitude": 100.5998,
      "latitude": 13.5990,
      "province": "Samut Prakan"
    }
  ]
}
```

**Step 4: Import**
```bash
uv run python examples/scrape_egat_dashboard.py \
  --input substations_template.json \
  --type substations

uv run python examples/scrape_egat_dashboard.py \
  --input transformers_template.json \
  --type transformers

uv run python examples/scrape_egat_dashboard.py \
  --input power_lines_template.json \
  --type lines
```

**Step 5: Verify**
```bash
curl http://localhost:8082/api/grid/postgis/statistics
```

**Step 6: Visualize**
```
http://localhost:5173/thai-grid-map
```

---

## 📋 Checklist

Before importing:

- [ ] Templates generated
- [ ] Data copied from EGAT dashboard
- [ ] Templates filled with data
- [ ] Coordinates verified (WGS84)
- [ ] Codes/IDs are unique
- [ ] Numeric fields have no units
- [ ] Database is running (`docker-compose up -d postgres`)
- [ ] Required dependencies installed

After importing:

- [ ] Import completed without errors
- [ ] Statistics show correct counts
- [ ] GeoJSON export works
- [ ] Map visualization shows assets
- [ ] API queries return data

---

## 📞 Support

For issues or questions:

1. Check error messages carefully
2. Verify template format matches examples
3. Ensure coordinates are valid (Thailand: 97°-106°E, 5°-21°N)
4. Test with small dataset first (5-10 records)

---

**Part of the GridTokenX Platform**

For more information:
- `docs/POSTGIS_API_REFERENCE.md` - API documentation
- `docs/THAI_GRID_INTEGRATION.md` - Thai grid modeling
- `examples/generate_thai_grid.py` - Sample data generator
