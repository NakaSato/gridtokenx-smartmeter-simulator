---
title: "Price Provider"
category: entities
created: 2026-04-19
updated: 2026-04-19
sources: ["src/smart_meter_simulator/core/price_provider.py"]
tags: [price, thai, market, p2p]
related: [[Billing Engine]], [[TOU Tariffs]], [[P2P Energy Trading]], [[LMP]]
---

# Price Provider

The Price Provider module manages electricity rates for both traditional utility billing and dynamic Peer-to-Peer (P2P) energy trading.

## Summary

It provides services for calculating Thai Time-of-Use (TOU) rates, simulating P2P market clearing prices (MCP) based on supply/demand, and comparing costs between utility and P2P options. It acts as the source of truth for pricing signals used across the simulator.

## Details

### TOU Tariff Provider
Calculates utility costs using standardized Thai rates:
- **FT Charge:** 0.0972 Baht/kWh.
- **VAT:** 7%.
- **Categories:** Supports Residential, Small Business, Medium Business, and Large Industrial tariffs.

### P2P Market Provider
Generates dynamic clearing prices based on:
- **Base Price:** 3.50 Baht/kWh with random walk fluctuations.
- **Supply/Demand Ratio:** Prices drop with oversupply and rise with shortages.
- **TOU Period:** Prices are inflated by 15% during on-peak and discounted by 15% during off-peak.
- **Nodal Price:** Optionally anchors to nodal prices from the grid engine.

### Comparison Service
Provides decision support by analyzing savings for buyers and revenue gains for sellers when switching from utility to P2P models.

## Key Parameters

| Parameter | Value | Description |
|-----------|-------|-------------|
| `P2P_MIN_PRICE` | 1.50 | Floor for P2P trading (Baht/kWh) |
| `P2P_MAX_PRICE` | 6.00 | Ceiling for P2P trading (Baht/kWh) |
| `WHEELING_RESIDENTIAL` | 0.35 | Grid usage fee for residential P2P |
| `GRID_LOSS_FACTOR` | 0.08 | Estimated 8% technical loss |

## Relationships

- **Feeds:** [[Billing Engine]]
- **Determines:** [[P2P Energy Trading]] clearing
- **Context from:** [[TOU Tariffs]]
- **Anchor to:** [[LMP]]

## Known Issues

- The current MCP calculation is a statistical simulation; it does not use a real-time order book matching engine (which is handled by the `MarketEngine`).
- Wheeling charges are fixed and not dynamically calculated based on electrical distance.
