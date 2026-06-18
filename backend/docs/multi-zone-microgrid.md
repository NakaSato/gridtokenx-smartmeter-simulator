# Multi-zone microgrid — zones, islanding, DER self-support, tie-switches

This document describes the **multi-zone microgrid** feature: how the simulator
groups the feeder into microgrid **zones**, disconnects ("islands") a zone from
the utility, holds an islanded zone alive on its own **DER**, decouples its
**frequency**, restores a dark zone through a **tie-switch**, and tags each
meter's reading with its **zone code** on egress to the parent Aggregator Bridge.

> Related: the underlying power flow and fault model are in
> [`modeling-equations.md`](modeling-equations.md) (DistFlow, faults, droop) and
> the per-tick flow in [`data-pipeline-methodology.md`](data-pipeline-methodology.md).
> Egress wire contract: [`realtime-telemetry.md`](realtime-telemetry.md) and the
> aggregator section of [`../CLAUDE.md`](../CLAUDE.md). Doc index:
> [`README.md`](README.md).

> Conventions: claims are cited to `file:line` into
> `backend/src/smart_meter_simulator/`. Line numbers drift — re-verify before publishing.

---

## 1. What a zone is

A **zone** is a contiguous group of buses that can run either grid-connected or
as a self-contained microgrid. It is defined entirely in the GLM topology and
resolved to a frozen `ZoneSpec` (`core/topology.py:109`) carried on
`GridTopology.zones: Dict[int, ZoneSpec]` (`core/topology.py:162`):

| Field | Meaning |
|---|---|
| `code` | Numeric zone code (matches the parent's `gridtokenx:events:zone_<n>` standard). |
| `pcc_bus` / `pcc_transformer` | Point of common coupling — the transformer LV terminal (`pcc_bus`) and the MV↔head **coupling branch** (`pcc_transformer`) where the zone meets the utility backbone. |
| `der_bus` | Largest-PV member bus — the island slack that holds voltage when islanded. |
| `member_buses` | All buses in the zone. |
| `islandable` | True iff a PCC transformer is bound (the zone can be disconnected). |

A topology with **no** zones runs exactly like the pre-zone single feeder — the
whole feature is backward-compatible and collapses away when unused.

---

## 2. Authoring zones in GLM

Tag buses with GridLAB-D **`groupid`** (or a `zone` alias); attach a PCC
transformer, optional DER (PV inverter), and optional normally-open tie-switch:

```glm
object node { name mv; bustype SWING; nominal_voltage 22000; }

// Zone 1 — solar prosumer microgrid (DER-capable)
object node { name z1_head; groupid 1; nominal_voltage 400; }
object node { name z1_a;    groupid 1; nominal_voltage 400; }
object transformer { name pcc1; from mv; to z1_head; }      // PCC coupling branch
object inverter { name inv1; parent z1_a; rated_power 120000; }
object solar    { name pv1;  parent inv1; rated_power 120000; }   // -> DER bus = z1_a

// Zone 2 — residential, no DER
object node { name z2_head; groupid 2; nominal_voltage 400; }
object transformer { name pcc2; from mv; to z2_head; }

// Tie z2<->z3 (normally open) — lets a healthy zone back-feed a dark one
object switch { name tie_2_3; from z2_b; to z3_a; status OPEN; }
```

Validate: `uv run cli --mode validate-topology --grid-topology glm:<path>.glm`.

### Ingestion (`adapters/glm_topology_loader.py`)

- **Numeric code** — bus `groupid`/`zone` → numeric `zone_code` via the cascade
  in `_derive_zone_codes` (`:64`): pure-int groupid → trailing digits → load-order
  counter. Label resolution in `_zone_label` (`:59`).
- **Zone binding** — `_build_zones` (`:350`) binds each zone's PCC transformer
  (the one whose LV bus is a member) and its DER bus (largest-PV member).
- **Tie-switches** — GridLAB-D `switch`/`recloser`/`sectionalizer` objects
  (`_SWITCH_OBJECTS`, `:31`; parsed `:477`) become `GridLine(is_switch=True,
  normally_open=(status==OPEN))`.

Transformers and switches are also **graph edges** in `to_networkx()`
(`core/topology.py:201`) so the approximate solver sees their connectivity.

---

## 3. Islanding by opening the PCC transformer

`ZoneController` (`core/zone_manager.py`) is a runtime control surface — like
fault injection — that keeps **no private state**: a zone reads islanded iff its
PCC transformer is currently faulted, so the view survives resets and topology
hot-swaps with nothing extra to reset.

- `island(code)` (`:56`) — opens the zone's **PCC transformer**
  (`grid.apply_fault("transformer", spec.pcc_transformer)`). It opens the MV↔head
  coupling branch **rather than faulting the head bus**, so the zone head stays a
  live load bus the island's DER can energize. Raises `KeyError` (unknown code) /
  `ValueError` (non-islandable).
- `reconnect(code)` (`:72`) — restores the PCC transformer. Idempotent.
- `is_islanded(code)` (`:47`) — `pcc_transformer ∈ grid.faulted_transformers`.

> **Design note — why the transformer, not the bus.** Earlier the controller
> faulted the PCC *bus*. That zeroed every load on the head bus, so an islanded
> DER zone's head went dark even though it had generation to serve it. Islanding
> the **coupling branch** instead leaves the head a normal load bus; the DER
> slack then energizes the whole zone. Regression pinned by
> `tests/test_zone_island_der.py`.

### Grid-side mechanics (`core/grid_manager.py`)

The solver takes the union `faulted_lines | open_switches | faulted_transformers |
faulted_buses` out of service before each solve:

- **pandapower** path: faulted transformers set `trafo.in_service = False`.
- **DistFlow fallback**: faulted transformer edges are dropped from the graph
  (`_faulted_undirected_graph`, `:501`).
- **DER self-support**: `_islanded_zones_with_der` (`:532`) selects zones whose
  PCC transformer is open *and* that have a DER bus; `_apply_island_slacks`
  (`:549`) drops last tick's island slacks and creates one local `ext_grid` at
  each such DER bus (`vm_pu=1.0`). The DistFlow fallback roots a second BFS from
  every islanded DER bus, so the island stays energized instead of de-energizing.
- A zone with **no** DER has no local slack → its buses lose every path to a slack
  → de-energized (voltage 0), recorded in `islanded_buses`.

`apply_fault` (`:955`) / `clear_fault` accept `element_type ∈ {line, bus,
transformer}`; `set_switch(name, closed)` (`:994`) toggles a tie.

---

## 4. Per-zone frequency decoupling (`core/engine.py`)

Each tick `_update_grid_frequency` (`:511`) partitions readings into a **grid
bucket** (connected/unzoned meters) and one bucket **per commanded-islanded
zone**. `_freq_from_balance(gen, load)` (`:501`) derives a frequency from each
bucket's supply/demand imbalance:

- The **grid** frequency floats on everything not in an islanded zone.
- Each islanded zone's frequency (`zone_frequency_hz[code]`, `:150`) floats on
  **only its own** members — decoupled from the grid.
- With nothing islanded, `zone_frequency_hz == {}` and every zone reports the
  single global grid frequency — identical to the pre-zone behaviour.

`_zone_summaries` (`:595`) emits the per-zone aggregate in the tick summary.

---

## 5. Tick-summary `zones[]` and the API

Every tick summary carries a `zones[]` array, one entry per zone:

```json
{
  "zone_code": 1, "label": "1", "bus_count": 3, "meter_count": 3,
  "generation_kwh": 0.2420, "consumption_kwh": 0.0443, "net_energy_kwh": 0.1977,
  "islandable": true, "island_capable": true,
  "commanded_island": false, "islanded": false,
  "frequency_hz": 50.331
}
```

- `commanded_island` — operator opened the PCC (flips immediately on command).
- `islanded` — a member bus is electrically dark this tick (true after the solve).
- `island_capable` — `islandable AND der_bus` (can self-support).

REST surface (`routers/simulation_v1.py`, all under `/api/v1`, effective **next tick**):

| Method + path | Action |
|---|---|
| `GET /simulation/zones` (`:235`) | Live state of every zone. |
| `POST /simulation/zones/{code}/island` (`:242`) | Open PCC. `404` unknown, `409` non-islandable. |
| `POST /simulation/zones/{code}/reconnect` (`:254`) | Restore PCC. |
| `GET /simulation/switches` (`:263`) | Every tie-switch + closed bool. |
| `POST /simulation/switches/{name}/close\|open` | Toggle tie. `404` unknown. |

Demand response can be scoped to zones: `POST /simulation/demand-response` with
`target_zones:[…]` for localized per-zone feeder relief.

---

## 6. Egress — zone code on the wire (`transport/aggregator_bridge.py`)

Each meter's numeric `zone_code` is encoded into its DLMS/COSEM payload **as a
string** (`:144`, `:237`) so the parent bridge's `dlms.rs` reads it into
`DeviceReading.zone_code` and `router.calculate_zone_index` routes the reading to
the `gridtokenx:events:zone_<n>` Redis stream. Unzoned meters (code 0) omit the
field and fall back to serial-hash routing. End-to-end verified live: code 1 →
`zone_1`, code 2 → `zone_2`, unzoned → hash.

---

## 7. Worked example — 3-zone feeder

Topology: z1 solar-DER (120 kW), z2 residential no-DER, z3 mixed-DER (60 kW),
normally-open tie z2↔z3. 30 meters, 15 s ticks. Driving island/tie events:

```
t1-3  gridf=50.33  all on, single global f        (nothing islanded -> backward-compat)
t4    ISLAND z1    z1 isl? f=50.41   grid 50.33->50.18 (lost z1 export)
t6    ISLAND z2    z2 ISL  f=49.50  islbus=3  z2 DARK (no DER)
t8    ISLAND z3 +  z1 50.41 | z2 49.50 | z3 50.39  islbus=0  (tie re-feeds z2 from z3 DER)
      CLOSE tie
t11   RECONNECT    gridf=50.33  zone_f -> {}  (single global, fully restored)
```

Per-zone energy at steady state (15 s interval):

| zone | meters | gen kWh | cons kWh | net kWh | role |
|---|---|---|---|---|---|
| 1 | 3 | 0.2420 | 0.0443 | +0.1977 | exporter (DER) |
| 2 | 3 | 0.0000 | 0.0288 | −0.0288 | pure load |
| 3 | 2 | 0.1245 | 0.0262 | +0.0982 | exporter (DER) |

Three islands ran simultaneously on three different frequencies (50.41 / 49.50 /
50.39 Hz); closing the tie restored the dark no-DER zone from a neighbour's DER;
reconnecting collapsed everything back to one global frequency.

---

## 8. Tests

| File | Pins |
|---|---|
| `tests/test_zone_manager.py` | island/reconnect via PCC transformer, commanded vs electrical status. |
| `tests/test_zone_island_der.py` | DER island stays energized (incl. head bus); no-DER island goes dark; slack drop on reconnect. |
| `tests/test_zone_frequency.py` | per-zone frequency decoupling; global collapse when nothing islanded. |
| `tests/test_tie_switch.py` | normally-open parse; toggle; tie-restore of a dark zone. |
| `tests/test_fault_injection.py` | line/bus/transformer fault out-of-service + islanded-bus reporting. |
