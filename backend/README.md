# GLM Grid Model Smart Meter Simulator

Backend simulator for smart meter readings on one GridLAB-D GLM topology model.

The simulator loads `GRID_TOPOLOGY=glm:<path>` into a native `GridTopology`, reads the per-node GridLAB-D inverter/solar objects in the GLM, uses the GLM PV capacity for each node meter, models PV output with `pvlib`, applies voltage-sensitive ZIP load behavior, and updates line flows, voltage drop, losses, and congestion with a distance/impedance-aware feeder solver.

## Quick Start

```bash
# Validate the configured GLM topology
uv run cli --mode validate-topology

# Run the REST API
uv run app

# Run a local standalone simulator loop
uv run cli --mode standalone --meters 80
```

API docs are available at `http://localhost:8082/docs` when the server is running.

## Documentation

See [`docs/README.md`](docs/README.md) for the full index — modeling equations,
the data-pipeline methodology, the model usage/configuration guide, real-telemetry
replay, the academic feature report, and the BibTeX bibliography.

## Configuration

The essential settings are:

```bash
SIMULATION_INTERVAL=15
NUM_METERS=80
GRID_TOPOLOGY=glm:src/smart_meter_simulator/data/grids/grid_bus_network.glm
PV_MODEL_ENABLED=true
PV_ON_EVERY_BUS=true
BUS_PV_CAPACITY_MIN_KW=10.0
BUS_PV_CAPACITY_MAX_KW=10.0
ZIP_IMPEDANCE_FRACTION=0.20
ZIP_CURRENT_FRACTION=0.30
ZIP_POWER_FRACTION=0.50
LINE_LENGTH_UNIT=ft
LINE_RESISTANCE_OHM_PER_KM=0.642
LINE_REACTANCE_OHM_PER_KM=0.083
```

See `.env.example` for meter mix, weather, solar, and load bounds.

### Deterministic / reproducible runs

```bash
RANDOM_SEED=42                              # fleet + all noise streams
SIMULATION_START_TIME=2026-06-10T08:00:00+00:00   # pin the sim clock (optional)
```

`RANDOM_SEED` seeds both the meter fleet generation (ids, serials, base loads)
and every meter's noise stream. Each meter draws from its **own** stream
(`Random(seed ⊕ sha256(meter_id))`), so adding or removing a meter does not
shift any other meter's readings. Same seed → identical fleet and identical
per-tick noise.

Reading values also depend on the **wall-clock time-of-day** (PV and load
curves). For byte-identical replay across days, also pin `SIMULATION_START_TIME`
(ISO-8601). Unset, the sim clock starts at today 08:00 UTC. Network retry
backoff jitter (`transport/`) is intentionally left unseeded — it is timing
only and does not affect telemetry. Pinned by `tests/test_determinism.py`.

When a GLM line references a `line_configuration` with direct impedance fields
such as `z11`, `z22`, `z33`, `resistance_ohm_per_km`, or
`reactance_ohm_per_km`, those values feed the simulator line model. If the GLM
only provides line length, the `LINE_*` defaults above are used.

## API Surface

- `GET /api/v1/quality/health`
- `GET /api/v1/simulation/status`
- `POST /api/v1/simulation/actions/start`
- `POST /api/v1/simulation/actions/stop`
- `POST /api/v1/simulation/actions/pause`
- `POST /api/v1/simulation/actions/resume`
- `POST /api/v1/simulation/actions/step`
- `PATCH /api/v1/simulation/environment`
- `GET /api/v1/simulation/mode`
- `PUT /api/v1/simulation/mode`
- `GET /api/v1/grid/status`
- `GET /api/v1/grid/topology`
- `GET /api/v1/grid/telemetry`
- `GET /api/v1/grid/stats`
- `GET /api/v1/meters`
- `POST /api/v1/meters`
- `GET /api/v1/meters/{meter_id}`
- `PATCH /api/v1/meters/{meter_id}`
- `DELETE /api/v1/meters/{meter_id}`
- `DELETE /api/v1/meters`
- `GET /api/v1/meters/{meter_id}/readings`
- `POST /api/v1/meters/{meter_id}/readings/override`
- `PUT /api/v1/meters/count`

## Project Shape

```text
src/smart_meter_simulator/
  adapters/       GLM parser and topology loader
  config/         simulator settings and enums
  core/           engine, topology model, DistFlow grid manager, reading manager
  data/grids/     reference GLM topology
  devices/        meter, load, solar (PV) models
  models/         reading model
  routers/        focused REST API
  utils/          local helpers
```

## Tests

```bash
PYTEST_ADDOPTS=--no-cov uv run pytest -q tests/test_glm_core_topology.py
```
