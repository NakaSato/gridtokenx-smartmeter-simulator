# GridTokenX Smart Meter Simulator

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Rust](https://img.shields.io/badge/rust-PyO3-orange.svg)](https://github.com/PyO3/pyo3)
[![License](https://img.shields.io/badge/license-Proprietary-red.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-4.0.0-green.svg)](CHANGELOG.md)

> **High-fidelity AMI (Advanced Metering Infrastructure) and Grid Orchestration simulator** for the GridTokenX ecosystem. Specialized in real-time power flow simulation (Pandapower), VPP grid services, and industrial-standard telemetry.

![image](./image.png)

---

## Quick Start

### 1. Start Infrastructure (Postgres + Redis)

```bash
docker compose up -d
```

### 2. Start Simulator

```bash
# Server mode (REST API + gRPC)
uv run uvicorn smart_meter_simulator.app:app --host 0.0.0.0 --port 8082

# Standing mode (Direct output)
uv run start-simulator --mode standalone --meters 20
```

### 3. Access Services

| Service | URL | Description |
|---------|-----|-------------|
| **API Gateway** | http://localhost:8082 | REST API & WebSocket |
| **API Docs** | http://localhost:8082/docs | Interactive Swagger UI |
| **PostgreSQL** | localhost:5432 | Relational database |
| **PostGIS** | localhost:5433 | Spatial database (Grid Topology) |

---

## Key Features

### Rust-Accelerated Performance
High-performance meter reading generation and VPP dispatch algorithms implemented in Rust via PyO3.

| Metric | Python | Rust (PyO3) | Speedup |
|--------|--------|-------------|---------|
| **1,000 meters** | ~3,000 ms | 0.82 ms | **3,655x** |

### High-Fidelity AMI Simulation
- **Accuracy Classes**: Models meter precision from Class 0.2 (Substation) to Class 2.0 (Residential).
- **Industrial Protocols**: Native support for **DLMS/COSEM** and **gRPC** ingestion.

### Grid & VPP Orchestration
- **Pandapower Integration**: Real-time State Estimation (WLS) and Power Flow.
- **VPP Dispatch**: Automated Frequency Restoration Reserve (aFRR) and Droop Control.
- **Islanding Management**: Microgrid stability and black-start sequencing.

### Spatial Grid Modeling
- **PostGIS integration** for spatial meter placement.
- **Thai distribution networks** (MEA/PEA topology models).

---

## Architecture

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                     Smart Meter Simulator                    │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │ Simulation   │  │ Grid Engine  │  │ VPP              │  │
│  │ Engine       │  │ (Pandapower) │  │ Orchestrator     │  │
│  │ (Rust/Py)    │  │ (Estimation) │  │ (AFRR, Droop)    │  │
│  └──────┬───────┘  └──────┬───────┘  └────────┬─────────┘  │
│         │                 │                    │             │
│  ┌──────▼─────────────────▼─────────────────▼────────────┐  │
│  │              Smart Meters (20-5000+)                  │  │
│  │         Ed25519 signing, accuracy classes             │  │
│  └──────────────────────┬────────────────────────────────┘  │
│                         │                                   │
│  ┌──────────────────────▼────────────────────────────────┐  │
│  │   gRPC (DLMS/COSEM) │ HTTP │ WebSocket │ Kafka        │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────┼───────────────────────────────────┘
                          │
              ┌───────────▼───────────┐
              │   Infrastructure      │
              ├───────────────────────┤
              │ PostgreSQL (PostGIS)  │ ← Grid Topology
              │ Redis (Cache)         │ ← State & Pub/Sub
              │ Kafka (Events)        │ ← Stream Processing
              └───────────────────────┘
```

### Data Flow

```
Meter Reading Generation (Rust/Python)
         ↓
    Ed25519 Signing
         ↓
    VPP Dispatch (Droop + AFRR)
         ↓
    Grid State Estimation (Pandapower WLS)
         ↓
    Industrial Transport
    ├──→ gRPC (ConnectRPC / Protobuf / DLMS)
    ├──→ HTTP (Legacy API)
    └──→ WebSocket (Live Dashboard)
```

---

## Project Structure

```
gridtokenx-smartmeter-simulator/
├── src/smart_meter_simulator/
│   ├── core/               # Engine, VPP, market, frequency, billing
│   │   ├── engine.py       # Main simulation orchestrator
│   │   ├── rust_engine.py  # PyO3 acceleration wrapper
│   │   ├── rust_vpp_engine.py # VPP dispatch wrapper
│   │   └── ...
│   ├── adapters/           # Pandapower, SE, CIM, Thai grid
│   ├── transport/          # HTTP, WS, Kafka, InfluxDB
│   │   ├── influxdb.py     # Time-series write transport
│   │   └── influxdb_query.py # Real-time query service
│   ├── routers/            # API v1 endpoints
│   │   └── api_v1.py       # All 67+ endpoints
│   ├── config/             # Settings, enums, Thai market
│   └── database/           # PostGIS models & repository
├── src/rust_sim/           # Rust acceleration (PyO3 + Maturin)
│   ├── Cargo.toml
│   └── src/lib.rs          # Reading generation, VPP dispatch
├── ui/                     # React dashboard (Vite + Bun)
├── docker/                 # Docker configurations
├── database/migrations/    # SQL migrations
├── tests/                  # pytest suite (30+ files)
├── examples/               # Usage examples
├── docs/                   # Comprehensive documentation
│   ├── guides/             # User guides
│   ├── architecture/       # System design
│   ├── integration/        # Integration docs (InfluxDB, PostGIS, Rust)
│   └── reference/          # Specifications
├── docker-compose.yml      # Full stack orchestration
└── pyproject.toml          # UV-managed dependencies
```

---

## Configuration

### Essential Environment Variables

```bash
# Simulator
SIMULATION_INTERVAL=15        # Seconds between readings
NUM_METERS=55                 # Number of meters

# InfluxDB (Time-Series Database)
INFLUXDB_URL=http://localhost:7020
INFLUXDB_TOKEN=admin_token
INFLUXDB_ORG=gridtokenx
INFLUXDB_BUCKET=meter_readings

# Databases
DATABASE_URL=postgresql+asyncpg://gridtokenx:gridtokenx_password@localhost:5432/gridtokenx
GIS_DATABASE_URL=postgresql+asyncpg://gridtokenx:gridtokenx_password@localhost:5433/gridtokenx_gis

# API Gateway (REST)
API_GATEWAY_URL=http://localhost:4000
API_KEY=your-api-key

# Industrial Ingestion (gRPC/DLMS)
TRANSPORT_TYPE=grpc           # Options: grpc, http, kafka
GRPC_GATEWAY_HOST=localhost
GRPC_GATEWAY_PORT=5030
```

See `.env.example` for complete list.

---

## Performance Benchmarks

### Reading Generation

```bash
# Run Rust acceleration benchmarks
uv run pytest tests/benchmark_rust_performance.py -v

# Results:
# 100_meters:   0.02 ms/iteration  (Python: ~300 ms)
# 500_meters:   0.11 ms/iteration  (Python: ~1,500 ms)
# 1000_meters:  0.28 ms/iteration  (Python: ~3,000 ms)
```

### VPP Dispatch

```bash
# VPP dispatch benchmark
uv run pytest tests/benchmark_vpp_performance.py -v

# Results:
# 50_meters:    15-67 µs (Rust direct)
# 100_meters:   33-1380 µs (Rust via PyO3 FFI)
```

---

## Testing

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=src --cov-report=html

# Run specific test suite
uv run pytest tests/test_grid_analysers.py -v
uv run pytest tests/test_rust_api_integration.py -v
uv run pytest tests/test_postgis/ -v

# Run benchmarks
uv run pytest tests/benchmark_rust_performance.py -v
uv run pytest tests/benchmark_vpp_performance.py -v
```

---

## Documentation

### Quick Start Guides

| Document | Description |
|----------|-------------|
| [Getting Started](docs/guides/getting-started.md) | Installation and setup |
| [Configuration](docs/guides/configuration.md) | Environment variables |
| [Running Simulations](docs/guides/running-simulations.md) | Simulation management |
| [Docker Deployment](docs/guides/docker-deployment.md) | Docker-based deployment |

### Integration Guides

| Document | Description |
|----------|-------------|
| [InfluxDB Complete Storage](docs/integration/INFLUXDB_COMPLETE_STORAGE.md) | All data types stored to InfluxDB |
| [InfluxDB Real-Time Database](docs/integration/INFLUXDB_REALTIME_DATABASE.md) | Query service and API |
| [Rust Acceleration](docs/integration/RUST_ACCELERATION.md) | PyO3 performance boost |
| [PostGIS Integration](docs/integration/POSTGIS_INTEGRATION.md) | Spatial database setup |
| [Thai Grid Integration](docs/integration/THAI_GRID_INTEGRATION.md) | MEA/PEA topology models |
| [API v1 Reference](docs/integration/API_V1_REFERENCE.md) | Complete endpoint reference |

### Architecture

| Document | Description |
|----------|-------------|
| [System Overview](docs/architecture/overview.md) | High-level architecture |
| [Simulation Engine](docs/architecture/simulation-engine.md) | Core orchestration |
| [Smart Meter Model](docs/architecture/smart-meter.md) | Meter implementation |
| [Grid Integration](docs/architecture/grid-integration.md) | Pandapower and SE |
| [Market Engine](docs/architecture/market-engine.md) | P2P trading and pricing |
| [Transport Layer](docs/architecture/transport-layer.md) | Data delivery |

### Reference Specifications

| Document | Description |
|----------|-------------|
| [Meter Specification](docs/reference/meter-spec.md) | AMI specification (Phases 1-22) |
| [Pandapower Integration](docs/reference/pandapower.md) | Grid modeling guide |
| [Thai Tariffs](docs/reference/thai-tariffs.md) | TOU tariff rates (2026) |
| [Thai Market Analysis](docs/reference/thai-market.md) | Market dynamics |
| [Economic Models](docs/reference/economic-models.md) | Single Buyer vs. P2P |
| [Thai Grid Topology](docs/reference/thai-grid-topology.md) | MEA/PEA network models |

### Full Index

See [docs/index.md](docs/index.md) for complete documentation listing.

---

## Roadmap

### ✅ Completed (Phases 1-24)

| Phase | Feature | Status |
|-------|---------|--------|
| 1-2 | AMI Foundation (Ed25519, meter types) | ✅ Complete |
| 3 | Grid Integration (SE, bad data detection) | ✅ Complete |
| 4 | Data Source Management (Polars/Parquet) | ✅ Complete |
| 5 | Co-Simulation (Mosaik, CIM) | ✅ Complete |
| 6-22 | Advanced Grid Intelligence (LMP, VPP, frequency) | ✅ Complete |
| 23 | OpenStreetMap Integration | ✅ Complete |
| 24 | Thai Grid Integration & Spatial Analytics | ✅ Complete |
| 25 | **Rust Acceleration** (3,655-7,500x speedup) | ✅ Complete |
| 26 | **API Consolidation** (67 endpoints under /api/v1/) | ✅ Complete |
| 27 | **InfluxDB Real-Time Database** (Complete storage) | ✅ Complete |
| 28 | **Grafana Dashboards** (Grid Observability) | ✅ Complete |

### In Progress

| Phase | Feature | Status |
|-------|---------|--------|
| 29 | Production-Scale Testing (1000+ meters) | 🚧 In Progress |
| 30 | Advanced InfluxDB Metrics (VPP, market, weather) | 🚧 Pending |

---

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'feat: add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Conventions

- **Formatter:** Black (line length 88)
- **Imports:** isort (Black profile)
- **Linting:** flake8
- **Type Hints:** Used throughout
- **Tests:** Required for new features

---

## License

Part of the GridTokenX Ecosystem - Proprietary

---

_Maintained by the GridTokenX Engineering Team._
