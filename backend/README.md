# GridTokenX Smart Meter Simulator

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Rust](https://img.shields.io/badge/rust-PyO3-orange.svg)](https://github.com/PyO3/pyo3)
[![License](https://img.shields.io/badge/license-Proprietary-red.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-5.1.0-green.svg)](CHANGELOG.md)

> **High-fidelity AMI (Advanced Metering Infrastructure) and Grid Orchestration simulator** for the GridTokenX ecosystem. Specialized in real-time power flow simulation (Pandapower), VPP grid services, and industrial-standard telemetry.

---

## 🚀 Quick Start

### 1. Start Infrastructure (Postgres + Redis)

```bash
docker compose up -d
```

### 2. Start Simulator

```bash
# Server mode (REST API + gRPC)
uv run app

# Standing mode (Direct output)
uv run cli --mode standalone --meters 20
```

### 3. Access Services

| Service | URL | Description |
|---------|-----|-------------|
| **API Gateway** | http://localhost:8082 | REST API & WebSocket |
| **API Docs** | http://localhost:8082/docs | Interactive Swagger UI |
| **PostgreSQL** | localhost:5432 | Relational database |
| **PostGIS** | localhost:5433 | Spatial database (Grid Topology) |

---

## 🌟 Key Features

### ⚡ Rust-Accelerated Performance
High-performance meter reading generation and VPP dispatch algorithms implemented in Rust via PyO3.

| Metric | Python | Rust (PyO3) | Speedup |
|--------|--------|-------------|---------|
| **1,000 meters** | ~3,000 ms | 0.82 ms | **3,655x** |

### 🌐 High-Fidelity AMI Simulation
- **Ed25519 Security**: Every reading is cryptographically signed at the source.
- **Accuracy Classes**: Models meter precision from Class 0.2 (Substation) to Class 2.0 (Residential).
- **Industrial Protocols**: Native support for **DLMS/COSEM** and **gRPC** ingestion.

### 🔌 Grid & VPP Orchestration
- **Pandapower Integration**: Real-time State Estimation (WLS) and Power Flow.
- **VPP Dispatch**: Automated Frequency Restoration Reserve (aFRR) and Droop Control.
- **Islanding Management**: Microgrid stability and black-start sequencing.

### 🗺️ Spatial Grid Modeling
- **PostGIS integration** for spatial meter placement.
- **Thai distribution networks** (MEA/PEA topology models).

---

## 🏗️ Architecture

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                     Smart Meter Simulator                    │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │ Domain       │  │ Grid Manager │  │ VPP              │  │
│  │ Managers     │  │ (Pandapower) │  │ Manager          │  │
│  │ (Reading/Sec)│  │ (Estimation) │  │ (AFRR, Droop)    │  │
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

## 📁 Project Structure

```
gridtokenx-smartmeter-simulator/backend/
├── src/smart_meter_simulator/
│   ├── core/               # Domain Managers (Grid, VPP, Reading, Security)
│   │   ├── engine.py       # Main orchestration loop
│   │   ├── grid_manager.py # Electrical state & nodal pricing
│   │   ├── vpp.py          # VPP coordination & dispatch
│   │   ├── reading_manager.py # Reading collection & signing
│   │   └── attacker.py     # FDI detection & security simulation
│   ├── adapters/           # Integration adapters
│   ├── transport/          # HTTP, WS, Kafka, InfluxDB, gRPC
│   ├── routers/            # API v1 endpoints
│   ├── config/             # Settings, enums, Thai market
│   ├── models/             # Data models (EGAT, Reading)
│   ├── database/           # PostGIS models & repository
│   └── utils/              # Common utilities
├── src/rust_sim/           # Rust acceleration (PyO3)
│   ├── Cargo.toml
│   └── src/lib.rs          # Core simulation logic in Rust
├── database/migrations/    # SQL migrations
├── scripts/                # Utility scripts (data ingestion, optimization)
├── proto/                  # Protobuf definitions
├── tests/                  # Test suite
├── pyproject.toml          # UV-managed dependencies
└── .env.example            # Environment template
```

---

## 🔧 Configuration

### Essential Environment Variables

```bash
# Simulator
SIMULATION_INTERVAL=15        # Seconds between readings
NUM_METERS=55                 # Number of meters

# InfluxDB (Time-Series Database)
INFLUXDB_URL=http://gridtokenx-influxdb:8086
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

## 🧪 Testing

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=src --cov-report=html

# Run specific test suite
uv run pytest tests/test_dlms.py -v
```

---

## 🗺️ Roadmap

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
| 29 | **Production-Scale Testing** (1000+ meters) | ✅ Complete |
| 30 | **Advanced InfluxDB Metrics** (VPP, market, weather) | ✅ Complete |

### 🔄 In Progress

| Phase | Feature | Status |
|-------|---------|--------|
| 31 | Advanced AI Forecaster Integration | 🚧 Pending |

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'feat: add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Conventions

- **Formatter:** Black (line length 88)
- **Imports:** isort (Black profile)
- **Linting:** flake8
- **Tests:** Required for new features

---

## 📄 License

Part of the GridTokenX Ecosystem - Proprietary

---

_Maintained by the GridTokenX Engineering Team._
