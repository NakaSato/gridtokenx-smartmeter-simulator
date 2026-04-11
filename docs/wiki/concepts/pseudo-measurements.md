---
title: "Pseudo-Measurements"
category: concepts
created: 2026-04-10
updated: 2026-04-10
sources: ["docs/reference/pandapower.md", "docs/architecture/grid-integration.md"]
tags: [grid, estimation, observability, virtual]
related: [[State Estimation]], [[State Estimator]], [[Bad Data Detection]]
---

# Pseudo-Measurements

Pseudo-measurements are virtual (non-physical) measurements injected into the state estimation process to improve observability when physical meter coverage is insufficient.

## Summary

In distribution grids with sparse metering, pseudo-measurements provide soft constraints that enable state estimation to converge. They represent known or assumed quantities — zero-injection buses, scheduled generation, and historical load profiles — assigned very high weights to act as anchors.

## Types

### Zero-Injection Buses

Buses with no load or generation satisfy Kirchhoff's Current Law:

```
Σ I_in = Σ I_out  →  P_net = 0, Q_net = 0
```

These are assigned:
- **Value:** P = 0 MW, Q = 0 MVAR
- **Weight:** Very high (σ = 0.001 MW → 1000× weight of typical meter)

### Scheduled Generation

Known DER output (solar farm, wind turbine with SCADA):

```
P_scheduled = nameplate_capacity × capacity_factor
```

Weight based on SCADA accuracy (typically ±2-5%).

### Historical Load Profiles

When no real-time meter exists at a bus:

```
P_estimated = SLP_factor(hour, weekday) × contracted_capacity
```

Weight based on profile uncertainty (typically ±20-30%).

## Weight Assignment

| Measurement Type | σ (per unit) | Relative Weight |
|-----------------|--------------|-----------------|
| Physical meter (Class 0.2) | 0.002 | 250,000 |
| Physical meter (Class 2.0) | 0.02 | 2,500 |
| Scheduled generation | 0.05 | 400 |
| Historical load profile | 0.20 | 25 |
| Zero-injection bus | 0.001 | 1,000,000 |

Weight = 1/σ²

## Impact on Observability

| Scenario | Physical Meters | Pseudo-Measurements | Redundancy Ratio |
|----------|-----------------|--------------------|-----------------|
| Dense AMI | 50 | 0 | r = 2.5 (good) |
| Sparse AMI | 15 | 35 (zero-injection) | r = 2.5 (good) |
| Minimal | 5 | 45 | r = 2.5 (acceptable) |

Without pseudo-measurements, sparse AMI would yield r < 1 (unobservable).

## Bad Data Risk

Pseudo-measurements can **mask** real errors:

| Risk | Description |
|------|-------------|
| Zero-injection assumed wrong | Bus actually has unmetered load |
| SLP outdated | Load pattern has changed (new appliance, EV) |
| Scheduled gen incorrect | Cloud cover reduces solar below schedule |

Mitigation: Assign realistic (not overly tight) weights to pseudo-measurements.

## Implementation

In the state estimator:

```python
# For each zero-injection bus
for bus in zero_injection_buses:
    measurement_table.add(
        element_type='bus',
        element=bus.id,
        meas_type='p',
        value=0.0,
        std_dev=0.001  # Very high weight
    )
    measurement_table.add(
        element_type='bus',
        element=bus.id,
        meas_type='q',
        value=0.0,
        std_dev=0.001
    )
```

## Relationships

- **Used by:** [[State Estimator]]
- **Purpose:** [[State Estimation]] (observability)
- **Risk:** [[Bad Data Detection]] (masking)
- **Grid model:** [[Pandapower Adapter]]

## Known Issues

- Zero-injection assumption may be violated by unmetered DER
- SLP-based pseudo-measurements have high uncertainty
- No adaptive weighting based on estimation quality
- No mechanism to validate pseudo-measurement accuracy post-estimation
