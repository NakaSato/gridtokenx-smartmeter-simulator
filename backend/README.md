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
