# GridTokenX Smart Meter Simulator

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Rust](https://img.shields.io/badge/rust-PyO3-orange.svg)](https://github.com/PyO3/pyo3)
[![License](https://img.shields.io/badge/license-Proprietary-red.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-5.0.0-green.svg)](CHANGELOG.md)

> **High-fidelity AMI (Advanced Metering Infrastructure), Grid Orchestration, and AI Forecasting simulator** for the GridTokenX ecosystem. Specialized in real-time power flow simulation (Pandapower), VPP grid services, industrial-standard telemetry, and PEA-mandated forecasting pillars.

![image](./image.png)

---

## Quick Start

### 1. Start Infrastructure (Postgres + Redis + InfluxDB)

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
| **InfluxDB** | http://localhost:7020 | Time-series database |

---

## Key Features

### AI / Forecasting (PEA Pillars)
Native support for the three non-negotiable PEA forecasting mandates:
- **24-Hour Horizon**: Hourly load and capacity predictions.
- **<10% MAPE**: Validated accuracy using LightGBM and Walk-Forward backtesting.
- **Dual-Target**: Forecast both `Load_Tao` and `Capacity_115kV_Remaining` to trigger VPP actions.

### Cost Optimization (OPF)
- **Physics-Validated Dispatch**: Optimal Power Flow (OPF) using `scipy.optimize.linprog` validated by Pandapower.
- **Diesel Displacement**: Automated BESS scheduling to avoid 13 THB/kWh diesel generation costs.

### Early Warning System (EWS)
- **Submarine Cable Monitoring**: Detects capacity drops and triggers emergency BESS grid-forming mode.
- **Incident Simulation**: API-driven injection of grid faults and overload scenarios.

### Rust-Accelerated Performance
High-performance meter reading generation and VPP dispatch algorithms implemented in Rust via PyO3.

| Metric | Python | Rust (PyO3) | Speedup |
|--------|--------|-------------|---------|
| **1,000 meters** | ~3,000 ms | 0.28 ms | **10,714x** |

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
│  │ AI Engine    │  │ Grid Engine  │  │ VPP              │  │
│  │ (LightGBM)   │  │ (Pandapower) │  │ Orchestrator     │  │
│  │ (Forecasting)│  │ (Estimation) │  │ (AFRR, OPF)      │  │
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
              │ InfluxDB (Metrics)    │ ← AI Training Data
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
├── backend/                # Refactored SOA Backend (Python + Rust)
│   ├── src/smart_meter_simulator/
│   │   ├── core/           # Domain Managers (Grid, VPP, Reading, Security)
│   │   ├── adapters/       # Pandapower, Regional Builders (Thai/EGAT)
│   │   ├── transport/      # Mappers & Connection Managers
│   │   └── ...
├── frontend/               # React Dashboard (SimulatorProvider + useSimulator)
├── src/rust_sim/           # Rust acceleration (PyO3 + Maturin)
├── docs/                   # Organized documentation
└── pyproject.toml          # UV-managed dependencies
├── src/rust_sim/           # Rust acceleration (PyO3 + Maturin)
├── ui/                     # React dashboard (Vite + Bun)
├── scripts/                # PEA Glue scripts (Trainer, Optimizer)
├── docs/                   # Organized documentation
│   ├── guides/             # Getting started & config
│   ├── features/           # AI, VPP, EWS, Rust details
│   ├── reference/          # API, Tariffs, Specs
│   ├── operations/         # Deployment & Monitoring
│   ├── architecture/       # System design
│   └── archive/            # Historical documents
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

- **Full Wiki**: See [docs/wiki/index.md](docs/wiki/index.md) for the 54-page technical manual.
- **Documentation Index**: See [docs/index.md](docs/index.md) for the complete directory.

### 🏁 Quick Start Guides
| Document | Description |
|----------|-------------|
| [Getting Started](docs/guides/getting-started.md) | Installation and setup |
| [Configuration](docs/guides/configuration.md) | Environment variables |
| [Running Simulations](docs/guides/running-simulations.md) | Simulation management |
| [Deployment Guide](docs/operations/DEPLOYMENT_GUIDE.md) | Deployment & service management |

### 🚀 Core Features
| Document | Description |
|----------|-------------|
| [AI Forecasting](docs/features/AI_IMPLEMENTATION_SUMMARY.md) | Dual-target PEA forecasting |
| [AI Quickstart](docs/features/AI_QUICKSTART.md) | Testing AI endpoints |
| [Rust Acceleration](docs/wiki/integration/rust-acceleration.md) | PyO3 performance boost |
| [PostGIS Integration](docs/wiki/integration/postgis-integration.md) | Spatial database setup |

### 📖 Reference & Architecture
| Document | Description |
|----------|-------------|
| [API Design](docs/reference/API_DESIGN.md) | Core endpoint reference |
| [System Overview](docs/architecture/overview.md) | High-level architecture |
| [Thai Tariffs](docs/reference/thai-tariffs.md) | TOU tariff rates (2026) |
| [Meter Specification](docs/reference/meter-spec.md) | AMI specification |

---

## Roadmap

### ✅ Completed (Phases 1-29)

| Phase | Feature | Status |
|-------|---------|--------|
| 1-22 | AMI Foundation, Grid Intel, VPP, Frequency | ✅ Complete |
| 23-24 | OSM & Thai Grid Integration | ✅ Complete |
| 25 | **Rust Acceleration** (3,655-7,500x speedup) | ✅ Complete |
| 26 | **API Consolidation** (67+ endpoints) | ✅ Complete |
| 27 | **InfluxDB Real-Time Database** | ✅ Complete |
| 28 | **Grafana Dashboards** | ✅ Complete |
| 29 | **AI Forecasting (PEA Pillars)** | ✅ Complete |
| 30 | **SOA Refactoring** (Managers & Adapters) | ✅ Complete |

### In Progress

| Phase | Feature | Status |
|-------|---------|--------|
| 31 | Production-Scale Testing (5000+ meters) | 🚧 In Progress |
| 32 | Advanced VPP Market Settlements | 🚧 Pending |

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
