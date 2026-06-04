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

## Validation rules (what `validate()` flags)

**Errors** (exit 1): no buses; duplicate bus name; line missing `from`/`to` or referencing a
nonexistent bus; load missing/nonexistent `parent`; PV with no resolvable bus.

**Warnings** (still exit 0): duplicate line name; no inferable substation; weakly-disconnected
graph (`nx.is_weakly_connected` fails — usually an orphan bus or a line endpoint typo).

## Quick debugging map

- *"references missing bus"* → `from`/`to`/`parent` string doesn't exactly match a bus `name`.
- *PV count is 0 / lower than expected* → broken solar→inverter→bus chain, or `solar` parented
  directly to a bus instead of to an inverter.
- *`static_load_kw` looks 1000× off* → you put kW where the parser expects VA.
- *Lines exist but voltages look flat/wrong* → no impedance on lines/configs, so the
  `LINE_*` env fallbacks are being used; add `resistance_ohm_per_km`/`reactance_ohm_per_km`.
- *Object silently absent from summary* → object type not in the accepted set, or it's nested
  inside a skipped `module`/`class` block.
