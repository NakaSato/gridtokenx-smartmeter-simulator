---
title: "State Estimator"
category: entities
created: 2026-04-10
updated: 2026-04-10
sources: ["src/smart_meter_simulator/adapters/state_estimator.py", "docs/architecture/grid-integration.md", "docs/reference/pandapower.md"]
tags: [grid, estimation, wls, bad-data]
related: [[State Estimation]], [[Bad Data Detection]], [[Pandapower Adapter]], [[Pseudo-Measurements]]
---

# State Estimator

The `StateEstimator` implements Weighted Least Squares (WLS) and Iwamoto algorithms for grid state estimation, with chi-squared testing and normalized residuals for bad data detection.

## Summary

State estimation determines the true operating state of the power grid from noisy, potentially erroneous meter readings. It uses redundant measurements to produce the most likely voltage magnitudes and phase angles at every bus.

## Algorithms

### Weighted Least Squares (WLS)
- **Method:** Newton-Raphson iterative solver
- **Measurement model:** z = h(x) + e, where z = measurements, x = state, e = noise
- **Weighting:** Inverse of measurement variance (from accuracy class std_dev)
- **Convergence:** Typically 3-5 iterations

### Iwamoto Method
- **Purpose:** Handles divergence cases where WLS fails
- **Method:** Modified Newton step with optimal multiplier
- **Use case:** Ill-conditioned systems, low redundancy, bad initial guess

## Bad Data Detection

### Chi-Squared Test
```
J(x̂) = Σ w_i × (z_i - h_i(x̂))²
Reject if: J(x̂) > χ²(ν, α)
Where: ν = m - n (redundancy), α = significance level (typically 0.01)
```

### Normalized Residuals
```
r_N_i = |z_i - h_i(x̂)| / σ_residual_i
Flag as bad data if: |r_N| > 3.0 (3-sigma threshold)
```

### Largest Normalized Residual Test
- Identifies the single most suspect measurement
- Remove and re-estimate iteratively until all residuals pass

## Measurement Types

| Type | Description | Weight Source |
|------|-------------|---------------|
| Real (P) | Active power injection/flow | Accuracy class std_dev |
| Reactive (Q) | Reactive power injection/flow | Accuracy class std_dev |
| Voltage (V) | Bus voltage magnitude | Accuracy class std_dev |
| Current (I) | Line current magnitude | Accuracy class std_dev |
| Pseudo (zero-injection) | Buses with no load/generation | Very high weight |

## Key Parameters

| Parameter | Value | Description |
|-----------|-------|-------------|
| `max_iterations` | 20 | WLS convergence limit |
| `tolerance` | 1e-6 | State update convergence threshold |
| `chi_squared_alpha` | 0.01 | Significance level for bad data test |
| `residual_threshold` | 3.0 | 3-sigma threshold for normalized residuals |
| `nominal_frequency` | 50.0 Hz | Grid nominal frequency |

## Relationships

- **Input from:** [[Pandapower Adapter]] (measurement table conversion)
- **Input from:** [[Smart Meter]] (signed readings)
- **Uses:** [[Pseudo-Measurements]] for observability improvement
- **Feeds:** [[Simulation Engine]] (estimation results)
- **Stored in:** [[InfluxDB Integration]] (grid_state_estimation measurement type)

## Known Issues

- Divergence possible with low measurement redundancy (< 2×)
- Unrealistic R/X ratios in grid topology cause numerical instability
- Iwamoto method is slower but more robust — should be fallback
- Virtual measurements (zero-injection) assume perfect knowledge — may mask real errors
