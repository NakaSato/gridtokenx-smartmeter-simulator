---
name: simulation-engine-dev
description: Develop the backend simulation — device models (PV/load/AMI), the per-tick feeder solver, reading generation, telemetry sources, and FastAPI routers. Use when adding or changing how meters generate readings, how the grid solver computes voltages/flows/losses, how real telemetry overrides synthetic models, or how a new measurement/field surfaces through the API. (For editing .glm topology files themselves, use glm-topology-authoring instead.)
---

# Developing the simulation backend

The simulator runs an async tick loop: each tick generates per-meter readings with Python
device models, then runs an approximate feeder solver over the grid to derive bus voltages,
line flows, losses, and congestion. This skill maps the data flow and the safe extension
points. All paths are under `src/smart_meter_simulator/`.

For grid-model file edits (`.glm` buses/lines/loads/PV) use the **glm-topology-authoring**
skill — that's a different parser concern. This skill is about the *Python simulation*.

## The tick data flow (read this first)

`core/engine.py` → `SimulationEngine.tick()` is the spine. One tick, in order:

1. **`_apply_telemetry(sim_time)`** — `telemetry_source.poll()` returns a frame of
   `{meter_id -> MeterTelemetry}`. For each matched meter it sets **one-shot** attributes
   `manual_override_cons / manual_override_gen / manual_override_reactive_kvar` and calls
   `meter.receive_frequency(...)`. Meters absent from the frame stay synthetic → partial
   coverage is a *hybrid* run.
2. **`reading_manager.generate_all(...)`** — `core/reading_manager.py`. Calls
   `meter.update_weather()` on every meter, then runs `_generate_python_loop` via
   **`asyncio.to_thread`** (reading generation is CPU-bound — keep it off the event loop).
   The loop reads each meter's override attrs, passes them to `generate_reading`, then
   **deletes the override attrs** (that's what makes them one-shot) and stores `last_reading`.
   It also looks up the meter's bus voltage from the *previous* tick (`bus_voltages` +
   `meter_to_bus`) and feeds it in as `grid_voltage_pu`.
3. **`grid.update_grid_state(meters, readings)`** — `core/grid_manager.py`. Buckets each
   reading's net load (kW) and reactive (kVAr) onto its bus, then solves.
4. `_summarize_tick` rolls totals into `last_tick_summary`; sim clock advances by `interval`.

So: **readings drive the solver; the solver's voltages feed the *next* tick's readings.** A
one-tick voltage lag is by design.

The engine is a process-global singleton — `core/app_state.engine`, created in `lifespan.py`.
Routers reach it via `Depends(get_engine)`; there is no per-request state.

## Where to make changes

### A new measurement field on a reading
1. Add the field to `EnergyReading` in `models/reading.py` (it's a pydantic model; mind the
   `ge=`/`le=` validators) and to `to_telemetry_payload()` if it should hit the API.
2. Populate it in `devices/ami.py::SmartMeter.generate_reading` — that's the single place a
   reading is constructed. Note the `round(...)` + `"key" in e_params` guarding pattern.
3. If it's a physics quantity, compute it in `core/meter_logic/electrical.py`
   (`calculate_electrical_params`) and gate it on the meter's measurement **channels**
   (the `"v"`/`"i"`/`"p"`/`"q" in channels` checks). Channels come from
   `METER_TYPE_CHANNELS` (`config/channels.py`) keyed by `MeterType`.

### Device model behavior (generation / consumption)
- **PV** — `devices/solar.py`. Real model is pvlib/PVWatts (`_get_pvlib_generation_kw`,
  gated by `cfg.pv_model_enabled`); falls back to `core/meter_logic/profiles.py::
  calculate_solar_generation`. Weather scales via `_WEATHER_FACTORS`. AR(1) noise via
  `self.last_noise` — preserve that smoothing if you touch it.
- **Load** — `devices/load.py`. Profile shape from `profiles.calculate_consumption`, then
  **ZIP voltage response** (`apply_zip_voltage_response`: Z∝V², I∝V, P constant), clamped to
  `min_load_kw`/`max_load_kw`. ZIP fractions come from config or per-meter `config` overrides.
- **Inverter/droop controls** live in `ami.py::generate_reading` (over-voltage curtailment
  above 1.05 pu) and `electrical.py::apply_droop_control` (frequency-watt, 50 mHz deadband).
  There is **no battery/EV/BESS model** — meters are load + optional PV only.

### The feeder solver
`core/grid_manager.py` has **two solvers, tried in order** inside `update_grid_state`:
1. **pandapower** (`_run_pandapower`) — full AC power flow, used only if `pandapower` is
   importable and a `pp_net` was built (`_build_pandapower_network` runs at
   `initialize_network`). Writes back `vm_pu`, line loading %, losses.
2. **DistFlow fallback** (`_run_distflow`) — pure-Python radial sweep over a `networkx`
   BFS tree rooted at the substation. Always available; pandapower is optional.

Both write the same `bus_voltages` / `line_flows` / `total_losses_kw` state. If you add a
metric, populate it in **both** paths or the result depends on whether pandapower is installed.
Line names must stay consistent between the networkx edge, `line_flows`, and the pandapower
`net.line.name` (see the comment in `_build_pandapower_network`) or write-back silently misses.

### Telemetry sources (drive meters from real data)
`core/telemetry_source.py`. Subclass `TelemetrySource`, implement `poll(sim_time) -> Frame`
(a `{meter_id -> MeterTelemetry}` dict), and register it in `build_telemetry_source` +
`parse_telemetry_spec`. Spec scheme mirrors topology: `TELEMETRY_SOURCE=replay:<csv>` /
`reference-grid:<folder>` / `synthetic` (default). Existing impls: `ReplaySource` (CSV,
hold-last-value), `ReferenceGridReplaySource` (CINELDI/MATPOWER `p_load.csv`/`q_load.csv`).
Meter ids must match the fleet — reference grids use `reference_meter_id(bus_id)`.

### A new API endpoint
`routers/` — `simulation_v1`, `meters_v1`, `grid_v1`, mounted under `/api/v1` by `api_v1.py`.
Handlers stay thin: `engine = Depends(get_engine)`, mutate/read engine state, return a dict.
`simulation_v1.py::update_environment` is the model for live reconfiguration (weather,
grid_stress, hot-swapping topology). Keep business logic in the engine/managers, not handlers.

## Conventions specific to this code

- `from __future__ import annotations` at module top. `black`/`isort` (profile black, len 88).
- Read config only through `get_config()` (`config/settings.py`, cached singleton). Per-meter
  `config` dict values override global config where the device models check
  `config.get(key, get_config().key)` — preserve that precedence.
- Reading generation must stay non-blocking — it runs under `asyncio.to_thread`. Don't add
  `await` into the device-model call path; don't do blocking I/O on the event loop.
- Overrides are one-shot attrs consumed-and-deleted each tick. Don't persist them on the meter.
- Keep new grid parsers/sources emitting the neutral shapes (`GridTopology`, `MeterTelemetry`,
  `EnergyReading`) rather than ad-hoc dicts.

## Verify a change

```bash
# Fast targeted tests (pytest.ini forces coverage; disable for speed)
PYTEST_ADDOPTS=--no-cov uv run pytest -q tests/test_telemetry_ingestion.py
uv run pytest -k <name> --no-cov

# Smoke the whole loop headless, then eyeball the tick summary / grid stats
uv run cli --mode standalone --meters 20
uv run cli --mode validate-topology        # confirms topology still loads

# Lint
uv run black src tests && uv run isort src tests && uv run flake8 src tests
```

Tests live in `tests/` (e.g. `test_glm_core_topology.py`, `test_telemetry_ingestion.py`,
`test_reference_grid_sources.py`). Add new device/solver/source tests there; prefer
constructing a small `GridTopology` + a handful of `SmartMeter`s and asserting on
`engine.tick()` output over mocking.
