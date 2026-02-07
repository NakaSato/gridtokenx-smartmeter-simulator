# API Reference

This document describes the REST API endpoints and WebSocket interface for the Smart Meter Simulator.

## Base URL

```
http://localhost:8000
```

## Authentication

Currently, the API does not require authentication. In production deployments, API key or JWT authentication should be configured.

---

## Dashboard Endpoints

### GET `/`

Returns the main dashboard HTML page.

**Response**: HTML page

### GET `/how-it-works`

Returns an animated explanation page.

**Response**: HTML page

---

## Status Endpoints

### GET `/api/status`

Get the current simulator status including all meters and grid metrics.

**Response**:
```json
{
  "status": "running",
  "running": true,
  "paused": false,
  "meters": [
    {
      "meter_id": "M001",
      "name": "Solar_Prosumer",
      "location": "Zone_1_Building_1",
      "capacity": 10.5,
      "current_generation": 2.5,
      "current_consumption": 1.2,
      "energy_type": "Solar_Prosumer",
      "status": "active"
    }
  ],
  "num_meters": 20,
  "mode": "Simulation",
  "api_gateway": "http://localhost:3000/api",
  "grid_metrics": {
    "converged": true,
    "num_measurements": 60,
    "chi2": 0.000123,
    "v_deviation_avg": 0.0012
  },
  "websocket_clients": 2
}
```

### GET `/health/ready`

Deep health check verifying connectivity to all dependencies.

**Response**:
```json
{
  "status": "ready",
  "dependencies": {
    "database": "ok",
    "KafkaTransport": "connected",
    "WebSocketTransport": "connected",
    "HttpTransport": "connected"
  }
}
```

### GET `/metrics`

Prometheus-compatible metrics endpoint.

**Response**: Prometheus text format

---

## Control Endpoints

### POST `/api/control/start`

Start the simulation.

**Response**:
```json
{
  "success": true,
  "message": "Simulation started",
  "status": {
    "running": true,
    "paused": false,
    "num_meters": 20
  }
}
```

### POST `/api/control/stop`

Stop the simulation.

**Response**:
```json
{
  "success": true,
  "message": "Simulation stopped",
  "status": {
    "running": false,
    "paused": false,
    "num_meters": 20
  }
}
```

### POST `/api/control/pause`

Pause the simulation (meters stop generating readings but state is preserved).

**Response**:
```json
{
  "success": true,
  "message": "Simulation paused",
  "status": {
    "running": true,
    "paused": true,
    "num_meters": 20
  }
}
```

### POST `/api/control/resume`

Resume a paused simulation.

**Response**:
```json
{
  "success": true,
  "message": "Simulation resumed",
  "status": {
    "running": true,
    "paused": false,
    "num_meters": 20
  }
}
```

### POST `/api/control/restart`

Stop and restart the simulation.

**Response**:
```json
{
  "success": true,
  "message": "Simulation restarted",
  "status": {
    "running": true,
    "paused": false,
    "num_meters": 20
  }
}
```

### POST `/api/control/meters`

Update the number of meters and restart simulation.

**Request Body**:
```json
{
  "num_meters": 50
}
```

**Response**:
```json
{
  "success": true,
  "message": "Updated to 50 meters and restarted",
  "status": {
    "running": true,
    "paused": false,
    "num_meters": 50
  }
}
```

### POST `/api/control/mode`

Set simulation mode (random generation or historical playback).

**Request Body**:
```json
{
  "mode": "playback",
  "profile": "summer_2025"
}
```

**Response**:
```json
{
  "success": true,
  "mode": "playback",
  "profile": "summer_2025"
}
```

---

## Grid Analysis Endpoints

### GET `/api/grid/status`

Get summarized grid topology status.

**Response**:
```json
{
  "num_buses": 25,
  "num_lines": 24,
  "num_loads": 20,
  "num_sgens": 8,
  "has_external_grid": true,
  "voltage_levels": [110.0, 20.0, 0.4]
}
```

### GET `/api/grid/topology`

Get detailed grid topology with buses and lines.

**Response**:
```json
{
  "buses": {
    "0": {
      "name": "HV_Bus",
      "vn_kv": 110.0,
      "type": "b"
    },
    "1": {
      "name": "MV_Bus",
      "vn_kv": 20.0,
      "type": "b"
    }
  },
  "lines": [
    {
      "name": "Line_0_1",
      "from_bus": 0,
      "to_bus": 1,
      "length_km": 5.0,
      "max_i_ka": 0.5
    }
  ]
}
```

### GET `/api/grid/legacy-topology`

Get topology in legacy format for frontend compatibility (zones/meters).

**Response**:
```json
{
  "zones": {
    "1": {
      "zone_id": 1,
      "transformer_name": "Transformer Zone 1",
      "centroid_lat": 13.736717,
      "centroid_lon": 100.523186,
      "radius_km": 0.5
    }
  },
  "meters": [
    {
      "meter_id": "M001",
      "meter_serial": "M001",
      "zone_id": 1,
      "type": "Solar_Prosumer",
      "location": "Zone_1_Building_1",
      "latitude": 13.7365,
      "longitude": 100.5230,
      "status": "active"
    }
  ]
}
```

### GET `/api/grid/estimation`

Get latest state estimation results.

**Response**:
```json
{
  "converged": true,
  "iterations": 4,
  "num_measurements": 60,
  "chi2": 0.000123,
  "mean_absolute_error": 0.000456,
  "max_residual": 0.001234,
  "v_deviation_avg": 0.0012,
  "total_losses_mw": 0.025,
  "timestamp": "2026-02-03T10:30:00.000Z"
}
```

### GET `/api/grid/measurements`

Get current measurements used for state estimation.

**Response**:
```json
{
  "measurements": [
    {
      "name": "M001_V",
      "measurement_type": "v",
      "element_type": "bus",
      "element": 5,
      "value": 1.002,
      "std_dev": 0.002,
      "side": null
    },
    {
      "name": "M001_P",
      "measurement_type": "p",
      "element_type": "load",
      "element": 0,
      "value": 0.0012,
      "std_dev": 0.00004,
      "side": null
    }
  ]
}
```

### GET `/api/grid/export/cim`

Export current grid state as CIM XML.

**Response**: XML document (application/xml)

---

## Profile Management Endpoints

### GET `/api/profiles`

List available historical profiles for playback.

**Response**:
```json
{
  "profiles": [
    "summer_2025",
    "winter_2025",
    "test_profile"
  ]
}
```

### POST `/api/profiles/upload`

Upload or save a profile dataset.

**Request Body**:
```json
{
  "name": "my_profile",
  "data": [...],
  "format": "csv"
}
```

**Response**:
```json
{
  "success": true,
  "message": "Profile saved to data/profiles/my_profile.csv"
}
```

### POST `/api/profiles/generate`

Generate a synthetic profile based on Standard Load Profile (SLP).

**Request Body**:
```json
{
  "name": "synthetic_h0",
  "profile_type": "H0",
  "annual_kwh": 3500,
  "days": 7,
  "meter_ids": ["M001", "M002", "M003"]
}
```

**Response**:
```json
{
  "success": true,
  "message": "Profile synthetic_h0 generated successfully"
}
```

---

## Analytics Endpoints

### GET `/api/analytics/report`

Get summarized grid health report.

**Response**:
```json
{
  "latest": {
    "loss_mw": 0.025,
    "loss_pct": 2.5,
    "avg_v": 1.002,
    "violations": 0
  },
  "history_size": 100,
  "total_violations_detected": 5,
  "max_loss_observed": 0.035,
  "min_v_observed": 0.96,
  "max_v_observed": 1.04
}
```

---

## Attack Simulation Endpoint

### POST `/api/control/attack`

Configure and start/stop a False Data Injection (FDI) attack simulation.

**Request Body**:
```json
{
  "active": true,
  "targets": ["M001", "M005"],
  "mode": "bias",
  "bias": 0.1,
  "scale": 1.0,
  "stealthy": true
}
```

**Response**:
```json
{
  "success": true,
  "status": {
    "active": true,
    "targets": ["M001", "M005"],
    "mode": "bias",
    "stealthy": true
  }
}
```

**Attack Modes**:
- `bias`: Add constant offset to readings
- `scale`: Multiply readings by scale factor
- `random`: Add random noise

---

## WebSocket Interface

### Endpoint: `/ws`

Connect to receive real-time meter readings and grid status updates.

**Connection**:
```javascript
const ws = new WebSocket('ws://localhost:8000/ws');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log(data);
};
```

### Message Types

#### Meter Readings
```json
{
  "type": "meter_readings",
  "timestamp": "2026-02-03T10:30:00.000Z",
  "readings": [
    {
      "meter_id": "M001",
      "timestamp": "2026-02-03T10:30:00.000Z",
      "energy_generated": 2.5,
      "energy_consumed": 1.2,
      "surplus_energy": 1.3,
      "deficit_energy": 0,
      "battery_level": 75.5,
      "voltage": 240.5,
      "current": 5.2,
      "power_factor": 0.95,
      "frequency": 50.02,
      "temperature": 22.5,
      "location": "Zone_1_Building_1",
      "meter_type": "Solar_Prosumer",
      "user_type": "residential",
      "rec_eligible": true,
      "carbon_offset": 0.625
    }
  ]
}
```

#### Single Meter Reading
```json
{
  "type": "meter_reading",
  "timestamp": "2026-02-03T10:30:00.000Z",
  "reading": {
    "meter_id": "M001",
    ...
  }
}
```

#### Grid Status
```json
{
  "type": "grid_status",
  "converged": true,
  "num_measurements": 60,
  "v_deviation_avg": 0.0012,
  "total_losses_mw": 0.025
}
```

---

## Error Responses

All API endpoints return consistent error responses:

```json
{
  "success": false,
  "message": "Error description"
}
```

Or for uninitialized simulator:

```json
{
  "error": "Simulator not initialized"
}
```

## HTTP Status Codes

| Code | Description |
|------|-------------|
| 200 | Success |
| 400 | Bad Request (invalid parameters) |
| 404 | Not Found |
| 500 | Internal Server Error |

---

## Rate Limits

The simulator does not impose rate limits by default. For production deployments, consider implementing rate limiting at the reverse proxy level.

## CORS

CORS is enabled for all origins by default. Configure `allow_origins` in production.
