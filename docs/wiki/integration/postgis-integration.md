---
title: "PostGIS Integration"
category: integration
created: 2026-04-10
updated: 2026-04-10
sources: ["docs/integration/POSTGIS_INTEGRATION.md", "src/smart_meter_simulator/database/models.py", "src/smart_meter_simulator/database/repository.py"]
tags: [database, spatial, postgis, geo]
related: [[Thai Grid Topology]], [[CIM RDF/XML]], [[Pandapower Adapter]]
---

# PostGIS Integration

PostGIS provides spatial database capabilities for geographic meter placement, grid topology modeling, and spatial analytics like nearest-neighbor matching and service area computation.

## Summary

A dedicated PostgreSQL + PostGIS instance (port 5433) stores spatial grid elements — substations, power lines, transformers, and meters — with full geometric operations. Meters are placed using OpenStreetMap data and Mapbox geographic matching.

## Spatial Schema

### Tables

| Table | Geometry | Description |
|-------|----------|-------------|
| `substations` | POINT | Substation locations |
| `power_lines` | LINESTRING | Distribution line routes |
| `transformers` | POINT | Transformer locations |
| `meters` | POINT | Smart meter locations |
| `feeders` | POLYGON | Feeder service areas |

### Key Columns

```sql
CREATE TABLE meters (
    id UUID PRIMARY KEY,
    meter_id VARCHAR(64) UNIQUE,
    meter_type VARCHAR(32),
    location GEOGRAPHY(POINT, 4326),  -- WGS84 coordinates
    feeder_id UUID REFERENCES feeders(id),
    transformer_id UUID REFERENCES transformers(id),
    accuracy_class FLOAT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE power_lines (
    id UUID PRIMARY KEY,
    from_substation_id UUID REFERENCES substations(id),
    to_substation_id UUID REFERENCES substations(id),
    route GEOGRAPHY(LINESTRING, 4326),
    voltage_kv FLOAT,
    conductor_type VARCHAR(32),
    length_km FLOAT
);
```

## Spatial Operations

### Nearest Neighbor

Find the closest substation to a meter:

```sql
SELECT name, location
FROM substations
ORDER BY location <-> meter_location
LIMIT 1;
```

The `<->` operator uses the KNN (k-nearest neighbors) index.

### Radius Search

Find all meters within 500m of a point:

```sql
SELECT meter_id, meter_type
FROM meters
WHERE ST_DWithin(location, ST_MakePoint(lon, lat)::geography, 500);
```

### Bounding Box

Find all grid elements in a region:

```sql
SELECT *
FROM power_lines
WHERE route && ST_MakeEnvelope(min_lon, min_lat, max_lon, max_lat, 4326);
```

### GeoJSON Export

Export grid topology for web visualization:

```python
from geoalchemy2.shape import to_shape
from geojson import Feature, FeatureCollection, Point

def meter_to_geojson(meter):
    geom = to_shape(meter.location)
    return Feature(
        geometry=Point(geom.x, geom.y),
        properties={"meter_id": meter.meter_id, "type": meter.meter_type}
    )
```

## Mapbox Geographic Matching

The `MapboxMatcher` uses Mapbox's geocoding API to:
1. Convert street addresses to coordinates
2. Match meters to the nearest power line
3. Validate meter placement against OSM road network

## Configuration

| Env Variable | Default | Description |
|--------------|---------|-------------|
| `GIS_DATABASE_URL` | postgresql+asyncpg://...@localhost:5433/gridtokenx_gis | GIS database |
| `ENABLE_POSTGIS` | true | Enable spatial features |
| `VITE_MAPBOX_ACCESS_TOKEN` | (empty) | Mapbox API key |

## Docker Service

```yaml
gis-postgres:
  image: postgis/postgis:17-3.4
  ports:
    - "5433:5432"
  environment:
    POSTGRES_DB: gridtokenx_gis
```

## Relationships

- **Database:** [[InfluxDB Integration]] (time-series), PostgreSQL (relational)
- **Grid model:** [[Thai Grid Topology]]
- **Import/export:** [[CIM RDF/XML]]
- **Visualization:** GeoJSON → UI dashboard

## Known Issues

- Separate database instance (5433) — not co-located with primary (5432)
- No spatial indexing configured on load (GIST indexes created in migrations)
- Mapbox token required for geocoding — fallback to random placement
- OSM data freshness not tracked (road network changes)
