---
title: "Standard Load Profiles"
category: concepts
created: 2026-04-10
updated: 2026-04-10
sources: ["docs/reference/thai-tariffs.md", "src/smart_meter_simulator/config/settings.py"]
tags: [load, profiles, consumption, slp]
related: [[Measurement Noise Model]], [[TOU Tariffs]], [[Meter Generator]]
---

# Standard Load Profiles (SLP)

Standard Load Profiles (SLPs) are representative consumption curves derived from historical meter data. They provide baseline consumption patterns for different customer categories when real-time data is unavailable.

## Summary

The simulator uses two primary SLPs: H0 (residential) with morning and evening peaks, and G0 (commercial) with business-hours concentration. These profiles shape the base consumption pattern before price elasticity and noise are applied.

## H0 Profile (Residential)

Typical residential consumption pattern:

```
Consumption
    ↑
1.5 |          *                    *
    |         * *                  * *
1.0 |    *   *   *        *      *   *
    |   * * *     *      * *    *     *
0.5 |  *             *  *    * *       *
    | *               **                *
0.0 +------------------------------------→ Hour
    0   4   8   12   16   20   24
         ↑Morning    ↑Evening peak
         peak
```

| Period | Factor | Description |
|--------|--------|-------------|
| 00:00-06:00 | 0.3-0.5 | Night baseline |
| 06:00-09:00 | 0.8-1.2 | Morning peak (cooking, heating) |
| 09:00-17:00 | 0.4-0.6 | Daytime low (empty house) |
| 17:00-22:00 | 1.0-1.5 | Evening peak (cooking, TV, AC) |
| 22:00-24:00 | 0.3-0.5 | Night decline |

## G0 Profile (Commercial)

Typical small business consumption pattern:

| Period | Factor | Description |
|--------|--------|-------------|
| 00:00-07:00 | 0.1-0.2 | Closed hours (refrigeration only) |
| 07:00-09:00 | 0.4-0.8 | Opening ramp |
| 09:00-17:00 | 1.5-2.0 | Business hours (HVAC, lighting, equipment) |
| 17:00-19:00 | 0.8-1.2 | Closing ramp down |
| 19:00-24:00 | 0.1-0.3 | After hours |

## Weekday vs. Weekend

| Profile | Weekday | Weekend |
|---------|---------|---------|
| H0 (Residential) | Morning + evening peaks | Flatter, higher baseline |
| G0 (Commercial) | Full business hours | 30% of weekday load |

## Application in Simulator

```python
# Consumption = base × profile_factor × price_response + noise
consumption = base_consumption * slp_factor(hour, weekday) * price_elasticity_response
consumption += brownian_noise(consumption * 0.015)
```

The SLP provides the **deterministic** shape; Brownian motion provides the **stochastic** variation.

## Thai Context

Thai residential profiles are influenced by:
- **Air conditioning** — dominant load (30-50% of consumption in hot season)
- **Cooking patterns** — morning (06:00-08:00) and evening (17:00-20:00)
- **Hot season** (Mar-May) — higher daytime AC usage
- **Rainy season** (Jun-Oct) — shifted indoor activity

## Relationship to TOU

SLPs interact with TOU tariffs:

| Scenario | Effect |
|----------|--------|
| High SLP during on-peak | Expensive — encourages demand response |
| High SLP during off-peak | Cheap — no incentive to shift |
| EV charging at night | Off-peak → benefits from low TOU rate |
| Battery charging | Can shift to off-peak for savings |

## Relationships

- **Used in:** [[Measurement Noise Model]] (consumption shape)
- **Pricing interaction:** [[TOU Tariffs]]
- **Source data:** [[Meter Generator]]
- **Time series:** [[Brownian Motion Simulation]]

## Known Issues

- Profiles are generic — not calibrated to Thai-specific data
- No seasonal variation in SLP shape (only weather factor scales)
- No customer diversity within each profile category
- Industrial/large commercial profiles not defined
