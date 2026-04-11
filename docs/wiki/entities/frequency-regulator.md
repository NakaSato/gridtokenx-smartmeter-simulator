---
title: "Frequency Regulator"
category: entities
created: 2026-04-10
updated: 2026-04-10
sources: ["src/smart_meter_simulator/core/frequency.py", "docs/architecture/market-engine.md"]
tags: [frequency, stability, swing, rocof]
related: [[Droop Control]], [[aFRR]], [[VPP Orchestrator]], [[Island Manager]]
---

# Frequency Regulator

The `FrequencyModel` tracks grid frequency dynamics using the Swing Equation, computing frequency deviation, Rate of Change of Frequency (RoCoF), and phase angle in response to power imbalances.

## Summary

Grid frequency deviates from the nominal 50 Hz when generation and consumption are unbalanced. The Frequency Regulator models this using a simplified swing equation with inertia and damping, providing the frequency signal that triggers droop control responses and aFRR dispatch.

## Model

### Swing Equation (Simplified)

```
2 × H × df/dt = P_acc(pu) × f₀ - D × Δf × f₀

Where:
  H = inertia constant (seconds, default 5.0)
  f₀ = nominal frequency (50.0 Hz)
  P_acc(pu) = power imbalance / S_base (per unit)
  D = damping factor (1.0, % load change per % frequency change)
  df/dt = rate of change of frequency
```

### Discrete Time Step

```python
def step(self, power_imbalance_mw, dt_seconds):
    P_acc_pu = power_imbalance_mw / self.s_base_mva
    rocof = (P_acc_pu * self.nominal_freq) / (2 * self.inertia_h)
    delta_f = rocof * dt_seconds
    self.frequency += delta_f
    # Apply damping
    self.frequency -= D * (self.frequency - self.nominal_freq) * (dt_seconds / self.nominal_freq)
```

### State Output

| Field | Type | Description |
|-------|------|-------------|
| `frequency` | float | Current grid frequency (Hz) |
| `rocof` | float | Rate of Change of Frequency (Hz/s) |
| `angle_deg` | float | Phase angle relative to nominal (degrees) |
| `time_step` | float | Simulation time step (seconds) |

## Key Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `nominal_freq` | 50.0 Hz | Grid nominal frequency |
| `inertia_h` | 5.0 s | Inertia constant (H) |
| `s_base_mva` | 10.0 MVA | Base power for per-unit calculation |
| `D` | 1.0 | Damping factor (% load change per % freq change) |

## Frequency Response Cascade

```
Power Imbalance (MW)
         ↓
   Swing Equation → df/dt (RoCoF)
         ↓
   Frequency Deviation (Hz)
         ↓
  ┌──────┴──────┐
  ↓             ↓
Droop Control  |Δf| > 0.02 Hz?
(primary)           ↓
Instant         aFRR Dispatch
response        (secondary)
```

## Interface

```python
model = FrequencyModel(nominal_freq=50.0, inertia_h=5.0, s_base_mva=10.0)

# Each tick
state = model.step(power_imbalance_mw=0.5, dt_seconds=15.0)
print(f"Freq: {state.frequency} Hz, RoCoF: {state.rocof} Hz/s")

# Direct set (for ADR events or testing)
model.set_frequency(49.95)

# Reset to nominal
model.reset()
```

## RoCoF Protection

In real grids, RoCoF triggers under-frequency load shedding:

| RoCoF Threshold | Action |
|-----------------|--------|
| > 0.5 Hz/s | Generator protection may trip |
| > 1.0 Hz/s | Fast-acting load shedding activates |
| > 2.0 Hz/s | Risk of cascading failure |

The simulator tracks RoCoF but does not implement automatic load shedding (handled by [[Island Manager]]).

## Relationships

- **Model:** `core/frequency.py`
- **Triggers:** [[Droop Control]] (primary response)
- **Triggers:** [[aFRR]] (secondary response when beyond deadband)
- **Manages island frequency:** [[Island Manager]]
- **Stored in:** InfluxDB (`grid_frequency` measurement)

## Known Issues

- Single-area model — no inter-area oscillations
- Inertia is constant — does not change as generators connect/disconnect
- Damping factor is heuristic, not derived from load composition
- No governor dynamics (turbine response delay)
