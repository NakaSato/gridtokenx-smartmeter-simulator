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

_Maintained by the GridTokenX Engineering Team._
