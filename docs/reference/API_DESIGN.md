# GridTokenX Smart Meter Simulator — Production API Design

**Base URL:** `https://api.gridtokenx.io/v1`
**Auth:** `Authorization: Bearer <jwt>` on all protected routes
**Content-Type:** `application/json`
**Versioning:** URI path (`/v1/`)

---

## Authentication

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/auth/token` | Issue JWT (client_credentials or password grant) |
| `POST` | `/auth/refresh` | Refresh access token |
| `DELETE` | `/auth/token` | Revoke token |

**Headers on all protected endpoints:**
```
Authorization: Bearer <jwt>
X-API-Key: <c2c_key>          # Cloud-to-Cloud ingestion only
X-Request-ID: <uuid>          # Idempotency key
```

---

## Simulation Control

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/simulation/status` | Current state, tick count, uptime |
| `POST` | `/simulation/start` | Start simulation loop |
| `POST` | `/simulation/stop` | Stop simulation loop |
| `POST` | `/simulation/pause` | Pause (keep state) |
| `POST` | `/simulation/resume` | Resume from pause |
| `PATCH` | `/simulation/config` | Update interval, meter count, mode |
| `PATCH` | `/simulation/environment` | Inject weather, grid_stress, time override |
| `GET` | `/simulation/tick` | Latest tick metadata |
| `POST` | `/simulation/scenarios/{scenario}` | Trigger named scenario |

**Scenarios:** `island`, `cable_fault`, `peak_demand`, `black_start`, `fdi_attack`

**`PATCH /simulation/environment` body:**
```json
{
  "weather": "Rainy",
  "grid_stress": 1.5,
  "sim_time_override": "2026-04-22T12:00:00Z"
}
```

---

## Meters

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/meters` | List meters (paginated) |
| `POST` | `/meters` | Create meter |
| `GET` | `/meters/{meter_id}` | Meter detail + latest reading |
| `DELETE` | `/meters/{meter_id}` | Remove meter from simulation |
| `PATCH` | `/meters/{meter_id}/config` | Update meter config |
| `GET` | `/meters/{meter_id}/readings` | Historical readings (time range) |
| `POST` | `/meters/{meter_id}/readings/override` | Force reading value |
| `GET` | `/meters/count` | Total meter count |
| `PUT` | `/meters/count` | Resize meter pool |

**Query params for `GET /meters`:**
```
?zone=Samui&type=battery_storage&page=1&limit=50
```

**`GET /meters/{meter_id}/readings` query params:**
```
?start=2026-04-20T00:00:00Z&end=2026-04-20T23:59:59Z&interval=1h&fields=energy_consumed,energy_generated
```

---

## Grid

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/grid/status` | Running state, frequency, bus count |
| `GET` | `/grid/topology` | Pandapower net summary (buses, lines, trafos) |
| `GET` | `/grid/state-estimation` | Latest WLS results, convergence, bad data |
| `GET` | `/grid/telemetry` | Real-time nodal measurements |
| `GET` | `/grid/map` | GeoJSON / MVT map render |
| `GET` | `/grid/lines` | All lines with loading % |
| `GET` | `/grid/lines/{line_id}` | Line detail + thermal history |
| `GET` | `/grid/buses` | All buses with voltage pu |
| `GET` | `/grid/substations` | Substation list |
| `GET` | `/grid/substations/{sub_id}` | Substation detail |
| `GET` | `/grid/snapshots` | Saved grid snapshots |
| `POST` | `/grid/snapshots` | Save current grid state |
| `GET` | `/grid/export` | Export topology (geojson, cim, csv) |
| `GET` | `/grid/stats` | Losses, avg voltage deviation, line loading |
| `GET` | `/grid/node/{node_id}/history` | Node voltage/load history |

**`GET /grid/map` query params:**
```
?format=geojson&layers=egat,meters&region=South&bbox=99.5,8.5,101.0,10.0
?format=mvt&layers=egat&z=8&x=196&y=119
```

---

## VPP (Virtual Power Plant)

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/vpp/clusters` | All clusters with SOC, flexibility, health |
| `GET` | `/vpp/clusters/{cluster_id}` | Cluster detail + resource list |
| `POST` | `/vpp/dispatch` | Send dispatch setpoint to cluster |
| `POST` | `/vpp/afrr` | Trigger aFRR response at given frequency |
| `GET` | `/vpp/resources` | All DER resources |
| `GET` | `/vpp/resources/{meter_id}` | DER resource detail |
| `POST` | `/vpp/shed` | Emergency load shed (priority ≥ threshold) |
| `POST` | `/vpp/bottleneck/resolve` | Trigger bottleneck game for line |
| `GET` | `/vpp/carbon` | Current carbon intensity + cumulative saved |

**`POST /vpp/dispatch` body:**
```json
{
  "cluster_id": "SAMUI-FEEDER",
  "action": "discharge",
  "setpoint_kw": 15000.0
}
```

**`POST /vpp/afrr` body:**
```json
{ "frequency_hz": 49.7 }
```

**`POST /vpp/bottleneck/resolve` body:**
```json
{ "line_id": "115kV KMB Circuit 3", "line_loading_pct": 110.0, "capacity_mw": 40.0 }
```

---

## AI / Forecasting (PEA Pillars)

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/forecast/24h` | 24h load forecast for a node |
| `GET` | `/forecast/mape` | Latest MAPE against actuals |
| `POST` | `/forecast/train` | Retrain LightGBM model from InfluxDB |
| `GET` | `/optimize/schedule` | OPF cost-minimized dispatch schedule |
| `GET` | `/optimize/savings` | Daily/monthly savings summary |
| `GET` | `/ews/status` | EWS active alerts |
| `POST` | `/ews/simulate` | Simulate incident (cable fault, overload) |
| `POST` | `/ews/reset` | Reset incident state |

**`GET /forecast/24h` query params:**
```
?node_id=SAMUI-HUB-01&current_load_mw=15.0&temp_c=33.0&cloud_cover=10
```

**`GET /forecast/24h` response:**
```json
{
  "node_id": "SAMUI-HUB-01",
  "generated_at": "2026-04-20T02:55:00Z",
  "mape_pct": 7.3,
  "model": "lightgbm",
  "forecast_mw": [8.1, 7.2, ...],
  "schedule": [
    { "hour": 0, "forecast_load_mw": 8.1, "status": "NORMAL", "recommended_action": "None", "potential_hourly_savings_thb": 0 },
    { "hour": 18, "forecast_load_mw": 39.5, "status": "WARNING: BOTTLENECK", "recommended_action": "Discharge BESS 1.75 MW", "potential_hourly_savings_thb": 15750 }
  ]
}
```

**`GET /optimize/schedule` response:**
```json
{
  "total_savings_thb": 284000,
  "total_cost_baseline_thb": 936000,
  "total_cost_optimized_thb": 652000,
  "schedule": [
    { "hour": 0, "load_mw": 8.1, "p_grid_mw": 8.1, "p_bess_mw": 0, "p_diesel_mw": 0, "bess_soc_mwh": 25.0, "savings_thb": 0 }
  ]
}
```

**`POST /ews/simulate` body:**
```json
{ "line_id": "115kV KMB Circuit 3", "line_capacity_mw": 70.0, "loading_pct": 98.0 }
```

**`POST /ews/simulate` response:**
```json
{
  "alert": {
    "type": "EWS_CAPACITY_DROP",
    "severity": "CRITICAL",
    "drop_pct": 30.0,
    "recommended_action": "TRIGGER_EMERGENCY_BESS"
  },
  "emergency_response": {
    "action": "BESS switched to grid-forming mode",
    "bess_dispatch_mw": 20.0,
    "diesel_spinup_mw": 0.0,
    "afrr_triggered": true
  }
}
```

---

## Billing & Pricing

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/billing/summary` | Billing summary for all meters |
| `GET` | `/billing/{meter_id}` | Meter bill detail (TOU breakdown) |
| `GET` | `/billing/{meter_id}/history` | Historical bills |
| `GET` | `/price/current` | Current spot price |
| `GET` | `/price/tou` | TOU tariff schedule |
| `GET` | `/price/comparison` | Utility vs P2P rate comparison |
| `GET` | `/price/lmp` | Locational Marginal Prices by node |

---

## Analytics

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/analytics/summary` | Grid health, market activity, carbon, LMP stats |
| `GET` | `/analytics/solar/inventory` | Detected solar panel inventory |
| `POST` | `/analytics/solar/detect` | Run Geo-SAM solar detection |
| `GET` | `/analytics/energy` | Generation/consumption totals (time range) |
| `GET` | `/analytics/carbon` | Carbon intensity history |

---

## Power Plants & Registry

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/power-plants` | List Thailand power plants |
| `GET` | `/power-plants/{id}` | Plant detail |
| `POST` | `/power-plants/load` | Load from GeoJSON |
| `GET` | `/power-plants/nearby` | Spatial query (lat, lon, radius_km) |
| `GET` | `/registry/thailand` | Thailand power plant registry |

---

## Microgrid

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/microgrid/status` | Island mode status |
| `POST` | `/microgrid/island` | Trigger islanding |
| `POST` | `/microgrid/reconnect` | Reconnect to main grid |
| `GET` | `/microgrid/black-start` | Black start sequence status |
| `POST` | `/microgrid/black-start/initiate` | Begin black start |

---

## Telemetry Ingestion (C2C)

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/ingest/readings` | Batch meter reading ingestion |
| `POST` | `/ingest/dlms` | DLMS/COSEM payload ingestion |
| `POST` | `/ingest/events` | Grid event ingestion |

**`POST /ingest/readings` body:**
```json
{
  "readings": [
    { "meter_id": "SAMUI-001", "generation_kwh": 1.2, "consumption_kwh": 3.4, "battery_kwh": 8.5 }
  ]
}
```

Requires `X-API-Key` header.

---

## WebSocket Streams

| Endpoint | Description |
|---|---|
| `WS /ws/telemetry` | Live meter readings broadcast |
| `WS /ws/grid` | Grid state updates (frequency, voltage, line loading) |
| `WS /ws/alerts` | EWS alerts and VPP dispatch events |

**Subscribe message:**
```json
{ "action": "subscribe", "channels": ["telemetry", "alerts"] }
```

---

## System

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Liveness probe |
| `GET` | `/ready` | Readiness probe (DB + InfluxDB connected) |
| `GET` | `/metrics` | Prometheus metrics |
| `GET` | `/version` | Build version, git SHA, uptime |

---

## Error Schema

All errors follow RFC 7807:

```json
{
  "type": "https://api.gridtokenx.io/errors/not-found",
  "title": "Meter not found",
  "status": 404,
  "detail": "Meter SAMUI-999 does not exist",
  "instance": "/v1/meters/SAMUI-999"
}
```

| Code | Meaning |
|---|---|
| `400` | Validation error |
| `401` | Missing / invalid token |
| `403` | Insufficient scope |
| `404` | Resource not found |
| `409` | Conflict (duplicate, already running) |
| `422` | Unprocessable entity (Pydantic) |
| `503` | Engine not initialized / dependency unavailable |

---

## Pagination

All list endpoints support:
```
?page=1&limit=50&sort=created_at&order=desc
```

Response envelope:
```json
{
  "data": [...],
  "pagination": { "page": 1, "limit": 50, "total": 312, "pages": 7 }
}
```

---

## Rate Limits

| Tier | Limit |
|---|---|
| Public / unauthenticated | 60 req/min |
| Authenticated | 600 req/min |
| C2C ingestion (`/ingest/*`) | 6000 req/min |
| WebSocket connections | 100 concurrent |

Headers returned: `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`
