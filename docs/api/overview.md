# API Reference

**Base URL:** `http://localhost:8082`  
**WebSocket:** `ws://localhost:8082/ws`

## Authentication

Most endpoints require an API key passed via header:

```http
Authorization: Bearer YOUR_API_KEY
```

## Endpoints

### Health & Status

#### Health Check

```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

#### Simulator Status

```http
GET /api/status
```

**Response:**
```json
{
  "running": true,
  "paused": false,
  "meters_count": 55,
  "simulation_time": "2024-01-01T12:00:00Z",
  "interval_seconds": 15
}
```

### Meter Endpoints

#### List Meters

```http
GET /api/meters
```

**Response:**
```json
{
  "meters": [
    {
      "meter_id": "AMI_METER_001",
      "type": "Solar_Prosumer",
      "accuracy_class": "CLASS_1_0",
      "status": "active"
    }
  ]
}
```

#### Get Meter Details

```http
GET /api/meters/{meter_id}
```

**Response:**
```json
{
  "meter_id": "AMI_METER_001",
  "type": "Solar_Prosumer",
  "accuracy_class": "CLASS_1_0",
  "public_key": "base64-encoded-key",
  "last_reading": {
    "timestamp": "2024-01-01T12:00:00Z",
    "energy_generated_kwh": 5.234,
    "energy_consumed_kwh": 2.145
  }
}
```

### Grid Endpoints

#### Grid Status

```http
GET /api/grid/status
```

**Response:**
```json
{
  "buses": 10,
  "lines": 15,
  "measurements": 55,
  "state_estimation": {
    "converged": true,
    "iterations": 3
  }
}
```

#### Grid Topology

```http
GET /api/grid/topology
```

**Response:** Detailed grid topology in JSON format

#### GeoJSON Topology

```http
GET /api/grid/geojson
```

**Response:** Grid topology in GeoJSON format for mapping

#### Measurements

```http
GET /api/grid/measurements
```

**Response:** Current state estimation measurements

#### State Estimation Results

```http
GET /api/grid/estimation
```

**Response:**
```json
{
  "converged": true,
  "iterations": 3,
  "chi_squared": 12.5,
  "chi_squared_critical": 15.2,
  "bad_data_detected": false,
  "results": {
    "voltage_magnitudes": [...],
    "voltage_angles": [...]
  }
}
```

### Market Endpoints

#### Market Orders

```http
GET /api/market/orders
```

**Response:**
```json
{
  "active_orders": [
    {
      "order_id": "ORD_001",
      "type": "SELL",
      "price": 3.50,
      "quantity_kwh": 10.0,
      "meter_id": "AMI_METER_001"
    }
  ]
}
```

#### Market Clearing

```http
GET /api/market/clearing
```

**Response:** Latest market clearing results

### VPP Endpoints

#### VPP Status

```http
GET /api/vpp/status
```

**Response:**
```json
{
  "clusters": 3,
  "total_capacity_kwh": 150.0,
  "available_capacity_kwh": 120.0,
  "active_dispatch": false
}
```

#### VPP Dispatch

```http
GET /api/vpp/dispatch
```

**Response:** Current VPP dispatch commands

### Frequency Endpoints

#### Grid Frequency

```http
GET /api/frequency
```

**Response:**
```json
{
  "frequency_hz": 50.02,
  "deviation_hz": 0.02,
  "rocobuf_hz_s": 0.001,
  "droop_control_active": true
}
```

### Islanding Endpoints

#### Island Status

```http
GET /api/island/status
```

**Response:**
```json
{
  "islanded": false,
  "island_id": null,
  "generation_load_balance": null
}
```

## Price & Revenue APIs

### Compare Prices

```http
POST /api/v1/price/compare
Content-Type: application/json

{
  "consumption_kwh": 500,
  "generation_kwh": 300,
  "tariff_type": "1.2"
}
```

**Response:**
```json
{
  "utility_bill": 2500.50,
  "p2p_bill": 2100.00,
  "savings": 400.50,
  "savings_percent": 16.02
}
```

### Utility Rates

```http
GET /api/v1/price/utility-rates
```

**Response:**
```json
{
  "tariff_type": "1.2",
  "on_peak_rate": 5.7982,
  "off_peak_rate": 2.6369,
  "service_charge": 33.29,
  "ft_charge": 0.0972
}
```

### Dynamic P2P Price

```http
GET /api/v1/price/p2p-dynamic
```

**Response:**
```json
{
  "current_price": 3.50,
  "price_floor": 2.20,
  "demand_supply_ratio": 1.2,
  "timestamp": "2024-01-01T12:00:00Z"
}
```

### Compare Revenue Models

```http
POST /api/v1/revenue/compare
Content-Type: application/json

{
  "generation_kwh": 300,
  "export_kwh": 200
}
```

**Response:**
```json
{
  "single_buyer_revenue": 440.00,
  "p2p_revenue": 700.00,
  "difference": 260.00,
  "improvement_percent": 59.09
}
```

### Optimize Revenue

```http
GET /api/v1/revenue/optimize
```

**Response:** Optimal revenue configuration recommendations

### Market Prices

```http
GET /api/v1/p2p/market-prices
```

**Response:** Current P2P market prices

### Calculate P2P Cost

```http
POST /api/v1/p2p/calculate-cost
Content-Type: application/json

{
  "quantity_kwh": 50,
  "price_baht_kwh": 3.50
}
```

**Response:**
```json
{
  "energy_cost": 175.00,
  "wheeling_cost": 88.00,
  "total_cost": 263.00
}
```

## WebSocket Protocol

### Connection

```javascript
const ws = new WebSocket('ws://localhost:8082/ws');
```

### Messages

**Meter Reading:**
```json
{
  "type": "reading",
  "data": {
    "timestamp": "2024-01-01T12:00:00Z",
    "meter_id": "AMI_METER_001",
    "energy_generated_kwh": 5.234,
    "energy_consumed_kwh": 2.145,
    "voltage_v": 239.8,
    "frequency_hz": 50.02,
    "signature": "base64-signature"
  }
}
```

**Price Update:**
```json
{
  "type": "price",
  "data": {
    "timestamp": "2024-01-01T12:00:00Z",
    "p2p_price": 3.50,
    "utility_rate": 4.22,
    "lmp": 3.75
  }
}
```

### Error Handling

```javascript
ws.onerror = (error) => {
  console.error('WebSocket error:', error);
};

ws.onclose = () => {
  console.log('Connection closed, reconnecting...');
  setTimeout(connect, 5000);
};
```

## Error Codes

| Code | Description |
|------|-------------|
| 200 | Success |
| 400 | Bad Request - Invalid parameters |
| 401 | Unauthorized - Invalid API key |
| 404 | Not Found |
| 500 | Internal Server Error |
| 503 | Service Unavailable |

## Rate Limiting

- **REST API:** 100 requests/minute
- **WebSocket:** 1000 messages/minute

## Related Documents

- [Getting Started](../guides/getting-started.md)
- [Running Simulations](../guides/running-simulations.md)
- [WebSocket Protocol](websocket.md)
