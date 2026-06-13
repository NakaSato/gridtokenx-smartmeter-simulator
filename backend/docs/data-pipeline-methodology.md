# Simulation Data Pipeline: A Methodological Description

**An academic-style account of the data flow from topology and telemetry inputs
through the device and feeder models to signed metering output.**

> Scope. This document presents the simulator's per-tick computation as a formal
> methodology, complementing the mathematical formulation in
> [`modeling-equations.md`](modeling-equations.md) and the operational guide in
> [`data-pipeline-and-model-usage.md`](data-pipeline-and-model-usage.md). It is
> written in the register of a methods section: numbered stages, defined
> notation, and architectural justification, with implementation evidence given
> as `file:line` citations into `backend/src/smart_meter_simulator/`. The
> real-telemetry data source (Stage I, §3.1) is documented in
> [`realtime-telemetry.md`](realtime-telemetry.md); feature-level framing in
> [`backend-core-features-academic-report.md`](backend-core-features-academic-report.md).
> Index: [`README.md`](README.md).

---

## Abstract

We describe a topology-aware Advanced Metering Infrastructure (AMI) digital twin
that couples behavioural device models to an exact distribution-feeder power
flow. The system ingests a GridLAB-D feeder topology and an optional stream of
real meter telemetry, generates per-meter energy readings through a chain of
photovoltaic, load, droop, and storage models, resolves the resulting bus
voltages by an iterative AC power flow with embedded IEEE 1547 inverter controls,
and exports cryptographically signed DLMS/COSEM readings for downstream
settlement. The simulation advances as a discrete-time dynamical system in which
voltage and frequency are coupled across successive ticks by a deliberate
one-step feedback delay.

---

## 1. Introduction and design rationale

The simulator is structured around a single architectural commitment:
**separation of behavioural generation from physical resolution**. Device models
(§4) decide how much energy each meter produces and consumes, expressed as a
power injection; the feeder model (§5) decides what voltages, flows, and losses
those injections imply on the physical network. The two are connected only
through aggregated bus quantities and a one-tick voltage feedback (§3.3). This
separation yields three properties relevant to a research instrument:

1. **Testability.** Behavioural models are pure, CPU-bound functions that can be
   exercised in isolation, without a power-flow solver or an event loop.
2. **Substitutability of the data source.** A meter's injection may originate
   from a synthetic model or from replayed real telemetry; the feeder model is
   indifferent to which (§4.4).
3. **Physical fidelity where it matters.** The network is resolved by an exact
   AC solver appropriate to radial low-voltage feeders, not a reduced linear
   surrogate, except as a graceful fallback (§5.4).

---

## 2. Notation and discrete-time formulation

Let $k \in \{0, 1, 2, \dots\}$ index simulation ticks of fixed length
$\Delta t$ seconds, with $h = \Delta t / 3600$ the interval in hours. Let
$\mathcal M$ denote the set of meters and $\mathcal B$ the set of feeder buses,
with a fixed surjection $\beta : \mathcal M \to \mathcal B$ assigning each meter
to a bus (`grid_manager.py:77`). For meter $m$ at tick $k$ we write
$P^{\mathrm{gen}}_{m,k}$ and $P^{\mathrm{con}}_{m,k}$ for generation and
consumption power; the resulting energy reading is the interval integral
$E_{m,k} = P_{m,k}\,h$.

The simulator is a discrete-time dynamical system whose state vector carries
three persistent quantities between ticks:

$$
\mathbf x_k = \big(\;\underbrace{V_{b,k}}_{\text{bus voltages}},\;
\underbrace{f_k}_{\text{system frequency}},\;
\underbrace{\mathrm{SoC}_{m,k}}_{\text{battery charge}}\;\big).
$$

Each tick computes $\mathbf x_{k+1}$ and the reading set
$\{E_{m,k}\}_{m\in\mathcal M}$ from $\mathbf x_k$ and any exogenous telemetry.

---

## 3. Pipeline architecture

The per-tick computation, implemented by `SimulationEngine.tick()`
(`core/engine.py:219`), proceeds in five stages.

### 3.1 Stage I — Exogenous telemetry application

Before any model runs, the engine polls the configured telemetry source at the
current simulation timestamp (`engine.py:248`–`274`). Where a real frame supplies
a meter, its consumption, generation, reactive power, and frequency are recorded
as one-shot overrides. Overrides are *consumed and cleared* within the same tick
(`reading_manager.py:67`–`72`), so telemetry must be re-supplied each tick to
persist — a design that makes partial coverage (some meters real, others
synthetic) the natural hybrid case rather than a special one.

### 3.2 Stage II — Behavioural reading generation

The reading manager (`reading_manager.py:15`) evaluates the device chain for
every meter. Because this work is CPU-bound, it is dispatched off the event loop
via `asyncio.to_thread` (`reading_manager.py:28`), preserving the
non-blocking property of the asynchronous server. For each meter the manager
first resolves the meter's bus voltage from the **previous** tick's solution
(`reading_manager.py:50`–`54`) and passes it into the model chain (§4).

### 3.3 Stage III — Physical resolution

The grid manager (`grid_manager.py:292`) aggregates the readings to per-bus net
real and reactive injections and resolves the network by AC power flow (§5),
producing the bus voltages $V_{b,k}$ that Stage II will consume at tick $k+1$.
This *one-tick voltage feedback* — load at tick $k$ responds (through the ZIP
model, §4.2) to voltage from tick $k-1$ — is the central temporal coupling of
the system. It is a deliberate model of finite control/measurement latency, not
an artefact; an instantaneous fixed point would conflate the metering interval
with the electrical settling time.

### 3.4 Stage IV — Frequency update

The aggregate generation–load imbalance over all readings sets the system
frequency for the next tick (`engine.py:288`–`296`, §5.1 of the equations doc),
which the meters' droop controllers (§4.3) react to one tick later. Frequency
thus carries the same one-step lag as voltage, modelling primary governor
response.

### 3.5 Stage V — Egress

Finally, readings are emitted to optional sinks — the Aggregator Bridge over the
DLMS/COSEM REST contract and a PostGIS store — each non-blocking and each
dropping a tick if its prior batch is still in flight (`engine.py:240`–`243`).
Egress never back-pressures the simulation loop.

The dependency structure is summarised below; the dashed edge is the inter-tick
feedback that makes the system dynamical rather than a sequence of independent
snapshots.

```
 telemetry ─┐
            ▼
       [II] reading      ──►  [III] power flow  ──►  [IV] frequency  ──►  [V] egress
       generation             (bus voltages)         (f_{k+1})
            ▲                        │
            └───────── V_{b,k-1} ◄───┘   (one-tick feedback, §3.3)
```

---

## 4. Behavioural model chain

For a single meter, `SmartMeter.generate_reading` (`devices/ami.py:66`) composes
the models in a fixed order, each stage consuming the previous stage's output.

### 4.1 Generation

Photovoltaic output is computed by a physics-based PVWatts chain (clear-sky
irradiance, cell-temperature derating, inverter model) or a sinusoidal fallback
(`devices/solar.py`; equations §2). When a generation override is present it
replaces the model output (`ami.py:81`–`85`).

### 4.2 Demand under voltage dependence

Consumption is drawn from a time-of-day behavioural profile and then made
voltage-dependent through the ZIP model (`devices/load.py`; equations §3), using
the bus voltage carried from the previous tick (§3.2). This is the mechanism
through which network conditions feed back into demand.

### 4.3 Primary frequency response

Frequency-watt droop throttles generation as a function of the system frequency
deviation (`core/meter_logic/electrical.py:6`; equations §5.2), closing the
primary-response loop initiated by Stage IV.

### 4.4 Behind-the-meter storage

On synthetic ticks only, a self-consumption battery dispatches against the
residual household balance (`devices/battery.py`; equations §4), with its state
of charge persisting across ticks as part of $\mathbf x_k$. Storage is bypassed
under telemetry override, since the measured net exchange already embeds any
real battery's effect (`ami.py:108`).

### 4.5 Measurement synthesis

Finally, secondary electrical quantities — voltage, current, power factor, and
reactive power — are synthesised with accuracy-class measurement noise
(`electrical.py:19`; equations §11) to populate the OBIS-coded reading.

The substitutability noted in §1 is realised precisely at this chain: a
telemetry override short-circuits stages 4.1–4.4 for the affected meter while
leaving the feeder model (§5) unchanged, so synthetic and measured meters are
resolved on the same physical network within a single tick.

---

## 5. Physical resolution model

The feeder model aggregates readings to bus injections and resolves them on a
`pandapower` network constructed once at initialisation from the neutral
`GridTopology` (`grid_manager.py:143`). The solver, control loops, transformer
model, contingency handling, and approximate fallback are specified in the
equations document, §6–§10; we summarise their methodological role here.

- **Solver selection (§6).** A backward/forward sweep is attempted first as the
  algorithm suited to radial low-voltage feeders, with Newton–Raphson as a
  second attempt, reflecting the poor conditioning of plain NR on high
  per-unit-impedance chains.
- **Embedded inverter controls (§7).** IEEE 1547 volt-VAR and volt-watt
  functions are solved *inside* the power-flow fixed point, reactive support
  before real-power curtailment — a sequential, non-co-optimised control order
  that mirrors standard utility practice.
- **Feeder-head regulation (§8).** An optional MV/LV transformer with an on-load
  tap changer regulates the substation voltage before local curtailment acts,
  so bulk and local voltage control are cleanly separated.
- **Contingency and graceful degradation (§9–10).** Fault injection removes
  elements before each solve to study N-1 reconfiguration and islanding; genuine
  non-convergence falls back to a linearised DistFlow sweep, preserving a usable
  (if approximate) result rather than failing the tick.

---

## 6. Inputs, outputs, and reproducibility

**Inputs.** (i) A feeder topology, supplied once as a GridLAB-D `.glm` file via
the `GRID_TOPOLOGY` specification and normalised to a `GridTopology`
(`core/topology_factory.py`); (ii) an optional telemetry stream; (iii) a set of
environment-driven parameters governing every model, accessed through a single
cached configuration object (`config/settings.py`) rather than ad-hoc reads, so
that an experiment is fully specified by its `.glm` file and its environment.

**Outputs.** Per-meter `EnergyReading` objects and a grid summary each tick,
exported to the REST API unconditionally and, when enabled, to the Aggregator
Bridge (signed DLMS/COSEM) and a PostGIS store; Prometheus counters expose
timing and failure rates.

**Reproducibility.** Because the topology, the data source, and every model
parameter are externalised as declarative inputs, a run is reproducible from its
`.glm` topology and environment alone. The behavioural models inject Gaussian
measurement noise (equations §2, §3, §11); a deterministic replay therefore
requires either disabling that noise or fixing the process random seed.

---

## 7. Summary

The pipeline realises a clean separation between *what energy is exchanged*
(behavioural device models, possibly overridden by real telemetry) and *what the
network does about it* (an exact AC feeder solve with embedded standards-based
controls), coupled across time by a single-tick voltage and frequency feedback.
This structure makes the simulator a controllable, reproducible instrument for
studying prosumer distribution grids: each model is independently testable, the
data source is swappable without touching the physics, and the physical
resolution is exact where it can be and gracefully approximate where it cannot.

---

### Implementation evidence index

| Stage / model | Source |
| --- | --- |
| Per-tick orchestration | `core/engine.py:219` |
| Telemetry override | `core/engine.py:248`–`274`, `reading_manager.py:67`–`72` |
| Reading generation (threaded) | `core/reading_manager.py:15`–`75` |
| Per-meter model chain | `devices/ami.py:66` |
| PV / load / droop / battery / measurement | `devices/solar.py`, `devices/load.py`, `core/meter_logic/electrical.py`, `devices/battery.py` |
| Bus aggregation + power flow | `core/grid_manager.py:292`, `:375` |
| Network construction | `core/grid_manager.py:143` |
| Frequency update | `core/engine.py:288` |
| Egress | `core/engine.py:240`–`243` |
| Configuration | `config/settings.py` |
