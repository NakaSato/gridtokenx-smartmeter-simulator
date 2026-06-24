# gridtokenx-smartmeter-simulator — Architecture

> A standalone GridLAB-D (GLM)-backed Advanced Metering Infrastructure (AMI) grid simulator:
> it parses a `.glm` feeder topology, generates per-meter energy readings from Python device
> models, runs a per-tick power flow, and ships cryptographically-signed telemetry into the
> parent Aggregator Bridge.
>
> This repo is a **git submodule** of the `gridtokenx-coresystem` superproject. The parent's
> Rust/Cargo/Solana conventions **do not apply here** — this is a **Python + TypeScript**
> sub-project. This doc covers **only** the contents of this folder.

---

## 1. What This Is

A monorepo of two independently-developed apps:

- **`backend/`** — a **Python 3.11+** FastAPI simulator (package `smart_meter_simulator`, version
  `6.0.0`), managed by **uv**. It is the simulation engine, GLM parser, device models, power-flow
  solver, and telemetry egress.
- **`frontend/`** — a **Next.js 16 / React 19** dashboard (map, 3D topology, real-time telemetry).
  Not covered further here.

The backend parses a `.glm` topology into a native `GridTopology`, generates per-meter readings
with device models (PV via `pvlib`, ZIP loads, optional BESS), and each tick runs an **exact AC
power flow** (pandapower backward/forward sweep, `bfsw`) with an **approximate DistFlow fallback**
on non-convergence — updating bus voltages, line flows, losses, and congestion. It is exposed as
a REST service on **port 8082** (`/docs` for Swagger), plus a root **WebSocket `/ws`** that pushes
live `grid_status` frames (APISIX exposes it publicly as `/api/market/ws`). Readings egress to the parent
`gridtokenx-aggregator-bridge` over the standard **DLMS/COSEM (IEC 62056)** REST contract, each
reading **signed at the meter with Ed25519**.

There is **no single shared Cargo/workspace** — the only Rust dependency of the platform is the
contract the bridge enforces; this folder ships no Rust (the legacy binary Protocol-v4 gRPC path
and its `rust_sim` crate were removed; DLMS/COSEM REST is now the **sole** egress).

## 2. Package Layout

```
gridtokenx-smartmeter-simulator/
├── backend/                              # Python 3.11+ FastAPI simulator (uv)
│   ├── pyproject.toml                    # deps + uv scripts (start/app/cli) — package smart_meter_simulator 6.0.0
│   ├── src/smart_meter_simulator/
│   │   ├── app.py                        # create_app() FastAPI factory; main() entry (uv run app/start)
│   │   ├── cli.py                        # CLI entry (uv run cli): standalone / validate-topology modes
│   │   ├── lifespan.py                   # FastAPI lifespan → builds the engine singleton
│   │   ├── config/                       # pydantic-settings; get_config() cached singleton, enums, channels
│   │   ├── core/
│   │   │   ├── engine.py                 # SimulationEngine — meter list, grid, async tick loop, frequency
│   │   │   ├── app_state.py              # process-global engine singleton (routers reach it here)
│   │   │   ├── topology.py               # GridTopology dataclass (buses/lines/loads/pvs) — neutral model
│   │   │   ├── topology_factory.py       # resolves a `glm:<path>` spec → GridTopology
│   │   │   ├── grid_manager.py           # per-tick power flow: pandapower bfsw + DistFlow fallback; volt-watt/volt-VAR/OLTC/faults
│   │   │   ├── reading_manager.py        # per-tick reading generation (dispatched via asyncio.to_thread)
│   │   │   ├── meter_logic/              # electrical.py (ZIP + freq-watt droop), profiles.py (load shapes)
│   │   │   ├── frequency.py, metrics.py  # system-frequency model; Prometheus metrics
│   │   │   └── telemetry_source.py       # real-telemetry overrides for synthetic models
│   │   ├── adapters/                     # GLM ingestion only: glm_converter (GLMParser), glm_topology_loader, reference_grid_loader
│   │   ├── devices/                      # ami.py (SmartMeter), solar.py (PV/pvlib), load.py (ZIP), battery.py (BESS)
│   │   ├── meter_generator.py            # builds the meter population (type mix, PV-per-bus) from topology
│   │   ├── meter_registry.py            # pin real meters by id to physical buses (telemetry-driven runs)
│   │   ├── models/reading.py             # EnergyReading pydantic model (the on-wire reading shape)
│   │   ├── transport/
│   │   │   ├── aggregator_bridge.py          # *** sole egress: DLMS/COSEM REST + MeterKey (Ed25519) + Redis pubkey/owner seeding
│   │   │   └── iam_onboarding.py         # live owner resolution via IAM gateway (register→verify→login)
│   │   ├── persistence/reading_store.py  # optional PostGIS egress (grid.meter_readings) via asyncpg
│   │   ├── routers/                      # FastAPI v1 (/api/v1): simulation_v1, meters_v1, grid_v1, history_v1, api_v1; market_ws.py (root /ws grid_status push)
│   │   └── data/grids/grid_bus_network.glm  # default reference feeder
│   ├── scripts/
│   │   ├── send_to_aggregator_bridge.py      # standalone DLMS egress driver (--meters/--interval/--once/--onboard/--dry-run)
│   │   ├── e2e_iam_flow.py, onboard_meters.py  # IAM register→verify→claim flows
│   │   └── simulate_pandapower.py, export_glm.py, plot_bus_network.py, fetch_*_grid.py  # offline tooling
│   └── tests/                            # pytest: test_glm_core_topology, test_aggregator_bridge_dlms, test_voltvar, test_oltc, …
└── frontend/                             # Next.js 16 / React 19 dashboard (own CLAUDE.md)
```

## 3. Architecture

### Telemetry generation → signing → egress

```
.glm topology file
   └─ adapters/ (GLMParser → glm_topology_loader) → topology_factory → GridTopology
        │
SimulationEngine.tick()  (core/engine.py, async loop)
   ├─ ReadingManager.generate_all()      # device models (PV/load/battery), asyncio.to_thread
   │     devices/ami.py SmartMeter.generate_reading → EnergyReading (energy_generated/consumed, V/I/f, PF, kvar …)
   ├─ GridManager.update_grid_state()    # pandapower bfsw AC power flow → DistFlow fallback
   │     volt-VAR (Q(V)) then volt-watt PV curtailment; optional MV/LV transformer + OLTC; fault/island injection
   └─ _update_grid_frequency()           # nominal ± FREQ_FULL_SWING_HZ × (gen−load); feeds frequency-watt droop
        │
        ▼  (when AGGREGATOR_DLMS_ENABLED=true)
AggregatorBridgeEmitter.emit(readings)       # transport/aggregator_bridge.py — non-blocking, one task/tick
   per meter:
     ├─ MeterKey(meter_id)               # Ed25519 keypair, seed = sha256("{secret}:{meter_id}") — deterministic, stable across restarts
     ├─ sign canonical = f"{device_id}:{kwh}:{timestamp_ms}"   # base58 signature
     └─ POST {protocol:"dlms", device_id, payload: <OBIS JSON>} → AGGREGATOR_BRIDGE_URL/v1/private-network/ingest  (expect 202)
        │  (all meters fired concurrently via asyncio.gather; tick dropped if prior batch still in flight)
        ▼
gridtokenx-aggregator-bridge (parent)
   DlmsStack.map_payload  → OBIS codes back to energy metrics
   verify_rest_signature  → checks Ed25519 sig against device pubkey held in Redis
```

On `AggregatorBridgeEmitter.start()` the engine seeds each meter's **Ed25519 public key** into the
bridge's Redis device registry (`gridtokenx:devices:{meter_id}:pubkey = <hex>`, via a raw RESP
socket — no `redis` dependency) so `verify_rest_signature` can authenticate telemetry, and
probes the bridge `/health`. It also seeds the meter→owner map
(`gridtokenx:meters:{serial}:user_id`) — from `AGGREGATOR_METER_OWNER_MAP` or resolved live through
the IAM gateway (`AGGREGATOR_IAM_ONBOARD_ENABLED`: register→verify→login) — so the bridge resolves a
`user_id` for settlement (without it telemetry resolves to `Uuid::nil` and settlement is skipped).

### The DLMS/COSEM payload

`_build_obis_payload` encodes each `EnergyReading` as an IEC 62056 OBIS-keyed JSON object — the
**full residential register set** (single-phase L1):

- active import/export energy total in **Wh** (`1.1.1.8.0.255` / `1.1.2.8.0.255`) — the settlement energy;
- optional reactive energy in varh (`1.1.3/4.8.0.255`), voltage L1 (`1.1.32.7.0.255`), current L1
  (`1.1.31.7.0.255`), frequency (`1.1.14.7.0.255`), power factor (`1.1.13.7.0.255`);
- sum (signed) active power in kW (`1.1.16.7.0.255` — the C=16 sum register A+−A−, negative on
  export; **not** the positive-only `1.7.0`) and rolling max import demand in kW (`1.1.1.6.0.255`,
  run-scoped peak held on the emitter, import only);
- demand-response status (`0.0.96.10.0.255`, set when the reading carries `dr_shed_kw`);
- when `AGGREGATOR_TOU_ENABLED` (default on), **2-tier time-of-use** registers: this interval's
  energy in the active rate's import/export register (rate 1 = peak `…8.1.255`, rate 2 = off-peak
  `…8.2.255`) plus the active-tariff indicator (`0.0.96.14.0.255`). The TOU period comes from
  `TouSchedule` (weekday peak `[AGGREGATOR_TOU_PEAK_START_HOUR, …END_HOUR)`, default 09–22; weekends
  off-peak), classified on the reading's own sim clock.

alongside convenience `kwh` / `energy_generated` / `energy_consumed` / `timestamp` / `signature`
fields read directly by the REST handler. The rate/demand/tariff registers are **additive** —
they never change the energy totals or the signed canonical string. The wire contract is pinned by
`tests/test_aggregator_bridge_dlms.py`. Note: only the bridge's **zone Redis Streams** carry this
full register set downstream; its InfluxDB/Kafka/settlement paths keep only energy (+ frequency).

### Optional PostGIS egress

When `POSTGIS_ENABLED=true`, the engine also batch-inserts each tick into the parent
`grid.meter_readings` PostGIS table via `asyncpg` (`persistence/reading_store.py`), upserting the
fleet into `grid.meters` on start. Same non-blocking, tick-dropping back-pressure as the Aggregator
emitter; exposed for replay/geo under `/api/v1/history`. Off by default.

## 4. Key Behaviors / Invariants

1. **DLMS/COSEM is the sole egress.** There is one telemetry path to the bridge: signed OBIS-coded
   JSON over REST (`protocol="dlms"` → `/v1/private-network/ingest`). No Rust extension, gRPC
   channel, or protobuf stubs — the legacy binary Protocol-v4 path was removed. Off by default
   (`AGGREGATOR_DLMS_ENABLED=false`).
2. **Sign at the source with Ed25519.** Every reading is signed by a per-meter `MeterKey` whose
   keypair is **deterministically derived** from `sha256("{secret}:{meter_id}")` (secret default
   `gridtokenx-sim`) — so the public key registered in Redis stays valid across process restarts
   without persisting key material.
3. **Signature canonical string must byte-match the bridge:** `f"{device_id}:{kwh}:{timestamp_ms}"`
   where `kwh` emulates Rust's `f64::to_string()` (`_rust_f64_str`, integral values drop `.0`) and
   `timestamp_ms` is epoch millis with **sub-second precision dropped** on both sides. Base58 over
   the raw signature bytes. Drift here = silent `4xx` rejection (not retried).
4. **Bridge needs its registry seeded first.** The emitter registers meter pubkeys (and, for
   settlement, meter→owner mappings) directly into the bridge's Redis on `start()`. Without the
   pubkey, signature verification fails; without the owner map, the bridge resolves `Uuid::nil`
   and skips settlement.
5. **Real-time back-pressure.** Egress is non-blocking: a whole tick's readings POST concurrently
   via `asyncio.gather` as one background task; if the prior batch is still in flight the current
   tick is **dropped, not queued**. Transport/5xx errors retry once with jittered backoff (never
   `4xx`); failures only bump `aggregator_emit_failed_total` and never propagate into the tick.
6. **Config is env-driven via `get_config()`.** All runtime behavior flows through the cached
   `pydantic-settings` singleton — never read `os.environ` in logic. Key setting:
   `GRID_TOPOLOGY=glm:<path-to-.glm>`. CLI flags override env by setting `os.environ` before config
   loads.
7. **Single process-global engine.** `core/app_state.engine` is the one mutable runtime object;
   routers stay thin and operate on it — there is no per-request state.
8. **Reading generation is CPU-bound, dispatched off the loop** via `asyncio.to_thread` to keep
   the event loop responsive.
9. **Default ports differ by deploy mode.** Local dev serves on **8082**; the combined Docker image
   serves on **8080**. Bridge egress in host-networked dev targets the bridge IoT gateway on
   **`:4030`** and Redis on **`:7010`** (note: host `:4010` is the IAM service, *not* the bridge);
   inside the docker network use `http://aggregator-bridge:4010` and `redis://redis:6379`.

## 5. Commands

Package manager is **uv**; run from `backend/`.

```bash
cd backend

# Run the REST API (http://localhost:8082, docs at /docs)
uv run app                                    # == uv run start; both → app:main

# Headless simulation loop (no server)
uv run cli --mode standalone --meters 20

# Validate the configured GLM topology (JSON summary, exit 1 if invalid)
uv run cli --mode validate-topology
uv run cli --mode validate-topology --grid-topology glm:<path>.glm

# Stream signed readings into the parent Aggregator Bridge (DLMS/COSEM egress;
# requires bridge + Redis reachable). Host-networked dev:
AGGREGATOR_DLMS_ENABLED=true \
AGGREGATOR_BRIDGE_URL=http://localhost:4030 \
REDIS_URL=redis://localhost:7010 \
uv run cli --mode standalone --meters 5

# Standalone egress driver script (alternative to the engine loop)
uv run python scripts/send_to_aggregator_bridge.py --meters 5 --interval 15
uv run python scripts/send_to_aggregator_bridge.py --once --onboard   # bind owners + 1 tick
uv run python scripts/send_to_aggregator_bridge.py --once --dry-run   # no network

# Tests — pytest.ini forces coverage on; disable for a quick run:
PYTEST_ADDOPTS=--no-cov uv run pytest -q tests/test_glm_core_topology.py
uv run pytest                                 # full suite with coverage
uv run pytest -k <name> --no-cov              # single test

# Lint / format
uv run black src tests
uv run isort src tests
uv run flake8 src tests
```

From the **superproject root** (Nushell `just`), convenience recipes wrap the egress run:

```bash
just auto-meter-send meters="5" interval="15"    # standalone egress into the bridge (:4030 / :7010)
just send-meter-reading meters="1" interval="15" # single-meter smoke burst
```

Docker (single combined image — Next.js UI via bun, Python backend via uv): entrypoint
`uv run start`, serves on **8080**.

## Further Reading (in this repo)

| File | Covers |
| :--- | :--- |
| `README.md` | Feature overview, quick start, API surface, config, project structure |
| `CLAUDE.md` | LLM working rules for this submodule (monorepo split, run commands, skills) |
| `backend/CLAUDE.md` | Deep dive: backend architecture, tick flow, Aggregator Bridge + PostGIS egress, conventions |
| `METER_PROTOCOL.md` | The meter telemetry / protocol reference |
| `AGENTS.md` | code-review-graph MCP tool usage for this repo |
| `Dockerfile` / `fly.toml` | Combined image build (bun UI + uv backend) and Fly deploy config |
| `backend/pyproject.toml` | Authoritative dependencies and uv entry-point scripts (`app`/`start`/`cli`) |
