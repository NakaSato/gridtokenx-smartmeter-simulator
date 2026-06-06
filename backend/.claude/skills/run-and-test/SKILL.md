---
name: run-and-test
description: Run, drive, and test the simulator end-to-end — the uv entry points (app/cli), server vs standalone vs validate-topology modes, the FastAPI lifespan/autostart, hot-swapping topology and telemetry sources at runtime, the pytest suite (coverage, markers), and the Docker image. Use when starting the simulator, reproducing a scenario, switching grids/telemetry, or figuring out how to run a specific test.
---

# Running & testing the simulator

Backend is **uv**-managed, Python 3.11+. All commands run from `backend/`. Entry points are
declared in `pyproject.toml [project.scripts]`: `app`/`start` → `app:main`, `cli` → `cli:main`.

## Run modes

```bash
# REST API server (uvicorn on 0.0.0.0:8082; Swagger at /docs)
uv run app                    # == uv run start

# Headless simulation loop, no HTTP server
uv run cli --mode standalone --meters 20

# Validate the configured topology — prints JSON summary(), exit 1 if invalid
uv run cli --mode validate-topology
uv run cli --mode validate-topology --grid-topology glm:<path>.glm

# cli --mode server also runs the API (port via --port, default 8082)
```

`cli.py` flags set `os.environ` **before** config loads, so they override `.env`:
`--meters` (NUM_METERS), `--grid-topology` (GRID_TOPOLOGY), `--port`, `--interval`,
`--base-gen-min/max`, `--base-cons-min/max`. Anything not exposed as a flag must go through
`.env` / env vars — config is read once via the cached `get_config()` singleton.

## How a run boots

- **API path** (`app.py::create_app` → `lifespan.py`): the lifespan builds the global
  `app_state.engine = SimulationEngine(grid_topology=...)`. If `AUTOSTART_SIMULATION` (default
  **true**) the loop starts immediately; otherwise the network initializes and the engine sits
  **paused** until `POST /api/v1/simulation/actions/start`. CORS is wide open (`allow_origins
  ["*"]`). `load_dotenv(override=True)` runs at import.
- **Standalone** (`cli.py::run_standalone`): builds the engine, `start()`s, sleeps until
  stopped. Same engine, no FastAPI.

The engine is a **process-global singleton** (`core/app_state.engine`). One simulation per
process; there is no multi-tenant/per-request state.

## Driving a scenario at runtime (no restart)

Everything below is live, via `/api/v1` (handlers in `routers/`):
- **Lifecycle**: `POST simulation/actions/{start,stop,pause,resume,step}`. `step` runs exactly
  one tick — the deterministic way to inspect one frame.
- **Environment**: `PATCH simulation/environment` with `{weather, grid_stress, topology}`.
  Setting `topology` **hot-swaps the GLM grid** (only `glm:<path>` accepted there) and rebuilds
  the meter fleet to match — the fast way to switch IEEE feeders / scenarios on the fly.
- **Fleet**: `meters_v1` (`POST/DELETE /meters`, `PUT /meters/count`), `grid_v1` (topology,
  telemetry, stats). `GET simulation/status` returns running/paused, sim clock, topology
  summary, and `last_tick` totals.

### Telemetry source & topology specs (env-driven)
Both use a `scheme:value` spec parsed at engine build:
- `GRID_TOPOLOGY=glm:<path.glm>` or `reference-grid:<folder>` — the grid model.
- `TELEMETRY_SOURCE=synthetic` (default) | `replay:<readings.csv>` | `reference-grid:<folder>`
  — drives meters from real data instead of synthetic models (see **meter-fleet-registry** and
  `docs/realtime-telemetry.md`).
- `METER_REGISTRY=<path .csv/.json>` or `reference-grid:<folder>` — pins real meters to buses.

## Testing

`pytest.ini` forces coverage on **and** `asyncio_mode = auto` (no `@pytest.mark.asyncio`
needed). Coverage to `htmlcov/` + `coverage.xml`; `--cov-fail-under=0` so coverage never fails
the run. **Disable coverage for fast local iteration** — it's the single biggest speedup:

```bash
PYTEST_ADDOPTS=--no-cov uv run pytest -q                       # whole suite, fast
PYTEST_ADDOPTS=--no-cov uv run pytest -q tests/test_glm_core_topology.py
uv run pytest -k <substr> --no-cov                             # one test
uv run pytest -m "not slow" --no-cov                           # skip slow
uv run pytest                                                  # full run WITH coverage report
```

Markers are declared in `pytest.ini` (`--strict-markers` — unknown markers error): `unit`,
`integration`, `slow`, `grid`, `crypto`, `api`, `e2e`, `vpp`, `market`, `phase1`–`phase5`.
Tests live in `tests/` (`test_glm_core_topology.py`, `test_telemetry_ingestion.py`,
`test_reference_grid_loader.py`, `test_reference_grid_sources.py`). Prefer building a small
topology + a few `SmartMeter`s and asserting on `engine.tick()` / source `poll()` output over
mocking.

Lint/format before committing:
```bash
uv run black src tests && uv run isort src tests && uv run flake8 src tests
```

## Docker (whole stack in one image)

The **root** `Dockerfile` (not under `backend/`) builds 2 stages: bun-built Next.js UI →
Python backend assembled with `uv`. Entrypoint `uv run start`, serves
on port **8080** (note: local dev uses **8082**), non-root `appuser`, healthcheck on `/health`.
Use it for a production-like all-in-one; use the two-process flow above for development.
