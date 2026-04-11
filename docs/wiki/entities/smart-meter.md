---
title: "Smart Meter"
category: entities
created: 2026-04-10
updated: 2026-04-10
sources: ["src/smart_meter_simulator/core/meter.py", "docs/architecture/smart-meter.md", "docs/reference/meter-spec.md"]
tags: [meter, crypto, battery, ev]
related: [[Ed25519 Signing]], [[ANSI C12.20 Accuracy Classes]], [[EnergyReading Model]], [[Measurement Noise Model]], [[Net Metering]]
---

# Smart Meter

The `SmartMeter` class represents a single simulated smart meter in the GridTokenX ecosystem. Each meter has its own Ed25519 keypair, accuracy class, energy profile, and optional DER (battery, solar, EV) capabilities.

## Summary

A Smart Meter generates cryptographically signed energy readings at each simulation tick. It models realistic measurement noise based on ANSI C12.20 accuracy classes, implements frequency-watt droop control for grid stability, and manages battery/EV charge-discharge cycles.

## Core Components

### Identity & Cryptography
- **Ed25519 Keypair** — Generated on initialization, used for Solana-compatible reading signatures
- **Meter ID** — Unique identifier (e.g., `AMI_METER_001`)
- **Meter Type** — Solar_Prosumer, Grid_Consumer, Hybrid_Prosumer, Battery_Storage, EV_Charger

### Accuracy Classes (ANSI C12.20)

| Class | Error Range | Typical Use |
|-------|-------------|-------------|
| CLASS_0_2 | ±0.2% | Substation metering |
| CLASS_0_5 | ±0.5% | Feeder head meters |
| CLASS_1_0 | ±1.0% | Commercial/Prosumer |
| CLASS_2_0 | ±2.0% | Residential meters |

Measurement noise: `σ = (Class / 300) × |Value|`

Example: CLASS_1_0 (1.0) with 5.0 kW reading → σ = (1.0/300) × 5000 = 16.67 W

### Energy Profile
Each reading includes:
- `energy_generated_kwh` — Solar/renewable generation
- `energy_consumed_kwh` — Load consumption
- `surplus_energy` — Net export (gen > cons)
- `deficit_energy` — Net import (cons > gen)
- `battery_level_kwh` — Current battery state
- `voltage_v`, `current_a`, `frequency_hz` — Electrical parameters
- `power_factor`, `reactive_power` — Power quality metrics

### Battery/EV Logic
- **Charge** when surplus > 0 (stores excess generation)
- **Discharge** when deficit > 0 (covers shortfall)
- **V2G (Vehicle-to-Grid)** — EV meters can export during peak demand
- **Capacity limits** enforced per meter configuration

### Frequency-Watt Droop Control
- **Nominal frequency:** 50 Hz
- **Droop:** 5% (standard grid-tied inverter response)
- **Deadband:** ±0.02 Hz (20 mHz) — no response within deadband
- **Response:** Reduce generation when frequency rises, increase when it drops

## Key Parameters

| Parameter | Range/Default | Description |
|-----------|---------------|-------------|
| `accuracy_class` | 0.2, 0.5, 1.0, 2.0 | Measurement precision |
| `solar_capacity` | 3-15 kW | Peak solar generation |
| `battery_capacity` | 10-30 kWh | Total battery storage |
| `battery_efficiency` | 0.90-0.95 | Round-trip efficiency |
| `panel_efficiency` | 0.85-0.95 | Solar panel conversion |
| `price_elasticity` | ~0.15 | Consumption response to price signals |

## Relationships

- **Created by:** [[Meter Generator]]
- **Managed by:** [[Simulation Engine]]
- **Signed with:** [[Ed25519 Signing]]
- **Noise model:** [[Measurement Noise Model]]
- **Grid mapping:** [[Pandapower Adapter]]
- **Market role:** Surplus/deficit feeds into [[Market Engine]]
- **VPP control:** [[VPP Orchestrator]] dispatches setpoints

## Known Issues

- Battery state is simplified (no degradation model, no temperature effects)
- Solar curve uses sin² pattern — real irradiance data not yet supported
- EV charging patterns are stochastic — no real driving profile integration
