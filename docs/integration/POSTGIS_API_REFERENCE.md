# PostGIS API Reference

Quick reference for all PostGIS REST API endpoints.

---

## Base URL

```
http://localhost:8082/api/grid/postgis
```

---

## Endpoints Summary

| Endpoint | Method | Description | Auth |
|----------|--------|-------------|------|
| [`/status`](#get-status) | GET | Database health & statistics | No |
| [`/network/geojson`](#get-networkgeojson) | GET | Export network as GeoJSON | No |
| [`/substations`](#get-substations) | GET | Query substations | No |
| [`/transformers/nearest`](#get-transformersnearest) | GET | Find nearest transformer | No |
| [`/meters/nearby`](#get-metersnearby) | GET | Find nearby meters | No |
| [`/meters`](#post-meters) | POST | Register new meter | No |
| [`/statistics`](#get-statistics) | GET | Network statistics | No |

---

## GET /status

Check database connection and get statistics.

### Request

```bash
curl http://localhost:8082/api/grid/postgis/status
```

### Response (200 OK)

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
      "hybrid_prosumer": 145,
      "battery": 45,
      "ev_charger": 78
    },
    "total_substations": 592,
    "total_lines_km": 3032.3,
    "total_meters": 1508
  }
}
```

### Response Codes

| Code | Description |
|------|-------------|
| 200 | Database connected |
| 503 | Database not available |

---

## GET /network/geojson

Export grid network as GeoJSON for map visualization.

### Request

```bash
# All voltage levels
curl http://localhost:8082/api/grid/postgis/network/geojson

# Filter by voltage (22kV only)
curl "http://localhost:8082/api/grid/postgis/network/geojson?voltage_min=22&voltage_max=22"

# MV and LV only
curl "http://localhost:8082/api/grid/postgis/network/geojson?voltage_min=0.4&voltage_max=22"
```

### Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `voltage_min` | float | 0 | Minimum voltage (kV) |
| `voltage_max` | float | 500 | Maximum voltage (kV) |

### Response (200 OK)

```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "geometry": {
        "type": "Point",
        "coordinates": [100.5018, 13.7563]
      },
      "properties": {
        "type": "substation",
        "name": "Bangkok Main",
        "code": "SUB-500-001",
        "voltage_level_kv": 500,
        "operator": "EGAT",
        "capacity_mva": 300,
        "status": "in_service"
      }
    },
    {
      "type": "Feature",
      "geometry": {
        "type": "LineString",
        "coordinates": [
          [100.5018, 13.7563],
          [100.5025, 13.7570]
        ]
      },
      "properties": {
        "type": "line",
        "name": "Bangkok Line 1",
        "code": "LINE-001",
        "voltage_level_kv": 22,
        "line_type": "overhead",
        "length_km": 2.45,
        "conductor_type": "NA2XS2Y 1x185 RM/25 12/20 kV",
        "status": "in_service"
      }
    }
  ]
}
```

### Response Codes

| Code | Description |
|------|-------------|
| 200 | Success |
| 503 | Database not available |

---

## GET /substations

Query substations with filters.

### Request

```bash
# All substations
curl http://localhost:8082/api/grid/postgis/substations

# Filter by voltage (22kV)
curl "http://localhost:8082/api/grid/postgis/substations?voltage=22"

# Filter by province
curl "http://localhost:8082/api/grid/postgis/substations?province=Bangkok"

# Bounding box query
curl "http://localhost:8082/api/grid/postgis/substations?min_lon=100.4&min_lat=13.7&max_lon=100.6&max_lat=13.8"
```

### Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `voltage` | float | - | Filter by voltage level (kV) |
| `province` | string | - | Filter by province |
| `min_lon` | float | - | Bounding box: min longitude |
| `min_lat` | float | - | Bounding box: min latitude |
| `max_lon` | float | - | Bounding box: max longitude |
| `max_lat` | float | - | Bounding box: max latitude |

### Response (200 OK)

```json
{
  "count": 3,
  "substations": [
    {
      "id": 1,
      "name": "500kV Bangkok Main",
      "code": "SUB-500-001",
      "voltage_level_kv": 500,
      "operator": "EGAT",
      "capacity_mva": 300,
      "status": "in_service",
      "province": "Bangkok",
      "location": {
        "type": "Point",
        "coordinates": [100.5000, 13.7500]
      }
    }
  ]
}
```

### Response Codes

| Code | Description |
|------|-------------|
| 200 | Success |
| 503 | Database not available |

---

## GET /transformers/nearest

Find nearest transformer to a location.

### Request

```bash
curl "http://localhost:8082/api/grid/postgis/transformers/nearest?longitude=100.5018&latitude=13.7563&max_distance_m=500"
```

### Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `longitude` | float | **required** | Search center longitude |
| `latitude` | float | **required** | Search center latitude |
| `max_distance_m` | float | 500 | Maximum search radius (meters) |

### Response (200 OK)

```json
{
  "transformer_id": 12,
  "code": "TXN-00012",
  "distance_m": 125.4,
  "capacity_kva": 500
}
```

### Response Codes

| Code | Description |
|------|-------------|
| 200 | Success |
| 404 | No transformer found within range |
| 422 | Missing required parameters |
| 503 | Database not available |

---

## GET /meters/nearby

Find meters within radius of a location.

### Request

```bash
# All meters within 1km
curl "http://localhost:8082/api/grid/postgis/meters/nearby?longitude=100.5018&latitude=13.7563&radius_m=1000"

# Filter by type (solar prosumers only)
curl "http://localhost:8082/api/grid/postgis/meters/nearby?longitude=100.5018&latitude=13.7563&radius_m=1000&meter_type=solar_prosumer"
```

### Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `longitude` | float | **required** | Search center longitude |
| `latitude` | float | **required** | Search center latitude |
| `radius_m` | float | 1000 | Search radius (meters) |
| `meter_type` | string | - | Filter by type |

**Meter Types:**
- `solar_prosumer`
- `grid_consumer`
- `hybrid_prosumer`
- `battery`
- `ev_charger`

### Response (200 OK)

```json
{
  "count": 45,
  "meters": [
    {
      "meter_id": "METER-SOL-000123",
      "meter_type": "solar_prosumer",
      "distance_m": 87.3,
      "location": "0101000020E6100000..."
    }
  ]
}
```

### Response Codes

| Code | Description |
|------|-------------|
| 200 | Success |
| 422 | Missing required parameters |
| 503 | Database not available |

---

## POST /meters

Register new smart meter.

### Request

```bash
curl -X POST "http://localhost:8082/api/grid/postgis/meters?meter_id=METER-NEW-001&meter_type=solar_prosumer&longitude=100.5018&latitude=13.7563&serial_number=SN123456789"
```

### Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `meter_id` | string | **required** | Unique meter identifier |
| `meter_type` | string | **required** | Meter type |
| `longitude` | float | **required** | Location longitude |
| `latitude` | float | **required** | Location latitude |
| `transformer_id` | int | - | Connected transformer ID |
| `serial_number` | string | - | Meter serial number |
| `province` | string | - | Province name |

### Response (200 OK)

```json
{
  "id": 123,
  "meter_id": "METER-NEW-001",
  "meter_type": "solar_prosumer",
  "location": {
    "type": "Point",
    "coordinates": [100.5018, 13.7563]
  }
}
```

### Response Codes

| Code | Description |
|------|-------------|
| 200 | Success |
| 400 | Invalid meter type |
| 409 | Meter ID already exists |
| 422 | Missing required parameters |
| 503 | Database not available |

---

## GET /statistics

Get comprehensive network statistics.

### Request

```bash
curl http://localhost:8082/api/grid/postgis/statistics
```

### Response (200 OK)

```json
{
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
    "hybrid_prosumer": 145,
    "battery": 45,
    "ev_charger": 78
  },
  "total_substations": 592,
  "total_lines_km": 3032.3,
  "total_meters": 1508
}
```

### Response Codes

| Code | Description |
|------|-------------|
| 200 | Success |
| 503 | Database not available |

---

## Error Responses

### 400 Bad Request

```json
{
  "detail": "Invalid meter type: unknown_type"
}
```

### 404 Not Found

```json
{
  "detail": "No transformer found within search radius"
}
```

### 422 Validation Error

```json
{
  "detail": [
    {
      "loc": ["query", "longitude"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

### 503 Service Unavailable

```json
{
  "detail": "Database not configured"
}
```

---

## Code Examples

### JavaScript (Fetch API)

```javascript
// Get network statistics
async function getStats() {
  const response = await fetch('/api/grid/postgis/statistics');
  const data = await response.json();
  console.log(`Total meters: ${data.total_meters}`);
}

// Find nearest transformer
async function findNearestTransformer(lon, lat) {
  const response = await fetch(
    `/api/grid/postgis/transformers/nearest?longitude=${lon}&latitude=${lat}&max_distance_m=500`
  );
  const data = await response.json();
  return data;
}

// Export GeoJSON for map
async function exportGeoJSON() {
  const response = await fetch('/api/grid/postgis/network/geojson');
  const geojson = await response.json();
  return geojson;
}
```

### Python (requests)

```python
import requests

BASE_URL = 'http://localhost:8082/api/grid/postgis'

# Get statistics
response = requests.get(f'{BASE_URL}/statistics')
stats = response.json()
print(f"Total substations: {stats['total_substations']}")

# Find nearby meters
response = requests.get(
    f'{BASE_URL}/meters/nearby',
    params={
        'longitude': 100.5018,
        'latitude': 13.7563,
        'radius_m': 1000,
        'meter_type': 'solar_prosumer'
    }
)
meters = response.json()
print(f"Found {meters['count']} solar prosumers")

# Register new meter
response = requests.post(
    f'{BASE_URL}/meters',
    params={
        'meter_id': 'METER-001',
        'meter_type': 'solar_prosumer',
        'longitude': 100.5018,
        'latitude': 13.7563,
        'serial_number': 'SN123456789'
    }
)
meter = response.json()
print(f"Registered meter: {meter['meter_id']}")
```

### cURL

```bash
# Health check
curl http://localhost:8082/api/grid/postgis/status

# Get all 22kV substations
curl "http://localhost:8082/api/grid/postgis/substations?voltage=22"

# Find nearest transformer
curl "http://localhost:8082/api/grid/postgis/transformers/nearest?longitude=100.5018&latitude=13.7563&max_distance_m=500"

# Export network GeoJSON
curl http://localhost:8082/api/grid/postgis/network/geojson -o network.geojson

# Register new meter
curl -X POST "http://localhost:8082/api/grid/postgis/meters?meter_id=METER-001&meter_type=solar_prosumer&longitude=100.5018&latitude=13.7563"
```

---

## Performance

**Expected Latencies (p95):**

| Endpoint | Latency |
|----------|---------|
| `/status` | < 50ms |
| `/network/geojson` | < 200ms |
| `/substations` | < 100ms |
| `/transformers/nearest` | < 10ms |
| `/meters/nearby` | < 20ms |
| `/meters` (POST) | < 50ms |
| `/statistics` | < 100ms |

**Rate Limits:**

- No authentication required (public endpoints)
- Recommended: 100 requests/minute per IP
- GeoJSON export: 10 requests/minute (expensive operation)

---

## See Also

- `docs/POSTGIS_INTEGRATION.md` - Complete integration guide
- `docs/THAI_GRID_INTEGRATION.md` - Thai grid specifics
- `docs/POSTGIS_QUICKSTART.md` - Quick start
- `tests/test_postgis/` - Test suite with examples

---

**Part of the GridTokenX Platform**
