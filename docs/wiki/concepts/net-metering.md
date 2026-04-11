---
title: "Net Metering"
category: concepts
created: 2026-04-10
updated: 2026-04-10
sources: ["docs/reference/thai-tariffs.md", "docs/reference/economic-models.md"]
tags: [meter, economics, fit, billing]
related: [[Smart Meter]], [[TOU Tariffs]], [[Progressive Tariff Tiers]], [[P2P Energy Trading]]
---

# Net Metering

Net metering is the billing mechanism where prosumers are credited for surplus energy exported to the grid, offsetting their consumption charges. The simulator supports both traditional net metering and P2P trading models.

## Summary

When a prosumer generates more energy than consumed in a billing period, the surplus is exported to the grid and credited at the Feed-in Tariff (FiT) rate. If consumption exceeds generation, the deficit is imported and charged at the retail rate.

## Calculation

```python
net_energy = energy_generated - energy_consumed

if net_energy > 0:
    # Prosumer exports surplus
    revenue = net_energy × FiT_rate
elif net_energy < 0:
    # Prosumer imports deficit
    cost = abs(net_energy) × retail_rate

# Net bill over billing period
bill = Σ(cost) - Σ(revenue) + service_charge + VAT
```

## FiT vs. Retail Rate

| Rate | Value | Description |
|------|-------|-------------|
| **FiT (Feed-in Tariff)** | ~2.20 Baht/kWh | Utility buys surplus from prosumer |
| **Retail (on-peak)** | ~5.80 Baht/kWh | Prosumer buys from utility |
| **Retail (off-peak)** | ~2.64 Baht/kWh | Prosumer buys from utility |
| **P2P clearing** | 2.50-4.50 Baht/kWh | Direct prosumer-to-consumer |

The FiT rate is typically lower than the retail rate, creating an incentive gap:
- **Export earns:** 2.20 Baht/kWh
- **Import costs:** 5.80 Baht/kWh (on-peak)
- **Net benefit of self-consumption:** 5.80 - 2.20 = 3.60 Baht/kWh

This drives prosumers to maximize self-consumption (via battery storage) rather than exporting.

## Thai Progressive Tariff Net Metering

For residential customers without TOU:

| Tier | Range (kWh/month) | Rate (Baht/kWh) |
|------|-------------------|-----------------|
| 1 | 0-150 | 3.24 |
| 2 | 151-400 | 4.22 |
| 3 | 400+ | 4.42 |

Surplus export credits apply at the FiT rate regardless of tier.

## Battery Arbitrage

With battery storage, prosumers can:

1. **Store surplus** instead of exporting at low FiT
2. **Discharge during on-peak** to avoid high retail imports
3. **Charge from grid during off-peak** (2.64 Baht) and discharge during on-peak (5.80 Baht avoided cost)

### Example

| Scenario | Without Battery | With Battery |
|----------|----------------|--------------|
| Solar generation | 30 kWh | 30 kWh |
| Consumption | 20 kWh | 20 kWh |
| Self-consumed | 15 kWh | 25 kWh (stored 10 kWh) |
| Exported (FiT) | 15 kWh × 2.20 = 33 Baht | 5 kWh × 2.20 = 11 Baht |
| Imported (retail) | 5 kWh × 5.80 = 29 Baht | 0 kWh = 0 Baht |
| **Net bill** | 29 - 33 = **-4 Baht** (credit) | **0 Baht** |
| **Value** | 4 Baht credit | Saved 29 Baht import |

Battery round-trip efficiency (90%) must be factored — storing 10 kWh delivers ~9 kWh usable.

## Relationships

- **Energy calculation:** [[Smart Meter]] (surplus/deficit)
- **Tariff rates:** [[TOU Tariffs]], [[Progressive Tariff Tiers]]
- **Alternative:** [[P2P Energy Trading]]
- **VPP value:** [[VPP Revenue Streams]] (battery optimization)

## Known Issues

- FiT rate subject to ERC policy changes (not modeled)
- No monthly/yearly netting (simulator uses per-interval calculation)
- No demand charge impact from net metering
- Thai net metering policy may differ from simulated model
