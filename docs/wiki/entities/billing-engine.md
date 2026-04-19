---
title: "Billing Engine"
category: entities
created: 2026-04-19
updated: 2026-04-19
sources: ["src/smart_meter_simulator/core/billing.py"]
tags: [billing, thai, tariff, net-metering]
related: [[Price Provider]], [[Net Metering]], [[Progressive Tariff Tiers]], [[TOU Tariffs]]
---

# Billing Engine

The Billing Engine manages the accumulation of energy readings and the calculation of periodic bills for all smart meters in the simulation.

## Summary

It implements three distinct billing methods: Thai Time-of-Use (TOU) tariffs, ERC progressive ladder rates (progressive tiers), and net metering with Feed-in Tariff (FiT) credits. It tracks consumption and generation in both on-peak and off-peak periods to provide accurate cost breakdowns.

## Details

### Billing Methods
1. **TOU (Time-of-Use):** Uses `on_peak` (5.7982) and `off_peak` (2.6369) rates with a monthly service charge, Ft adjustment, and VAT.
2. **ERC (Progressive Ladder):** Implements a 3-tier progressive rate based on total monthly consumption (0-150, 151-400, 400+ kWh).
3. **Net Metering:** Bills consumption at retail rates and provides a credit for exported energy at the FiT rate (2.20 Baht/kWh).

### Meter Registration
Meters are registered with a specific tariff category (e.g., Residential 1.2 or Small Business 2.2). The engine maintains `MeterBillingRecord` objects to accumulate energy totals between billing cycles.

## Key Parameters

| Parameter | Value | Description |
|-----------|-------|-------------|
| `FT_CHARGE` | 0.0972 | Fuel adjustment per kWh |
| `VAT_RATE` | 0.07 | Value Added Tax (7%) |
| `FiT_RATE` | 2.20 | Net metering export credit |
| `PEAK_HOURS` | 09:00 - 22:00 | Mon-Fri on-peak period |

## Relationships

- **Input from:** [[Smart Meter]] readings via the engine.
- **Rates from:** [[TOU Tariffs]], [[Progressive Tariff Tiers]].
- **Pricing Logic:** [[Price Provider]].

## Known Issues

- Monthly service charges are pro-rated per reading in some contexts but treated as fixed in others.
- The net metering implementation simplifies retail rates to on-peak averages for the deficit portion.
- Public holiday detection is not currently implemented in the `is_on_peak` logic.
