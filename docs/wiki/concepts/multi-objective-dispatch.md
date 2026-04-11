---
title: "Multi-Objective Dispatch"
category: concepts
created: 2026-04-10
updated: 2026-04-10
sources: ["src/smart_meter_simulator/core/vpp.py", "src/rust_sim/src/lib.rs", "docs/architecture/market-engine.md"]
tags: [vpp, optimization, dispatch, multi-objective]
related: [[VPP Orchestrator]], [[aFRR]], [[LMP]], [[VPP Revenue Streams]]
---

# Multi-Objective Dispatch

Multi-objective dispatch is the optimization algorithm that distributes a VPP cluster's total power target among individual DER resources, balancing three competing objectives: SoC balance, economic value, and carbon impact.

## Summary

The dispatch algorithm assigns a weighted score to each resource based on its state of charge (30%), nodal price (40%), and carbon intensity (30%), then allocates power proportionally. The result maximizes economic return while maintaining cluster health and minimizing environmental impact.

## Objective Functions

### 1. SoC Balance (Weight: 30%)

**Goal:** Keep all batteries at similar SoC levels to maximize cluster availability.

```
If discharging (target > 0):
  soc_weight = SoC% / 100    → Prefer high-SoC batteries

If charging (target < 0):
  soc_weight = (100 - SoC%) / 100  → Prefer low-SoC batteries
```

**Why:** Prevents some batteries from being overused while others sit idle.

### 2. Nodal Price (Weight: 40%)

**Goal:** Maximize revenue by dispatching resources at the most favorable prices.

```
If discharging (target > 0):
  price_weight = price / 0.5   → Prefer high-price nodes

If charging (target < 0):
  price_weight = 1 - (price / 0.5)  → Prefer low-price nodes
```

**Why:** Discharging at high-price nodes earns more; charging at low-price nodes costs less.

### 3. Carbon Intensity (Weight: 30%)

**Goal:** Maximize carbon displacement by dispatching when/where grid is dirtiest.

```
If discharging (target > 0):
  carbon_weight = intensity / 500   → Prefer high-intensity periods

If charging (target < 0):
  carbon_weight = 1 - (intensity / 500)  → Prefer low-intensity periods
```

**Why:** Discharging during high-carbon periods displaces fossil generation.

## Combined Weight

```
weight_i = (soc_weight_i × 0.3 + price_weight_i × 0.4 + carbon_weight_i × 0.3) × reputation_i
```

The reputation multiplier penalizes unreliable resources (historical non-delivery).

## Allocation

```
total_weight = Σ weight_i

For each resource:
  raw_dispatch = (weight_i / total_weight) × target_kw
  dispatch = clip(raw_dispatch, -max_flex_down, max_flex_up)
```

If total_weight ≤ 0 (edge case), fallback to equal distribution.

## Example

Three-battery cluster, target = +5 kW (discharge):

| Meter | SoC | Price | Carbon | Reputation | Weight | Dispatch |
|-------|-----|-------|--------|------------|--------|----------|
| A | 80% | 0.35 | 400 | 1.0 | 0.62 | 2.1 kW |
| B | 50% | 0.25 | 250 | 0.9 | 0.41 | 1.4 kW |
| C | 30% | 0.40 | 350 | 0.8 | 0.44 | 1.5 kW |

Meter A gets the most dispatch because it has high SoC, good price, and high carbon intensity.

## Implementation

Available in both Python (`core/vpp.py`) and Rust (`src/rust_sim/src/lib.rs` via `VPPDispatchEngine.dispatch()`).

## Relationships

- **Used by:** [[VPP Orchestrator]]
- **Price input:** [[LMP]] / [[Price Provider]]
- **Flexibility from:** [[aFRR]]
- **Revenue from:** [[VPP Revenue Streams]]

## Known Issues

- Weight ratios (30/40/30) are hardcoded — not configurable
- Carbon intensity assumed constant per dispatch interval — no real-time feed
- Reputation score is static — no learning from actual delivery performance
- No constraint for ramp rate limits (batteries can jump from 0 to max instantly)
