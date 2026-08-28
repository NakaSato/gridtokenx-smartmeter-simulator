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

## 🔄 How It Works

`ARCHITECTURE.md` covers the components and the egress contract. This section covers the part
that is easy to get wrong when editing the loop: **the order things happen in, and why.**

### From topology file to a solved feeder

```
.glm  ──GLMParser──▶ glm_topology_loader ──▶ topology_factory ──▶ GridTopology
                                                                      │
                                              ┌───────────────────────┴───────────────────┐
                                       meter_generator                              GridManager
                                  meter population, pinned to buses            pandapower net (bus/line/trafo/tap)
```

`GridTopology` is the neutral model — `.glm` is one way in, and `reference_grid_loader` reads
CINELDI MATPOWER CSVs directly as another. Nothing downstream knows which was used.

### One tick, in order

```
1  _apply_telemetry()        overlay real meter data, when a telemetry source is configured
2  read transformer loading  ← from the PREVIOUS tick (see below)
3  generate_all()            device models (PV via pvlib / ZIP load / battery) → EnergyReading
4  _apply_bess()             behind-the-meter storage absorbs surplus first
5  _apply_export_limit()     power limit (kW) — a physical device on the premises
6  _apply_export_cap()       daily energy budget (kWh) — accrues from what step 5 let through
7  update_grid_state()       ← the power flow
8  _update_grid_frequency()  f = nominal ± swing × (gen − load)
9  emit()                    sign Ed25519 → DLMS/COSEM egress
```

Two orderings carry meaning:

**Curtailment runs before the solve (4–6 before 7).** `GridManager` derives every bus injection
from the readings, so suppressing generation here removes it from the power flow — the resulting
voltages and line loadings are those of the *curtailed* network. Move any of these after the solve
and the caps become bookkeeping that the grid never feels.

**Frequency and transformer loading lag by one tick (2 and 8).** Both are feedback into the next
tick's device models — frequency drives frequency-watt droop, transformer loading drives BESS
congestion dispatch. Reading the current tick's values instead would close the loop on itself.

Step 7 can be throttled by `grid_solve_stride` (default `1`, solve every tick). The first tick
always solves, so bus voltages exist before any reading uses them; between solves the grid holds
the last solved voltages.

### Inside the solve: cheapest control first

The solver itself falls back twice before giving up:

```
pandapower bfsw (backward/forward sweep)   ← right algorithm for a radial LV feeder
      │ no convergence
pandapower nr, seeded from a DC solve
      │ no convergence
approximate DistFlow sweep
```

Plain Newton-Raphson is not the first choice on purpose: it diverges on the high per-unit
impedance of a 230 V radial chain and would silently drop every solve onto the approximate
fallback.

Once solved, the grid-edge controls run cheapest-first:

```
OLTC          step the tap until the LV head is in band            bulk regulation, no energy lost
      ▼
volt-VAR      inverters trade Q against local voltage (IEEE 1547)  reactive only, still no kW lost
      ▼
volt-watt     curtail PV real power                                last resort
```

Faults and normally-open tie switches are applied when the network is built, so they are out of
service before the solve. An islanded zone holding DER is re-rooted on its own slack and stays
energized; buses reachable from no slack are de-energized and reported as islanded.

### What the `.glm` actually feeds

| GLM object | Model field | What depends on it |
|------------|-------------|--------------------|
| `overhead_line` impedance | `GridLine.resistance/reactance_ohm_per_km` | every voltage and loss in the block above |
| `overhead_line` `capacity_kw` | `GridLine.capacity_kw` | line overload / congestion reporting |
| `transformer` | `GridTransformer` | **defines the zones**, and is where the OLTC acts |
| `solar` + `inverter` | `GridPV` | volt-VAR and volt-watt headroom; whether a zone survives islanding |

Zones are not authored — they are *derived*: one connected component of the line-only graph, i.e.
everything behind a transformer. Adding a transformer is the only way to create one. The four
shipped CINELDI grids are generated by `backend/scripts/regen_reference_glm.py`, which is also
where their zone structure and PV fleets are defined.

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
│   ├── scripts/                # offline tooling — regen_reference_glm (CINELDI CSV → .glm),
│   │                           #   export_glm (pandapower → .glm), DLMS/IAM drivers, plotting
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

## 🐳 Docker

The two halves are **two images**, matching the two-process local flow:

- root `Dockerfile` → the backend API. A builder stage compiles the Python venv (gcc lives
  there and is discarded), and the runtime stage carries only `/app/.venv` plus the source.
  Entrypoint `uv run start`, serving on **8082**.
- `frontend/Dockerfile` → the Next.js dashboard, on **3000**.

```bash
docker build -t gridtokenx-smartmeter-sim .
docker run -p 8082:8082 gridtokenx-smartmeter-sim     # API only on http://localhost:8082
```

The backend image serves **no UI** — `create_app()` mounts no static files and the image has no
Node runtime. It did once copy in the built `.next` output, but nothing ever read it; that stage
was removed on 2026-07-29 (−72 MB, and UI changes no longer invalidate backend layers).

Under the parent monorepo both run as compose services `smartmeter-simulator` and
`smartmeter-ui`, with the UI reaching the API over the compose network.

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
