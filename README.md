# GridTokenX Smart Meter Simulator (GLM Core)

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-Proprietary-red.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-6.0.0-green.svg)](CHANGELOG.md)

> **High-fidelity Advanced Metering Infrastructure (AMI) and pure GridLab-D (GLM) Grid Simulator** for the GridTokenX ecosystem. Specialized in parsing and simulating real-time power flows directly from GLM topology models.

---

## ⚡ Core Features

- **Pure GLM Grid Topology**: Directly parses `.glm` files to construct electrical feeder topologies, maintaining nodal mapping without external dependencies.
- **Approximate Topology Solver**: Updates bus voltages, line flows, system losses, and congestion internally on every tick.
- **High-Fidelity AMI Modeling**: Accurately simulates smart meters mapped perfectly onto the distribution buses based on their grid node locations.
- **Dynamic Scenarios**: Seamlessly switch between different `.glm` topology definitions (e.g., IEEE reference feeders) on the fly via the API.
- **Full-Stack Monitoring UI**: Includes a Next.js dashboard for visualizing real-time telemetry, 3D topology views, and aggregate grid metrics.

---

## 🚀 Quick Start

### 1. Start Simulator Backend

```bash
cd backend

# Validate the configured GLM topology
uv run cli --mode validate-topology

# Run the REST API
uv run app

# Or run a local standalone simulator loop without the server
uv run cli --mode standalone --meters 20
```

### 2. Start Simulator Frontend

```bash
cd frontend
npm install
npm run dev
```

### 3. Access Services

| Service | URL | Description |
|---------|-----|-------------|
| **Simulator API** | `http://localhost:8082` | REST API |
| **API Docs** | `http://localhost:8082/docs` | Interactive Swagger UI |
| **Simulator UI** | `http://localhost:3000` | Next.js Dashboard & Map |
| **Health Check** | `http://localhost:8082/api/v1/quality/health` | Backend health endpoint |

---

## 🔧 Configuration

The essential backend settings are controlled via `.env`:

```bash
# Simulator
SIMULATION_INTERVAL=900
NUM_METERS=20

# Topology Definition
GRID_TOPOLOGY=glm:src/smart_meter_simulator/data/grids/grid_bus_network.glm
```

See `backend/.env.example` for additional configurations regarding meter mix, weather, solar, and load profiles.

### Egress to the parent Aggregator Bridge (DLMS/COSEM)

DLMS/COSEM egress is **off by default**. To stream signed readings into the parent
`gridtokenx-aggregator-bridge`, the bridge and Redis must be reachable and egress enabled.
For host-networked dev (bridge IoT gateway on `:4030`, Redis on `:7010`):

```bash
cd backend
AGGREGATOR_DLMS_ENABLED=true \
AGGREGATOR_BRIDGE_URL=http://localhost:4030 \
REDIS_URL=redis://localhost:7010 \
uv run cli --mode standalone --meters 5
```

The engine generates a per-meter Ed25519 key, seeds the pubkey into the bridge's Redis
registry on start, then POSTs each reading as a signed OBIS frame to
`/v1/private-network/ingest` (expect `202 Accepted`). Note: host `:4010` is the IAM
service, **not** the bridge — use `:4030`. Inside the docker network use
`http://aggregator-bridge:4010` and `redis://redis:6379`.

---

## 🗺️ API Surface

The API provides clean integration points for controlling the GLM simulation environment:

- `GET /api/v1/simulation/status`
- `POST /api/v1/simulation/actions/start`
- `POST /api/v1/simulation/actions/stop`
- `POST /api/v1/simulation/actions/step`
- `PATCH /api/v1/simulation/environment`
- `GET /api/v1/grid/topology`
- `GET /api/v1/grid/telemetry`
- `GET /api/v1/grid/stats`
- `GET /api/v1/meters`
- `POST /api/v1/meters`
- `DELETE /api/v1/meters`
- `PUT /api/v1/meters/count`

---

## 📁 Project Structure

```
gridtokenx-smartmeter-simulator/
├── backend/
│   ├── src/smart_meter_simulator/
│   │   ├── adapters/           # GLM topology parsers (glm_converter, loader, adapter)
│   │   ├── core/               # Engine, Topology Model, Grid Manager, Reading Manager
│   │   ├── data/grids/         # Reference `.glm` files (IEEE models, custom models)
│   │   ├── devices/            # AMI (meter), Solar (PV), Load definitions
│   │   ├── models/             # Data structure schemas
│   │   ├── routers/            # FastAPI v1 endpoints
│   │   └── utils/              # Local helper utilities
│   ├── tests/                  # Core topology tests
│   └── pyproject.toml          # UV-managed Python dependencies
└── frontend/
    ├── src/app/                # Next.js App Router (Dashboard, Map, Topology)
    ├── src/components/         # React Components (Grid controls, meter lists)
    └── package.json            # Node dependencies
```

---

## 🧪 Testing

The backend is thoroughly tested for GLM topology parsing and simulation accuracy.

```bash
cd backend
PYTEST_ADDOPTS=--no-cov uv run pytest -q tests/test_glm_core_topology.py
```

---

## 🛣️ Roadmap — Toward a Smart-Meter-Fed Virtual Power Plant (VPP)

The simulator already emits the verified-efficient **DLMS/COSEM (IEC 62056)** meter→aggregator
wire contract and models the exact grid-edge actuators a VPP commands — **volt-watt** PV
curtailment, **volt-VAR** reactive support, and **frequency-watt** droop (IEEE 1547-2018,
experimentally validated for voltage/over-frequency mitigation). That makes it a natural base
for a meter-fed VPP aggregator. Planned direction, grounded in current literature:

**Aggregation & dispatch (`backend/`)**
- [ ] **Forecast-then-optimize loop** — multi-timescale receding-horizon MPC (day-ahead 1 h +
      intra-day rolling 15 min), real-time telemetry correcting the day-ahead plan.
- [ ] **Load/generation forecasting** — pluggable model (baseline → attention-BiLSTM); treat
      published 2.5 % MAPE as illustrative, not a benchmark.
- [ ] **Stochastic offering strategy** — multistage stochastic DP / MDP bidding, or three-stage
      bi-level (VPP-vs-ISO market clearing); co-optimize energy + frequency-regulation reserve.
- [ ] **Aggregation/disaggregation** — collapse real-time dispatch to economic dispatch to cut
      compute (note: needs distribution-network data — feasible region from DER constraints
      *alone* is not sufficient).
- [ ] **Demand-response coupling** — curtailable/shiftable load split driven by MPC outputs for
      peak-shaving / valley-filling.

**Standards & telemetry**
- [ ] **Fast-telemetry channel** — evaluate whether DLMS/COSEM push meets CAISO **4-second**
      ancillary-services telemetry + **5-minute** interval-data, or needs a separate stream
      (e.g. IEC 61850 GOOSE/MMS).
- [ ] **Protocol breadth** — add IEEE 2030.5 (SEP2) / OpenADR 2.0/3.0 for DR signaling and
      IEC 61968/CIM for back-office model exchange alongside DLMS/COSEM telemetry.
- [ ] **"Aggregated accuracy" metering study** — use the many-cheap-meters fleet to generate
      law-of-large-numbers evidence for the ±0.5 % aggregate market-accuracy bar.

**Visualization (`frontend/`)**
- [ ] VPP dashboard — aggregate dispatchable capacity, per-program rollups, market-revenue
      stack (capacity / DR / ancillary services), live curtailment & reserve.

> Sources: IEEE 1547-2018; Applied Energy (Maui ASI, S0306261919316873); PLOS ONE 0339606;
> arXiv 2309.08642, 2008.11125; IEEE SmartGridComm 2011 (DLMS/COSEM comparison, doc 6102357);
> RMI VP3 Metering & Telemetry; INFORMS inte.2022.1120; Kardakos IEEE TSG 2016; Mujeeb 2025
> (Wiley etep/6640754); Applied Energy S0306261924015253; Sunrun FY2024 VPP report.

---

_Maintained by the GridTokenX Engineering Team._
