# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

> Scope: this is the **backend** of the GridTokenX Smart Meter Simulator (a standalone
> sub-project, separate from the parent `gridtokenx-coresystem` Rust monorepo whose
> `CLAUDE.md` does not apply here). The Next.js frontend lives in `../frontend` and has its
> own `CLAUDE.md`.

## What this is

A GridLAB-D **GLM-backed** smart meter / AMI grid simulator. It parses a `.glm` topology file
into a native `GridTopology`, generates per-meter energy readings with Python device models
(PV via `pvlib`, ZIP loads), and runs an exact AC power flow (pandapower, backward/forward
sweep) each tick — with an approximate DistFlow fallback if it fails to converge —
to update bus voltages, line flows, losses, and congestion. Exposed as a FastAPI REST service
(default port **8082**). Part of the larger GridTokenX ecosystem — readings are ingested into
the parent Oracle Bridge over the standard DLMS/COSEM (IEC 62056) REST contract.

Package manager is **uv**. Python 3.11+.

## Commands

```bash
# Run the REST API (http://localhost:8082, docs at /docs)
uv run app                  # == uv run start; both -> app:main

# Run a headless simulation loop (no server)
uv run cli --mode standalone --meters 80

# Validate the configured GLM topology (prints JSON summary, exit 1 if invalid)
uv run cli --mode validate-topology
uv run cli --mode validate-topology --grid-topology glm:<path>.glm

# Tests — pytest.ini forces coverage on; disable it for a quick run:
PYTEST_ADDOPTS=--no-cov uv run pytest -q tests/test_glm_core_topology.py
uv run pytest                       # full suite with coverage (htmlcov/, coverage.xml)
uv run pytest -k <name> --no-cov    # single test

# Lint / format
uv run black src tests
uv run isort src tests
uv run flake8 src tests
```

CLI flags override env vars by setting `os.environ` before config loads (`--interval`,
`--base-gen-min/max`, `--base-cons-min/max`, `--port`, `--meters`, `--grid-topology`).

## Configuration

All runtime behavior is env-driven via `pydantic-settings`. Copy `.env.example` to `.env`.
Access config through the cached singleton `get_config()` (`config/settings.py`) — never read
`os.environ` directly in logic. The key setting is `GRID_TOPOLOGY=glm:<path-to-.glm>`; the
`glm:` prefix is the topology spec scheme parsed by `topology_factory`. Other env groups:
meter-type mix ratios (solar prosumer / grid consumer / hybrid), PV/`pvlib` params, ZIP load
fractions, line impedance defaults, weather weights, geo coords.

## Architecture

Request/tick flow:

```
app.py (create_app) → lifespan.py → app_state.engine = SimulationEngine (global singleton)
SimulationEngine.tick():
  ReadingManager.generate_all()   # device models, run in a thread via asyncio.to_thread
  GridManager.update_grid_state() # exact pandapower AC power flow (bfsw), DistFlow fallback
```

- **`core/engine.py`** — `SimulationEngine` owns the meter list, grid, reading manager, and the
  async tick loop. State (running/paused, sim clock, weather, stress multiplier) lives here.
  It is the single mutable runtime object; routers reach it via `core/app_state.engine`. Each tick
  `_update_grid_frequency` derives a system frequency from the supply/demand imbalance
  (`FREQ_*` config: nominal + `FREQ_FULL_SWING_HZ` × the gen−load ratio, clamped to ±1) and feeds it
  to the meters, where `electrical.apply_droop_control` throttles export under over-frequency —
  closing the **frequency-watt** primary-response loop alongside grid_manager's volt-watt. One-tick
  governor lag; external telemetry frequency (re-applied first each tick) stays authoritative.
  `frequency_hz` is in the tick summary.
- **`core/topology.py`** — `GridTopology` dataclass (buses/lines/loads/pvs) — the neutral grid
  model everything downstream consumes. `to_networkx()` / `to_legacy_net()` adapt it.
- **`core/topology_factory.py`** — resolves a `glm:<path>` spec into a `GridTopology`.
- **`adapters/`** — GLM ingestion only: `glm_converter.py` (`GLMParser` tokenizer) →
  `glm_topology_loader.py` (maps GLM objects to `GridBus/GridLine/GridLoad/GridPV`, pulls line
  impedance from `line_configuration` or falls back to `LINE_*` env defaults). No external
  power-flow solver is run by the loader. To author, edit, or validate `.glm` topology files,
  use the **`glm-topology-authoring`** skill (`.claude/skills/glm-topology-authoring/`) — it
  documents exactly which GLM object types/fields this subset parser reads.
- **`core/grid_manager.py`** — maps meters to buses and runs the power flow each tick (bus
  voltages, line flows, losses, congestion). Builds a pandapower net and solves it with the
  backward/forward sweep algorithm (`bfsw`, right for radial LV feeders; NR/DC seed as second
  try). On non-convergence (e.g. voltage collapse under overload) falls back to an approximate
  DistFlow sweep over the networkx graph. 3-phase buses model at line-to-line base (L-N ×√3),
  line R/X/ampacity from `LINE_*` config when the GLM omits them; both solvers share one length
  converter (`_convert_length_km`), so a unitless GLM `length` resolves to `LINE_LENGTH_UNIT`
  (default ft) consistently. Models IEEE 1547 **volt-watt** PV curtailment (`PV_VOLTWATT_*`): an
  exporting bus above `v_start` (pu) throttles inverter export to zero at `v_end`, ratcheted to a
  stable fixed point each tick — caps overvoltage backfeed; curtailed kW is in the grid summary.
  When `TRANSFORMER_ENABLED` (default), models a real MV/LV distribution transformer at the feeder
  head: an MV (`TRANSFORMER_MV_KV`, 22 kV) external-grid slack → a transformer (`TRANSFORMER_SN_MVA`
  /`VK_PERCENT`/`VKR_PERCENT`/`PFE_KW`/`I0_PERCENT`) → the substation LV bus. The slack moves
  upstream, so the LV bus voltage sags under load and rises on PV backfeed across the transformer
  impedance instead of being a stiff 1.0 pu source; transformer loss + loading% are in the summary.
  With `TRANSFORMER_OLTC_ENABLED` the transformer also runs an **on-load tap changer**: before the
  volt-watt pass it steps the HV-side tap (`TRANSFORMER_TAP_STEP_PERCENT`, bounded `±TRANSFORMER_TAP_MAX`)
  to hold the LV head at `TRANSFORMER_OLTC_V_TARGET` within `TRANSFORMER_OLTC_DEADBAND`, re-solving
  until in-band or saturated — so the tap absorbs bulk voltage and curtailment only handles residual
  local overvoltage (`transformer_tap_pos` in the summary). Note: the `bfsw` solver in pandapower 3.3
  errors on a non-neutral tap, so a tapped solve transparently falls through to NR; the transformer is
  created with `tap_changer_type="Ratio"` (pp 3.x ignores the tap otherwise).
  Supports **fault/outage injection** for N-1 contingency / resilience study: faulted lines and
  buses (`faulted_lines`/`faulted_buses`) are flagged out of service before each solve (and removed
  from the distflow fallback's graph), so the radial feeder reroutes or **islands**. Buses cut off
  from the substation slack are de-energized (voltage 0) and reported in `islanded_buses`, recomputed
  every tick (`fault_count` + `islanded_bus_count` in the tick summary). Drive it via the
  `apply_fault`/`clear_fault`/`clear_all_faults`/`fault_status` methods, exposed over
  `/api/v1/simulation/faults` (GET list / POST trip / DELETE clear). A topology hot-swap clears all
  faults (old element names no longer valid). Pinned by `tests/test_fault_injection.py`.
- **`core/reading_manager.py`** + **`core/meter_logic/`** — reading generation. `electrical.py`
  applies ZIP voltage sensitivity and frequency-watt droop; `profiles.py` load shapes.
- **`devices/`** — `ami.py` (`SmartMeter`), `solar.py` (PV), `load.py`. The simulator models
  meters + solar PV only; there is no battery/EV/BESS device model.
- **`meter_generator.py`** — builds the meter population (type mix, PV-per-bus) from topology.
- **`routers/`** — FastAPI v1 under `/api/v1`: `simulation_v1`, `meters_v1`, `grid_v1`,
  aggregated by `api_v1.py`. Handlers stay thin and operate on `app_state.engine`.
- **`core/metrics.py`** — Prometheus metrics (`ACTIVE_METERS`, `SIMULATION_TICK_TIME`).

### Oracle Bridge egress (`transport/oracle_bridge.py`)

The simulator's **sole egress** to the parent Oracle Bridge is the standard
**DLMS/COSEM (IEC 62056)** REST path. Set `ORACLE_DLMS_ENABLED=true` and the engine
ships each tick's readings to `ORACLE_BRIDGE_URL` (`/v1/private-network/ingest`,
`protocol="dlms"`) via `OracleBridgeEmitter`: one signed OBIS-coded JSON POST per
meter, all fired concurrently with `asyncio.gather`, non-blocking, drops a tick if
the prior batch is still in flight. On start it registers each meter's Ed25519
public key in the bridge's Redis device registry (`REDIS_URL`) so
`verify_rest_signature` can authenticate telemetry, probes the bridge `/health`
(warns if unreachable), and — when `ORACLE_METER_OWNER_MAP` (JSON `{meter_id:
user_id}`) is set — seeds the bridge's meter→owner map so telemetry resolves to a
`user_id` for settlement (without it the bridge resolves `Uuid::nil` and skips
settlement). With `ORACLE_IAM_ONBOARD_ENABLED` the engine instead resolves owners
live via the IAM gateway (`onboard_fleet` → `onboard_meter`: register → verify →
login). Verification uses IAM's dev `verify_<email>` token (no email round-trip) to
activate the deterministic sim account so login succeeds on every run and returns
the `user_id` — making re-runs idempotent without depending on Redis. (Ownership
only: there is no IAM endpoint to claim a meter / register its on-chain PDA — that
path is an Anchor `registry` instruction via Chain Bridge, out of scope here.) As
a safety net, for any meter IAM can't resolve this run it falls back to
`read_meter_owners_redis`, reading back any owner a prior run already seeded in the
bridge registry. Meters still unresolved (no IAM user_id, none in Redis) are logged
with an actionable warning. `send_reading` retries once with
jittered backoff on transport errors
/ 5xx (never on 4xx); failed sends increment the `oracle_emit_failed_total`
Prometheus counter. Default is off.

Per-reading OBIS encoding + the `device_id:kwh:timestamp_ms` Ed25519 signature
contract live in `_build_obis_payload` / `MeterKey`; the payload carries active
import/export energy (Wh) plus optional voltage, current, frequency, power factor
(`1.1.13.7.0.255`), and reactive energy (`1.1.3.8.0.255`/`1.1.4.8.0.255`, varh
derived from `reactive_power_kvar` over the interval). The wire contract is pinned
by `tests/test_oracle_bridge_dlms.py`. No Rust extension, gRPC channel, or protobuf
stubs are involved — the legacy binary Protocol-v4 (UTT-S+) gRPC path and its
`src/rust_sim` crate were removed.

### PostGIS persistence (`persistence/reading_store.py`)

Optional egress mirroring the Oracle emitter's non-blocking shape. Set
`POSTGIS_ENABLED=true` and the engine batch-inserts each tick's readings into the
parent **`grid.meter_readings`** table (PostGIS asset schema under
`database/migrations/`) via `ReadingStore`, so a run is queryable for replay,
history, and geo lookups. On start it connects an `asyncpg` pool to `POSTGIS_URL`
and upserts the meter population into **`grid.meters`** (location from each meter's
config `latitude`/`longitude`, falling back to `BASE_LATITUDE`/`BASE_LONGITUDE`) so
the reading foreign key resolves. Each tick `persist()` fires a background
`executemany` and **drops the tick if the prior batch is still in flight** (same
back-pressure as the Oracle emitter); `POSTGIS_PERSIST_EVERY` thins the cadence.
Numeric params are cast `::float8` in SQL so plain floats insert into the `NUMERIC`
columns without `Decimal`. All failures are logged, increment
`postgis_persist_failed_total`, and never propagate into the tick; init failure
(DB down / schema missing) disables persistence for the run. Requires migrations
`002_postgis_simple.sql` + `004_reading_replay_columns.sql`. Default is off.

Replay/geo is exposed under `/api/v1/history` (`routers/history_v1.py`):
`GET /history/readings` (filter by `meter_id`/`start`/`end`, newest first),
`GET /history/network/geojson` and `/history/network/stats` (the geo asset network
via the `grid.export_network_geojson` / `grid.get_network_stats` SQL functions).
All return 503 when persistence is off. The store's wire shape is pinned by
`tests/test_reading_store.py` (no live DB — fake asyncpg pool).

## Conventions

- `from __future__ import annotations` at the top of modules; `black`/`isort` profile = black,
  line length 88.
- Config flows through `get_config()`; topology flows as a `GridTopology` instance — keep new
  parsers emitting that shape rather than ad-hoc dicts.
- Reading generation is CPU-bound and is dispatched with `asyncio.to_thread`; keep it
  non-blocking on the event loop.
- The engine is a process-global singleton (`app_state.engine`); there is no per-request state.
