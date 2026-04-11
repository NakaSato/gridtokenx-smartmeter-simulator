---
title: "Bad Data Detection"
category: concepts
created: 2026-04-10
updated: 2026-04-10
sources: ["docs/architecture/grid-integration.md", "src/smart_meter_simulator/adapters/state_estimator.py"]
tags: [grid, quality, detection, statistics]
related: [[State Estimator]], [[State Estimation]], [[Measurement Noise Model]], [[FDI Attacker]]
---

# Bad Data Detection

Bad data detection identifies and removes erroneous measurements that would corrupt the grid state estimate. It uses statistical hypothesis testing on the residuals of the state estimation.

## Summary

Two complementary methods are used: the global chi-squared test detects whether bad data exists, and normalized residuals identify which specific measurements are bad.

## Chi-Squared Test (Global Detection)

After WLS convergence, compute the objective function value:

```
J(x̂) = Σᵢ wᵢ × (zᵢ - hᵢ(x̂))²
```

**Hypothesis test:**
- H₀: No bad data (all errors are random noise)
- H₁: Bad data present

```
If J(x̂) > χ²(ν, α) → Reject H₀ → Bad data exists

Where:
  ν = m - n  (degrees of freedom = measurements - state variables)
  α = 0.01   (significance level, 99% confidence)
```

**Properties:**
- Detects presence but NOT location of bad data
- Sensitivity increases with redundancy (higher ν)
- False positive rate: α (1% by default)

## Normalized Residuals (Identification)

For each measurement:

```
Residual:       rᵢ = zᵢ - hᵢ(x̂)
Variance:       Ωᵢᵢ = Wᵢᵢ - [H(HᵀW⁻¹H)⁻¹Hᵀ]ᵢᵢ
Normalized:     r_Nᵢ = |rᵢ| / √Ωᵢᵢ
```

**Decision rule:**
```
If |r_Nᵢ| > 3.0 → Flag measurement i as bad data
```

The 3.0 threshold corresponds to a 3-sigma test (99.7% confidence for normal distribution).

## Largest Normalized Residual Test

Iterative identification:
1. Compute all normalized residuals
2. Find measurement with largest |r_N|
3. If > 3.0: remove it and re-estimate
4. Repeat until all |r_N| < 3.0

## Relationship to Accuracy Classes

Measurement variance comes from the meter's ANSI accuracy class:

```
σ = (Class / 300) × |Value|
W = σ²  (weight = inverse variance)
```

| Class | σ at 5 kW | σ at 10 kW |
|-------|-----------|------------|
| 0.2 | 3.3 W | 6.7 W |
| 0.5 | 8.3 W | 16.7 W |
| 1.0 | 16.7 W | 33.3 W |
| 2.0 | 33.3 W | 66.7 W |

## FDI Attack Simulation

The [[FDI Attacker]] module intentionally injects bad data to test detection:
- **Magnitude attacks:** Scale readings by factor
- **Bias attacks:** Add constant offset
- **Replay attacks:** Resend old readings
- **Stealth attacks:** Craft correlated attacks that bypass chi-squared test

## Relationships

- **Implemented in:** [[State Estimator]]
- **Concept foundation:** [[State Estimation]]
- **Noise model:** [[Measurement Noise Model]]
- **Attack testing:** [[FDI Attacker]]

## Known Issues

- Chi-squared test assumes independent Gaussian errors — may not hold for correlated noise
- Multiple simultaneous bad measurements can mask each other
- Stealth FDI attacks can be crafted to stay within chi-squared bounds
- 3-sigma threshold trades off detection sensitivity vs false alarms
