---
name: glm-topology-authoring
description: Author, edit, and validate GridLAB-D .glm topology files for the smart meter simulator. Use when creating or modifying a grid topology (.glm), adding buses/lines/loads/PV, debugging "validate-topology" errors, fixing missing-bus / disconnected-graph / PV-not-mapped issues, or understanding which GLM object types and fields this backend's parser actually reads.
---

# Authoring GLM topologies for the simulator

This backend does **not** run GridLAB-D. It ships its own **subset parser**
(`src/smart_meter_simulator/adapters/glm_converter.py`) that turns a `.glm` file into the
neutral `GridTopology` model (`core/topology.py`) via
`adapters/glm_topology_loader.py`. Only the object types and fields listed below are read;
everything else in a real GLM file is silently ignored. Author to *this* parser, not to the
full GridLAB-D spec.

Reference model to copy from: `src/smart_meter_simulator/data/grids/grid_bus_network.glm`.

## Workflow

1. Edit / create the `.glm` (use the patterns below).
2. **Validate** before running:
   ```bash
   uv run cli --mode validate-topology --grid-topology glm:<path-to>.glm
   ```
   Prints a JSON `summary()` (`num_buses`, `num_lines`, `num_pv`, `pv_capacity_kw`,
   `static_load_kw`, inferred `substation`) plus a `validation` block. Exit code 1 = invalid.
3. Confirm the counts match intent (a typo'd object type just vanishes — no error).
4. Point the simulator at it: set `GRID_TOPOLOGY=glm:<path>` in `.env`, or pass
   `--grid-topology` to `uv run cli`. Then `uv run app`.

## Parser behavior (important constraints)

- Reads top-level `object { ... }` blocks. `module`, `clock`, `class` blocks are skipped.
- `//` line comments are stripped; `#define X = val` + `${X}` expansion is supported.
- An object's identity fields are `name` and `parent` (special-cased); all other
  `key value;` lines become string properties. **No type/unit checking** — a misspelled
  field name is just dropped.
- Object type → role mapping (anything else is ignored):
  | role  | accepted `object` types |
  |-------|--------------------------|
  | bus   | `node`, `meter`, `substation` |
  | line  | `overhead_line`, `underground_line`, `triplex_line` |
  | line config | `line_configuration` (+ overhead/underground/triplex variants) |
  | load  | `load` |
  | inverter | `inverter`, `inverter_dyn` |
  | PV    | `solar` |
  | BESS  | `battery` |
  | EV station | `evcharger`, `evcharger_det` |

## Object recipes

### Bus
```glm
object meter {           // or node / substation
    name "ref_lv_bus_1";
    phases ABCN;
    nominal_voltage 230.00;
}
```
- **Slack/substation inference** (`get_substation_bus`): first match wins —
  a bus named `ref_lv_bus_1`, `sourcebus`, or `swing_bus`; else any bus with
  `bustype SWING;`; else the first bus declared. Name your reference bus accordingly or
  you'll get a "No substation/slack bus could be inferred" warning.

### Line
```glm
object overhead_line {
    name "Line_0";
    phases ABCN;
    from "ref_lv_bus_35";
    to   "ref_lv_bus_36";
    length 142.26;
}
```
- `from` and `to` **must reference existing bus names** (else hard error).
- Impedance resolution order (Ω/km): explicit `resistance_ohm_per_km`/`reactance_ohm_per_km`
  on the line → same on the referenced `configuration` → `*_ohm_per_mile` (converted) →
  averaged `z11/z22/z33`/`z1`/`impedance` (complex, see below) → generic `r1`/`x1`/
  `resistance`/`reactance`. If none are present, the simulator falls back to the
  `LINE_RESISTANCE_OHM_PER_KM` / `LINE_REACTANCE_OHM_PER_KM` env defaults.
- Length unit is parsed from the unit suffix *inside the length value text* (e.g.
  `length 100 ft;`). A bare number has no unit and falls back to the `LINE_LENGTH_UNIT` env.
- Optional capacity: `capacity_kw` / `rating_kw` / `emergency_rating_kw`.

### Line configuration (optional, referenced by lines)
```glm
object line_configuration {
    name "lc_default";
    z11 0.642+0.083j ohm/km;   // complex impedance; 'i' or 'j' accepted
    impedance_length_unit km;  // or impedance_unit; defaults to mile for configs
}
object underground_line {
    name "Line_5"; from "a"; to "b"; length 0.3;
    configuration "lc_default";   // <-- links the config in
}
```

### Load
```glm
object load {
    name "Load_0";
    parent "ref_lv_bus_8";        // must be an existing bus
    phases ABCN;
    constant_power_A 2547.0+25.0j; // VA, complex (P + Qj)
    nominal_voltage 230.00;
}
```
- Power is summed across `constant_power_A/B/C` (or a single `constant_power`).
- **Values are in VA / var, not kW.** The summary divides by 1000 for `static_load_kw`.
- `parent` is required and must resolve to a bus, else hard error.

### PV (two-object chain — order matters)
PV capacity is what feeds the meter generator's per-bus PV (`PV_ON_EVERY_BUS`,
`pv_capacity_kw_by_node`), so the chain must be intact:

```glm
object inverter {
    name "PV_Inverter_ref_lv_bus_4";
    parent "ref_lv_bus_4";        // inverter's parent = the BUS
    rated_power 10000.0;          // W  -> 10 kW
    inverter_efficiency 0.96;
}
object solar {
    name "PV_ref_lv_bus_4";
    parent "PV_Inverter_ref_lv_bus_4";  // solar's parent = the INVERTER
    efficiency 0.20;
    area 538.20 sf;               // fallback sizing if no rated_power
}
```
- The bus a PV attaches to is found by walking `solar.parent` → inverter → `inverter.parent`.
  If the inverter is missing or its parent isn't a bus, the PV gets `bus=""` → hard error.
- Capacity_kw priority: inverter `rated_power` (W÷1000) → solar `rated_power` (W÷1000) →
  `area × efficiency` (area auto-converted from `sf`/`sqft`/`ft^2` to m²; efficiency
  default 0.20).

### BESS (battery energy storage) — dedicated-transformer node
A BESS becomes a storage meter (`MeterType.BESS`) that dispatches autonomously:
frequency-reserve droop (discharge on under-frequency, charge on over-frequency,
holding a reserved SoC band) plus congestion relief (discharge when its local
transformer overloads). Author it on its **own node behind its own transformer**,
attached through an inverter like PV (or parented directly to the node):

```glm
object node { name "bess_bus"; nominal_voltage 400; }
object transformer { name "tr_bess"; from "feeder"; to "bess_bus"; }
object inverter { name "inv_bess"; parent "bess_bus"; rated_power 500000; } // 500 kW
object battery  { name "bat_1"; parent "inv_bess"; battery_capacity 2000000; } // 2000 kWh (Wh)
```
- **Power (kW)** = inverter `rated_power` (W÷1000) → else battery `rated_power` (W÷1000).
- **Energy (kWh)** = battery `battery_capacity` / `energy` / `capacity` (Wh÷1000).
- Bus resolution mirrors PV: `battery.parent` → inverter → `inverter.parent`; if the
  parent is a node (no inverter), the node itself is the bus.
- A large BESS is a natural **island DER slack** — `_build_zones` scores DER capacity as
  PV + BESS power, so a battery can hold a PV-less zone's voltage when islanded.
- SoC/reserve/droop/congestion tuning is via `BESS_*` env (`BESS_RESERVE_SOC_FLOOR`,
  `BESS_DROOP_PERCENT`, `BESS_CONGEST_HIGH_PCT`, …); GLM only sets power + energy.

### EV charging station — dedicated-transformer node
An EV station becomes a charging meter (`MeterType.EV_Charger`, or `DC_Fast_Charger`
for `evcharger_det`) modeled as a large constant-power additive load with a diurnal
utilization profile (no ZIP voltage scaling). Author it on its own transformer node:

```glm
object node { name "ev_bus"; nominal_voltage 400; }
object transformer { name "tr_ev"; from "feeder"; to "ev_bus"; }
object evcharger { name "ev_1"; parent "ev_bus"; charge_rate 60000; num_ports 6; } // 60 kW/port
```
- **Per-port kW** = `charge_rate` / `max_charge_rate` / `rated_power` / `power_rating` (W÷1000).
- `num_ports` (or `ports`) sets the number of charging bays (default 1).
- `evcharger_det`, or `charger_type DC`, marks a DC fast charger (higher default rating,
  midday-peaked profile). `parent` may be a node (direct bus) or an inverter.

### Transformer (optional — MV/LV or nested MV/MV units)
Couples two **existing** buses. `from` = primary (HV) terminal, `to` = secondary (LV).
Multiple transformers are supported (nested cascades and per-zone units); the single
external-grid slack auto-seats on the grid-edge HV bus (the HV terminal that is not any
transformer's LV side). When **no** transformer object is present the engine falls back to
the configured single feeder-head transformer (`TRANSFORMER_*`) above the substation bus.

```glm
object transformer_configuration {
    name "xfmr_cfg";
    connect_type WYE_WYE;
    power_rating 500;          // kVA   -> sn_mva 0.5
    primary_voltage 12700;     // informational; the ratio comes from the bus vn_kv
    secondary_voltage 240;
    resistance 0.011;          // per-unit R -> vkr% = R·100 = 1.1
    reactance 0.020;           // per-unit X -> vk%  = |R+jX|·100
}
object transformer {
    name "feeder_tx";
    phases ABCN;
    from "mv_src";             // HV bus (must exist)
    to "ref_lv_bus_1";         // LV bus (must exist)
    configuration "xfmr_cfg";  // links the config; omit to use TRANSFORMER_* defaults
}
```
- Voltage ratio is taken from the connected buses' `nominal_voltage` (L-N ×√3 for 3-phase),
  **not** from `primary_voltage`/`secondary_voltage` — size the bus voltages correctly.
- Missing `power_rating`/`resistance`/`reactance` fall back to the configured
  `TRANSFORMER_SN_MVA`/`VK_PERCENT`/`VKR_PERCENT` (and `PFE_KW`/`I0_PERCENT`).
- An HV tap is always created; the OLTC regulates the LV side when `TRANSFORMER_OLTC_ENABLED`.

### Microgrid zones — you don't author them, you author transformers

**There is no zone object and `groupid` does nothing.** A zone is *derived*: every bus under
the same transformer, i.e. one connected component of the line-only graph. So adding a
transformer creates a zone out of everything behind it, and that is the only way to make one.

- **Zone code** comes from the **PCC transformer's name**: pure int → itself; trailing digits
  (`pcc_3` → 3); otherwise a load-order counter. Name transformers with unique numeric
  suffixes and the codes are yours to pick — they become the parent bridge's `zone_<code>`
  telemetry partitions, so keep them stable.
- **Nested transformers split.** An inner MV/LV unit's buses form their own zone, separate
  from the outer unit's — there is no "which transformer owns this bus" ambiguity.
- **Normally-open ties are cut** from the partition, so a `status OPEN` switch between two
  zones can't merge them. A **closed** switch is an ordinary edge: it *will* fuse the buses on
  both sides into one zone (fed by whichever transformer is declared first).
- **Buses above every transformer are unzoned** (`zone_code 0`) — that's the grid edge, and
  unzoned meters omit `zone_code` on DLMS egress.
- Every derived zone has a PCC, so every zone is **islandable**. Whether it survives islanding
  is a separate question: it needs a DER member (PV or BESS) to hold voltage, else it goes dark.
- If a bus group is fed by **more than one** transformer, the loader logs a warning and uses
  the first as PCC — opening it alone will not island that zone.

## Validation rules (what `validate()` flags)

**Errors** (exit 1): no buses; duplicate bus name; line missing `from`/`to` or referencing a
nonexistent bus; load missing/nonexistent `parent`; PV with no resolvable bus; battery or EV
station with no resolvable bus; transformer missing a terminal, referencing a nonexistent
HV/LV bus, or with HV == LV.

**Warnings** (still exit 0): duplicate line name; duplicate transformer name; no inferable
substation; weakly-disconnected graph (`nx.is_weakly_connected` fails — usually an orphan bus
or a line endpoint typo; transformers count as graph edges so a transformer-only link keeps
the graph connected).

## Quick debugging map

- *"references missing bus"* → `from`/`to`/`parent` string doesn't exactly match a bus `name`.
- *PV count is 0 / lower than expected* → broken solar→inverter→bus chain, or `solar` parented
  directly to a bus instead of to an inverter.
- *`static_load_kw` looks 1000× off* → you put kW where the parser expects VA.
- *Lines exist but voltages look flat/wrong* → no impedance on lines/configs, so the
  `LINE_*` env fallbacks are being used; add `resistance_ohm_per_km`/`reactance_ohm_per_km`.
- *Object silently absent from summary* → object type not in the accepted set, or it's nested
  inside a skipped `module`/`class` block.
- *`num_batteries`/`num_ev_stations` is 0* → broken `battery`→inverter→bus chain, or the
  `battery`/`evcharger` `parent` doesn't resolve to a bus (check `summary()` counts).
