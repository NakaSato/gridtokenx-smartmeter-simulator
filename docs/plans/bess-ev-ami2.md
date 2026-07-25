# Plan: EV Charging Stations + BESS nodes (autonomous freq-reserve, congestion relief)

> Living plan with implementation status. Phase 1 (simulator) implemented + tested;
> Phase 2 minimal (bridge → Influx) implemented + tested; Phase 2 full (Kafka) pending.

## Context

The simulator modeled only Solar PV + ZIP loads as per-meter devices. Two new grid assets were
added, each authored as a **dedicated-transformer node** in the `.glm` topology:

- **EV charging station** — a node behind its own distribution transformer, modeled as a large
  controllable **load** (charging draw).
- **BESS** (battery energy storage) — a node behind its own transformer, sized for **high
  power/energy**, for **grid-congestion reserve**. Dispatch is **autonomous frequency-reserve
  droop** (discharge on under-frequency/deficit, charge on over-frequency/surplus) holding a
  reserved SoC band, plus discharge to relieve local transformer congestion.

Motivated by AMI 2.0 DER-visibility (EV/BESS as V2G-capable DERs, 5–15-min DER telemetry into
DERMS) — the sim's DLMS/COSEM egress now carries storage/EV state to the parent bridge.

**Frontend discovery:** the dashboard already had EV/BESS scaffolding the backend never
implemented (`frontend/src/lib/types.ts`, `EditMeterModal.tsx` `EV_TYPES=["EV_Charger","DC_Fast_Charger"]`);
`routers/meters_v1.py` dropped those fields. Phase 1 completed the missing backend half.

## Architecture fit

- Devices attach to `SmartMeter` by config flag (`devices/ami.py`): `self.battery`/`self.ev`
  alongside `self.solar`. **BESS discharge → `energy_generated`, charge/EV draw →
  `energy_consumed`**, so both flow automatically into the power-flow net-load
  (`grid_manager.update_grid_state`) and the frequency balance (`engine._update_grid_frequency`) —
  **no new pandapower element** (PV is already signed net load; no `create_sgen`/`create_storage`).
- GLM transformers declared in `.glm` are **always built** → a dedicated-TR node = node +
  transformer + device object, parsed as-is.
- BESS reacts to **previous-tick** frequency + transformer loading (one-tick governor lag, like
  the existing generator droop) → dispatch computed once per tick, **outside** the pandapower
  fixed point → no oscillation.
- A large BESS is a natural island DER slack — `_build_zones` scores DER capacity as PV + BESS
  power.

---

## Phase 1 — Simulator (STATUS: ✅ implemented + tested)

- **Enums/channels/config** — `config/enums.py` (`BESS`/`EV_Charger`/`DC_Fast_Charger`),
  `config/channels.py` (BESS omits `i` — it exports; signed-current model is magnitude-only),
  `config/settings.py` `BESS_*`/`EV_*` env (default off).
- **Device models** — `devices/battery.py` (`Battery`: droop + congestion hysteresis +
  reserve-floor discipline + SoC integration w/ efficiency, deterministic no-RNG),
  `devices/ev.py` (`EVCharger`: constant-power additive load, diurnal profile).
- **`devices/ami.py`** — battery/EV applied **after** `apply_droop_control` (critical: battery
  runs its own droop, must not be re-scaled by the generation-only governor); `receive_grid_loading`.
- **`models/reading.py`** — `battery_soc_pct`/`battery_dispatch_kw`/`ev_charge_kw` (optional).
- **Topology/GLM** — `core/topology.py` `GridBattery`/`GridEVStation`;
  `adapters/glm_topology_loader.py` parses `battery`/`evcharger`(`_det`); `_build_zones` folds
  BESS into DER slack.
- **Placement** — `meter_generator.py` places BESS/EV meters on their nodes (guaranteed coverage).
- **Engine/control** — `core/engine.py` node maps + prev-tick loading thread + summary aggregates
  (`total_battery_discharge_kw`, `avg_battery_soc_pct`, `total_ev_load_kw`);
  `core/reading_manager.py` loading map; `core/bess_manager.py` `BessController`.
- **REST** — `routers/simulation_v1.py` `GET /simulation/bess`, `POST .../{id}/reserve`;
  `routers/meters_v1.py` accepts battery/EV fields.
- **OBIS egress** — `transport/aggregator_bridge.py` `0.0.96.130/131/132` (SoC/dispatch/EV);
  additive metadata, never alters the signed canonical string.
- **Frontend** — `types.ts`, `meterHmi.ts` (isBattery/isEV roles), `GraphLegend.tsx`.
- **Docs** — GLM-authoring skill + backend `CLAUDE.md`.

**Result:** `pytest` **282 passed** (new `test_battery.py`, `test_ev.py`, +2 DLMS tests);
1 pre-existing unrelated failure (`test_config_defaults_grid_topology_to_reference_glm`, stale
since commit `08f0a42`). black/isort/flake8 clean. E2E: validate-topology + standalone verified —
BESS discharges 160 kW at 49.2 Hz, SoC drops, **frequency recovers to 50.06 Hz (closed loop)**;
EV draws 128 kW at evening peak. Frontend `tsc` pending `npm install`.

## Open decisions folded in
- BESS/EV = **meter-borne devices on dedicated-TR GLM nodes** (satisfies "separate TR" without a
  new pandapower storage element).
- Dispatch **autonomous** (freq droop + congestion); REST = status + reserve-frac override only.
- All new behavior **flag-gated / benign default** → zero change to existing topologies/runs.

---

## Phase 2 — Bridge-side wiring: surface SoC/dispatch/EV to sinks

**Separate repo:** `gridtokenx-aggregator-bridge` (branch `feat/bess-ev-obis-sinks`). The 3
registers reach the bridge but land in `DeviceReading.metadata` under **raw dotted OBIS codes**
(`dlms.rs:201-203` fallback); every sink except the raw zone Redis stream reads metadata by
**exact named key**, so raw codes are invisible. Naming them unlocks the named sinks.

### Minimal path — Influx dashboards (STATUS: ✅ implemented + tested)
- **① `dlms.rs`** — 3 `obis::` consts + 3 decode arms → named keys `battery_soc_percent`,
  `battery_dispatch_kw`, `ev_charging_kw`. (Reading stays `DeviceMetrics::Energy`, does NOT
  populate the separate `BatteryState`/`EvSession` variants.)
- **② `router.rs`** — 3 named keys added to Influx `EXTRA_FIELDS` allow-list (`reading_to_point`
  promotes numeric metadata; `TelemetryPoint.fields` is generic → no schema change; measurement
  `"energy"`).

**Result:** `cargo test -p aggregator-stacks dlms` **8 passed** (new
`test_dlms_bess_ev_registers_decode_to_named_metadata`); `cargo check -p aggregator-logic` clean.
+56 lines / 2 files, additive. **Not committed.** Live E2E pending `just orb-up`.

### Full path — Kafka consumers (STATUS: ⬜ pending, optional)
- **③** add 3 fields to `MeterReadingEvent` (`kafka.rs:24-36`); populate in the constructor
  (`aggregator-api/src/handlers.rs:1081-1110`) via `metadata.get("battery_soc_percent").and_then(v.as_f64())`;
  update field-count roundtrip test (`kafka.rs:247`). **Wire-contract change** (additive,
  serde-default-safe). Do only when a Kafka consumer needs storage state.

### Explicitly out of scope (confirmed)
- **Settlement / mint** — energy-only (`mint_settlement.rs`; binning `zone_ingester.rs:582-697`).
  SoC/dispatch don't drive minting.
- **Proto / gRPC** — dead path (legacy forwarder bypassed, `batcher.rs:213-214`).
- **Zone Redis stream** — already carries all 3 (raw-code metadata). Named-side read in
  `zone_ingester` needs a `extract_frequency`-style extractor (optional).
- **Postgres `meter_readings`** — 4th cherry-pick sink (`reading_to_row`); add only if SoC should
  be PG-queryable.

---

## Remaining / next steps
- [ ] Commit Phase 1 simulator work (uncommitted on this repo).
- [ ] Commit bridge branch `feat/bess-ev-obis-sinks` + bump superproject pointer.
- [ ] Live E2E: `just orb-up` + sim `AGGREGATOR_DLMS_ENABLED=true` + BESS/EV GLM → confirm Influx
      `energy` measurement carries `battery_soc_percent` (ties to
      `smartmeter-egress-paths-and-verification` runbook).
- [ ] Frontend `npm install && npm run build` type-check.
- [ ] (optional) Phase 2 full path ③ (Kafka).
