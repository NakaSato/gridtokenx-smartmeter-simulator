# The 80-bus Rural Reference Grid Dataset

This document explains the dataset bundled at
[`backend/data/80_bus_rural_reference_grid/`](../data/80_bus_rural_reference_grid/):
where it comes from, what each file contains, and exactly how the simulator
consumes it. The dataset is **external, published, read-only ground truth** — the
simulator does *not* generate it. It supplies a fixed feeder topology plus a full
year of measured hourly load, on top of which the device models (PV, ZIP, battery)
and the power-flow solver run.

---

## 1. Provenance

The folder is one grid from a four-grid open-access dataset published in
*Data in Brief*:

> L. M. Engan, S. Ekrheim, S. Bjarghov, J. R. A. Klemets, I. Schytte, G. Kjølle,
> "Reference dataset for semi-urban and rural Norwegian low voltage distribution
> grids," *Data in Brief*, vol. 59, art. 111453, 2025.
> DOI: [10.1016/j.dib.2025.111453](https://doi.org/10.1016/j.dib.2025.111453).
> Data: Zenodo [10.5281/zenodo.14528192](https://doi.org/10.5281/zenodo.14528192).
> License: **CC BY 4.0**.

The bundled PDF
[`1-s2.0-S2352340925001854-main.pdf`](../data/80_bus_rural_reference_grid/1-s2.0-S2352340925001854-main.pdf)
is that article. Key facts about the specific grid we ship:

- Created by the Norwegian research centre **CINELDI** (SINTEF Energy Research),
  anonymized from a **real** Norwegian distribution feeder.
- One of two **rural** grids in the dataset (the other is 50-bus). Rural = long
  lines, large voltage drops at peak — the 80-bus is the **weaker** of the two.
- Nominal voltage **230 V**, radial structure, price area **NO2**, load year **2021**.
- Load profiles are mostly **cabins and holiday homes**, so demand peaks in
  **summer and Easter** rather than winter — atypical of Norwegian households.
- Reported statistics (from the paper): mean yearly energy demand **8.17 MWh**,
  mean peak load **5.57 kWh/h**, lowest full-year power-flow voltage **0.854 p.u.**
- Deliberately **bare**: no PV, no EV charging, no storage in the raw data — those
  are exactly what this simulator layers on top so they stay customizable.

The files follow the **MATPOWER "case struct" (mpc)** convention, omitting columns
not needed for power flow.

---

## 2. Files in the folder

Verified against the shipped CSVs (headers and row counts below are real, not from
the paper).

| File | Rows | What it is |
| --- | --- | --- |
| `mpc_bus.csv` | 80 buses | Bus table — `bus_i,type,Pd,Qd,Gs,Bs,area,Vm,Va,basekV,zone,Vmax,Vmin` |
| `mpc_branch.csv` | 79 branches | Branch table — `,fbus,tbus,r,x,b,rateA,rateB,rateC,ratio,angle,status,angmin,angmax` |
| `mpc_base_mva.csv` | 1 value | Base power: **0.015967 MVA** |
| `p_load.csv` | 8760 hourly | Active-power time series, wide: `Date` + one column per **load** bus |
| `q_load.csv` | 8760 hourly | Reactive-power time series, same shape as `p_load` |
| `load_bus_extra.csv` | — | Per-load-bus metadata (`bus_i`, `Consumer type`) — *not* used for power flow |
| `branch_extra.csv` | — | Per-branch metadata (`From Bus`, `To Bus`, `Length [km]`, `Branch type`) — *not* used for power flow |
| `1-s2.0-S2352340925001854-main.pdf` | — | The source article |

Notes on shape:

- **80 buses, 32 of them are loads.** `p_load.csv` / `q_load.csv` carry only the
  load buses as columns: `Date,8,11,12,13,14,15,18,20,22,25,27,30,36,39,41,45,46,48,50,53,56,57,58,59,60,64,71,73,74,75,77,80`.
- **`Date` format** is `YYYY-MM-DD HH:MM:SS` (e.g. `2021-01-01 00:00:00`), hourly,
  8760 rows = one non-leap year.
- Power values are in **MW / MVAr**. `branch_extra.csv` line types are real cable
  specs (e.g. `EX 3x25 Al`) with span lengths in km.

---

## 3. How the simulator consumes it

The dataset feeds two distinct paths. Both key off the same folder; which one runs
depends on the config spec.

### 3a. As a topology — `GRID_TOPOLOGY=reference-grid:<folder>`

`adapters/reference_grid_loader.py:32` (`load_reference_grid_topology`) parses the
`mpc_*` files into the neutral `GridTopology` (buses / lines / loads), the same
shape the GLM path emits. Mapping:

- Each `mpc_bus.csv` row → a `GridBus` named `ref_lv_bus_<bus_i>`
  (`reference_grid_loader.py:19`, `reference_bus_name`).
- Each `mpc_branch.csv` row → a `GridLine` with `r`/`x`/`rateA` from the file.
- Each load bus → a `GridLoad`; its default meter id is also
  `ref_lv_bus_<bus_i>` (`reference_grid_loader.py:27`, `reference_meter_id`).
- `mpc_base_mva.csv` sets the per-unit base.

This gives the **fixed feeder** — buses, line impedances, ampacities — that
`core/grid_manager.py` solves each tick.

### 3b. As measured load telemetry — `TELEMETRY_SOURCE=reference-grid:<folder>`

`core/telemetry_source.py:191` (`ReferenceGridReplaySource`) replays the **hourly
load** as real telemetry overriding the synthetic device load. Per
`telemetry_source.py:222`:

- Reads `p_load.csv` (and `q_load.csv` if present), one column per load bus.
- Each cell becomes a `MeterTelemetry` for meter `ref_lv_bus_<bus_id>` with
  `cons_kw = value * 1000` and `reactive_kvar = q_value * 1000` —
  **MW/MVAr → kW/kVAr** (`telemetry_source.py:236`, `:238`).
- `poll(sim_time)` (`telemetry_source.py:271`) matches the sim clock to a row:
  exact UTC-hour hit first, then same calendar `(month, day, hour)`, then a
  day-of-year + hour index wrapped modulo the row count — so any sim start time
  lands on a real 2021 hour and the year loops seamlessly.

When this source drives a meter, the reading manager treats the cell as the
authoritative consumption and **skips synthetic load + battery** for that tick;
PV (if configured on that bus) and the power-flow solve still run on top.

The spec is parsed by `parse_telemetry_spec` (`telemetry_source.py:288`):
`reference-grid:<folder>`, `replay:<file.csv>`, or `synthetic`.

### Typical combined use

Point **both** at the folder to run the real Norwegian feeder with its real 2021
load, then add the simulator's PV/storage/controls:

```bash
# .env
GRID_TOPOLOGY=reference-grid:data/80_bus_rural_reference_grid
TELEMETRY_SOURCE=reference-grid:data/80_bus_rural_reference_grid
```

```bash
cd backend
uv run cli --mode validate-topology     # confirms the 80-bus grid parses
uv run cli --mode standalone --meters 80
```

---

## 4. What is and isn't ours

| Concern | Source |
| --- | --- |
| Feeder topology (80 buses, 79 lines, impedances, ampacities) | **Dataset** (CINELDI/SINTEF) |
| Hourly active/reactive load for one year | **Dataset** (real 2021 smart-meter measurements) |
| PV production, battery/BESS, EV | **Simulator** device models — *not* in the dataset |
| Power-flow solution (voltages, flows, losses, congestion) | **Simulator** (`grid_manager.py`, pandapower bfsw / DistFlow) |
| IEEE 1547 volt-watt / volt-VAR, droop, transformer/OLTC, faults | **Simulator** |

Bottom line: the dataset is the *measured world* (grid + demand); everything the
simulator publishes downstream is computed from it.

---

## 5. License and attribution

CC BY 4.0 — reuse is fine **with attribution**. Cite the *Data in Brief* article
(§1) in any report or paper. A BibTeX entry is in
[`references.bib`](references.bib) under `engan2025reference`.
