---
title: "State Estimation"
category: concepts
created: 2026-04-10
updated: 2026-04-10
sources: ["docs/architecture/grid-integration.md", "docs/reference/pandapower.md", "src/smart_meter_simulator/adapters/state_estimator.py"]
tags: [grid, algorithm, estimation, wls]
related: [[State Estimator]], [[Bad Data Detection]], [[Pseudo-Measurements]], [[Pandapower Adapter]]
---

# State Estimation

State estimation is the mathematical process of determining the most likely operating state of a power grid from noisy, redundant, and potentially erroneous measurements.

## Summary

In the Smart Meter Simulator, state estimation uses Weighted Least Squares (WLS) optimization to find voltage magnitudes and phase angles at every bus. The estimated state is more accurate than any individual measurement because it leverages redundancy and statistical filtering.

## Why It Matters

Real power grids don't have perfect sensors. Every measurement has noise, some have gross errors, and not every point is instrumented. State estimation:
1. **Filters noise** — weighted averaging reduces random error
2. **Detects bad data** — statistical tests identify faulty sensors
3. **Fills gaps** — pseudo-measurements estimate unmonitored points
4. **Enables control** — dispatch decisions need accurate state knowledge

## WLS Algorithm

The core optimization problem:

```
minimize:  J(x) = [z - h(x)]ᵀ W⁻¹ [z - h(x)]

where:
  x = state vector (voltage magnitudes + angles)
  z = measurement vector (P, Q, V, I readings)
  h(x) = measurement functions (power flow equations)
  W = covariance matrix (diagonal, from accuracy class std_dev)
```

Solved iteratively via Gauss-Newton:
```
x_{k+1} = x_k + (Hᵀ W⁻¹ H)⁻¹ Hᵀ W⁻¹ [z - h(x_k)]
```

Where H is the Jacobian of h(x).

## Observability

A system is **observable** if the state can be uniquely determined from measurements.

**Rule of thumb:** m ≥ 2n (measurements ≥ 2× state variables)

**Redundancy ratio:** r = m / (2n - 1)
- r < 1: Unobservable (need pseudo-measurements)
- r ≈ 2: Adequate (typical distribution grid)
- r > 5: Highly redundant (transmission-level)

## Pseudo-Measurements

When physical meters are insufficient:
- **Zero-injection buses:** Buses with no load/generation (KCL constraint)
- **Virtual flow measurements:** Known line status (open/closed)
- **Standard load profiles:** Historical consumption curves

These are assigned very high weights (low variance) to act as soft constraints.

## Iwamoto Method

When WLS diverges (ill-conditioned H matrix):
```
x_{k+1} = x_k + μ × Δx
```
Where μ is an optimal step size multiplier (0 < μ ≤ 1) chosen to minimize the cost function along the search direction. More robust than WLS but slower.

## Relationships

- **Implemented in:** [[State Estimator]]
- **Measurement source:** [[Pandapower Adapter]]
- **Quality check:** [[Bad Data Detection]]
- **Improves:** [[Pseudo-Measurements]]

## Known Issues

- Distribution grids often have low redundancy (r ≈ 1.5-2.0)
- R/X ratios in distribution networks violate transmission assumptions
- Real-time PMU data not modeled — only SCADA-rate (15s) readings
