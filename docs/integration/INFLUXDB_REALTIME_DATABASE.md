# InfluxDB Real-Time Database Integration

## 📋 **Overview**

InfluxDB has been integrated into the GridTokenX Smart Meter Simulator as a **real-time time-series database** for:

- **High-frequency meter readings** (15-second intervals)
- **Grid state estimation metrics**
- **Alert history and monitoring**
- **Dashboard data for Grafana/visualization**
- **Historical trend analysis**

---

## 🚀 **Quick Start**

### 1. Start InfluxDB

```bash
# Start InfluxDB via Docker Compose
cd /Users/chanthawat/Developments/gridtokenx-platform-infa/gridtokenx-smartmeter-simulator
docker-compose up -d influxdb

# Verify InfluxDB is running
curl http://localhost:8086/health
```

### 2. Configure Environment

Add to `.env`:

```bash
INFLUXDB_URL=http://localhost:8086
INFLUXDB_TOKEN=admin_token
INFLUXDB_ORG=gridtokenx
INFLUXDB_BUCKET=meter_readings
```

### 3. Start Simulator

```bash
uv run uvicorn smart_meter_simulator.app:app --host 0.0.0.0 --port 8082
```

The InfluxDB query service will automatically connect during startup.

---

## 📊 **API Endpoints**

All endpoints are under `/api/v1/timeseries/`

### **Real-Time Dashboard**

```bash
GET /api/v1/timeseries/dashboard?meter_ids=METER_1,METER_2
```

**Response:**
```json
{
  "timestamp": "2026-04-04T16:30:00Z",
  "active_meters": 20,
  "total_generation_kw": 45.2,
  "total_consumption_kw": 78.5,
  "net_balance_kw": -33.3,
  "readings": [ ... ]
}
```

---

### **Meter History**

```bash
GET /api/v1/timeseries/meters/{meter_id}/history?duration=24h&aggregation=mean
```

**Parameters:**
- `duration`: Time range (`1h`, `24h`, `7d`, `30d`)
- `aggregation`: `mean`, `max`, `min`, `sum`, `last`, `first`

**Response:**
```json
{
  "meter_id": "METER_001",
  "duration": "24h",
  "aggregation": "mean",
  "data_points": 288,
  "readings": [
    {
      "time": "2026-04-04T00:00:00Z",
      "energy_generated": 2.5,
      "energy_consumed": 1.8,
      "battery_level": 7.2
    },
    ...
  ]
}
```

---

### **Energy Summary**

```bash
GET /api/v1/timeseries/energy-summary?duration=24h&meter_ids=METER_1,METER_2
```

**Response:**
```json
{
  "duration": "24h",
  "total_generation_kwh": 542.5,
  "total_consumption_kwh": 1884.2,
  "net_energy_kwh": -1341.7,
  "self_sufficiency_pct": 28.8
}
```

---

### **Alerts**

```bash
GET /api/v1/timeseries/alerts?duration=24h&severity=warning&limit=50
```

**Response:**
```json
{
  "duration": "24h",
  "severity_filter": "warning",
  "total_alerts": 12,
  "alerts": [
    {
      "time": "2026-04-04T14:23:00Z",
      "type": "GRID_EVENT",
      "severity": "warning",
      "message": "High voltage detected",
      "value": 252.3
    },
    ...
  ]
}
```

---

### **InfluxDB Status**

```bash
GET /api/v1/timeseries/status
```

**Response:**
```json
{
  "influxdb_connected": true,
  "url": "http://localhost:8086",
  "bucket": "meter_readings",
  "org": "gridtokenx",
  "available_endpoints": [
    "GET /api/v1/timeseries/dashboard",
    "GET /api/v1/timeseries/meters/{meter_id}/history",
    "GET /api/v1/timeseries/energy-summary",
    "GET /api/v1/timeseries/alerts",
    "GET /api/v1/timeseries/status"
  ]
}
```

---

## 🏗️ **Architecture**

### **Data Flow**

```
Smart Meter → SimulationEngine.tick()
                  ↓
         CompositeTransport
                  ↓
         InfluxDBTransport (Write)
                  ↓
         InfluxDB Bucket: meter_readings
                  ↓
    InfluxDBQueryService (Read)
                  ↓
         API Endpoints (/api/v1/timeseries/*)
                  ↓
         Dashboard / Grafana / Client Apps
```

### **Components**

| Component | File | Purpose |
|-----------|------|---------|
| **InfluxDBTransport** | `transport/influxdb.py` | Writes readings to InfluxDB |
| **InfluxDBQueryService** | `transport/influxdb_query.py` | Queries time-series data |
| **API Endpoints** | `routers/api_v1.py` | REST API for querying |
| **Docker Compose** | `docker-compose.yml` | InfluxDB container |

---

## 📈 **InfluxDB Schema**

### **Measurements**

#### `meter_reading`

**Tags:**
- `meter_id`: Unique meter identifier
- `meter_type`: Solar_Prosumer, Residential, etc.
- `location`: Geographic location

**Fields:**
- `energy_generated`: kWh generated
- `energy_consumed`: kWh consumed
- `battery_level`: kWh stored
- `carbon_offset`: kg CO2 offset

**Time:** UTC timestamp

---

#### `grid_status`

**Tags:**
- `status`: converged, failed

**Fields:**
- `mae`: Mean absolute error
- `max_residual`: Maximum residual
- `total_losses_mw`: Grid losses
- `loss_pct`: Loss percentage
- `avg_v`: Average voltage
- `health_score`: Grid health (0-100)
- `violations`: Number of violations

---

#### `alert`

**Tags:**
- `type`: GRID_EVENT, ISLANDING, etc.
- `severity`: info, warning, critical

**Fields:**
- `message`: Alert description
- `value`: Numeric value associated with alert

---

## 🔧 **Grafana Integration**

### Dashboard Setup

1. Add InfluxDB data source in Grafana:
   - URL: `http://localhost:8086`
   - Token: `admin_token`
   - Org: `gridtokenx`
   - Bucket: `meter_readings`

2. Example Flux Query for energy generation:

```flux
from(bucket: "meter_readings")
  |> range(start: -24h)
  |> filter(fn: (r) => r._measurement == "meter_reading")
  |> filter(fn: (r) => r._field == "energy_generated")
  |> aggregateWindow(every: 5m, fn: mean)
  |> yield(name: "mean")
```

---

## 🧪 **Testing**

### Test InfluxDB Connection

```bash
curl http://localhost:8082/api/v1/timeseries/status
```

### Query Dashboard

```bash
curl http://localhost:8082/api/v1/timeseries/dashboard
```

### Get Meter History

```bash
curl "http://localhost:8082/api/v1/timeseries/meters/METER_001/history?duration=1h&aggregation=mean"
```

---

## ⚙️ **Configuration**

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `INFLUXDB_URL` | `http://localhost:8086` | InfluxDB server URL |
| `INFLUXDB_TOKEN` | `admin_token` | Authentication token |
| `INFLUXDB_ORG` | `gridtokenx` | Organization name |
| `INFLUXDB_BUCKET` | `meter_readings` | Bucket name |

### Docker Compose

InfluxDB is configured in `docker-compose.yml`:

```yaml
influxdb:
  image: influxdb:2.7
  ports:
    - "8086:8086"
  environment:
    DOCKER_INFLUXDB_INIT_MODE: setup
    DOCKER_INFLUXDB_INIT_USERNAME: admin
    DOCKER_INFLUXDB_INIT_PASSWORD: admin_password
    DOCKER_INFLUXDB_INIT_ORG: gridtokenx
    DOCKER_INFLUXDB_INIT_BUCKET: meter_readings
    DOCKER_INFLUXDB_INIT_RETENTION: 1y
```

---

## 📊 **Performance**

### Expected Query Latencies

| Query Type | Latency | Data Points |
|------------|---------|-------------|
| Latest readings | <50ms | 100 meters |
| 24h history (5m agg) | <100ms | 288 points |
| 7d history (1h agg) | <200ms | 168 points |
| Energy summary | <50ms | Aggregated |
| Alerts (24h) | <30ms | 50 alerts |

---

## 🚨 **Troubleshooting**

### InfluxDB Not Connected

```bash
# Check InfluxDB container
docker ps | grep influxdb

# Check logs
docker logs gridtokenx-influxdb

# Test connection
curl http://localhost:8086/health
```

### Query Returns Empty

```bash
# Check if data is being written
curl http://localhost:8082/api/v1/timeseries/status

# Verify bucket exists
curl -H "Authorization: Token admin_token" \
  http://localhost:8086/api/v2/buckets
```

### High Latency

- Reduce query duration (`1h` instead of `7d`)
- Use aggregation (`mean`, `max`) to reduce data points
- Increase InfluxDB resources (CPU/RAM)

---

## 📁 **Files Modified/Created**

| File | Type | Description |
|------|------|-------------|
| `transport/influxdb_query.py` | Created | Query service for real-time data |
| `routers/api_v1.py` | Modified | Added 5 new `/timeseries/` endpoints |
| `app.py` | Modified | InfluxDB query service initialization |
| `.env.example` | Modified | Updated InfluxDB defaults |

---

**Status:** ✅ InfluxDB integrated as real-time database with 5 API endpoints
