---
name: meter-fleet-registry
description: Build and control the meter population — MeterGenerator (synthetic fleets, type-mix ratios, PV-per-bus, spreading meters across topology buses) and the meter registry (pinning real meters by id to physical buses for telemetry-driven runs). Use when changing how meters are created, how many there are, how meter types/solar are assigned, how meters map to buses, or wiring a CSV/JSON registry.
---

# Meter fleet generation & registry

Two ways a `SmartMeter` fleet is built, both producing **config dicts** consumed by
`SmartMeter(config)` (`devices/ami.py`). Which one runs is decided in `core/engine.py`'s
constructor, in this precedence:

1. `meters=` passed in explicitly → used as-is.
2. **`METER_REGISTRY` set** → `meter_registry.load_meter_registry` + `build_meter_configs`
   (real meters pinned to buses).
3. else → **`MeterGenerator`** (`meter_generator.py`): `generate_ieee_meters` when a topology
   with buses exists, else `generate_meters`.

## Synthetic generation — `meter_generator.py`

- **`generate_meters()`** — flat fleet by **type-mix ratios** from config
  (`solar_prosumer_ratio`, `grid_consumer_ratio`, `hybrid_prosumer_ratio`). Rounding remainder
  is added to the first type (`_calculate_meter_counts`). No bus awareness.
- **`generate_ieee_meters(num_nodes, target_meters, pv_on_every_bus, node_ids,
  pv_capacity_kw_by_node)`** — topology-aware, the default for GLM runs. Key behaviors:
  - Always returns **exactly `target_meters`** meters (unless `pv_on_every_bus`). When buses >
    meters, meters are **spread across the bus index range** (`int(offset*num_nodes/
    target_meters)`) — it does *not* silently make one meter per bus.
  - `pv_on_every_bus=True` flips control: **one solar meter per bus**, count driven by topology,
    PV capacity per node from `pv_capacity_kw_by_node` (falls back to
    `bus_pv_capacity_min/max_kw`).
  - Otherwise types are randomly weighted 70% consumer / 20% solar / 10% hybrid.
  - Each config is tagged with `bus_idx`, `node_id`, `bus_name` — **this is how
    `GridManager._map_meters_to_topology_buses` pins a meter to a bus.** Preserve these keys or
    bus mapping falls back to enumeration order.
- **`_create_meter_config(...)`** is the single builder both paths funnel through. It sets
  identity (`meter_id` = provided or `uuid4`, `serial_number`, `logical_device_name`,
  `manufacturer_id`), base gen/cons/solar-efficiency randomized within config bounds, and solar
  fields. **Solar assignment rule**: explicit `has_solar` in location_data wins; else
  SOLAR/HYBRID prosumer types get `has_solar=True`, `solar_capacity 5–15 kW`; else no solar.
  `create_meter_config(...)` (no underscore) is the public entry the registry reuses.

## Registry — `meter_registry.py` (pin real meters to buses)

The identity layer that turns a random synthetic fleet into a model of a **known physical
fleet** — prerequisite for telemetry-driven runs (`core/telemetry_source.py`,
`docs/realtime-telemetry.md`). Set `METER_REGISTRY=<path>` (`.csv`/`.json`) or
`reference-grid:<folder>`.

- **`MeterRegistryEntry`** — one real meter: `meter_id`, `bus` (required), `meter_type`
  (default `grid_consumer`), `has_solar`, `solar_capacity_kw`, `phase`, lat/lon, `serial_number`.
  `from_mapping` is lenient: accepts `meter_id`/`meter_serial`, `bus`/`bus_name`/`node_id`;
  infers `has_solar` from a positive capacity; raises if `meter_id` or `bus` is missing.
- **`build_meter_configs(entries, topology)`** — resolves each entry's `bus` **name → index**
  in `topology.buses` and emits configs via `MeterGenerator.create_meter_config`, so registry
  meters reuse the same defaulting/physics as synthetic ones. **Unknown bus names leave
  `bus_idx` unset** → the grid mapper falls back to enumeration order (a silent placement bug;
  validate bus names against the active topology first).

CSV example (header names are flexible per `from_mapping`):
```csv
meter_id,bus,meter_type,has_solar,solar_capacity_kw,phase
MTR-0001,node_2,solar_prosumer,true,8.0,A
MTR-0002,node_2,grid_consumer,false,0,B
```
JSON: a list, or `{"meters": [...]}`.

`reference-grid:<folder>` registries are derived from the grid's load buses via
`reference_grid_loader.load_reference_grid_load_buses` — meter ids follow
`reference_meter_id(bus_id)` so they line up with `ReferenceGridReplaySource` telemetry.

## Where the fleet flows next

`engine.meters` → `GridManager.initialize_network` maps them to buses (`bus_name`/`node_id`
first, then `bus_idx`, then offset) → each tick `ReadingManager` calls
`SmartMeter.generate_reading`. So a meter's `config` keys are the contract between fleet
construction, **bus mapping**, and the device models (which read per-meter overrides like
`zip_*_fraction`, `solar_capacity` from the same dict). When adding a fleet attribute, thread
it through `_create_meter_config` and consume it in the device model — don't special-case it in
the engine.

## Verify

```bash
PYTEST_ADDOPTS=--no-cov uv run pytest -q tests/test_reference_grid_loader.py
uv run cli --mode standalone --meters 20      # confirm fleet size / mapping in the logs
```
For registry/mapping changes, assert on `GridManager.meter_to_bus` after
`initialize_network`, and check `mapped_meters` in `get_topology_summary()`.
