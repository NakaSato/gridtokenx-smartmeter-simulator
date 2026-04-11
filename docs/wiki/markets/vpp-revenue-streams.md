---
title: "VPP Revenue Streams"
category: markets
created: 2026-04-10
updated: 2026-04-10
sources: ["docs/reference/economic-models.md", "docs/architecture/market-engine.md"]
tags: [vpp, economics, revenue, ancillary]
related: [[VPP Orchestrator]], [[aFRR]], [[P2P Energy Trading]], [[Carbon Offset Model]]
---

# VPP Revenue Streams

A Virtual Power Plant generates revenue through multiple streams: ancillary services (aFRR), peak shaving, P2P trading commissions, and carbon credit sales. The optimal mix depends on cluster composition, market prices, and grid conditions.

## Summary

VPP revenue is aggregated from four sources: frequency regulation payments, demand charge reduction, P2P market commissions, and carbon offset credits. Each stream has different risk profiles and revenue certainty.

## Revenue Breakdown

### 1. aFRR (Frequency Regulation)

| Component | Rate | Description |
|-----------|------|-------------|
| Capacity payment | ~50-100 €/MW-h reserved | Paid for being available |
| Energy payment | Market rate × delivered energy | Paid for actual dispatch |
| Penalty | Capacity payment × 2 | Non-delivery penalty |

**Revenue certainty:** High (contracted in advance)
**Revenue risk:** Medium (depends on frequency events)

### 2. Peak Shaving (Demand Charge Reduction)

For commercial/industrial customers with demand charges:

```
savings = (peak_demand_before - peak_demand_after) × demand_charge_rate
```

| Parameter | Typical Value |
|-----------|--------------|
| Demand charge | 150-300 Baht/kW-month |
| Peak reduction | 10-30% of peak |
| Billing period | Monthly |

**Revenue certainty:** High (predictable load pattern)
**Revenue risk:** Low (savings are guaranteed if battery available)

### 3. P2P Trading Commission

The VPP operator earns a small commission on P2P trades:

```
commission = traded_kwh × commission_rate
commission_rate ≈ 0.05-0.10 Baht/kWh
```

| Volume | Commission Rate | Monthly Revenue |
|--------|----------------|-----------------|
| 100 kWh/day | 0.05 Baht | 150 Baht |
| 500 kWh/day | 0.05 Baht | 750 Baht |
| 1,000 kWh/day | 0.05 Baht | 1,500 Baht |

**Revenue certainty:** Medium (depends on P2P market activity)
**Revenue risk:** Medium (market maturity dependent)

### 4. Carbon Credits

```
carbon_credits = displaced_kwh × grid_intensity_gCO2/kWh / 1,000,000
carbon_revenue = carbon_credits × carbon_price_per_ton
```

| Parameter | Value |
|-----------|-------|
| Grid intensity (Thailand) | ~400 gCO₂/kWh |
| Carbon price | ~200-500 Baht/ton CO₂ |
| Revenue per MWh displaced | ~80-200 Baht |

**Revenue certainty:** Low (voluntary market, price volatility)
**Revenue risk:** High (market still developing)

## Revenue Comparison

| Stream | Revenue/kWh | Certainty | Risk |
|--------|------------|-----------|------|
| aFRR capacity | 0.05-0.10 Baht | High | Low |
| aFRR energy | Market rate | Medium | Medium |
| Peak shaving | 0.10-0.30 Baht | High | Low |
| P2P commission | 0.05 Baht | Medium | Medium |
| Carbon credits | 0.08-0.20 Baht | Low | High |

## Optimization

The VPP dispatch algorithm ([[Multi-Objective Dispatch]]) implicitly optimizes revenue by:
1. Prioritizing high-price nodes for discharge (40% weight)
2. Balancing SoC for future availability (30% weight)
3. Maximizing carbon displacement when profitable (30% weight)

### Revenue-Maximizing Strategy

| Market Condition | Optimal Strategy |
|-----------------|------------------|
| High aFRR price | Reserve capacity for frequency regulation |
| High on-peak TOU | Discharge during on-peak, charge off-peak |
| High P2P demand | Participate in P2P market |
| High carbon price | Maximize carbon displacement |

## Example: 100 kW / 200 kWh Battery Cluster

| Stream | Monthly Revenue |
|--------|----------------|
| aFRR capacity | 15,000 Baht |
| aFRR energy | 8,000 Baht |
| Peak shaving | 12,000 Baht |
| P2P commission | 2,000 Baht |
| Carbon credits | 3,000 Baht |
| **Total** | **40,000 Baht/month** |

Assumes: 50% utilization, moderate market conditions.

## Relationships

- **Orchestrated by:** [[VPP Orchestrator]]
- **aFRR mechanism:** [[aFRR]]
- **P2P market:** [[P2P Energy Trading]]
- **Carbon tracking:** [[Carbon Offset Model]]
- **Optimization:** [[Multi-Objective Dispatch]]

## Known Issues

- Revenue rates are estimates — actual rates depend on TSO contracts
- Carbon credit market is voluntary in Thailand — no mandatory scheme
- P2P commission rate not standardized
- Peak shaving savings depend on customer demand profile
