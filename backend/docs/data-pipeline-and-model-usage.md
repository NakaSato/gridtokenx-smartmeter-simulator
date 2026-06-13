# Data Pipeline and Model Usage

**How data flows into the models each tick, and how to drive / extend the models.**

> Companion to [`modeling-equations.md`](modeling-equations.md) (the math) and
> [`references.bib`](references.bib) (citations). This doc is the *operational*
> view: what data enters each model, in what order, and how an engineer runs or
> changes them. All paths are into `backend/src/smart_meter_simulator/`. Real-telemetry replay
(data source 2 in §3) has its own guide: [`realtime-telemetry.md`](realtime-telemetry.md).
Doc index: [`README.md`](README.md).

---

## 1. End-to-end pipeline

One tick of `SimulationEngine.tick()` (`core/engine.py:219`) runs this chain:

```
                        ┌─────────────────────────────────────────────┐
   .glm topology  ──►   │ topology_factory → GridTopology (buses,      │   (once, at startup)
   (GRID_TOPOLOGY)      │ lines, loads, PV)  → GridManager network     │
                        └─────────────────────────────────────────────┘
                                          │
  ┌───────────────────────────── per tick k ──────────────────────────────┐
  │                                                                        │
  │  1. _apply_telemetry(t)        real frames override matched meters     │
  │         engine.py:248          (cons/gen/reactive/freq), one-shot      │
  │                                                                        │
  │  2. reading_manager.generate_all()   reading_manager.py:15             │
  │       └─ per meter (in a thread, asyncio.to_thread):                   │
  │            grid_voltage_pu ← bus_voltages[meter_to_bus[id]]  (tick k-1)│
  │            meter.generate_reading(...)        devices/ami.py:66        │
  │              a. PV gen      solar.get_generation_kw   §2 equations     │
  │              b. load        load.get_consumption_kw(V_pu)  ZIP §3.2    │
  │              c. droop       electrical.apply_droop_control(f)  §5.2    │
  │              d. battery     battery.dispatch(gen-cons)  §4 (synth only)│
  │              e. V/I/Q/PF    electrical.calculate_electrical_params §11 │
  │            → EnergyReading                                             │
  │                                                                        │
  │  3. grid.update_grid_state(meters, readings)   grid_manager.py:292     │
  │       aggregate readings → bus P,Q → AC power flow (§6),               │
  │       volt-VAR (§7.1), volt-watt (§7.2), OLTC (§8) → bus_voltages,     │
  │       line flows, losses                                               │
  │                                                                        │
  │  4. _update_grid_frequency(readings)   engine.py:288  → f_{k+1}  §5.1  │
  │                                                                        │
  │  5. egress (non-blocking):                                            │
  │       aggregator_emitter.emit(readings)   DLMS/COSEM POST   §11        │
  │       reading_store.persist(readings)     PostGIS insert              │
  └────────────────────────────────────────────────────────────────────────┘
```

**Key coupling — the one-tick voltage feedback.** Step 2 reads
`bus_voltages` computed by step 3 of the **previous** tick
(`reading_manager.py:50`–`54`): the ZIP load (§3.2) responds to last tick's
voltage, this tick's load sets this tick's voltage. Frequency is the same
one-tick lag (`engine.py:283`). This is deliberate (a governor/feedback delay),
not a bug.

---

## 2. Data entering each model

| Model | Inputs (where from) | Output | Eq |
| --- | --- | --- | --- |
| **PV** `solar.py` | timestamp, weather mode, lat/lon + PV config, `solar_capacity` | `gen_kw` | §2 |
| **Load** `load.py` | timestamp, meter type, `base_consumption`, **`grid_voltage_pu`** (prev tick) | `cons_kw` | §3 |
| **Droop** `electrical.py` | `gen, cons`, `current_frequency` (prev tick / telemetry) | throttled `gen` | §5.2 |
| **Battery** `battery.py` | `net = gen − cons`, interval `h`, persistent `soc_kwh` | `charge/discharge_kw`, new SoC | §4 |
| **Electrical** `electrical.py` | `gen, cons`, accuracy class, channels, `grid_voltage_pu` | V, I, Q, pf, f | §11 |
| **Power flow** `grid_manager.py` | per-bus `P,Q` from readings, line `R/X`, transformer cfg | `bus_voltages`, flows, losses | §6–8 |
| **Frequency** `engine.py` | Σ`gen`, Σ`cons` over all readings | `f_{k+1}` | §5.1 |

**Telemetry override path.** If a real frame supplies a meter
(`engine.py:263`–`274`), `override_gen/cons/reactive` **replace** the PV+load
model outputs for that meter that tick (`ami.py:81`–`91`), and the battery is
skipped (`ami.py:108`). Synthetic and real meters coexist → hybrid run. Override
is consumed and cleared each tick (`reading_manager.py:67`–`72`).

---

## 3. Data sources (what feeds the pipeline)

Three mutually-exclusive ways a meter gets its `(gen, cons)` each tick:

1. **Synthetic** — Python device models (§2–4). Default. No external data.
2. **Telemetry replay** — a `telemetry_source` polled at the tick timestamp
   (`engine.py:256`); CSV/JSON real-meter frames override matched meters.
3. **Mixed** — meters in the frame are real, the rest synthetic (partial
   coverage = hybrid).

Topology (the grid the models run on) is loaded **once** at startup from
`GRID_TOPOLOGY=glm:<path>.glm` via `topology_factory` → `GridTopology`. Hot-swap
at runtime is supported (clears all faults).

---

## 4. How to use the models

### 4.1 Run the whole pipeline

```bash
# REST server — full tick loop, API on :8082, docs at /docs
uv run app

# Headless loop, no server — N synthetic meters
uv run cli --mode standalone --meters 80

# One-shot CLI overrides (set os.environ before config loads)
uv run cli --mode standalone --meters 20 --interval 60 \
  --base-gen-min 0 --base-gen-max 5 --base-cons-min 0.2 --base-cons-max 3
```

Inspect a tick's model outputs over the API:

```bash
curl localhost:8082/api/v1/simulation/state     # frequency, stress, clock
curl localhost:8082/api/v1/grid/summary         # losses, curtailed kW, reactive kvar, tap pos
curl localhost:8082/api/v1/meters               # per-meter readings
```

### 4.2 Configure the models (no code)

All model parameters are env-driven through `get_config()`
(`config/settings.py`) — never read `os.environ` in logic. Copy `.env.example`
to `.env`. Groups that map to the equations:

| Env group | Controls | Eq |
| --- | --- | --- |
| `PV_*`, `GRID_TOPOLOGY` lat/lon | PVWatts tilt/azimuth, DC/AC ratio, temp coeff | §2.1 |
| `ZIP_*_FRACTION` | ZIP $a_Z, a_I, a_P$ mix | §3.2 |
| `BATTERY_*` | capacity, C-rate, round-trip efficiency, SoC bounds | §4 |
| `FREQ_*` | nominal, full-swing Hz, droop enable | §5 |
| `LINE_*` | default R/X/ampacity/length-unit when GLM omits them | §6 |
| `PV_VOLTVAR_*` | $Q(V)$ breakpoints $v_1..v_4$, $q_{\max}$ frac, oversize | §7.1 |
| `PV_VOLTWATT_*` | $v_{\mathrm{start}}, v_{\mathrm{end}}$ | §7.2 |
| `TRANSFORMER_*`, `TRANSFORMER_OLTC_*` | MV/LV ratings, tap target/deadband/step | §8 |

Example — turn a constant-power load into a 50/50 Z/P mix and enable volt-watt:

```bash
ZIP_IMPEDANCE_FRACTION=0.5 ZIP_CURRENT_FRACTION=0 ZIP_POWER_FRACTION=0.5 \
PV_VOLTWATT_ENABLED=true PV_VOLTWATT_V_START=1.05 PV_VOLTWATT_V_END=1.10 \
uv run cli --mode standalone --meters 40
```

### 4.3 Drive faults / contingency (runtime)

```bash
# Trip a line, watch it island, then clear
curl -X POST localhost:8082/api/v1/simulation/faults -d '{"type":"line","name":"L1"}'
curl localhost:8082/api/v1/simulation/faults          # islanded_buses
curl -X DELETE localhost:8082/api/v1/simulation/faults # clear all
```

### 4.4 Call a model directly (unit-level)

The device models are plain classes — usable without the engine:

```python
from smart_meter_simulator.devices.solar import Solar
from smart_meter_simulator.devices.load import Load
from datetime import datetime

pv = Solar({"solar_capacity": 5.0, "latitude": 13.7, "longitude": 100.5})
gen_kw = pv.get_generation_kw(datetime(2026, 6, 9, 12, 0), "sunny")   # §2.1

# ZIP response is a pure static method — test it standalone (§3.2)
draw = Load.apply_zip_voltage_response(
    base_kw=3.0, voltage_pu=0.95, z_fraction=0.5, i_fraction=0, p_fraction=0.5
)
```

---

## 5. How to extend / add a model

Follow the existing seams:

1. **New device** → add a class under `devices/` returning kW (mirror
   `Load`/`Solar`), wire it into `SmartMeter.__init__` (`ami.py:29`) and the
   dispatch order in `generate_reading` (`ami.py:66`). Keep it pure/CPU-bound —
   it runs inside `asyncio.to_thread`, so never block the event loop.
2. **New grid control** (e.g. a storage inverter Q rule) → add a fixed-point
   pass in `GridManager._run_pandapower` (`grid_manager.py:375`), respecting the
   control order: volt-VAR (reactive) before volt-watt (real-power curtail).
   Re-solve via the inner `solve()` after mutating loads.
3. **New parameter** → add to `config/settings.py`, read via `get_config()`,
   document the env key in `.env.example`. Never hardcode.
4. **New reading field** → add to `EnergyReading` (`models/reading.py`), populate
   in `generate_reading`, surface through the relevant `routers/*_v1.py` handler
   (handlers stay thin).
5. **Pin behavior with a test** — the wire contracts are pinned by
   `tests/test_aggregator_bridge_dlms.py`, `tests/test_fault_injection.py`,
   `tests/test_reading_store.py`. Add one for new behavior:
   `PYTEST_ADDOPTS=--no-cov uv run pytest -k <name>`.

---

## 6. Outputs (what leaves the pipeline)

Each tick produces an `EnergyReading` per meter and a grid summary. Egress is
non-blocking and drops a tick if the prior batch is still in flight:

| Sink | Trigger | Payload | Eq |
| --- | --- | --- | --- |
| **Aggregator Bridge** | `AGGREGATOR_DLMS_ENABLED` | signed OBIS DLMS/COSEM POST per meter | §11 |
| **PostGIS** | `POSTGIS_ENABLED` | batch insert into `grid.meter_readings` | — |
| **REST API** | always | `/api/v1/meters`, `/grid/summary`, `/history/*` | — |
| **Prometheus** | always | `ACTIVE_METERS`, `SIMULATION_TICK_TIME`, emit/persist failures | — |

Both external sinks are **off by default**; enable per `.env`. See
`backend/CLAUDE.md` for the full egress contract.
