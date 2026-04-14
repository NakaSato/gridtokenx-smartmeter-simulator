# Using OpenStreetMap Data for Thailand High Voltage Transmission Grid

## Overview

OpenStreetMap (OSM) contains ~22,224 km of mapped power lines in Thailand, including high-voltage transmission infrastructure operated by EGAT (การไฟฟ้าฝ่ายผลิตแห่งประเทศไทย). This guide covers how to extract, filter, and integrate this data into the GridTokenX simulator.

---

## Thailand Grid Structure

### Voltage Levels

| Voltage | Purpose | Mapped Length | OSM Tag |
|---------|---------|---------------|---------|
| **500 kV** | Bulk transmission | 4,223 km | `voltage=500000` |
| **230 kV** | Major transmission | 8,102 km | `voltage=230000` |
| **115 kV** | Subtransmission | 9,790 km | `voltage=115000` |

### Grid Operators

| Operator | Thai Name | Role | Wikidata |
|----------|-----------|------|----------|
| **EGAT** | การไฟฟ้าฝ่ายผลิตแห่งประเทศไทย | Transmission (500/230/115 kV) | `Q3050569` |
| **MEA** | การไฟฟ้านครหลวง | Bangkok distribution | `Q13013018` |
| **PEA** | การไฟฟ้าส่วนภูมิภาค | Provincial distribution | `Q13013017` |

---

## Quick Start

### 1. Fetch HV Transmission Grid

```bash
cd backend

# Fetch around Bangkok (100km radius)
uv run python scripts/fetch_thailand_hv_grid.py \
  --mode fetch \
  --lat 13.757559 \
  --lon 100.688337 \
  --dist 100000 \
  --output data/thailand_hv_grid.geojson

# Fetch using bounding box (covers central Thailand)
uv run python scripts/fetch_thailand_hv_grid.py \
  --mode fetch \
  --bbox 13.0,99.0,18.0,101.0 \
  --output data/thailand_hv_grid.geojson
```

### 2. Convert to Pandapower Format

```bash
# Convert GeoJSON → pandapower-compatible JSON
uv run python scripts/fetch_thailand_hv_grid.py \
  --mode convert \
  --input data/thailand_hv_grid.geojson \
  --output-pandapower data/pandapower_hv_grid.json

# Fetch + Convert in one step
uv run python scripts/fetch_thailand_hv_grid.py \
  --mode fetch-convert \
  --lat 13.757559 \
  --lon 100.688337 \
  --dist 100000
```

### 3. Load into Simulator

```python
import json
import pandapower as pp
from smart_meter_simulator.adapters.pandapower_adapter import PandapowerAdapter

# Load converted OSM data
with open("data/pandapower_hv_grid.json") as f:
    osm_grid = json.load(f)

# Create pandapower network
net = pp.create_empty_network()

# Add buses
for bus in osm_grid["buses"]:
    pp.create_bus(
        net,
        vn_kv=bus["voltage_kv"],
        name=bus["id"],
        type="b",
    )

# Add lines
for line in osm_grid["lines"]:
    from_idx = net.bus.index[net.bus.name == line["from_bus"]][0]
    to_idx = net.bus.index[net.bus.name == line["to_bus"]][0]
    
    pp.create_line(
        net,
        from_bus=from_idx,
        to_bus=to_idx,
        length_km=line["length_km"],
        std_type="NAYY 4x120 SE",  # Or use custom params
        r_ohm_per_km=line["r_ohm_per_km"],
        x_ohm_per_km=line["x_ohm_per_km"],
    )

print(f"Created network with {len(net.bus)} buses, {len(net.line)} lines")
```

---

## OSM Data Extraction Methods

### Method 1: Overpass API via OSMnx (Recommended)

**Pros:** Easy, Python-native, cached automatically  
**Cons:** Rate-limited for large queries

```python
import osmnx as ox

# Fetch HV transmission lines
hv_tags = {
    "power": "line",
    "voltage": ["500000", "230000", "115000"],
}

gdf = ox.features_from_point(
    (13.757559, 100.688337),  # Bangkok
    tags=hv_tags,
    dist=100000,  # 100km radius
)

print(f"Found {len(gdf)} HV transmission lines")
print(gdf.columns)  # Available OSM tags
```

### Method 2: Overpass Turbo (Web UI)

**URL:** https://overpass-turbo.eu/

**Query for EGAT transmission lines:**

```overpass
[out:json][timeout:300];
(
  way["power"="line"]["voltage"~"^(115000|230000|500000)$"]["operator"="การไฟฟ้าฝ่ายผลิตแห่งประเทศไทย"]
    (13.0,99.0,18.0,101.0);
  relation["power"="line"]["voltage"~"^(115000|230000|500000)$"]["operator"="การไฟฟ้าฝ่ายผลิตแห่งประเทศไทย"]
    (13.0,99.0,18.0,101.0);
);
out geom;
```

**Export:** Click "Export" → "Download as GeoJSON"

### Method 3: Geofabrik Download

**URL:** https://download.geofabrik.de/asia/thailand.html

```bash
# Download full Thailand OSM extract
wget https://download.geofabrik.de/asia/thailand-latest.osm.pbf

# Extract power lines using osmium
osmium tags-filter thailand-latest.osm.pbf w/power=line -o thailand_power_lines.osm.pbf

# Convert to GeoJSON using osmconvert or ogr2ogr
ogr2ogr -f GeoJSON thailand_power_lines.geojson thailand_power_lines.osm.pbf
```

### Method 4: OpenInfraMap Visualization

**URL:** https://openinframap.org/

- Visual inspection of mapped infrastructure
- View voltage layers (500kV, 230kV, 115kV)
- Identify unmapped areas
- **Note:** No direct data export; use Overpass API instead

---

## OSM Tags Reference

### Power Line Tags

| Tag | Value | Description |
|-----|-------|-------------|
| `power` | `line` | High voltage transmission |
| `power` | `minor_line` | Distribution (exclude for HV) |
| `voltage` | `500000`, `230000`, `115000` | Voltage in volts |
| `cable` | `yes`, `no` | Underground or overhead |
| `line_type` | `overhead`, `underground` | Physical type |
| `operator` | `การไฟฟ้าฝ่ายผลิตแห่งประเทศไทย` | EGAT |
| `ref` | `Line ID` | Operator reference |
| `frequency` | `50` | Grid frequency (Hz) |

### Substation Tags

| Tag | Value | Description |
|-----|-------|-------------|
| `power` | `substation` | Electrical substation |
| `substation` | `transmission`, `distribution` | Type |
| `voltage` | `500000;230000` | Multiple voltages (semicolon-separated) |
| `operator` | EGAT/MEA/PEA | Operating authority |
| `name` | Substation name | Human-readable |

### Tower/Pole Tags

| Tag | Value | Description |
|-----|-------|-------------|
| `power` | `tower` | Transmission tower |
| `power` | `pole` | Distribution pole |
| `material` | `steel`, `concrete`, `wood` | Construction material |
| `height` | Height in meters | Physical height |

---

## Data Quality Notes

### Completeness (as of 2026)

- ✅ **500 kV**: Well-mapped (double-circuit towers, V-insulators)
- ✅ **230 kV**: Good coverage (bundled conductors)
- ⚠️ **115 kV**: Mixed quality (some missing voltage tags)
- ❌ **~106 km** of lines missing `voltage` tag entirely

### Common Issues

1. **Missing voltage tags:** Some lines lack `voltage=*` tag. Filter with care.
2. **Incorrect operator attribution:** Some PEA/MEA lines tagged as EGAT. Verify with OpenInfraMap.
3. **Semicolon-separated voltages:** `voltage=500000;230000` means dual-voltage line. Parse accordingly.
4. **Geometry accuracy:** Tower positions approximate; line routes may be simplified.

### Validation

```python
import geopandas as gpd

gdf = gpd.read_file("data/thailand_hv_grid.geojson")

# Check for missing voltage
missing_voltage = gdf["voltage"].isna().sum()
print(f"Lines missing voltage: {missing_voltage} ({missing_voltage/len(gdf)*100:.1f}%)")

# Check voltage distribution
print("\nVoltage distribution:")
print(gdf["voltage"].value_counts())

# Check operator distribution
if "operator" in gdf.columns:
    print("\nOperator distribution:")
    print(gdf["operator"].value_counts())
```

---

## Integration with Pandapower

### Step 1: Extract Buses and Lines

```python
import geopandas as gpd
import pandas as pd
from shapely.geometry import Point

gdf = gpd.read_file("data/thailand_hv_grid.geojson")

# Extract unique endpoints (buses)
buses = []
bus_counter = 0

for idx, row in gdf.iterrows():
    geom = row.geometry
    if hasattr(geom, "coords"):
        coords = list(geom.coords)
        for coord in [coords[0], coords[-1]]:
            buses.append({
                "bus_id": bus_counter,
                "lon": coord[0],
                "lat": coord[1],
                "voltage_kv": int(row.get("voltage", "0")) / 1000,
                "osm_id": idx,
            })
            bus_counter += 1

buses_df = pd.DataFrame(buses).drop_duplicates(subset=["lon", "lat"])
print(f"Extracted {len(buses_df)} unique buses")
```

### Step 2: Create Pandapower Network

```python
import pandapower as pp

net = pp.create_empty_network()

# Add buses
for _, bus_row in buses_df.iterrows():
    pp.create_bus(
        net,
        vn_kv=bus_row["voltage_kv"],
        name=f"bus_{bus_row['bus_id']}",
        type="b",
        geodata=(bus_row["lon"], bus_row["lat"]),
    )

# Add lines
for idx, row in gdf.iterrows():
    geom = row.geometry
    if not hasattr(geom, "coords"):
        continue
    
    coords = list(geom.coords)
    start_point = Point(coords[0])
    end_point = Point(coords[-1])
    
    # Find matching buses
    start_match = buses_df[
        (buses_df["lon"].round(6) == coords[0][0]) & 
        (buses_df["lat"].round(6) == coords[0][1])
    ]
    end_match = buses_df[
        (buses_df["lon"].round(6) == coords[-1][0]) & 
        (buses_df["lat"].round(6) == coords[-1][1])
    ]
    
    if start_match.empty or end_match.empty:
        continue
    
    from_bus = start_match.iloc[0]["bus_id"]
    to_bus = end_match.iloc[0]["bus_id"]
    
    # Calculate length (approximate)
    length_km = start_point.distance(end_point) * 111.0  # Rough km from degrees
    
    voltage_kv = int(row.get("voltage", "0")) / 1000
    
    pp.create_line(
        net,
        from_bus=from_bus,
        to_bus=to_bus,
        length_km=length_km,
        std_type="NAYY 4x120 SE",
        name=f"line_{idx}",
    )

print(f"Network: {len(net.bus)} buses, {len(net.line)} lines")
```

### Step 3: Run State Estimation

```python
from smart_meter_simulator.adapters.state_estimator import StateEstimator

# Add measurements to network
# ... (add virtual measurements, real meter readings)

# Run state estimation
se = StateEstimator(net)
result = se.estimate_state()

print(f"State estimation converged: {result.converged}")
print(f"Voltage profile: {result.vmag}")
```

---

## Integration with Simulator Engine

### Option A: Static Grid Topology

Load OSM grid once at simulation startup:

```python
# In your simulation engine initialization
import json

with open("data/pandapower_hv_grid.json") as f:
    osm_grid = json.load(f)

# Build pandapower network from OSM data
# ... (as shown above)

# Pass to simulator
engine = SimulationEngine(pandapower_net=net)
```

### Option B: Dynamic Updates

Periodically refresh OSM data (e.g., weekly):

```python
import schedule
import time

def update_grid_from_osm():
    """Refresh grid topology from latest OSM data."""
    print("Updating grid topology from OSM...")
    # Run fetch script
    os.system("uv run python scripts/fetch_thailand_hv_grid.py --mode fetch-convert")
    
    # Reload into pandapower
    # ... (reload logic)
    print("Grid topology updated")

# Schedule weekly update
schedule.every().monday.at("02:00").do(update_grid_from_osm)

while True:
    schedule.run_pending()
    time.sleep(60)
```

---

## Advanced: Overpass QL Queries

### Query EGAT Transmission Lines Only

```overpass
[out:json][timeout:300];
(
  way["power"="line"]
    ["voltage"~"^(115000|230000|500000)$"]
    ["operator:wikidata"="Q3050569"]
    ({{bbox}});
);
out body;
>;
out skel qt;
```

### Query with Voltage + Cable Type

```overpass
[out:json][timeout:300];
(
  way["power"="line"]
    ["voltage"~"^(230000|500000)$"]
    ["cable"="no"]  // Overhead only
    (13.0,99.0,18.0,101.0);
);
out geom;
```

### Query Substations with Multiple Voltages

```overpass
[out:json][timeout:300];
(
  node["power"="substation"]
    ["voltage"~";"]  // Has multiple voltages
    ["operator"="การไฟฟ้าฝ่ายผลิตแห่งประเทศไทย"]
    (13.0,99.0,18.0,101.0);
  way["power"="substation"]
    ["voltage"~";"]
    ["operator"="การไฟฟ้าฝ่ายผลิตแห่งประเทศไทย"]
    (13.0,99.0,18.0,101.0);
);
out center;
```

---

## Troubleshooting

### Issue: No Data Returned

**Cause:** Query area too small or no HV lines in area

**Fix:**
```bash
# Increase search radius
--dist 200000  # 200km

# Or use bounding box covering entire Thailand
--bbox 5.0,97.0,20.0,106.0
```

### Issue: Rate Limit from Overpass API

**Error:** `You have exceeded the memory limit of the Overpass API`

**Fix:**
- Use smaller bounding boxes
- Add `timeout:600` to query
- Use Geofabrik download instead

### Issue: Missing Voltage Tags

**Check:**
```python
gdf = gpd.read_file("data/thailand_hv_grid.geojson")
missing = gdf[gdf["voltage"].isna()]
print(f"Missing voltage: {len(missing)} lines")

# Save unmapped lines for manual review
missing.to_file("data/unmapped_lines.geojson", driver="GeoJSON")
```

### Issue: GeoJSON Export Fails

**Error:** `ValueError: Invalid geometry type`

**Fix:**
```python
# Drop complex geometry types
gdf = gdf[gdf.geometry.type.isin(["LineString", "MultiLineString", "Point"])]
gdf.to_file("output.geojson", driver="GeoJSON")
```

---

## References

- **OpenInfraMap Thailand:** https://openinframap.org/stats/area/Thailand
- **OSM Wiki - Thailand Power:** https://wiki.openstreetmap.org/wiki/Power_networks/Thailand
- **Overpass Turbo:** https://overpass-turbo.eu/
- **Geofabrik Downloads:** https://download.geofabrik.de/asia/thailand.html
- **OSMnx Documentation:** https://osmnx.readthedocs.io/
- **Pandapower Documentation:** https://pandapower.readthedocs.io/

---

## Next Steps

1. **Fetch OSM data** using `fetch_thailand_hv_grid.py`
2. **Validate data quality** (check voltage tags, operator distribution)
3. **Convert to pandapower** format using script
4. **Integrate with simulator** engine
5. **Run state estimation** on OSM-derived grid
6. **Compare with EGAT official data** (if available)
7. **Contribute back to OSM** by mapping unmapped lines

---

*Last updated: 2026-04-13*  
*Data source: OpenStreetMap contributors (ODbL license)*
