---
title: "VPP Orchestrator"
category: entities
created: 2026-04-10
updated: 2026-04-10
sources: ["src/smart_meter_simulator/core/vpp.py", "docs/architecture/market-engine.md", "src/rust_sim/src/lib.rs"]
tags: [vpp, dispatch, afrr, control]
related: [[aFRR]], [[Multi-Objective Dispatch]], [[Droop Control]], [[Frequency Regulator]], [[VPP Revenue Streams]]
---

# VPP Orchestrator

The `VPPManager` (Virtual Power Plant Orchestrator) aggregates distributed energy resources (DERs) into dispatchable clusters and executes multi-objective optimization for grid services.

## Summary

The VPP orchestrator groups meters by feeder/cluster, calculates aggregate flexibility, and dispatches individual setpoints using a weighted optimization: SoC balance (30%) + nodal price (40%) + carbon intensity (30%). It provides automatic Frequency Restoration Reserve (aFRR) and manual dispatch commands.

## Cluster Aggregation

Each VPP cluster tracks:
- **Total capacity** (kW/kWh) — sum of all DER resources
- **Aggregate flexibility** — upward (discharge) and downward (charge) headroom
- **State of Charge** — weighted average across cluster
- **Reputation score** — historical reliability of each resource
- **Health metric** — 0-100 score based on SoC balance + reputation

## Dispatch Algorithms

### aFRR (Automatic Frequency Restoration Reserve)

```python
def calculate_afrr(frequency_hz, max_flex_up, max_flex_down):
    deadband = 0.02  # Hz (20 mHz)
    deviation = frequency_hz - 50.0

    if abs(deviation) < deadband:
        return 0.0

    gain = 10.0  # MW/Hz scaled for simulation
    target = -deviation * gain

    # Clip to cluster limits
    if target > 0:
        return min(target, max_flex_up)
    else:
        return max(target, -max_flex_down)
```

### Multi-Objective Dispatch

For each resource in cluster:

```
weight = (soc_weight × 0.3 + price_weight × 0.4 + carbon_weight × 0.3) × reputation

where:
  soc_weight = SoC% / 100          (if discharging)
             = (100 - SoC%) / 100  (if charging)

  price_weight = price / 0.5       (if discharging — prefer high price)
               = 1 - (price / 0.5) (if charging — prefer low price)

  carbon_weight = intensity / 500  (if discharging)
                = 1 - (intensity / 500) (if charging)
```

Allocation: `dispatch_i = (weight_i / Σweight) × target_kw`, clipped to individual limits.

## Dispatch Result

| Field | Type | Description |
|-------|------|-------------|
| `dispatches` | Dict[str, float] | Per-meter setpoint (kW) |
| `carbon_saved_g` | float | Estimated CO₂ savings (grams) |
| `cluster_health` | float | 0-100 health score |
| `execution_time_us` | int | Dispatch computation time |

## Key Parameters

| Parameter | Value | Description |
|-----------|-------|-------------|
| `deadband_hz` | ±0.02 | Frequency deadband (20 mHz) |
| `droop_percent` | 5% | Standard droop curve |
| `dispatch_interval` | 15 min | Typical aFRR dispatch period |
| `soc_weight` | 30% | SoC balance priority |
| `price_weight` | 40% | Economic priority |
| `carbon_weight` | 30% | Environmental priority |

## Rust VPP Engine

The dispatch optimization is also implemented in Rust (`VPPDispatchEngine` in `src/rust_sim/src/lib.rs`) via PyO3:

| Meters | Rust (direct) | Rust (PyO3 FFI) |
|--------|---------------|-----------------|
| 50 | 15 µs | 33 µs |
| 100 | 33 µs | 1,380 µs |

## Relationships

- **Aggregates:** [[Smart Meter]] DER resources (battery, solar, EV)
- **Dispatched by:** [[Simulation Engine]] (tick cycle)
- **Frequency input:** [[Frequency Regulator]]
- **Price input:** [[LMP]] / [[Price Provider]]
- **Revenue from:** [[VPP Revenue Streams]]
- **Stored in:** [[InfluxDB Integration]] (vpp_cluster measurement)

## Known Issues

- FFI overhead for PyO3 dispatch is significant at small cluster sizes (1,380 µs vs 33 µs)
- Carbon weight assumes grid intensity is known — may need real-time feed
- Reputation score is static in simulation — no degradation/learning yet
