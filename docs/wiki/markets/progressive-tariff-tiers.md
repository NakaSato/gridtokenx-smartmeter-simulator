---
title: "Progressive Tariff Tiers"
category: markets
created: 2026-04-10
updated: 2026-04-10
sources: ["docs/reference/thai-tariffs.md", "src/smart_meter_simulator/config/thai_market.py"]
tags: [thai, tariff, progressive, residential]
related: [[Thai Electricity Market]], [[TOU Tariffs]], [[Net Metering]]
---

# Progressive Tariff Tiers

Progressive tariff tiers charge increasing rates as monthly consumption volume rises, incentivizing energy conservation. This is the default residential tariff in Thailand, used by customers who do not opt for TOU pricing.

## Summary

Thai residential tariffs use three progressive tiers: consumption is split into blocks, each priced higher than the previous. A customer using 500 kWh/month pays tier-1 rates for the first 150 kWh, tier-2 for the next 250 kWh, and tier-3 for the remaining 100 kWh.

## Tier Structure

| Tier | Range (kWh/month) | Rate (Baht/kWh) | Description |
|------|-------------------|-----------------|-------------|
| 1 | 0-150 | 3.24 | Lifeline rate (basic needs) |
| 2 | 151-400 | 4.22 | Normal consumption |
| 3 | 400+ | 4.42 | High consumption |

Service charge: 38.22 Baht/month

## Calculation Example

Customer using 500 kWh/month:

```
Tier 1: 150 × 3.24 = 486.00 Baht
Tier 2: 250 × 4.22 = 1,055.00 Baht
Tier 3: 100 × 4.42 = 442.00 Baht
Energy subtotal:         1,983.00 Baht
Ft adjustment: 500 × 0.0972 = 48.60 Baht
Service charge:           38.22 Baht
Subtotal:               2,069.82 Baht
VAT (7%):                144.89 Baht
Total:                  2,214.71 Baht
```

**Effective average rate:** 2,214.71 / 500 = 4.43 Baht/kWh

## Comparison with TOU

| Monthly Usage | Progressive | TOU (On:Off = 60:40) | Cheaper |
|---------------|------------|----------------------|---------|
| 100 kWh | 324 + 38 + Ft + VAT ≈ 420 | 100 × weighted avg + 33 + Ft + VAT ≈ 410 | TOU (barely) |
| 300 kWh | ≈ 1,290 | ≈ 1,150 | TOU |
| 500 kWh | ≈ 2,215 | ≈ 1,850 | TOU |
| 800 kWh | ≈ 3,670 | ≈ 2,800 | TOU |

TOU becomes more attractive as consumption increases and as the customer can shift load to off-peak.

## Social Policy

The progressive tier structure serves social policy objectives:

| Tier | Purpose |
|------|---------|
| Tier 1 (0-150) | Subsidized rate for low-income households |
| Tier 2 (151-400) | Cost-recovery for typical consumption |
| Tier 3 (400+) | Cross-subsidy — high users pay more |

The lifeline rate (3.24 Baht) is below the marginal cost of supply, subsidized by Tier 3 customers.

## Standard Load Profiles with Progressive Tariffs

The H0 (residential) SLP determines how much consumption falls into each tier:

| Profile | Typical Monthly | Dominant Tier |
|---------|----------------|---------------|
| Small household | 100-200 kWh | Tier 1 |
| Average family | 300-500 kWh | Tier 2-3 |
| Large household with AC | 600+ kWh | Tier 3 |

## Relationships

- **Alternative:** [[TOU Tariffs]]
- **Market context:** [[Thai Electricity Market]]
- **Net metering:** [[Net Metering]] (FiT applies regardless of tier)
- **Implementation:** `config/thai_market.py`

## Known Issues

- Tier thresholds fixed — not indexed to inflation
- No seasonal adjustment (hot season consumption naturally higher)
- Service charge (38.22 Baht) differs from TOU (33.29 Baht)
- No time-differentiated tiers (could combine progressive + TOU)
