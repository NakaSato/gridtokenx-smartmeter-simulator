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
(default port **8082**). Part of the larger GridTokenX ecosystem — `proto/oracle.proto` defines
the Protocol v4 (UTT) telemetry contract for ingesting readings into the Oracle Bridge.

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
- **`core/reading_manager.py`** + **`core/meter_logic/`** — reading generation. `electrical.py`
  applies ZIP voltage sensitivity and frequency-watt droop; `profiles.py` load shapes.
- **`devices/`** — `ami.py` (`SmartMeter`), `solar.py` (PV), `load.py`. The simulator models
  meters + solar PV only; there is no battery/EV/BESS device model.
- **`meter_generator.py`** — builds the meter population (type mix, PV-per-bus) from topology.
- **`routers/`** — FastAPI v1 under `/api/v1`: `simulation_v1`, `meters_v1`, `grid_v1`,
  aggregated by `api_v1.py`. Handlers stay thin and operate on `app_state.engine`.
- **`core/metrics.py`** — Prometheus metrics (`ACTIVE_METERS`, `SIMULATION_TICK_TIME`).

### Rust extension (`src/rust_sim/`)

`gridtokenx_sim` is a PyO3 crate — **Protocol-v4 (UTT-S+) framing + crypto only**
(TLV → AES-256-GCM → CRC-32 → Ed25519); reading *generation* stays in the Python path.
`ReadingManager` still runs the pure-Python loop, so the crate is **off the default path**.

It is wired as an **opt-in egress accelerator**: set `ORACLE_GRPC_ENABLED=true` and the
engine ships each tick's readings to the Oracle Bridge `BulkRawIngest` gRPC endpoint via
`transport/oracle_grpc.py` (`OracleGrpcEmitter`, non-blocking, drops a tick if the prior
send is still in flight). Default is off; with it off the crate is never imported, so a
missing `.so` is harmless (the emitter logs once and degrades).

Build the extension natively with:
```bash
cd src/rust_sim
RUSTFLAGS="-C link-arg=-undefined -C link-arg=dynamic_lookup" cargo build --release
cp target/release/libgridtokenx_sim.dylib ../gridtokenx_sim.so   # .so on Linux
```
The `dynamic_lookup` flags are **required on macOS** (PyO3 `extension-module` leaves Python
symbols undefined for runtime resolution; Linux/Docker handles this automatically).
`maturin develop` from `src/rust_sim/` also works (maturin is not in `pyproject.toml`).
gRPC stubs are generated from `proto/oracle.proto` into `transport/grpc_gen/` (committed).

## Conventions

- `from __future__ import annotations` at the top of modules; `black`/`isort` profile = black,
  line length 88.
- Config flows through `get_config()`; topology flows as a `GridTopology` instance — keep new
  parsers emitting that shape rather than ad-hoc dicts.
- Reading generation is CPU-bound and is dispatched with `asyncio.to_thread`; keep it
  non-blocking on the event loop.
- The engine is a process-global singleton (`app_state.engine`); there is no per-request state.
