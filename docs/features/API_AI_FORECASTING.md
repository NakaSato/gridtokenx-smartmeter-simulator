# AI Forecasting API Documentation

## Overview

The AI forecasting system implements a dual-layer architecture:
1. **Centralized Forecasting Engine**: Complex multi-island constraint analysis
2. **Edge Forecasting Engine**: Lightweight substation-level forecasting

## Base URL

```
http://localhost:8082/api/v1
```

## Endpoints

### 1. Dual-Target Forecast

Generate 24-hour forecast for both Load_Tao (Yellow Line) and Capacity_115kV (Blue Line).

**Endpoint:** `GET /forecast/dual-target`

**Query Parameters:**
- `current_load_kw` (float, default: 15000.0): Current load on Koh Tao in kW
- `start_time` (string, optional): ISO format start time (defaults to now)

**Example Request:**
```bash
curl "http://localhost:8082/api/v1/forecast/dual-target?current_load_kw=15000"
```

**Example Response:**
```json
{
  "generated_at": "2026-04-20T05:10:00.000000",
  "forecast_start": "2026-04-20T00:00:00",
  "forecasts": [
    {
      "timestamp": "2026-04-20T00:00:00",
      "hour_offset": 0,
      "Load_Tao": 19333.33,
      "Capacity_115kV": -34975.0,
      "delta": -54308.33,
      "constraint_active": true,
      "DAP_d": 15333,
      "T_active": 5333,
      "thermal_derating_kw": 0.0
    }
  ],
  "summary": {
    "constraint_hours": 24,
    "total_deficit_kw": 1498154.98,
    "avg_load_kw": 21267.5,
    "avg_capacity_kw": -41155.62,
    "peak_load_kw": 26199.36,
    "min_capacity_kw": -52750.0
  },
  "constraints": [
    {
      "hour": 0,
      "timestamp": "2026-04-20T00:00:00",
      "deficit_kw": 54308.33,
      "required_bess_kw": 54308.33
    }
  ]
}
```

### 2. Constraint Analysis

Analyze capacity constraints and calculate BESS dispatch requirements.

**Endpoint:** `GET /forecast/constraints`

**Query Parameters:**
- `current_load_kw` (float, default: 15000.0)
- `start_time` (string, optional)

**Example Request:**
```bash
curl "http://localhost:8082/api/v1/forecast/constraints?current_load_kw=15000"
```

**Example Response:**
```json
{
  "status": "CONSTRAINTS_DETECTED",
  "constraint_count": 24,
  "bess_required": true,
  "bess_requirements": {
    "peak_power_kw": 78949.36,
    "total_energy_kwh": 1498154.98,
    "recommended_capacity_kwh": 1797785.98,
    "recommended_power_kw": 86844.3
  },
  "critical_hours": [
    {
      "hour": 18,
      "timestamp": "2026-04-20T18:00:00",
      "deficit_kw": 78949.36
    }
  ]
}
```

### 3. Demographic Metrics

Calculate Daily Active Population (DAP) and dynamic base load for Koh Tao and Koh Phangan.

**Endpoint:** `GET /forecast/demographics`

**Query Parameters:**
- `target_date` (string, optional): ISO format date (defaults to today)

**Example Request:**
```bash
curl "http://localhost:8082/api/v1/forecast/demographics?target_date=2026-04-20"
```

**Example Response:**
```json
{
  "date": "2026-04-20",
  "koh_tao": {
    "daily_active_population": 15333,
    "tourist_active": 5333,
    "base_load_kw": 20333.33
  },
  "koh_phangan": {
    "tourist_active": 6000,
    "digital_nomad_active": 5000,
    "base_load_kw": 49500.0,
    "full_moon_window": false
  }
}
```

### 4. Edge 24-Hour Forecast

Lightweight edge forecasting for substation deployment.

**Endpoint:** `GET /forecast/24h`

**Query Parameters:**
- `node_id` (string, default: "SAMUI-HUB-01")
- `current_load_mw` (float, default: 15.0)
- `temp_c` (float, default: 33.0)
- `cloud_cover` (float, default: 10.0)

**Example Request:**
```bash
curl "http://localhost:8082/api/v1/forecast/24h?node_id=SAMUI-HUB-01&current_load_mw=15.0"
```

**Example Response:**
```json
{
  "node_id": "SAMUI-HUB-01",
  "generated_at": "2026-04-20T05:10:00.000000+00:00",
  "mape_pct": 5.23,
  "model": "rule_based",
  "forecast_mw": [9.0, 7.5, 6.75, ...],
  "schedule": [
    {
      "hour": 0,
      "load_mw": 9.0,
      "p_grid_mw": 9.0,
      "p_bess_mw": 0.0,
      "p_diesel_mw": 0.0
    }
  ]
}
```

### 5. MAPE Validation

Get Mean Absolute Percentage Error for forecast accuracy.

**Endpoint:** `GET /forecast/mape`

**Query Parameters:**
- `node_id` (string, default: "SAMUI-HUB-01")

**Example Request:**
```bash
curl "http://localhost:8082/api/v1/forecast/mape?node_id=SAMUI-HUB-01"
```

**Example Response:**
```json
{
  "node_id": "SAMUI-HUB-01",
  "last_mape_pct": 5.23,
  "target_pct": 10.0
}
```

### 6. Optimal Dispatch Schedule

Calculate cost-optimized 24-hour dispatch schedule using OPF.

**Endpoint:** `GET /optimize/schedule`

**Query Parameters:**
- `node_id` (string, default: "SAMUI-HUB-01")
- `current_load_mw` (float, default: 15.0)

**Example Request:**
```bash
curl "http://localhost:8082/api/v1/optimize/schedule?current_load_mw=15.0"
```

**Example Response:**
```json
{
  "node_id": "SAMUI-HUB-01",
  "schedule": [
    {
      "hour": 0,
      "load_mw": 5.0,
      "p_grid_mw": 5.0,
      "p_bess_mw": 0.0,
      "p_diesel_mw": 0.0,
      "bess_soc_mwh": 25.0,
      "savings_thb": 47500
    }
  ],
  "total_savings_thb": 1140000,
  "total_cost_baseline_thb": 3744000,
  "total_cost_optimized_thb": 2604000
}
```

### 7. Cost Savings Analysis

Get daily, monthly, and annual cost savings from optimization.

**Endpoint:** `GET /optimize/savings`

**Query Parameters:**
- `node_id` (string, default: "SAMUI-HUB-01")
- `current_load_mw` (float, default: 15.0)

**Example Request:**
```bash
curl "http://localhost:8082/api/v1/optimize/savings?current_load_mw=15.0"
```

**Example Response:**
```json
{
  "node_id": "SAMUI-HUB-01",
  "daily_savings_thb": 1140000,
  "monthly_savings_thb": 34200000,
  "annual_savings_thb": 416100000,
  "baseline_thb": 3744000,
  "optimized_thb": 2604000,
  "cost_reduction_pct": 30.4
}
```

### 8. Early Warning System Status

Get current EWS status and alert history.

**Endpoint:** `GET /ews/status`

**Example Request:**
```bash
curl "http://localhost:8082/api/v1/ews/status"
```

**Example Response:**
```json
{
  "incident_active": false,
  "alert_count": 0,
  "latest_alert": null
}
```

### 9. Simulate Grid Incident

Trigger EWS incident simulation for submarine cable fault.

**Endpoint:** `POST /ews/simulate`

**Request Body:**
```json
{
  "line_id": "115kV KMB Circuit 3",
  "line_capacity_mw": 70.0,
  "loading_pct": 98.0
}
```

**Example Request:**
```bash
curl -X POST "http://localhost:8082/api/v1/ews/simulate" \
  -H "Content-Type: application/json" \
  -d '{
    "line_id": "115kV KMB Circuit 3",
    "line_capacity_mw": 70.0,
    "loading_pct": 98.0
  }'
```

**Example Response:**
```json
{
  "alert": {
    "type": "EWS_OVERLOAD_WARNING",
    "severity": "HIGH",
    "line_id": "115kV KMB Circuit 3",
    "loading_pct": 98.0,
    "timestamp": "2026-04-20T05:10:00.000000",
    "recommended_action": "PREEMPTIVE_PEAK_SHAVING"
  },
  "emergency_response": {
    "action": "BESS switched to grid-forming mode",
    "bess_dispatch_mw": 20.0,
    "diesel_spinup_mw": 1.0,
    "afrr_triggered": true
  }
}
```

### 10. Reset EWS Incident

Reset the Early Warning System incident status.

**Endpoint:** `POST /ews/reset`

**Example Request:**
```bash
curl -X POST "http://localhost:8082/api/v1/ews/reset"
```

**Example Response:**
```json
{
  "status": "reset"
}
```

### 11. Train LightGBM Model

Trigger model training using historical data from InfluxDB.

**Endpoint:** `POST /forecast/train`

**Example Request:**
```bash
curl -X POST "http://localhost:8082/api/v1/forecast/train"
```

**Example Response:**
```json
{
  "status": "ok",
  "output": "Training completed. MAPE: 7.23%",
  "error": ""
}
```

## Key Concepts

### Dual-Target Forecasting

The system predicts two critical metrics:

1. **Load_Tao (Yellow Line)**: Forecasted electrical demand on Koh Tao
2. **Capacity_115kV (Blue Line)**: Dynamic remaining capacity of submarine cable

When `Capacity_115kV < Load_Tao`, a constraint is triggered requiring BESS dispatch.

### Demographic Load Models

Load calculations incorporate real-world tourism and residency data:

- **Koh Tao DAP**: Daily Active Population based on seasonal tourism patterns
- **Koh Phangan Lunar Factor**: Full Moon Party spikes (+8 MW on days 22-24)
- **Digital Nomad Baseload**: Fixed active population with high energy intensity

### Dynamic Line Rating (DLR)

Cable capacity includes thermal derating simulation:
- Heat accumulation when upstream load exceeds 18 MW
- Ambient temperature penalties
- 150 kW reduction per unit of thermal stress

## Error Codes

- `200`: Success
- `400`: Bad Request (invalid parameters)
- `500`: Internal Server Error

## Rate Limits

No rate limits currently enforced in development mode.

## Authentication

No authentication required in development mode. Production deployment should implement API key authentication.
