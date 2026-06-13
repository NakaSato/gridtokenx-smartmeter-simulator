# Backend Documentation Index

Documentation for the GridTokenX Smart Meter Simulator **backend**. Start here.
Each entry is scoped; the math, the methodology, the how-to, and the feature
prose are separate documents that cross-reference each other.

## Modeling and methodology

| Document | What it is | Read it for |
| --- | --- | --- |
| [`modeling-equations.md`](modeling-equations.md) | Mathematical formulation — every device, load, and power-flow equation, cited to `file:line`. | The governing math: PV, ZIP, battery, droop, AC power flow, IEEE 1547 controls, transformer/OLTC, DistFlow, faults, measurement. |
| [`data-pipeline-methodology.md`](data-pipeline-methodology.md) | Academic methods-section account of the per-tick data flow. | *Why* the pipeline is shaped this way — discrete-time formalism, the one-tick voltage/frequency feedback, behavioural/physical separation. |
| [`data-pipeline-and-model-usage.md`](data-pipeline-and-model-usage.md) | Operational guide to running, configuring, and extending the models. | *How* to drive it — tick diagram, env→equation map, fault API, calling a model directly, adding a model. |
| [`references.bib`](references.bib) | BibTeX bibliography. | Citing the standards and papers behind the models (IEEE 1547, PVWatts, DistFlow, pandapower, DLMS/COSEM, …). |

## Features and integration

| Document | What it is | Read it for |
| --- | --- | --- |
| [`backend-core-features-academic-report.md`](backend-core-features-academic-report.md) | Prose summary of backend contributions for a paper/report. | High-level academic framing of each feature with implementation evidence. |
| [`realtime-telemetry.md`](realtime-telemetry.md) | Real-telemetry replay and the meter→bus registry. | Driving the simulator from measured data, hybrid runs, pinning meters to buses. |
| [`reference-grid-dataset.md`](reference-grid-dataset.md) | The bundled CINELDI/MATPOWER 80-bus rural grid — provenance, file formats, how the loader and telemetry source consume it. | Where `backend/data/80_bus_rural_reference_grid/` comes from and how to run the real Norwegian feeder with its 2021 load. |

## Suggested reading order

1. **Orientation** — repo [`README.md`](../README.md) (quick start, API surface, config) and
   [`backend-core-features-academic-report.md`](backend-core-features-academic-report.md) (what the backend does).
2. **The math** — [`modeling-equations.md`](modeling-equations.md).
3. **The pipeline** — [`data-pipeline-methodology.md`](data-pipeline-methodology.md) (the why),
   then [`data-pipeline-and-model-usage.md`](data-pipeline-and-model-usage.md) (the how).
4. **Real data** — [`realtime-telemetry.md`](realtime-telemetry.md).
5. **Citing** — [`references.bib`](references.bib).

> Conventions: architectural claims are backed by `file:line` citations into
> `backend/src/smart_meter_simulator/`. Re-verify citations against the tree
> before publishing — line numbers drift as code changes.
