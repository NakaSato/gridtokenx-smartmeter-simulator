# Real telemetry ingestion — synthetic simulator → digital twin

This document describes how to drive the simulator from **real measured meter data**
instead of (or alongside) the synthetic device models, and the registry that pins real
meters to physical buses.

## Why this works without an engine rewrite

The synthetic pipeline funnels every meter through one call:

```
SmartMeter.generate_reading(override_gen=..., override_cons=...)   # devices/ami.py:63
```

When `override_gen` / `override_cons` are supplied, the synthetic load/solar models are
bypassed and the meter emits exactly those values (`ami.py:80-91`). The grid solver then
computes bus voltages, line flows, losses and congestion **from those real injections**
(`grid_manager.update_grid_state`). So feeding real data is a matter of supplying per-meter
overrides each tick — not changing the physics.

## The three levels

| Level | What it gives you | Status |
|-------|-------------------|--------|
| **1. Replay / live injection** | Per-meter gen/cons come from real measurements; grid state computed from them. | **Implemented** (`core/telemetry_source.py`) |
| **2. Identity & time alignment** | Real meters pinned to real buses; clock driven by data; staleness/gap handling. | **Registry implemented** (`meter_registry.py`); hold-last-value in replay source |
| **3. State estimation (true twin)** | Reconcile measured vs computed voltages; flag bad data; estimate unmeasured buses. | Not implemented — see "Next" |

## Components added

### Meter registry — `meter_registry.py`
Maps real meters to physical buses. CSV or JSON.

```csv
meter_id,bus,meter_type,has_solar,solar_capacity_kw,phase
MTR-0001,node_2,solar_prosumer,true,8.0,A
MTR-0002,node_2,grid_consumer,false,0,B
```

`bus` must match a bus name in the active GLM topology. `load_meter_registry(path)` returns
`MeterRegistryEntry` objects; `build_meter_configs(entries, topology)` turns them into the
same config shape `MeterGenerator` emits, with `bus_name`/`bus_idx` set so the grid mapper
pins each meter to its real bus.

Set `METER_REGISTRY=path/to/registry.csv` to build the fleet from the registry instead of
the random `MeterGenerator`.

### Telemetry source — `core/telemetry_source.py`
A `TelemetrySource` supplies `{meter_id -> MeterTelemetry}` each tick.

- `SyntheticSource` — returns nothing; meters fall back to synthetic models (default).
- `ReplaySource` — reads a CSV of timestamped readings and replays them, holding the
  last value for sim-times past the latest sample (hold-last-value alignment).

Spec scheme, mirroring `GRID_TOPOLOGY=glm:`:

```
TELEMETRY_SOURCE=synthetic                 # default, unchanged behavior
TELEMETRY_SOURCE=replay:data/telemetry.csv # replay a CSV
```

Replay CSV columns (energy in kWh per interval **or** power in kW; `timestamp` optional):

```csv
meter_id,timestamp,energy_consumed,energy_generated
MTR-0001,2026-06-05T08:00:00+00:00,0.18,0.05
MTR-0002,2026-06-05T08:00:00+00:00,0.22,0.0
```

### Engine wiring — `core/engine.py`
- `__init__` builds `self.telemetry_source` from `TELEMETRY_SOURCE` and, when
  `METER_REGISTRY` is set, builds the meter fleet from the registry.
- `tick()` calls `_apply_telemetry()` before reading generation, which sets
  `manual_override_gen/cons` (and frequency) on matched meters. Unmatched meters stay
  synthetic — so partial real coverage is a **hybrid** run automatically.

## Hybrid behavior

A meter present in the telemetry frame is real; a meter absent from it is synthetic. This is
the natural path when real data covers only part of the feeder.

## Next — Level 3 (state estimation)

Today the flow is one-way: injections → solver → voltages. A true twin closes the loop:
feed measured voltages/flows as observations, run weighted-least-squares state estimation
(pandapower has `estimation`), compute residuals to flag bad data / topology errors, and
estimate unmeasured buses. That is genuinely new code, not a seam — the registry + telemetry
source built here are the prerequisites for it.
