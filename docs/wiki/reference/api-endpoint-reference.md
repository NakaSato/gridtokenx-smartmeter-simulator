---
title: "API Endpoint Reference"
category: reference
created: 2026-04-10
updated: 2026-04-10
sources: ["src/smart_meter_simulator/routers/api_v1.py", "docs/integration/API_V1_REFERENCE.md", "src/smart_meter_simulator/app.py"]
tags: [api, reference, rest, websocket]
related: [[FastAPI App]], [[WebSocket Protocol]], [[Transport Layer]]
---

# API Endpoint Reference

The Smart Meter Simulator exposes 67+ REST endpoints under `/api/v1/` for simulation control, meter management, grid analysis, VPP operations, market data, and analytics. Interactive documentation is available at `http://localhost:8082/docs`.

## Summary

All endpoints are organized under `/api/v1/` prefix. The FastAPI app serves Swagger UI at `/docs` and OpenAPI schema at `/openapi.json`.

## Simulation Control

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check (always returns 200) |
| GET | `/api/status` | Simulator status, running state, meter count |
| POST | `/api/v1/simulation/start` | Start simulation |
| POST | `/api/v1/simulation/stop` | Stop simulation |
| POST | `/api/v1/simulation/pause` | Pause simulation |
| POST | `/api/v1/simulation/resume` | Resume paused simulation |
| GET | `/api/v1/simulation/status` | Detailed simulation status |

## Meter Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/meters` | List all meters |
| GET | `/api/meters/{meter_id}` | Get specific meter details |
| GET | `/api/v1/meters` | List meters (v1) |
| GET | `/api/v1/meters/{meter_id}` | Get meter details (v1) |
| GET | `/api/v1/meters/{meter_id}/readings` | Get latest reading for meter |
| POST | `/api/v1/meters/{meter_id}/dispatch` | Send VPP dispatch to meter |
| GET | `/api/v1/meters/{meter_id}/history` | Get reading history |

## Grid & Topology

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/grid/status` | Grid topology summary |
| GET | `/api/grid/topology` | Detailed grid topology |
| GET | `/api/grid/geojson` | Grid topology in GeoJSON format |
| GET | `/api/grid/measurements` | Current SE measurements |
| GET | `/api/grid/estimation` | Latest state estimation results |
| GET | `/api/v1/grid/topology` | Grid topology (v1) |
| GET | `/api/v1/grid/measurements` | SE measurements (v1) |
| GET | `/api/v1/grid/estimation` | SE results (v1) |
| GET | `/api/v1/grid/spatial` | Spatial grid data (PostGIS) |

## VPP & Frequency

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/vpp/status` | VPP cluster status |
| GET | `/api/vpp/dispatch` | VPP dispatch commands |
| GET | `/api/vpp/clusters` | List VPP clusters |
| POST | `/api/vpp/dispatch` | Trigger VPP dispatch |
| GET | `/api/frequency` | Grid frequency metrics |
| GET | `/api/v1/vpp/status` | VPP status (v1) |
| GET | `/api/v1/frequency` | Frequency (v1) |

## Market & Pricing

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/market/orders` | Active market orders |
| GET | `/api/market/clearing` | Market clearing results |
| POST | `/api/v1/price/compare` | Compare utility vs P2P prices |
| GET | `/api/v1/price/utility-rates` | Get utility rates |
| GET | `/api/v1/price/p2p-dynamic` | Get dynamic P2P price |
| POST | `/api/v1/revenue/compare` | Compare revenue models |
| GET | `/api/v1/revenue/optimize` | Optimize revenue config |
| GET | `/api/v1/p2p/market-prices` | Get market prices |
| POST | `/api/v1/p2p/calculate-cost` | Calculate P2P transaction cost |

## Islanding & ADR

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/island/status` | Islanding detection status |
| POST | `/api/island/disconnect` | Trigger islanding |
| POST | `/api/island/reconnect` | Reconnect to main grid |
| POST | `/api/island/black-start` | Initiate black start |
| GET | `/api/v1/island/status` | Island status (v1) |

## Analytics & Data

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/analytics/summary` | Analytics summary |
| GET | `/api/v1/analytics/grid-health` | Grid health metrics |
| GET | `/api/v1/analytics/carbon` | Carbon savings report |
| GET | `/api/v1/analytics/revenue` | Revenue analytics |
| GET | `/api/v1/data/export` | Export data (CSV/JSON) |
| GET | `/api/v1/data/readings` | Query recent readings |

## WebSocket

| Endpoint | Description |
|----------|-------------|
| `ws://localhost:8765/ws` | Real-time meter reading broadcast |

See [[WebSocket Protocol]] for message format.

## Response Formats

### Health Check
```json
{ "status": "ok" }
```

### Meter
```json
{
  "meter_id": "AMI_METER_001",
  "meter_type": "Solar_Prosumer",
  "accuracy_class": "CLASS_1_0",
  "has_solar": true,
  "has_battery": false,
  "solar_capacity_kw": 8.5,
  "location": { "latitude": 13.758, "longitude": 100.687 }
}
```

### Reading
```json
{
  "meter_id": "AMI_METER_001",
  "timestamp": "2026-04-10T12:00:00Z",
  "energy_generated_kwh": 5.234,
  "energy_consumed_kwh": 2.145,
  "voltage_v": 239.8,
  "current_a": 12.3,
  "frequency_hz": 50.02
}
```

### State Estimation
```json
{
  "algorithm": "WLS",
  "converged": true,
  "iterations": 4,
  "chi_squared_statistic": 12.5,
  "chi_squared_critical": 24.7,
  "bad_data_detected": false,
  "max_normalized_residual": 1.8
}
```

## Relationships

- **Router:** `src/smart_meter_simulator/routers/api_v1.py`
- **App:** [[FastAPI App]]
- **Real-time:** [[WebSocket Protocol]]
- **Interactive docs:** `http://localhost:8082/docs`

## Known Issues

- Some endpoints duplicated (legacy `/api/` and v1 `/api/v1/`)
- Not all endpoints have v1 versions
- WebSocket port (8765) differs from API port (8082)
- No pagination on list endpoints (returns all results)
- No rate limiting on API endpoints
- API key authentication not enforced on all endpoints
