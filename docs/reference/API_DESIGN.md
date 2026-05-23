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

---

## WebSocket Streams

| Endpoint | Description |
|---|---|
| `WS /ws/telemetry` | Live meter readings broadcast |
| `WS /ws/grid` | Grid state updates (frequency, voltage, line loading) |
| `WS /ws/alerts` | EWS alerts and VPP dispatch events |

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

---

## Pagination

All list endpoints support:
```
?page=1&limit=50&sort=created_at&order=desc
```

---

## Rate Limits

| Tier | Limit |
|---|---|
| Public / unauthenticated | 60 req/min |
| Authenticated | 600 req/min |
| C2C ingestion (`/ingest/*`) | 6000 req/min |
| WebSocket connections | 100 concurrent |
