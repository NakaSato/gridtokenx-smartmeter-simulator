# CLAUDE.md

Guides Claude Code (claude.ai/code) for this repo.

> Scope: **backend** of GridTokenX Smart Meter Simulator (standalone sub-project, separate
> from parent `gridtokenx-coresystem` Rust monorepo — that `CLAUDE.md` does not apply here).
> Next.js frontend in `../frontend`, own `CLAUDE.md`.

## What this is

GridLAB-D **GLM-backed** smart meter / AMI grid simulator. Parses `.glm` topology into native
`GridTopology`, generates per-meter readings via Python device models (PV via `pvlib`, ZIP
loads), runs exact AC power flow (pandapower, backward/forward sweep) each tick — approximate
DistFlow fallback on non-convergence — updating bus voltages, line flows, losses, congestion.
Exposed as FastAPI REST service (default port **8082**). Part of GridTokenX ecosystem —
readings ingest into parent Aggregator Bridge over standard DLMS/COSEM (IEC 62056) REST contract.

Package manager **uv**. Python 3.11+.

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

Runtime behavior env-driven via `pydantic-settings`. Copy `.env.example` to `.env`. Access
config through cached singleton `get_config()` (`config/settings.py`) — never read
`os.environ` directly in logic. Key setting `GRID_TOPOLOGY=glm:<path-to-.glm>`; `glm:` prefix
= topology spec scheme parsed by `topology_factory`. Other env groups: meter-type mix ratios
(solar prosumer / grid consumer / hybrid), PV/`pvlib` params, ZIP load fractions, line
impedance defaults, weather weights, geo coords.

## Architecture

Request/tick flow:

```
app.py (create_app) → lifespan.py → app_state.engine = SimulationEngine (global singleton)
SimulationEngine.tick():
  ReadingManager.generate_all()   # device models, run in a thread via asyncio.to_thread
  GridManager.update_grid_state() # exact pandapower AC power flow (bfsw), DistFlow fallback
```

- **`core/engine.py`** — `SimulationEngine` owns meter list, grid, reading manager, async tick
  loop. State (running/paused, sim clock, weather, stress multiplier) lives here. Single mutable
  runtime object; routers reach it via `core/app_state.engine`. Each tick `_update_grid_frequency`
  derives system frequency from supply/demand imbalance (`FREQ_*` config: nominal +
  `FREQ_FULL_SWING_HZ` × gen−load ratio, clamped ±1), feeds it to meters, where
  `electrical.apply_droop_control` throttles export under over-frequency — closing
  **frequency-watt** primary-response loop alongside grid_manager's volt-watt. One-tick governor
  lag; external telemetry frequency (re-applied first each tick) stays authoritative. `frequency_hz`
  in tick summary. **Per-zone frequency** (multi-zone): a commanded-islanded zone's frequency
  decouples onto *its own* members' supply/demand balance (`zone_frequency_hz[code]`), while
  connected/unzoned meters keep the grid frequency — collapses to the single global frequency when
  nothing is islanded (backward-compatible). Engine also owns `zone_controller` (island/reconnect)
  and emits per-zone aggregates (`zones[]`: energy, `frequency_hz`, `islandable`/`island_capable`/
  `commanded_island`/`islanded`) in the tick summary.
- **`core/topology.py`** — `GridTopology` dataclass (buses/lines/loads/pvs/transformers/**zones**) —
  neutral grid model everything downstream consumes. `to_networkx()` / `to_legacy_net()` adapt it.
  `GridBus` carries `zone`/`zone_code` (microgrid grouping); `GridLine` carries `is_switch`/
  `normally_open` (tie-switches); `ZoneSpec` (in `GridTopology.zones[code]`) holds a zone's members,
  PCC (`pcc_bus`/`pcc_transformer`), DER bus (largest-PV member, the island slack), and `islandable`.
- **`core/topology_factory.py`** — resolves `glm:<path>` spec into `GridTopology`.
- **`adapters/`** — GLM ingestion only: `glm_converter.py` (`GLMParser` tokenizer) →
  `glm_topology_loader.py` (maps GLM objects to `GridBus/GridLine/GridLoad/GridPV`, pulls line
  impedance from `line_configuration` or falls back to `LINE_*` env defaults). Reads bus
  **`groupid`/`zone`** into a numeric `zone_code` (cascade: int groupid → trailing digits → load-order
  counter), binds each zone's PCC transformer + largest-PV DER bus (`_build_zones`), and parses
  GridLAB-D **`switch`** objects (`status OPEN` → normally-open tie-line). No external
  power-flow solver run by loader. To author, edit, validate `.glm` files, use
  **`glm-topology-authoring`** skill (`.claude/skills/glm-topology-authoring/`) — documents which
  GLM object types/fields this subset parser reads.
- **`core/grid_manager.py`** — maps meters to buses, runs power flow each tick (bus voltages, line
  flows, losses, congestion). Builds pandapower net, solves with backward/forward sweep (`bfsw`,
  right for radial LV feeders; NR/DC seed as second try). On non-convergence (e.g. voltage collapse
  under overload) falls back to approximate DistFlow sweep over networkx graph. 3-phase buses model
  at line-to-line base (L-N ×√3), line R/X/ampacity from `LINE_*` config when GLM omits them; both
  solvers share one length converter (`_convert_length_km`), so unitless GLM `length` resolves to
  `LINE_LENGTH_UNIT` (default ft) consistently. Models IEEE 1547 **volt-watt** PV curtailment
  (`PV_VOLTWATT_*`): exporting bus above `v_start` (pu) throttles inverter export to zero at
  `v_end`, ratcheted to stable fixed point each tick — caps overvoltage backfeed; curtailed kW in
  grid summary. Models IEEE 1547 **volt-VAR** reactive support (`PV_VOLTVAR_*`) ahead of volt-watt:
  each PV inverter follows piecewise `Q(V)` curve (four pu breakpoints `v1..v4` with `v2..v3`
  deadband) — injecting reactive power to raise sagging bus, absorbing to pull down overvoltage one,
  bounded by inverter headroom `sqrt(sn² − p²)` and `q_max_frac` of apparent rating
  (`sn` = PV nameplate × `inverter_oversize`). Iterated to fixed point; `total_reactive_support_kvar`
  in summary. Reactive (volt-VAR) acts first, then real-power curtailment (volt-watt) handles
  residual overvoltage — sequential, not co-optimized, control order.
  When `TRANSFORMER_ENABLED` (default), models real MV/LV distribution transformer at feeder head:
  MV (`TRANSFORMER_MV_KV`, 22 kV) external-grid slack → transformer (`TRANSFORMER_SN_MVA`
  /`VK_PERCENT`/`VKR_PERCENT`/`PFE_KW`/`I0_PERCENT`) → substation LV bus. Slack moves upstream, so
  LV bus voltage sags under load and rises on PV backfeed across transformer impedance instead of
  stiff 1.0 pu source; transformer loss + loading% in summary. `TRANSFORMER_ENABLED` governs only
  this **synthesized** feeder-head transformer (the legacy zero-config path). Transformers declared
  in the `.glm` topology are explicit grid elements and are always built regardless of the flag —
  setting it false on a topology with transformers does **not** strip them.
  With `TRANSFORMER_OLTC_ENABLED` transformer also runs **on-load tap changer**: before volt-watt
  pass steps HV-side tap (`TRANSFORMER_TAP_STEP_PERCENT`, bounded `±TRANSFORMER_TAP_MAX`) to hold
  LV head at `TRANSFORMER_OLTC_V_TARGET` within `TRANSFORMER_OLTC_DEADBAND`, re-solving until in-band
  or saturated — tap absorbs bulk voltage, curtailment handles only residual local overvoltage
  (`transformer_tap_pos` in summary). Note: `bfsw` solver in pandapower 3.3 errors on non-neutral
  tap, so tapped solve transparently falls through to NR; transformer created with
  `tap_changer_type="Ratio"` (pp 3.x ignores tap otherwise).
  Supports **fault/outage injection** for N-1 contingency / resilience study: faulted lines and
  buses (`faulted_lines`/`faulted_buses`) flagged out of service before each solve (and removed from
  distflow fallback's graph), so radial feeder reroutes or **islands**. Buses cut off from substation
  slack de-energized (voltage 0), reported in `islanded_buses`, recomputed every tick (`fault_count`
  + `islanded_bus_count` in tick summary). Drive via `apply_fault`/`clear_fault`/`clear_all_faults`/
  `fault_status` methods, exposed over `/api/v1/simulation/faults` (GET list / POST trip / DELETE
  clear). Topology hot-swap clears all faults (old element names no longer valid). Pinned by
  `tests/test_fault_injection.py`.
  **Microgrid zones** (multi-zone): islanding a zone (via `ZoneController`, below) trips its **PCC
  bus** so the zone falls off the substation slack. A zone with a **DER bus** gets a temporary local
  `ext_grid` slack there (`_apply_island_slacks`, tracked in `_island_ext_grid_idx`; distflow roots a
  second BFS from the DER bus) so the island **holds voltage** instead of de-energizing — a zone with
  no DER goes dark (Phase-2 disconnect). **Tie-switches** (`switch_lines`/`open_switches`,
  `set_switch`/`switch_status`): normally-open inter-zone lines are out-of-service alongside faults;
  closing one transfers/restores load. Pinned by `tests/test_zone_island_der.py`,
  `tests/test_tie_switch.py`.
- **`core/demand_response.py`** — `DemandResponseController` holds API-scheduled **load-shed
  (DR) events** (runtime control like grid faults, *not* part of seeded replay; ids are a
  monotonic `dr-N` counter, no RNG). Each event is a half-open sim-clock window `[start, end)`
  curtailing `reduction_fraction` of participating load (optional `target_meter_types` **and/or
  `target_zones`** filters — AND together, for localized per-zone feeder relief; overlapping events
  compose by the **most aggressive** reduction, not additive). Engine resolves a per-
  `(meter_type, zone_code)` load factor each tick (cached) and threads it through
  `ReadingManager.generate_all` → `SmartMeter.generate_reading(dr_load_factor=…)`, which scales
  `cons` after grid-stress (skipped on real-telemetry overrides) and records `dr_shed_kw` on the
  reading. Lower aggregate load relieves the feeder in the same power-flow solve; tick summary
  carries `total_dr_shed_kw` + `active_dr_events`. Drive over `/api/v1/simulation/demand-response`
  (GET status / POST schedule — `reduction_fraction` + `start`?/`end`|`duration_minutes` /
  `target_meter_types`? / `target_zones`? / DELETE cancel-by-id or clear-all). Cleared on
  deterministic reset. Pinned by `tests/test_demand_response.py`.
- **`core/zone_manager.py`** — `ZoneController` islands/reconnects microgrid zones as a runtime
  control surface (like faults). `island(code)` trips the zone's PCC bus, `reconnect(code)` clears it;
  state is **derived live** from `grid.faulted_buses` (no private state → consistent through resets
  and topology swaps). Reads zones live from `grid.topology.zones`. `status`/`list_status` report
  `commanded_island` (PCC tripped) vs electrical `islanded` + `der_bus`/`island_capable`. Exposed over
  `/api/v1/simulation/zones` (GET list / POST `{code}/island` / POST `{code}/reconnect`). Pinned by
  `tests/test_zone_manager.py`, `tests/test_zone_frequency.py`.
- **`core/reading_manager.py`** + **`core/meter_logic/`** — reading generation. `electrical.py`
  applies ZIP voltage sensitivity and frequency-watt droop; `profiles.py` load shapes.
- **`devices/`** — `ami.py` (`SmartMeter`), `solar.py` (PV), `load.py`. No battery/EV device
  model.
- **`meter_generator.py`** — builds meter population (type mix, PV-per-bus) from topology.
- **`routers/`** — FastAPI v1 under `/api/v1`: `simulation_v1`, `meters_v1`, `grid_v1`, aggregated
  by `api_v1.py`. Handlers thin, operate on `app_state.engine`. `simulation_v1` also exposes the
  zone/switch controls (`/simulation/zones[/{code}/island|reconnect]`, `/simulation/switches[/{name}/
  close|open]`); `meters_v1` adds `zone`/`zone_code` per meter.
- **`core/metrics.py`** — Prometheus metrics (`ACTIVE_METERS`, `SIMULATION_TICK_TIME`).

### Aggregator Bridge egress (`transport/aggregator_bridge.py`)

Simulator's **sole egress** to parent Aggregator Bridge is standard **DLMS/COSEM (IEC 62056)**
REST path. Set `AGGREGATOR_DLMS_ENABLED=true` and engine ships each tick's readings to
`AGGREGATOR_BRIDGE_URL` (`/v1/private-network/ingest`, `protocol="dlms"`) via
`AggregatorBridgeEmitter`: one signed OBIS-coded JSON POST per meter, fired concurrently with
`asyncio.gather`, non-blocking, drops a tick if prior batch still in flight. On start registers
each meter's Ed25519 public key in bridge's Redis device registry (`REDIS_URL`) so
`verify_rest_signature` can authenticate telemetry, probes bridge `/health` (warns if unreachable),
and — when `AGGREGATOR_METER_OWNER_MAP` (JSON `{meter_id:
user_id}`) set — seeds bridge's
meter→owner map so telemetry resolves to `user_id` for settlement (without it bridge resolves
`Uuid::nil` and skips settlement). With `AGGREGATOR_IAM_ONBOARD_ENABLED` engine instead resolves
owners live via IAM gateway (`onboard_fleet` → `onboard_meter`: register → verify → login).
Verification uses IAM's dev `verify_<email>` token (no email round-trip) to activate deterministic
sim account so login succeeds every run and returns `user_id` — making re-runs idempotent without
depending on Redis. (Ownership only: no IAM endpoint to claim a meter / register on-chain PDA —
that path is Anchor `registry` instruction via Chain Bridge, out of scope here.) As safety net,
for any meter IAM can't resolve this run falls back to `read_meter_owners_redis`, reading back any
owner a prior run seeded in bridge registry. Meters still unresolved (no IAM user_id, none in Redis)
logged with actionable warning. `send_reading` retries once with jittered backoff on transport
errors / 5xx (never on 4xx); failed sends increment `aggregator_emit_failed_total` Prometheus
counter. Default off.

Per-reading OBIS encoding + `device_id:kwh:timestamp_ms` Ed25519 signature contract live in
`_build_obis_payload` / `MeterKey`. The payload carries the **full residential register set**
(single-phase L1): active import/export energy total (`1.1.1.8.0.255`/`1.1.2.8.0.255`, Wh) plus
optional voltage, current, frequency, power factor (`1.1.13.7.0.255`), reactive energy
(`1.1.3.8.0.255`/`1.1.4.8.0.255`, varh derived from `reactive_power_kvar` over interval),
sum (signed) active power (`1.1.16.7.0.255`, kW — the C=16 sum register, **not** the positive-only
`1.7.0`), rolling max import demand (`1.1.1.6.0.255`, kW), DR status (`0.0.96.10.0.255`, set when
`dr_shed_kw` present), **`zone_code`** (the meter's numeric microgrid zone, sent as a string so the
bridge's `dlms.rs` reads it into `DeviceReading.zone_code` and `router.calculate_zone_index` routes
to `gridtokenx:events:zone_<n>`; omitted for unzoned/code 0), and — when `AGGREGATOR_TOU_ENABLED`
(default on) — 2-tier time-of-use registers: this interval's energy in the active rate's
import/export register (rate 1 = peak `…8.1.255`, rate 2 = off-peak `…8.2.255`) plus the
active-tariff indicator (`0.0.96.14.0.255`). TOU period comes from `TouSchedule` (weekday peak
`[AGGREGATOR_TOU_PEAK_START_HOUR, …END_HOUR)`, default 09–22; weekends off-peak), classified on the
reading's own sim clock. The energy *totals* stay the settlement value — rate/demand/tariff
registers are additive billing metadata on the bridge (`DlmsStack.map_payload`, not double-counted)
and never alter the signed canonical string. Max demand is a run-scoped rolling peak held on
`AggregatorBridgeEmitter` (import only; resets on restart). Wire contract pinned by
`tests/test_aggregator_bridge_dlms.py`. No Rust extension, gRPC channel, or protobuf stubs —
legacy binary Protocol-v4 (UTT-S+) gRPC path and its `src/rust_sim` crate removed.

> **Read before planning OBIS/telemetry work — which sink keeps our OBIS metadata (verified live 2026-06-14).**
> The parent `gridtokenx-aggregator-bridge` decodes our OBIS into `DeviceReading.metadata`
> (`DlmsStack.map_payload`); where that map then goes depends on the sink:
> - **Zone Redis Streams** (`router.disseminate`, `gridtokenx:events:zone_<n>`) serialize the **whole
>   `DeviceReading` incl. metadata** — the full residential register set IS observable here
>   (confirmed live: `sum_active_power_kw`, `0.0.96.14.0.255` tariff, `1.1.1.8.2.255` import-rate2,
>   `1.1.1.6.0.255` max demand). Un-rebuilt bridge → raw OBIS-code keys (fallback arm); after the
>   Phase-2 `dlms.rs` rebuild → named keys.
> - **InfluxDB** (`router.reading_to_point`) emits only `generated/consumed/net_kwh` — metadata dropped.
> - **Kafka** `MeterReadingEvent` cherry-picks only `voltage_v`/`frequency_hz`/`power_factor`/`signature`.
> - **Settlement** (15-min `gridtokenx:settlement:bins`) uses only energy + `frequency`.
>
> So the registers reach the zone stream but NOT Influx/Kafka/settlement. To expose one to *those*
> sinks, wire it bridge-side into `reading_to_point` / the Kafka struct / zone_ingester — encoding it
> in `_build_obis_payload` alone only reaches the zone stream. Live E2E verified: ingest 200 (IAM key),
> signature OK, owner resolved (non-nil `user_id`), settlement bins aggregating real energy, full
> register set in zone streams with correct TOU classification.

### PostGIS persistence (`persistence/reading_store.py`)

Optional egress mirroring Aggregator emitter's non-blocking shape. Set `POSTGIS_ENABLED=true` and
engine batch-inserts each tick's readings into parent **`grid.meter_readings`** table (PostGIS asset
schema under `database/migrations/`) via `ReadingStore`, so a run is queryable for replay, history,
geo lookups. On start connects `asyncpg` pool to `POSTGIS_URL` and upserts meter population into
**`grid.meters`** (location from each meter's config `latitude`/`longitude`, falling back to
`BASE_LATITUDE`/`BASE_LONGITUDE`) so reading foreign key resolves. Each tick `persist()` fires
background `executemany` and **drops the tick if prior batch still in flight** (same back-pressure as
Aggregator emitter); `POSTGIS_PERSIST_EVERY` thins cadence. Numeric params cast `::float8` in SQL so
plain floats insert into `NUMERIC` columns without `Decimal`. All failures logged, increment
`postgis_persist_failed_total`, never propagate into tick; init failure (DB down / schema missing)
disables persistence for the run. Requires migrations `002_postgis_simple.sql` +
`004_reading_replay_columns.sql`. Default off.

Replay/geo exposed under `/api/v1/history` (`routers/history_v1.py`): `GET /history/readings`
(filter by `meter_id`/`start`/`end`, newest first), `GET /history/network/geojson` and
`/history/network/stats` (geo asset network via `grid.export_network_geojson` /
`grid.get_network_stats` SQL functions). All return 503 when persistence off. Store's wire shape
pinned by `tests/test_reading_store.py` (no live DB — fake asyncpg pool).

## Conventions

- `from __future__ import annotations` at top of modules; `black`/`isort` profile = black, line
  length 88.
- Config flows through `get_config()`; topology flows as `GridTopology` instance — keep new parsers
  emitting that shape, not ad-hoc dicts.
- Reading generation CPU-bound, dispatched with `asyncio.to_thread`; keep non-blocking on event loop.
- Engine is process-global singleton (`app_state.engine`); no per-request state.
## Search Tooling

> **Use `rg` (ripgrep), never `grep`.** When shelling out to search files, run `rg` —
> it respects `.gitignore`, skips binaries, and is far faster than `grep`/`find -exec grep`.
> Reserve plain `grep` only for piping non-file streams.
