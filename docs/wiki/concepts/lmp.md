---
title: "LMP"
category: concepts
created: 2026-04-10
updated: 2026-04-10
sources: ["docs/reference/economic-models.md", "docs/architecture/market-engine.md"]
tags: [market, pricing, nodal, congestion]
related: [[Market Engine]], [[Double Auction]], [[P2P Energy Trading]], [[Multi-Objective Dispatch]], [[Price Provider]]
---

# LMP (Locational Marginal Pricing)

Locational Marginal Pricing is a nodal pricing mechanism that reflects the true marginal cost of delivering one additional MWh of electricity at each specific location (bus) in the grid, accounting for energy costs, transmission congestion, and losses.

## Summary

In the Smart Meter Simulator, LMP is approximated from nodal prices derived from grid topology, VPP dispatch costs, and local supply/demand imbalance. It provides price signals that vary by location, reflecting real grid conditions.

## LMP Components

```
LMP_node = Energy + Congestion + Losses
```

| Component | Description | Typical Range |
|-----------|-------------|---------------|
| **Energy** | System-wide marginal cost (reference bus) | 0.20-0.35 Baht/kWh |
| **Congestion** | Cost from transmission constraints | 0.00-0.10 Baht/kWh |
| **Losses** | Marginal loss cost (I²R heating) | 0.01-0.05 Baht/kWh |

## How It Works

### Energy Component

Based on the system lambda (marginal cost of the most expensive generator needed to meet demand):

```
Energy = max(marginal_cost_of_all_online_generators)
```

In the simulator: derived from VPP dispatch cost and grid purchase rate.

### Congestion Component

When a transmission line reaches its thermal limit, cheaper generation on one side cannot serve load on the other side. The congestion cost is the price difference:

```
Congestion_node = λ_reference - λ_node  (when constrained)
```

In the simulator: approximated from feeder loading and substation capacity.

### Loss Component

Power losses increase with distance from the source. The marginal loss at each node:

```
Loss_factor_node = ∂(Total Losses) / ∂(Load at node)
Loss_component = Loss_factor × Energy_price
```

In the simulator: approximated from electrical distance to substation.

## Nodal Price Map

In a typical radial distribution feeder:

```
Substation (reference)  →  0.28 Baht/kWh
  ├── Bus 1 (close)     →  0.29 Baht/kWh  (+losses)
  ├── Bus 2 (mid)       →  0.31 Baht/kWh  (+losses + congestion)
  └── Bus 3 (far)       →  0.35 Baht/kWh  (+losses + congestion)
```

End-of-feeder nodes pay more because delivering energy there costs more.

## Use in Simulator

| Application | How LMP is Used |
|-------------|-----------------|
| **P2P Trading** | Clearing price for matched orders |
| **VPP Dispatch** | Price weight in [[Multi-Objective Dispatch]] |
| **Billing** | Node-specific tariff for consumers |
| **Signal** | Price encourages demand response at congested nodes |

## Relationship to TOU Tariffs

| Property | TOU Tariff | LMP |
|----------|-----------|-----|
| **Granularity** | Time-based (on/off peak) | Location + time |
| **Variability** | 2 prices per day | N prices per node |
| **Reflects** | Time-of-generation cost | True marginal cost |
| **Complexity** | Simple | Complex |
| **Signal** | When to consume | When AND where to consume |

## Relationships

- **Computed by:** [[Market Engine]]
- **Used by:** [[Multi-Objective Dispatch]] (price weight)
- **Compared to:** [[Price Provider]] (TOU tariffs)
- **Settled via:** [[P2P Energy Trading]]

## Known Issues

- Full AC-OPF not implemented — LMP is approximated
- Congestion based on thermal limits only — no voltage constraints
- Loss factors are static — no real-time power flow calculation
- No market power mitigation (generators can't strategically raise prices)
