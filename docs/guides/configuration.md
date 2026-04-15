# Configuration Guide

The **GridTokenX Smart Meter Simulator** is highly configurable via environment variables and `.env` files. It uses Pydantic for robust type-safe configuration.

## 📄 Environment Variables

Create a `.env` file in the project root to override default settings. See `.env.example` for a comprehensive list.

### Core Simulation Settings

| Variable | Default | Description |
| :--- | :--- | :--- |
| `NUM_METERS` | `20` | Number of smart meters to simulate. |
| `SIMULATION_INTERVAL` | `900` | Seconds between each simulation tick (default 15 mins). |
| `AUTOSTART_SIMULATION` | `True` | Whether to start the simulation loop automatically on boot. |
| `RUST_ACCELERATION_ENABLED` | `True` | Enables high-performance Rust engine if available. |

### Grid & Economic Settings

| Variable | Default | Description |
| :--- | :--- | :--- |
| `GRID_PURCHASE_RATE` | `0.28` | Cost of electricity from the grid (Baht/kWh). |
| `BASE_LATITUDE` | `13.758252` | Center latitude for meter placement. |
| `BASE_LONGITUDE` | `100.687455` | Center longitude for meter placement. |

### Meter Type Distribution

The simulator distributes meter types based on these ratios (must sum to 1.0):

- `SOLAR_PROSUMER_RATIO`: `0.35`
- `GRID_CONSUMER_RATIO`: `0.30`
- `HYBRID_PROSUMER_RATIO`: `0.20`
- `EV_CHARGER_RATIO`: `0.10`
- `BATTERY_STORAGE_RATIO`: `0.05`

### Transport & Infrastructure

| Variable | Default | Description |
| :--- | :--- | :--- |
| `TRANSPORT_TYPE` | `grpc` | Options: `grpc`, `http`, `kafka`, `mqtt`. |
| `DATABASE_URL` | `postgresql://...` | Connection string for the main relational DB. |
| `GIS_DATABASE_URL` | `postgresql+asyncpg://...` | Connection string for the spatial PostGIS DB. |
| `INFLUXDB_URL` | `http://localhost:7020` | InfluxDB endpoint for time-series storage. |

## 🛠️ Advanced Physics Configuration

You can fine-tune the consumption and generation models:

- `BASE_GENERATION_MAX`: Maximum solar peak (kW).
- `BASE_CONSUMPTION_MAX`: Maximum residential load peak (kW).
- `NOISE_FACTOR_MAX`: Maximum stochastic noise applied to readings (0.0 - 1.0).
- `WEATHER_SUNNY_WEIGHT`: Probability of sunny weather in the random walk.

## 🔐 API Security

To secure Cloud-to-Cloud (C2C) ingestion, set the following:

```bash
C2C_API_KEY=your_secure_api_key
```

Include this key in the `X-API-Key` header for protected endpoints.

---
_Next: [Running Simulations](running-simulations.md)_
