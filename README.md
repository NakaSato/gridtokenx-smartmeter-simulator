# GridTokenX Smart Meter Simulator (GLM Core)

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-Proprietary-red.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-6.0.0-green.svg)](CHANGELOG.md)

> **High-fidelity Advanced Metering Infrastructure (AMI) and pure GridLab-D (GLM) Grid Simulator** for the GridTokenX ecosystem. Specialized in parsing and simulating real-time power flows directly from GLM topology models.

---

## ⚡ Core Features

- **Pure GLM Grid Topology**: Directly parses `.glm` files into a native `GridTopology` model, maintaining nodal mapping without an external power-flow engine.
- **Exact AC Power Flow**: Solves the feeder each tick with pandapower backward/forward sweep (`bfsw`, suited to radial LV feeders), with an approximate DistFlow sweep as fallback on non-convergence — bus voltages, line flows, losses, congestion.
- **IEEE 1547 Grid-Edge Controls**: PV **volt-watt** curtailment, **volt-VAR** reactive support, and **frequency-watt** droop close the local voltage/frequency response loops.
- **Distribution Transformer + OLTC**: Optional MV/LV feeder-head transformer (real impedance, loss model) with an on-load tap changer holding the LV head in band; transformers declared in `.glm` are always modeled.
- **Resilience Studies**: Fault/outage injection (N-1 contingency) trips lines/buses out of service — radial feeder reroutes or **islands**, with de-energized buses reported.
- **Demand Response**: API-scheduled load-shed (DR) events curtail participating load over a sim-clock window, relieving the feeder in the same solve.
- **High-Fidelity AMI Modeling**: Per-meter readings from Python device models (PV via `pvlib`, ZIP loads) mapped onto distribution buses by grid node location.
- **DLMS/COSEM Egress**: Streams signed, OBIS-coded readings into the parent Aggregator Bridge over the standard IEC 62056 REST contract (optional, off by default).
- **Optional Persistence**: Mirror each tick to PostGIS (replay/geo/history) or InfluxDB (run plotting) — both non-blocking, off by default.
- **Dynamic Scenarios**: Hot-swap `.glm` topology definitions (e.g. IEEE reference feeders) on the fly via the API.
- **Full-Stack Monitoring UI**: Next.js dashboard for real-time telemetry, 3D topology views, and aggregate grid metrics.

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

Each frame carries the **full residential register set** (single-phase L1): active import/export
energy, reactive energy, voltage, current, frequency, power factor, instantaneous active power,
rolling max demand, demand-response status, and — when `AGGREGATOR_TOU_ENABLED` (default on) —
2-tier time-of-use registers (peak/off-peak rate + active-tariff indicator, weekday peak window
`AGGREGATOR_TOU_PEAK_START_HOUR`–`AGGREGATOR_TOU_PEAK_END_HOUR`, default 09–22). See
[`ARCHITECTURE.md`](ARCHITECTURE.md) §“The DLMS/COSEM payload” for the OBIS code map.

---

## 🗺️ API Surface

All routes are mounted under `/api/v1` (full interactive reference at `/docs`).

**Simulation control**
- `GET /simulation/status` · `GET /simulation/runtime` · `GET|PUT /simulation/mode`
- `POST /simulation/actions/start` · `start-deterministic` · `stop` · `pause` · `resume` · `step`
- `PATCH /simulation/environment` — weather / stress multiplier
- `GET|POST|DELETE /simulation/faults` — list / trip / clear (N-1 contingency)
- `GET|POST|DELETE /simulation/demand-response` — status / schedule / cancel

**Grid & meters**
- `GET /grid/status` · `/grid/topology` · `/grid/telemetry` · `/grid/stats`
- `GET|POST|DELETE /meters`, `GET /meters/count`, `PUT /meters/count`
- `GET|PATCH|DELETE /meters/{id}`, `GET /meters/{id}/readings` · `/bill` · `/carbon`
- `POST /meters/{id}/readings/override` — inject real telemetry

**Pricing / carbon / history**
- `GET /pricing/tariffs` · `POST /pricing/quote`
- `GET /carbon/factors` · `POST /carbon/quote` · `GET /carbon/summary`
- `GET /history/readings` · `/history/network/geojson` · `/network/stats` · `/runs` · `/run/current` · `/run/series` (503 when persistence off)
- `GET /quality/health` — backend health probe

---

## 📁 Project Structure

```
gridtokenx-smartmeter-simulator/
├── backend/                     # Python 3.11+ FastAPI simulator (uv) — see backend/CLAUDE.md
│   ├── src/smart_meter_simulator/
│   │   ├── adapters/           # GLM ingestion: glm_converter (tokenizer) → topology loader
│   │   ├── core/               # engine, topology, grid_manager (power flow), reading_manager,
│   │   │                       #   demand_response, meter_logic/, metrics, app_state
│   │   ├── devices/            # AMI (meter), Solar (PV), Load device models
│   │   ├── routers/            # FastAPI v1: simulation, grid, meters, history, pricing, carbon
│   │   ├── transport/          # Aggregator Bridge DLMS/COSEM egress
│   │   ├── persistence/        # Optional PostGIS + InfluxDB reading stores
│   │   ├── config/             # pydantic-settings (get_config singleton)
│   │   └── data/grids/         # Reference `.glm` topologies
│   ├── database/migrations/    # PostGIS asset/replay schema (parent grid.* tables)
│   ├── tests/                  # pytest suite (topology, power flow, faults, DR, egress, store)
│   └── pyproject.toml          # uv-managed Python dependencies
└── frontend/                    # Next.js 16 / React 19 dashboard (bun/npm) — see frontend/CLAUDE.md
    ├── src/app/                # App Router (Dashboard, Map, 3D Topology, /run plots)
    ├── src/components/         # React components (grid controls, meter lists, charts)
    └── package.json            # Node dependencies
```

---

## 🧪 Testing

The backend is thoroughly tested for GLM topology parsing and simulation accuracy.

```bash
cd backend
uv run pytest                                        # full suite (coverage on via pytest.ini)
PYTEST_ADDOPTS=--no-cov uv run pytest -q tests/test_glm_core_topology.py   # quick, no coverage
uv run pytest -k <name> --no-cov                     # single test
```

---

## 🐳 Docker & Deploy

The root `Dockerfile` builds **both pieces into one image** (unlike the two-process local flow):
stage 1 builds the Next.js UI with **bun**, stage 2 assembles the Python backend with `uv` and
copies in the built UI. The entrypoint is `uv run start`, serving on port **8080** (note: local
dev uses **8082**).

```bash
docker build -t gridtokenx-smartmeter-sim .
docker run -p 8080:8080 gridtokenx-smartmeter-sim     # UI + API on http://localhost:8080
```

Deploy to Fly.io (`fly.toml`) — the sim is **stateful** (in-memory grid advanced each tick), so it
runs as exactly one always-on machine (never scale-to-zero, never multi-instance):

```bash
fly launch --no-deploy     # first time: claim app name
fly deploy                 # build root Dockerfile + release
```

Then point the frontend at it via `SIMULATOR_URL = https://<app-name>.fly.dev`.

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
