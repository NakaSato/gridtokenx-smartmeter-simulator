# OSMOSE Integration - Complete Reference

Complete integration of OSMOSE QA (Quality Assurance) system into the GridTokenX Smart Meter Simulator.

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Installation](#installation)
4. [API Reference](#api-reference)
5. [Frontend Integration](#frontend-integration)
6. [Usage Examples](#usage-examples)
7. [Configuration](#configuration)

---

## Overview

### What is OSMOSE?

**OSMOSE QA** (OpenStreetMap Quality Assurance) is an automated validation system that checks OSM data for errors and inconsistencies.

- **Backend**: https://github.com/osmose-qa/osmose-backend
- **Frontend**: https://osmose.openstreetmap.fr
- **Coverage**: 30+ countries, 300+ validation rules
- **Issues Detected**: 100,000+ daily

### Integration Benefits

| Feature | Benefit |
|---------|---------|
| **Automated Validation** | Continuous quality checking of OSM data |
| **300+ Rules** | Comprehensive coverage of tagging errors |
| **Vector Tiles** | Real-time issue overlay on maps |
| **Database Storage** | Persistent issue tracking and analytics |
| **REST API** | Easy integration with existing systems |
| **Plugin System** | Extensible validation rules |

---

## Architecture

### System Components

```
┌─────────────────────────────────────────────────────────┐
│                  GridTokenX Platform                     │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────────┐     ┌──────────────┐     ┌─────────┐ │
│  │   Frontend   │     │  Smart Meter │     │ OSMOSE  │ │
│  │  (React UI)  │◄───►│  Simulator   │◄───►│ Backend │ │
│  │              │     │   (FastAPI)  │     │ Engine  │ │
│  └──────────────┘     └──────────────┘     └─────────┘ │
│         │                    │                    │     │
│         │                    │                    │     │
│  ┌──────▼────────────────────▼────────────────────▼──┐ │
│  │           PostgreSQL / PostGIS Database            │ │
│  │  - OSM data (Osmosis schema)                       │ │
│  │  - Validation results                              │ │
│  │  - Issue history                                   │ │
│  └────────────────────────────────────────────────────┘ │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### Module Structure

```
src/smart_meter_simulator/osmose/
├── __init__.py              # Package exports
├── core/
│   ├── issue.py             # Issue data models
│   ├── analyser.py          # Analyser base classes
│   └── plugin.py            # Plugin validation system
├── fetcher.py               # Data fetching (Overpass API)
├── runner.py                # Analyser orchestration
├── database.py              # PostgreSQL integration
├── tile_server.py           # Vector tile generation
└── utils/
    ├── mapcss_parser.py     # MapCSS rule parsing
    └── pbf_parser.py        # PBF file parsing
```

### Data Flow

```
1. Data Fetch
   Overpass API → OSM PBF → Parser → OSM Data Dict

2. Validation
   OSM Data → Analysers → Plugins → Issues List

3. Storage
   Issues → PostgreSQL → Spatial Index → Query API

4. Visualization
   Database → Vector Tiles → MapLibre GL → User Display
```

---

## Installation

### Prerequisites

```bash
# Python 3.11+
python --version

# UV package manager
uv --version

# PostgreSQL 14+ with PostGIS
psql --version
```

### Install Dependencies

```bash
cd /Users/chanthawat/Developments/gridtokenx-platform-infa/gridtokenx-smartmeter-simulator

# Install with OSMOSE support
uv sync --extra osmose

# Or install MVT support separately
uv pip install mapbox-vector-tile
```

### Database Setup

```sql
-- Create database
CREATE DATABASE gridtokenx_osmose;

-- Enable PostGIS
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS hstore;

-- Create user
CREATE USER gridtokenx WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE gridtokenx_osmose TO gridtokenx;
```

### Environment Configuration

Add to `.env`:

```bash
# OSMOSE Database
OSMOSE_DATABASE_URL=postgresql://gridtokenx:your_password@localhost:5432/gridtokenx_osmose

# Overpass API
OVERPASS_ENDPOINT=https://overpass-api.de/api/interpreter
OVERPASS_TIMEOUT=120

# Validation Settings
OSMOSE_ENABLED=true
OSMOSE_AUTO_RUN=true
OSMOSE_RUN_INTERVAL_HOURS=24
```

---

## API Reference

### Base URL

```
http://localhost:8082/api/0.3
```

### Endpoints

#### Get Vector Tile

```http
GET /issues/{z}/{x}/{y}.mvt
```

**Parameters:**
- `z` (int): Zoom level (10-18)
- `x` (int): Tile X coordinate
- `y` (int): Tile Y coordinate
- `tags` (string): Filter by tags (comma-separated)
- `level` (int): Filter by severity (1-3)

**Example:**
```bash
curl http://localhost:8082/api/0.3/issues/14/12774/7532.mvt?tags=power
```

#### List Issues

```http
GET /issues
```

**Parameters:**
- `bbox` (string): Bounding box (min_lat,min_lon,max_lat,max_lon)
- `tags` (string): Filter by tags
- `level` (int): Filter by severity
- `item` (int): Filter by category
- `limit` (int): Maximum results (default: 1000)

**Example:**
```bash
curl "http://localhost:8082/api/0.3/issues?bbox=13.7,100.5,14.0,100.8&tags=power"
```

#### Get Issue Details

```http
GET /issues/{issue_id}
```

**Example:**
```bash
curl http://localhost:8082/api/0.3/issues/142857
```

#### List Analysers

```http
GET /analyser
```

**Response:**
```json
[
  {
    "id": "power_plugin",
    "name": "Power Infrastructure Validation",
    "description": "Validates power infrastructure tagging and topology",
    "enabled": true,
    "last_run": "2026-03-30T12:00:00Z",
    "issues_found": 1250
  }
]
```

#### Get Statistics

```http
GET /stats
```

**Response:**
```json
{
  "total_issues": 15420,
  "total_objects_validated": 1250000,
  "issues_by_level": {
    "1": 1250,
    "2": 5670,
    "3": 8500
  },
  "issues_by_tag": {
    "power": 1250,
    "building": 3420,
    "transport": 2100
  }
}
```

#### Run Validation

```http
POST /validate?country=th&analyser=power_plugin
```

**Response:**
```json
{
  "status": "started",
  "country": "th",
  "analyser": "power_plugin",
  "estimated_time_seconds": 300
}
```

---

## Frontend Integration

### React Component

```typescript
import { OsmosePanel } from './features/open-infra-map/components/OsmosePanel';

function MapViewer() {
  const [osmoseOpen, setOsmoseOpen] = useState(false);
  const bbox = {
    north: 14.5,
    south: 13.0,
    east: 101.0,
    west: 100.0,
  };

  return (
    <>
      <MapLibreMap />
      <OsmosePanel
        isOpen={osmoseOpen}
        onClose={() => setOsmoseOpen(false)}
        bbox={bbox}
      />
    </>
  );
}
```

### MapLibre GL Integration

```typescript
import maplibregl from 'maplibre-gl';

// Add OSMOSE vector tile layer
const map = new maplibregl.Map({
  container: 'map',
  style: 'https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json',
});

// Add OSMOSE source
map.addSource('osmose-issues', {
  type: 'vector',
  tiles: [
    'http://localhost:8082/api/0.3/issues/{z}/{x}/{y}.mvt?tags=power'
  ],
  minzoom: 10,
  maxzoom: 18,
});

// Add OSMOSE markers layer
map.addLayer({
  id: 'osmose-markers',
  type: 'circle',
  source: 'osmose-issues',
  'source-layer': 'issues',
  paint: {
    'circle-radius': 8,
    'circle-color': [
      'case',
      ['==', ['get', 'level'], 1], '#ff0000',  // Critical
      ['==', ['get', 'level'], 2], '#ffa500',  // Normal
      '#0080ff'                                 // Low
    ],
    'circle-opacity': 0.8,
    'circle-stroke-width': 2,
    'circle-stroke-color': '#ffffff',
  },
});

// Add click popup
map.on('click', 'osmose-markers', (e) => {
  const features = map.queryRenderedFeatures(e.point, {
    layers: ['osmose-markers']
  });
  
  new maplibregl.Popup()
    .setLngLat(e.lngLat)
    .setHTML(`<div>${features[0].properties.title}</div>`)
    .addTo(map);
});
```

---

## Usage Examples

### Python: Run Validation

```python
from smart_meter_simulator.osmose import (
    OSMOSERunner,
    create_power_runner,
    PowerPlugin,
)

# Create runner for Thailand
runner = create_power_runner(country="th")

# Run validation
import asyncio

async def main():
    bbox = {
        "north": 14.5,
        "south": 13.0,
        "east": 101.0,
        "west": 100.0,
    }
    
    results = await runner.run_all(bbox=bbox)
    
    print(f"Total issues: {runner.get_summary()['total_issues']}")
    
    for result in results:
        print(f"Analyser {result.analyser}: {result.total_issues} issues")

asyncio.run(main())
```

### Python: Query Issues

```python
import aiohttp
import asyncio

async def query_issues():
    async with aiohttp.ClientSession() as session:
        # Query by bbox
        bbox = "13.7,100.5,14.0,100.8"
        async with session.get(
            f"http://localhost:8082/api/0.3/issues?bbox={bbox}&tags=power"
        ) as response:
            issues = await response.json()
            print(f"Found {len(issues)} issues")
        
        # Get statistics
        async with session.get("http://localhost:8082/api/0.3/stats") as response:
            stats = await response.json()
            print(f"Total issues: {stats['total_issues']}")

asyncio.run(query_issues())
```

### JavaScript: Fetch Vector Tiles

```javascript
async function fetchOsmoseTile(z, x, y) {
  const response = await fetch(
    `http://localhost:8082/api/0.3/issues/${z}/${x}/${y}.mvt?tags=power`
  );
  
  if (!response.ok) return null;
  
  const mvtData = await response.arrayBuffer();
  
  // Use mapbox-vector-tile to parse
  const tile = mapboxvt.parse(mvtData);
  return tile;
}

// Usage
fetchOsmoseTile(14, 12774, 7532).then(tile => {
  console.log('OSMOSE issues:', tile.issues);
});
```

---

## Configuration

### Analyser Configuration

Create `osmose_config.py`:

```python
# OSMOSE Configuration

# Country settings
COUNTRY = "th"
COUNTRY_NAME = "Thailand"

# Database
DATABASE_URL = "postgresql://gridtokenx:password@localhost:5432/gridtokenx_osmose"

# Overpass API
OVERPASS_ENDPOINTS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
]
OVERPASS_TIMEOUT = 120

# Validation settings
VALIDATION_LEVELS = {
    "high": 1,    # Critical errors
    "normal": 2,  # Common mistakes
    "low": 3,     # Suggestions
}

# Enabled analysers
ANALYSERS = [
    "power_plugin",
    "building_validation",
    "transport_infrastructure",
]

# Schedule
RUN_INTERVAL_HOURS = 24
AUTO_RUN = True
```

### Plugin Configuration

Enable/disable specific validation rules:

```python
# Enable power validation
from smart_meter_simulator.osmose.core.plugin import PowerPlugin

plugin = PowerPlugin()
plugin.init(logger)

# Register specific issue classes
plugin.errors[91001] = plugin.def_class(
    item=9100,
    level=2,
    tags=["power", "fix:chair", "geom"],
    title="Power Transformers should always be on a node"
)
```

### Performance Tuning

```python
# Database connection pool
DB_POOL_MIN_SIZE = 2
DB_POOL_MAX_SIZE = 10
DB_COMMAND_TIMEOUT = 60

# Tile generation
MVT_MIN_ZOOM = 10
MVT_MAX_ZOOM = 18
MVT_EXTENT = 4096
MVT_FEATURES_LIMIT = 1000

# Caching
CACHE_TTL_SECONDS = 3600
CACHE_MAX_SIZE_MB = 500
```

---

## Troubleshooting

### Common Issues

**1. Database Connection Failed**
```
Error: Multiple exceptions in connect list
Solution: Check DATABASE_URL and ensure PostgreSQL is running
```

**2. Overpass API Timeout**
```
Error: Overpass error 504: Gateway Timeout
Solution: Rotate to different endpoint or increase timeout
```

**3. MVT Generation Failed**
```
Error: mapbox_vector_tile not installed
Solution: pip install mapbox-vector-tile
```

### Debug Mode

Enable verbose logging:

```bash
export LOG_LEVEL=DEBUG
export OSMOSE_DEBUG=true
```

### Performance Monitoring

```python
# Monitor validation performance
from prometheus_client import Counter, Histogram

VALIDATION_TIME = Histogram('osmose_validation_seconds', 'Validation time')
ISSUES_FOUND = Counter('osmose_issues_total', 'Issues found')

@VALIDATION_TIME.time()
def run_validation():
    issues = validator.run()
    ISSUES_FOUND.inc(len(issues))
```

---

## Resources

- **OSMOSE Backend**: https://github.com/osmose-qa/osmose-backend
- **OSMOSE Frontend**: https://osmose.openstreetmap.fr
- **Documentation**: https://github.com/osmose-qa/osmose-backend/tree/master/doc
- **Issue Tracker**: https://github.com/osmose-qa/osmose-backend/issues
- **OSM Power Tagging**: https://wiki.openstreetmap.org/wiki/Tag:power=line

---

_Document Version: 1.0_  
_Last Updated: 2026-03-30_  
_Author: GridTokenX Engineering Team_
