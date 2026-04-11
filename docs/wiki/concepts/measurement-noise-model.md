---
title: "Measurement Noise Model"
category: concepts
created: 2026-04-10
updated: 2026-04-10
sources: ["docs/reference/meter-spec.md", "docs/architecture/smart-meter.md", "src/smart_meter_simulator/core/meter.py"]
tags: [meter, accuracy, noise, statistics]
related: [[Smart Meter]], [[ANSI C12.20 Accuracy Classes]], [[Bad Data Detection]], [[Brownian Motion Simulation]]
---

# Measurement Noise Model

The measurement noise model simulates realistic meter inaccuracies using ANSI C12.20 accuracy classes. Every electrical parameter reading has Gaussian noise scaled to the meter's precision class and the magnitude of the measured value.

## Summary

Each measurement is perturbed by zero-mean Gaussian noise with standard deviation proportional to the reading value and the accuracy class rating. This produces realistic data where cheap meters are noisier and large readings have larger absolute errors.

## Core Formula

```python
sigma = (accuracy_class / 300.0) × |value| × multiplier
noisy_reading = random.normal(value, sigma)
```

### Parameters

| Parameter | Description |
|-----------|-------------|
| `accuracy_class` | ANSI class: 0.2, 0.5, 1.0, or 2.0 |
| `value` | True value of the measurement |
| `multiplier` | Type-specific scaling (1.0 for P/Q, 0.5 for power factor, 0.1 for frequency) |

### Denominator (300)

The factor of 300 maps ANSI accuracy class to a reasonable σ:
- Class 2.0 (residential) at 5 kW: σ = (2.0/300) × 5000 = 33.3 W (0.67%)
- Class 0.2 (substation) at 5 kW: σ = (0.2/300) × 5000 = 3.3 W (0.067%)

This is slightly tighter than the ANSI specification (which defines maximum error, not σ).

## Per-Parameter Multipliers

| Parameter | Multiplier | Reasoning |
|-----------|-----------|-----------|
| Active power (P) | 1.0 | Primary measurement |
| Reactive power (Q) | 1.0 | Primary measurement |
| Voltage (V) | 1.0 | Primary measurement |
| Current (I) | 1.0 | Primary measurement |
| Power factor | 0.5 | Derived quantity, naturally bounded [0, 1] |
| Frequency | 0.1 | Very stable in real grids (±0.1 Hz typical) |

## Accuracy Class Examples

At a 5 kW reading:

| Class | σ (W) | ±1σ Range | ±2σ Range |
|-------|-------|-----------|-----------|
| 0.2 | 3.3 | 4996.7-5003.3 W | 4993.3-5006.7 W |
| 0.5 | 8.3 | 4991.7-5008.3 W | 4983.3-5016.7 W |
| 1.0 | 16.7 | 4983.3-5016.7 W | 4966.7-5033.3 W |
| 2.0 | 33.3 | 4966.7-5033.3 W | 4933.3-5066.7 W |

## Zero Value Handling

```python
if value == 0.0:
    return 0.0  # No noise for zero readings
```

This prevents spurious noise when meters read zero (e.g., solar generation at night).

## Relationship to State Estimation

The noise model directly feeds into the state estimator's weight matrix:

```
W_ii = σ_i²  (measurement weight = variance)
```

Higher accuracy class → higher σ → lower weight → less influence on state estimate.

## Brownian Motion for Time Series

In addition to per-tick noise, generation and consumption use **autocorrelated** noise (Brownian motion with mean reversion):

```
noise_t = 0.8 × noise_{t-1} + innovation
innovation ~ N(0, base_value × 0.02)
```

This produces smooth, realistic time series rather than independent white noise.

See [[Brownian Motion Simulation]].

## Relationships

- **Applied in:** [[Smart Meter]] (apply_noise function)
- **Class definition:** [[ANSI C12.20 Accuracy Classes]]
- **Used by:** [[State Estimator]] (weight matrix)
- **Detection:** [[Bad Data Detection]]
- **Time series:** [[Brownian Motion Simulation]]

## Known Issues

- Multipliers are heuristic — not calibrated to specific meter models
- Gaussian assumption may not hold for real meter errors (bias, quantization)
- No temperature dependency (real meters drift with temperature)
- No aging model (meters degrade over time)
