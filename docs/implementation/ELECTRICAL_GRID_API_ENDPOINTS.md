# Electrical Grid API Endpoints

## Base URL

```
http://localhost:8082/api/v1/grid
```

---

## Available Endpoints

### 1. Get Electrical Infrastructure

**Endpoint:** `GET /api/v1/grid/electrical-infrastructure`

**Description:** Retrieve electrical infrastructure data with filtering and search capabilities.

**Query Parameters:**

| Parameter | Type | Required | Description | Example |
|-----------|------|----------|-------------|---------|
| `operators` | string | No | Comma-separated list of operators | `EGAT,MEA,PEA` |
| `types` | string | No | Comma-separated list of infrastructure types | `transmission_substation,distribution_pole` |
| `voltage` | string | No | Comma-separated list of voltage levels | `500,230,115` |
| `province` | string | No | Filter by province name | `Bangkok` |
| `search` | string | No | Search by name, ID, or location | `Wang Noi` |
| `limit` | integer | No | Maximum number of results (1-10000) | `1000` |

**Example Request:**
```bash
curl "http://localhost:8082/api/v1/grid/electrical-infrastructure?operators=EGAT,MEA&voltage=500,230&limit=100"
```

**Example Response:**
```json
{
  "infrastructure": [
    {
      "id": "EGAT-WN-001",
      "type": "transmission_substation",
      "operator": "EGAT",
      "latitude": 14.3567,
      "longitude": 100.6234,
      "voltage_kv": 500.0,
      "name_en": "Wang Noi",
      "name_th": "วังน้อย",
      "status": "operational",
      "commissioning_year": 1985,
      "province": "Phra Nakhon Si Ayutthaya",
      "ref": "EGAT-WN-001"
    }
  ],
  "stats": {
    "totalInfrastructure": 30,
    "byOperator": {
      "EGAT": 15,
      "MEA": 10,
      "PEA": 5
    },
    "byType": {
      "transmission_substation": 10,
      "distribution_substation": 15,
      "distribution_pole": 5
    },
    "byVoltage": {
      "500kV": 5,
      "230kV": 8,
      "115kV": 12,
      "22kV": 5,
      "33kV": 0
    },
    "byProvince": {
      "Bangkok": 10,
      "Chiang Mai": 5,
      "Phuket": 3
    }
  },
  "count": 30,
  "total": 100,
  "timestamp": "2024-03-30T12:00:00Z"
}
```

---

### 2. Get Infrastructure Statistics

**Endpoint:** `GET /api/v1/grid/electrical-infrastructure/stats`

**Description:** Get aggregated statistics for all electrical infrastructure.

**Example Request:**
```bash
curl "http://localhost:8082/api/v1/grid/electrical-infrastructure/stats"
```

**Example Response:**
```json
{
  "stats": {
    "totalInfrastructure": 1000,
    "byOperator": {
      "EGAT": 500,
      "MEA": 300,
      "PEA": 200
    },
    "byType": {
      "transmission_substation": 100,
      "distribution_substation": 200,
      "transmission_tower": 150,
      "distribution_pole": 500,
      "power_plant": 50
    },
    "byVoltage": {
      "500kV": 50,
      "230kV": 100,
      "115kV": 200,
      "22kV": 400,
      "33kV": 50
    },
    "byProvince": {
      "Bangkok": 200,
      "Chiang Mai": 100,
      "Phuket": 50
    }
  },
  "timestamp": "2024-03-30T12:00:00Z"
}
```

---

### 3. Get Infrastructure as GeoJSON

**Endpoint:** `GET /api/v1/grid/electrical-infrastructure/geojson`

**Description:** Get infrastructure data in GeoJSON format for mapping libraries.

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `operators` | string | No | Filter by operators |
| `types` | string | No | Filter by types |

**Example Request:**
```bash
curl "http://localhost:8082/api/v1/grid/electrical-infrastructure/geojson?operators=EGAT"
```

**Example Response:**
```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "geometry": {
        "type": "Point",
        "coordinates": [100.6234, 14.3567]
      },
      "properties": {
        "id": "EGAT-WN-001",
        "type": "transmission_substation",
        "operator": "EGAT",
        "voltage_kv": 500.0,
        "name_en": "Wang Noi",
        "name_th": "วังน้อย"
      }
    }
  ],
  "metadata": {
    "count": 500,
    "total": 1000,
    "timestamp": "2024-03-30T12:00:00Z"
  }
}
```

---

### 4. Get Operators

**Endpoint:** `GET /api/v1/grid/electrical-infrastructure/operators`

**Description:** Get information about utility operators (EGAT, MEA, PEA).

**Example Request:**
```bash
curl "http://localhost:8082/api/v1/grid/electrical-infrastructure/operators"
```

**Example Response:**
```json
{
  "operators": {
    "EGAT": {
      "name": "Electricity Generating Authority of Thailand",
      "name_th": "การไฟฟ้าฝ่ายผลิตแห่งประเทศไทย",
      "wikidata": "Q5353891",
      "service_area": "National (Transmission)",
      "color": "#EF4444",
      "voltage_levels": [500, 230, 115]
    },
    "MEA": {
      "name": "Metropolitan Electricity Authority",
      "name_th": "การไฟฟ้านครหลวง",
      "wikidata": "Q13116849",
      "service_area": "Bangkok, Nonthaburi, Samut Prakan",
      "color": "#3B82F6",
      "voltage_levels": [115, 22, 33]
    },
    "PEA": {
      "name": "Provincial Electricity Authority",
      "name_th": "การไฟฟ้าส่วนภูมิภาค",
      "wikidata": "Q7385915",
      "service_area": "All other provinces",
      "color": "#10B981",
      "voltage_levels": [115, 22, 33]
    }
  }
}
```

---

### 5. Get Infrastructure Types

**Endpoint:** `GET /api/v1/grid/electrical-infrastructure/types`

**Description:** Get information about supported infrastructure types.

**Example Request:**
```bash
curl "http://localhost:8082/api/v1/grid/electrical-infrastructure/types"
```

**Example Response:**
```json
{
  "types": {
    "transmission_substation": {
      "name": "Transmission Substation",
      "name_th": "สถานีไฟฟ้าแรงสูง",
      "description": "EGAT transmission substations (500kV, 230kV, 115kV)",
      "min_zoom": 6,
      "color": "#EF4444"
    },
    "distribution_substation": {
      "name": "Distribution Substation",
      "name_th": "สถานีไฟฟ้าจำหน่าย",
      "description": "MEA/PEA distribution substations (115kV, 22kV, 33kV)",
      "min_zoom": 8,
      "color": "#3B82F6"
    },
    "transmission_tower": {
      "name": "Transmission Tower",
      "name_th": "เสาส่งไฟฟ้า",
      "description": "EGAT transmission towers",
      "min_zoom": 10,
      "color": "#F59E0B"
    },
    "distribution_pole": {
      "name": "Distribution Pole",
      "name_th": "เสาไฟฟ้าจำหน่าย",
      "description": "MEA/PEA distribution poles",
      "min_zoom": 12,
      "color": "#60A5FA"
    },
    "power_plant": {
      "name": "Power Plant",
      "name_th": "โรงไฟฟ้า",
      "description": "EGAT power generation facilities",
      "min_zoom": 6,
      "color": "#8B5CF6"
    },
    "solar_farm": {
      "name": "Solar Farm",
      "name_th": "โรงไฟฟ้าพลังงานแสงอาทิตย์",
      "description": "Solar power generation facilities",
      "min_zoom": 8,
      "color": "#FBBF24"
    },
    "battery_storage": {
      "name": "Battery Storage",
      "name_th": "ระบบกักเก็บพลังงานแบตเตอรี่",
      "description": "Battery energy storage systems (BESS)",
      "min_zoom": 8,
      "color": "#EC4899"
    },
    "ev_charging_station": {
      "name": "EV Charging Station",
      "name_th": "สถานีชาร์จรถไฟฟ้า",
      "description": "Electric vehicle charging stations",
      "min_zoom": 10,
      "color": "#06B6D4"
    }
  }
}
```

---

## Frontend Integration

### React Hook Example

```typescript
import { useEffect, useState } from 'react';

function useElectricalGridData() {
  const [infrastructure, setInfrastructure] = useState([]);
  const [stats, setStats] = useState({});
  
  useEffect(() => {
    const fetchData = async () => {
      const response = await fetch('/api/v1/grid/electrical-infrastructure');
      const data = await response.json();
      
      setInfrastructure(data.infrastructure);
      setStats(data.stats);
    };
    
    fetchData();
  }, []);
  
  return { infrastructure, stats };
}
```

### Mapbox GL Example

```javascript
// Fetch GeoJSON
const response = await fetch('/api/v1/grid/electrical-infrastructure/geojson');
const geojson = await response.json();

// Add to map
map.addSource('electrical-infrastructure', {
  type: 'geojson',
  data: geojson
});

map.addLayer({
  id: 'electrical-infrastructure-points',
  type: 'circle',
  source: 'electrical-infrastructure',
  paint: {
    'circle-radius': 8,
    'circle-color': '#EF4444'
  }
});
```

---

## Error Responses

### 400 Bad Request
```json
{
  "detail": "Invalid parameter value"
}
```

### 404 Not Found
```json
{
  "detail": "No infrastructure found matching filters"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Internal server error"
}
```

---

## Rate Limiting

- **Default Limit:** 100 requests per minute per IP
- **GeoJSON Endpoint:** 20 requests per minute (larger responses)

---

## Caching

**Recommended Cache Headers:**
```
Cache-Control: public, max-age=300
ETag: "infrastructure-2024-03-30"
```

**Infrastructure data should be cached for 5 minutes** as it doesn't change frequently.

---

## Testing

### Test with curl

```bash
# Get all infrastructure
curl http://localhost:8082/api/v1/grid/electrical-infrastructure

# Filter by operator
curl "http://localhost:8082/api/v1/grid/electrical-infrastructure?operators=EGAT"

# Filter by voltage
curl "http://localhost:8082/api/v1/grid/electrical-infrastructure?voltage=500,230"

# Get statistics
curl http://localhost:8082/api/v1/grid/electrical-infrastructure/stats

# Get GeoJSON
curl http://localhost:8082/api/v1/grid/electrical-infrastructure/geojson
```

### Test with Python

```python
import requests

# Get infrastructure
response = requests.get('http://localhost:8082/api/v1/grid/electrical-infrastructure')
data = response.json()

# Filter by operator
response = requests.get(
    'http://localhost:8082/api/v1/grid/electrical-infrastructure',
    params={'operators': 'EGAT,MEA'}
)
data = response.json()

# Get GeoJSON
response = requests.get('http://localhost:8082/api/v1/grid/electrical-infrastructure/geojson')
geojson = response.json()
```

---

## Implementation Status

| Endpoint | Status | Mock Data | Production Ready |
|----------|--------|-----------|------------------|
| `/electrical-infrastructure` | ✅ Complete | ✅ Yes | ⚠️ Needs real data |
| `/electrical-infrastructure/stats` | ✅ Complete | ✅ Yes | ⚠️ Needs real data |
| `/electrical-infrastructure/geojson` | ✅ Complete | ✅ Yes | ⚠️ Needs real data |
| `/electrical-infrastructure/operators` | ✅ Complete | ✅ Yes | ✅ Ready |
| `/electrical-infrastructure/types` | ✅ Complete | ✅ Yes | ✅ Ready |

---

**Version:** 1.0.0  
**Date:** 2024-03-30  
**Status:** ✅ Complete with Mock Data
