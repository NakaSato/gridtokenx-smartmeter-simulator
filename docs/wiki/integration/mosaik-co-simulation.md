---
title: "Mosaik Co-Simulation"
category: integration
created: 2026-04-10
updated: 2026-04-10
sources: ["src/smart_meter_simulator/adapters/mosaik_adapter.py", "docs/architecture/simulation-engine.md"]
tags: [cosimulation, mosaik, federated, multi-domain]
related: [[Simulation Engine]], [[CIM RDF/XML]]
---

# Mosaik Co-Simulation

Mosaik is a modular co-simulation orchestration framework that enables multi-domain simulation — coupling power system simulators, communication network simulators, and market models in a single federated experiment.

## Summary

The Smart Meter Simulator includes a Mosaik adapter that allows it to participate as a co-simulation federate, exchanging meter readings and grid state data with other simulation domains (e.g., NS-3 for network simulation, MATSim for transport modeling).

## Architecture

```
┌─────────────────────────────────────────────────┐
│                  Mosaik Orchestrator             │
│  ┌────────────┐  ┌──────────────┐  ┌─────────┐ │
│  │ Smart Meter│  │ Comm Network │  │ Market  │ │
│  │ Simulator  │  │ (NS-3/OMNeT) │  │ Model   │ │
│  │ (Federate) │  │ (Federate)   │  │(Federate)│ │
│  └─────┬──────┘  └──────┬───────┘  └────┬────┘ │
│        │                │                │       │
│        └────────────────┼────────────────┘       │
│              Data exchange (per step)             │
└─────────────────────────────────────────────────┘
```

## Federate Role

The Smart Meter Simulator federate provides:

| Output | Input |
|--------|-------|
| Meter readings (energy, voltage, current) | Communication delays/packet loss |
| Grid state (frequency, voltage profile) | Market clearing prices |
| VPP dispatch signals | Demand response events |

## Co-Simulation Step

```
Time t:
  1. Mosaik advances all federates to t
  2. Smart Meter Simulator generates readings
  3. Mosaik routes readings to Comm Network federate
  4. Comm Network applies delays/errors
  5. Mosaik routes (delayed) readings to Market federate
  6. Market federate computes clearing prices
  7. Mosaik routes prices back to Smart Meter Simulator
  8. All federates advance to t + step_size
```

## Adapter Interface

```python
class MosaikAdapter:
    def __init__(self, config):
        self.mosaik_config = config

    def start(self, sid):
        # Register with Mosaik orchestrator
        pass

    def create(self, num, model, **params):
        # Create simulation entities
        pass

    def step(self, time, inputs, max_advance):
        # Execute one co-simulation step
        # inputs: data from other federates
        # returns: outputs to other federates
        pass

    def get_data(self, outputs):
        # Return requested data
        pass
```

## Use Cases

| Scenario | Federates Involved |
|----------|-------------------|
| AMI communication latency | Smart Meter + NS-3 (network) |
| Market response to DER | Smart Meter + Market model |
| EV fleet charging | Smart Meter + MATSim (transport) |
| Building energy management | Smart Meter + Building simulator |

## Configuration

Mosaik is an optional dependency:

```toml
[project.optional-dependencies]
mosaik = ["mosaik>=3.3.0"]
```

Install with: `uv sync --extra mosaik`

## Limitations

The current adapter is a stub — full co-simulation requires:
1. Mosaik installation and scenario configuration
2. Scenario file defining federates and data exchanges
3. Proper time synchronization handling

## Relationships

- **Adapter:** `src/smart_meter_simulator/adapters/mosaik_adapter.py`
- **Orchestration:** [[Simulation Engine]]
- **Data exchange:** [[CIM RDF/XML]] (topology)

## Known Issues

- Adapter is a stub — not functional co-simulation
- Mosaik not included in Docker stack
- No scenario files provided
- Time step synchronization not implemented
- Optional dependency not commonly installed
