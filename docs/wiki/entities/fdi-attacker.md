---
title: "FDI Attacker"
category: entities
created: 2026-04-19
updated: 2026-04-19
sources: ["src/smart_meter_simulator/core/attacker.py"]
tags: [security, attack, cyber-physical, fdi]
related: [[State Estimator]], [[Bad Data Detection]], [[Measurement Noise Model]]
---

# FDI Attacker

The False Data Injection (FDI) Attacker module simulates cyber-physical attacks on smart meter readings to test the security and resilience of grid analysis components.

## Summary

The `FDIAttacker` modifies energy and electrical readings in real-time. It supports multiple attack vectors including constant bias, scaling, random noise injection, and "stealth" attacks designed to bypass statistical bad data detection thresholds.

## Details

### Attack Modes
- **Bias:** Adds a constant offset (kW) to consumption or generation readings.
- **Scale:** Multiplies readings by a scale factor, simulating a meter that consistently over- or under-reports.
- **Random:** Injects stochastic noise within specified bounds.
- **Stealth:** Crafts errors that remain statistically plausible relative to the meter's [[ANSI C12.20 Accuracy Classes]]. It targets a specific normalized residual to stay below the typical detection threshold (3.0).

### Targeted Attacks
Attacks can be applied globally to all meters or targeted at a specific set of compromised `meter_id`s. When a reading is attacked, it is flagged as `is_compromised` for internal tracking and evaluation of detection performance.

## Key Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `bias_kw` | 0.0 | Constant offset for bias attacks |
| `scale_factor` | 1.0 | Multiplier for scale attacks |
| `noise_bound_kw` | 5.0 | Range for random noise injection |
| `residual_target`| 0.5 | Target residual for stealth attacks |

## Relationships

- **Targets:** [[Smart Meter]] readings.
- **Tested by:** [[Bad Data Detection]].
- **Impacts:** [[State Estimator]] convergence and accuracy.
- **Uses:** [[Measurement Noise Model]] principles to craft stealthy errors.

## Known Issues

- Stealth attacks currently use a simplified standard deviation fraction rather than reading the actual real-time covariance matrix from the state estimator.
- Replay attacks (re-sending old valid data) are not yet implemented.
- Coordinated attacks across multiple meters to shift the slack bus reference are not modeled.
