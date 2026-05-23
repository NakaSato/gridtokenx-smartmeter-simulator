# GridTokenX Smart Meter Simulator

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Rust](https://img.shields.io/badge/rust-PyO3-orange.svg)](https://github.com/PyO3/pyo3)
[![License](https://img.shields.io/badge/license-Proprietary-red.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-5.0.0-green.svg)](CHANGELOG.md)

> **High-fidelity AMI (Advanced Metering Infrastructure), Grid Orchestration, and AI Forecasting simulator** for the GridTokenX ecosystem. Specialized in real-time power flow simulation (Pandapower), VPP grid services, industrial-standard telemetry (DLMS/COSEM IEC 62056), and PEA-mandated forecasting pillars.

![image](./image.png)

---

## Quick Start

### 1. Start Infrastructure (Postgres + Redis + InfluxDB)

```bash
docker compose up -d
```

### 2. Start Simulator Backend

```bash
# Server mode (REST API + gRPC) — default port 12010
PORT=12010 uv run start

# Or with uvicorn directly
PORT=12010 uv run uvicorn smart_meter_simulator.app:app --host 0.0.0.0 --port 12010

# Standalone mode (Direct output, no server)
uv run start-simulator --mode standalone --meters 20
```

### 3. Start Simulator Frontend

```bash
cd frontend
bun install
bun run dev --port 12011
```

### 4. Access Services

| Service | URL | Description |
|---------|-----|-------------|
| **Simulator API** | http://localhost:12010 | REST API & WebSocket |
| **API Docs** | http://localhost:12010/docs | Interactive Swagger UI |
| **Simulator UI** | http://localhost:12011 | Next.js Dashboard & Map |
| **Health Check** | http://localhost:12010/health | Backend health endpoint |

---

## Key Features

### Dual-Path Telemetry Routing

The simulator implements two distinct telemetry paths aligned with the Oracle Bridge ingestion model:

| Path | Meter Types | Protocol | Frequency | Purpose |
|------|-------------|----------|-----------|---------|
| **Path A** | Residential, Resideltail | gRPC / HTTP | Real-time (per tick) | Live telemetry streaming |
| **Path B** | Commercial, Feeder, Substation, etc. | gRPC / HTTP | 15-minute windows | Settlement attestations |

- **Path A (Real-time)**: Each reading is individually Ed25519-signed (`{meter_id}:{kwh}:{timestamp}`) and sent via `send_batch()`.
- **Path B (Settlement)**: Aggregated attestations are signed (`{meter_id}:{total_kwh}:{start_time}:{end_time}`) and sent via `send_attestation_batch()`.

### DLMS/COSEM IEC 62056 Protocol

Native implementation of the industrial metering standard with binary and JSON encoding modes:

| OBIS Code | Description | Encoding |
|-----------|-------------|----------|
| `1.1.1.8.0.255` | Active Energy Import (+A) | 8 bytes (Wh) |
| `1.1.2.8.0.255` | Active Energy Export (-A) | 8 bytes (Wh) |
| `1.1.32.7.0.255` | Voltage L1 | 4 bytes (centivolts) |
| `1.1.31.7.0.255` | Current L1 | 4 bytes (milliamps) |
| `1.1.3.8.0.255` | Reactive Energy Import (+Q) | — |
| `1.1.14.7.0.255` | Frequency | — |
| `1.1.13.7.0.255` | Power Factor | — |
| `0.0.96.6.3.255` | Battery SOC (custom) | 4 bytes (basis points) |

Binary frames include a 3-byte manufacturer ID (`GXT`), 8-byte logical device name, and 8-byte timestamp header.

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

- **10 Meter Types**: Solar Prosumer, Grid Consumer, Hybrid Prosumer, Battery Storage, Residential, Commercial, Feeder, Substation, EV Charger, DC Fast Charger.
- **Accuracy Classes**: Models meter precision from Class 0.2 (Substation) to Class 2.0 (Residential).
- **Ed25519 Cryptographic Signing**: Base58-encoded signatures aligned with the Solana ecosystem.

### Grid & VPP Orchestration

- **Pandapower Integration**: Real-time State Estimation (WLS) and Power Flow.
- **VPP Dispatch**: Automated Frequency Restoration Reserve (aFRR) and Droop Control.
- **Islanding Management**: Microgrid stability and black-start sequencing.

### Spatial Grid Modeling

- **PostGIS integration** for spatial meter placement.
- **Thai distribution networks** (MEA/PEA/EGAT topology models).

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
│  ┌──────▼─────────────────▼────────────────────▼──────────┐ │
│  │              Smart Meters (20-5000+)                    │ │
│  │    Ed25519 signing · DLMS/COSEM · Accuracy classes      │ │
│  └──────────────────────┬─────────────────────────────────┘ │
│                         │                                   │
│  ┌──────────────────────▼─────────────────────────────────┐ │
│  │  Transport Layer (Composite Fan-Out)                    │ │
│  │  gRPC │ HTTP │ WebSocket │ Kafka │ MQTT │ InfluxDB      │ │
│  └──────────────────────┬─────────────────────────────────┘ │
└─────────────────────────┼───────────────────────────────────┘
                          │
              ┌───────────▼───────────┐
              │   Oracle Bridge       │
              │   :4030 (HTTP/gRPC)   │
              ├───────────────────────┤
              │ Path A → Real-time    │
              │ Path B → Attestations │
              └───────────────────────┘
```

### Telemetry Data Flow

```
Meter Reading Generation (Rust/Python)
         ↓
    DLMS/COSEM Binary Encoding (IEC 62056)
         ↓
    Ed25519 Signing (Base58 / Solana-aligned)
         ↓
    Dual-Path Routing
    ├── Path A (Residential) → send_batch() → Oracle Bridge (real-time)
    └── Path B (B2B)         → send_attestation_batch() → Oracle Bridge (15-min settlement)
         ↓
    Oracle Bridge → Zone Partitioning → Solana Blockchain
```

---

## Meter Types & Accuracy Classes

| Meter Type | Accuracy Class | Error % | Channels | Routing |
|------------|---------------|---------|----------|---------|
| **Residential** | Class 2.0 | ±2.0% | v, p, q | Path A |
| **Grid Consumer** | Class 2.0 | ±2.0% | v, p, q | Path B |
| **Solar Prosumer** | Class 1.0 | ±1.0% | v, p, q | Path B |
| **Hybrid Prosumer** | Class 1.0 | ±1.0% | v, p, q | Path B |
| **Commercial** | Class 1.0 | ±1.0% | v, p, q, i | Path B |
| **Battery Storage** | Class 0.5 | ±0.5% | v, p, q | Path B |
| **Feeder** | Class 0.5 | ±0.5% | v, p, q, i | Path B |
| **DC Fast Charger** | Class 0.5 | ±0.5% | v, p, q, i, soc, connector | Path B |
| **Substation** | Class 0.2 | ±0.2% | v, p, q, i, ia, va | Path B |
| **EV Charger** | Class 1.0 | ±1.0% | v, p, q, i, soc | Path B |

> **Note:** The meter type `"Resideltail"` (a legacy typo) is automatically mapped to `"Residential"` at initialization and routed through Path A.

---

## Transport Layer

The simulator supports multiple transport backends via a composite fan-out architecture. All transports implement the abstract `TransportLayer` interface with built-in retry logic and exponential backoff.

| Transport | Target | Protocol | Use Case |
|-----------|--------|----------|----------|
| **gRPC** | Oracle Bridge `:50051` | Protobuf / betterproto | Primary ingestion (DLMS binary payloads) |
| **HTTP** | Oracle Bridge `:4030` | REST / JSON | Fallback ingestion (DLMS JSON + OBIS codes) |
| **WebSocket** | Dashboard `:8765` | JSON | Live UI streaming |
| **Kafka** | Broker | Avro / JSON | Event sourcing (`meter-readings` topic) |
| **MQTT** | AMI Broker `:1883` | MQTT v5 | Industrial AMI integration |
| **InfluxDB** | Time-series DB | Line Protocol | AI training data & metrics |

---

## Project Structure

```
gridtokenx-smartmeter-simulator/
├── backend/                          # Python + Rust Backend
│   ├── src/smart_meter_simulator/
│   │   ├── app.py                    # FastAPI entry point (v3.0.0)
│   │   ├── cli.py                    # CLI entry point
│   │   ├── lifespan.py               # FastAPI lifespan manager
│   │   ├── core/                     # Domain Logic (23 modules)
│   │   │   ├── engine.py             # Simulation orchestrator (Path A/B routing)
│   │   │   ├── meter.py              # SmartMeter class (signing, attestations)
│   │   │   ├── dlms.py               # DLMS/COSEM IEC 62056 encoder
│   │   │   ├── grid_manager.py       # Pandapower grid management
│   │   │   ├── vpp.py                # VPP orchestration
│   │   │   ├── vpp_handler.py        # Frequency response & island stability
│   │   │   ├── frequency.py          # Frequency model
│   │   │   ├── island.py             # Microgrid islanding
│   │   │   ├── billing.py            # TOU billing engine
│   │   │   ├── attacker.py           # FDI (False Data Injection) simulation
│   │   │   ├── rust_engine.py        # Rust acceleration bindings
│   │   │   ├── rust_vpp_engine.py    # Rust VPP engine bindings
│   │   │   ├── charging_station.py   # EV charging station simulation
│   │   │   ├── microgrid_core.py     # Microgrid core logic
│   │   │   ├── power_plants.py       # Power plant simulation
│   │   │   └── meter_logic/          # Profile & electrical calculations
│   │   ├── transport/                # Multi-Transport Layer (10 modules)
│   │   │   ├── base.py               # Abstract TransportLayer (retry logic)
│   │   │   ├── composite.py          # Composite fan-out transport
│   │   │   ├── grpc.py               # gRPC transport (betterproto)
│   │   │   ├── http.py               # HTTP REST transport
│   │   │   ├── mqtt.py               # MQTT transport
│   │   │   ├── kafka.py              # Kafka transport
│   │   │   ├── websocket.py          # WebSocket transport
│   │   │   ├── influxdb.py           # InfluxDB write transport
│   │   │   └── proto/                # Protobuf definitions
│   │   ├── config/                   # Configuration & Enums
│   │   │   ├── settings.py           # Pydantic SimulatorConfig
│   │   │   ├── enums.py              # MeterType, AccuracyClass, etc.
│   │   │   ├── channels.py           # Measurement channels per meter type
│   │   │   └── initial_locations*.json
│   │   ├── models/                   # Pydantic Data Models
│   │   │   ├── reading.py            # EnergyReading, Attestation
│   │   │   └── egat.py               # EGAT data model
│   │   ├── routers/                  # FastAPI Routers (11 modules)
│   │   │   ├── api_v1.py             # Core API endpoints
│   │   │   ├── simulation_v1.py      # Simulation control
│   │   │   ├── meters_v1.py          # Meter management
│   │   │   ├── grid_v1.py            # Grid state & topology
│   │   │   ├── vpp_v1.py             # VPP orchestration
│   │   │   ├── microgrid_v1.py       # Microgrid management
│   │   │   └── ...                   # billing, analytics, price, registry
│   │   ├── services/                 # Application Services
│   │   │   ├── telemetry_service.py  # Telemetry processing
│   │   │   ├── strategy_service.py   # Trading strategy
│   │   │   ├── map_service.py        # Map data service
│   │   │   └── export_service.py     # Data export
│   │   ├── database/                 # SQLAlchemy + EGAT Ingestion
│   │   ├── utils/                    # Utilities
│   │   │   ├── crypto.py             # Ed25519 KeyManager (Base58 sigs)
│   │   │   └── telemetry.py          # OpenTelemetry setup
│   │   └── templates/                # Meter config templates
│   └── pyproject.toml                # UV-managed dependencies
│
├── frontend/                         # Next.js 16 Dashboard (React 19)
│   ├── src/
│   │   ├── app/                      # App Router Pages
│   │   │   ├── dashboard/            # Main dashboard
│   │   │   ├── map/                  # Interactive meter map (Mapbox GL)
│   │   │   ├── meter/[meterId]/      # Individual meter detail
│   │   │   ├── vpp/                  # VPP dashboard
│   │   │   ├── topology/             # 3D network topology (Three.js)
│   │   │   ├── resilience/           # Grid resilience view
│   │   │   ├── lpc/                  # Locational Price Curves
│   │   │   ├── adr/                  # Automated Demand Response
│   │   │   └── api/                  # API proxy routes (→ :12010)
│   │   ├── components/
│   │   │   ├── maps/                 # Map overlays (EGAT, OSM, microgrid)
│   │   │   ├── meters/               # Meter popups & detail views
│   │   │   ├── dashboard/            # Dashboard widgets
│   │   │   ├── providers/            # NetworkProvider, SimulatorProvider
│   │   │   └── ui/                   # GlobalNav, StatCard, ControlButton
│   │   ├── hooks/                    # useApi, useWebSocket, useMapStyle
│   │   └── lib/                      # Constants, types, pricing utils
│   ├── next.config.ts                # Rewrites proxy to backend :12010
│   └── package.json                  # bun, Next.js 16, Tailwind v4
│
├── data/                             # EGAT infrastructure data
├── docs/                             # Documentation
└── docker-compose.postgis.yml        # PostGIS for spatial data
```

---

## Configuration

### Essential Environment Variables

```bash
# Simulator Backend
PORT=12010                    # Backend API port
SIMULATION_INTERVAL=15        # Seconds between readings
NUM_METERS=55                 # Number of meters
AUTOSTART_SIMULATION=true     # Auto-start on boot

# Transport Configuration
TRANSPORT_TYPE=grpc           # Options: grpc, http, kafka, mqtt
ENABLE_DLMS_BINARY=true       # Enable DLMS/COSEM binary encoding

# Oracle Bridge (Telemetry Target)
API_GATEWAY_URL=http://localhost:4030    # Oracle Bridge REST endpoint
GRPC_GATEWAY_HOST=localhost             # Oracle Bridge gRPC host
GRPC_GATEWAY_PORT=50051                 # Oracle Bridge gRPC port

# Databases
DATABASE_URL=postgresql+asyncpg://gridtokenx:gridtokenx_password@localhost:5432/gridtokenx
GIS_DATABASE_URL=postgresql+asyncpg://gridtokenx:gridtokenx_password@localhost:5433/gridtokenx_gis
REDIS_URL=redis://localhost:6379

# InfluxDB (Time-Series)
INFLUXDB_URL=http://localhost:7020
INFLUXDB_TOKEN=admin_token
INFLUXDB_ORG=gridtokenx
INFLUXDB_BUCKET=meter_readings

# API Authentication
API_KEY=your-api-key

# Rust Acceleration
RUST_ACCELERATION_ENABLED=true

# AI Forecasting
AI_MODEL_PATH=/app/data/pea_lgbm_model.pkl
AI_FORECAST_HORIZON=24
```

See `.env.production.template` for the complete list.

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

### ✅ Completed (Phases 1-30)

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
| 31 | **DLMS/COSEM IEC 62056** (Binary + JSON) | ✅ Complete |
| 32 | **Dual-Path Routing** (Path A/B Separation) | ✅ Complete |
| 33 | **Next.js 16 Frontend** (App Router, Mapbox GL, 3D Topology) | ✅ Complete |

### In Progress

| Phase | Feature | Status |
|-------|---------|--------|
| 34 | Production-Scale Testing (5000+ meters) | 🚧 In Progress |
| 35 | Advanced VPP Market Settlements | 🚧 Pending |

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
