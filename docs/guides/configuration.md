# Configuration Guide

The **GridTokenX Smart Meter Simulator** is highly configurable via environment variables and `.env` files. It uses Pydantic for robust type-safe configuration. The `.env` file lives in the `backend/` directory.

## 📄 Environment Variables

Create a `.env` file in the `backend/` directory to override default settings. See `backend/.env.example` for a comprehensive list.

### Core Simulation Settings

| Variable | Default | Description |
| :--- | :--- | :--- |
| `NUM_METERS` | `20` | Number of smart meters to simulate. |
| `SIMULATION_INTERVAL` | `900` | Seconds between each simulation tick (default 15 mins). |
| `AUTOSTART_SIMULATION` | `True` | Whether to start the simulation loop automatically on boot. |
| `RUST_ACCELERATION_ENABLED` | `True` | Enables high-performance Rust engine if available. |
| `LOCATIONS_FILE` | — | JSON file for meter placement (e.g. `initial_locations_islands.json`). |

### Grid & Economic Settings

| Variable | Default | Description |
| :--- | :--- | :--- |
| `GRID_PURCHASE_RATE` | `0.28` | Cost of electricity from the grid (Baht/kWh). |
| `BASE_LATITUDE` | `13.758252` | Center latitude for meter placement. |
| `BASE_LONGITUDE` | `100.687455` | Center longitude for meter placement. |

### Island Scenario Settings

For island simulations, override these via the run scripts or environment:

| Variable | Island Value | Description |
| :--- | :--- | :--- |
| `LOCATIONS_FILE` | `initial_locations_islands.json` | Island meter placement config |
| `BASE_LATITUDE` | `9.45` | Samui archipelago center |
| `BASE_LONGITUDE` | `100.0` | Samui archipelago center |
| `NUM_METERS` | `60` | Meters across all island zones |
| `TRANSPORT_TYPE` | `no-db` | Run without DB for standalone island testing |

### Meter Type Distribution

The simulator distributes meter types based on these ratios (must sum to 1.0):

- `SOLAR_PROSUMER_RATIO`: `0.40`
- `GRID_CONSUMER_RATIO`: `0.35`
- `HYBRID_PROSUMER_RATIO`: `0.20`
- `BATTERY_STORAGE_RATIO`: `0.05`
- `EV_CHARGER_RATIO`: `0.00`

### Transport & Infrastructure

| Variable | Default | Description |
| :--- | :--- | :--- |
| `TRANSPORT_TYPE` | `grpc` | Options: `grpc`, `http`, `kafka`, `mqtt`, `no-db`. |
| `DATABASE_URL` | `postgresql://...@localhost:5432/gridtokenx` | Main relational DB. |
| `GIS_DATABASE_URL` | `postgresql+asyncpg://...@localhost:5433/gridtokenx_gis` | Spatial PostGIS DB. |
| `INFLUXDB_URL` | `http://localhost:8086` | InfluxDB endpoint for time-series storage. |
| `INFLUXDB_TOKEN` | `admin_token` | InfluxDB authentication token. |
| `INFLUXDB_ORG` | `gridtokenx` | InfluxDB organization. |
| `INFLUXDB_BUCKET` | `meter_readings` | InfluxDB bucket. |
| `REDIS_URL` | `redis://localhost:6379` | Redis connection URL. |
| `KAFKA_BOOTSTRAP_SERVERS` | `localhost:29092` | Kafka bootstrap servers. |
| `GRPC_GATEWAY_HOST` | `localhost` | gRPC gateway host. |
| `GRPC_GATEWAY_PORT` | `5030` | gRPC gateway port. |

### API Gateway

| Variable | Default | Description |
| :--- | :--- | :--- |
| `API_GATEWAY_URL` | `http://localhost:4000` | GridTokenX API Gateway URL. |
| `API_KEY` | — | API key for C2C ingestion. |

## 🛠️ Advanced Physics Configuration

You can fine-tune the consumption and generation models:

- `BASE_GENERATION_MAX`: Maximum solar peak (kW).
- `BASE_CONSUMPTION_MAX`: Maximum residential load peak (kW).
- `NOISE_FACTOR_MAX`: Maximum stochastic noise applied to readings (0.0 - 1.0).
- `WEATHER_SUNNY_WEIGHT`: Probability of sunny weather in the random walk.

## 🔐 API Security

To secure Cloud-to-Cloud (C2C) ingestion, set the following:

```bash
API_KEY=your_secure_api_key
```

Include this key in the `X-API-Key` header for protected endpoints.

---
_Next: [Running Simulations](running-simulations.md)_
