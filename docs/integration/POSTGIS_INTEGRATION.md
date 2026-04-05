# PostGIS Integration

The **GridTokenX Smart Meter Simulator** uses **PostGIS**, a spatial database extender for PostgreSQL, to manage and query the physical infrastructure of the electrical distribution network.

## 🏗️ Spatial Data Architecture

PostGIS allows the simulator to perform complex geospatial operations that are critical for realistic grid modeling. The data is managed by the `PostGISRepository` (located in `src/smart_meter_simulator/database/repository.py`).

### Supported Spatial Elements
-   **Points**: Represent Substations, Transformers, and Smart Meters.
-   **LineStrings**: Represent High-Voltage (69-115kV) transmission lines and Medium-Voltage (22kV) distribution feeders.
-   **Polygons**: Define electrical Zones and service areas (e.g., MEA District or PEA Province).

## 🔍 Key Spatial Operations

The simulator leverages PostGIS's specialized functions for various real-time operations:

### 1. Nearest Neighbor Search
Finds the closest electrical asset to a newly registered meter.
```sql
SELECT transformer_id, code, ST_Distance(location, ST_SetSRID(ST_Point(lon, lat), 4326)) as distance
FROM grid.transformers
ORDER BY location <-> ST_SetSRID(ST_Point(lon, lat), 4326)
LIMIT 1;
```

### 2. Radius Search (Geofencing)
Identifies all meters within a specific radius of a feeder fault or a VPP cluster center.
```sql
SELECT meter_id FROM grid.meters
WHERE ST_DWithin(location, ST_SetSRID(ST_Point(lon, lat), 4326), radius_meters);
```

### 3. Bounding Box (BBOX) Queries
Retrieves all grid assets for a specific map viewport in the dashboard or for localized `pandapower` network building.

## 🗺️ GeoJSON Export

The repository provides an optimized mechanism to export the entire electrical network directly as a **GeoJSON FeatureCollection**. This enables high-performance rendering on the simulator's web dashboard using tools like Mapbox or Leaflet.

```python
# From repository.py
geojson = await repository.export_network_geojson(voltage_min=0, voltage_max=22.0)
```

## ⚙️ Database Schema (Grid Schema)

The spatial tables are organized within the `grid` schema:
-   **`substations`**: High-voltage nodes.
-   **`transformers`**: Distribution step-down points (22kV to 400V).
-   **`power_lines`**: Conductors with physical properties (R, X, C).
-   **`meters`**: Service connection points with geospatial coordinates.

---
_Next: [Thai Grid Integration](THAI_GRID_INTEGRATION.md)_
