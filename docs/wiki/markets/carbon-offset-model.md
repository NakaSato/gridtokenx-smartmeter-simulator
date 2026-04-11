---
title: "Carbon Offset Model"
category: markets
created: 2026-04-10
updated: 2026-04-10
sources: ["docs/reference/economic-models.md", "src/smart_meter_simulator/config/settings.py"]
tags: [carbon, economics, environment, credits]
related: [[VPP Revenue Streams]], [[P2P Energy Trading]], [[Multi-Objective Dispatch]]
---

# Carbon Offset Model

The carbon offset model tracks and monetizes the carbon emissions displaced by renewable energy generation and VPP dispatch actions, enabling carbon credit generation for the GridTokenX ecosystem.

## Summary

Carbon savings are calculated from the difference between grid-sourced energy and renewable-sourced energy, multiplied by the grid's carbon intensity. The resulting credits can be sold in voluntary carbon markets or used for REC (Renewable Energy Certificate) certification.

## Carbon Intensity

### Thai Grid Baseline

| Parameter | Value | Source |
|-----------|-------|--------|
| Grid intensity | ~400 gCO₂/kWh | Thailand TGO (2024) |
| Natural gas mix | 60% of generation | EGAT |
| Coal | 20% of generation | EGAT |
| Renewables | 15% of generation | EGAT |
| Imports | 5% | Laos hydro |

### Carbon Intensity by Time

In the simulator, carbon intensity can vary by time of day:

| Period | Intensity (gCO₂/kWh) | Reason |
|--------|---------------------|--------|
| On-peak (daytime) | 350-450 | Solar reduces daytime intensity |
| On-peak (evening) | 450-550 | Gas peakers ramp up |
| Off-peak (night) | 400-500 | Baseload (coal + gas) |

## Carbon Savings Calculation

### Per-Reading

```python
# Renewable energy displaces grid energy
carbon_saved_kg = energy_generated_kwh × grid_intensity_gco2 / 1000

# Battery discharge during high-carbon periods
if grid_intensity > threshold:
    carbon_saved_kg += battery_discharge_kwh × grid_intensity_gco2 / 1000
```

### Cumulative

```python
total_carbon_saved_kg = Σ(carbon_saved_per_interval)
carbon_credits_tons = total_carbon_saved_kg / 1000
```

## Carbon Credit Pricing

| Market | Price Range (Baht/ton CO₂) | Description |
|--------|--------------------------|-------------|
| Thailand VCM (voluntary) | 200-500 | Voluntary Carbon Market |
| Regional (Asia) | 300-800 | Regional carbon exchanges |
| International (EU ETS) | 2,000-3,000 | Not accessible for Thai projects |

Simulator default: **0.7 Baht/kWh** carbon offset value (derived from ~400 gCO₂/kWh × ~500 Baht/ton / 1000).

## Revenue from Carbon

| Scenario | Monthly Generation | Carbon Saved | Revenue (500 Baht/ton) |
|----------|-------------------|-------------|----------------------|
| 10 solar homes | 3,000 kWh | 1.2 tons CO₂ | 600 Baht |
| 100 solar homes | 30,000 kWh | 12 tons CO₂ | 6,000 Baht |
| 1 MW VPP cluster | 150,000 kWh | 60 tons CO₂ | 30,000 Baht |

Carbon revenue is modest compared to energy revenue but provides an additional incentive layer.

## Carbon in VPP Dispatch

The [[Multi-Objective Dispatch]] algorithm includes carbon as a 30% weighted objective:

```
carbon_weight = intensity / 500   (if discharging)
              = 1 - (intensity / 500)   (if charging)
```

This dispatches batteries to discharge during high-carbon periods (displacing fossil generation) and charge during low-carbon periods (absorbing renewable surplus).

## REC (Renewable Energy Certificate)

RECs certify the environmental attributes of renewable energy:

| Attribute | Description |
|-----------|-------------|
| 1 REC = | 1 MWh of renewable generation |
| Issued to | Generator/Prosumer |
| Traded | Separately from energy |
| Solana | Minted as NFT on Energy Token Program |

### REC Value Chain

```
Solar Generation → Ed25519 Signed Reading → Oracle Verification → REC Minting → Sale
```

## Carbon Tracking in InfluxDB

Carbon intensity is stored as a measurement:

```
Measurement: carbon_intensity
Fields: intensity_gco2_kwh, carbon_saved_g
Tags: region
```

## Relationships

- **Revenue stream:** [[VPP Revenue Streams]]
- **Dispatch weight:** [[Multi-Objective Dispatch]]
- **P2P attribute:** [[P2P Energy Trading]] (green premium)
- **REC minting:** [[Solana Integration]]

## Known Issues

- Grid intensity is static — not real-time marginal emission rate
- Carbon credit market is voluntary — no guaranteed buyer
- REC certification requires third-party verification (not modeled)
- No additionality test (would the renewable have been built anyway?)
- No double-counting prevention (same MWh claimed by multiple parties)
