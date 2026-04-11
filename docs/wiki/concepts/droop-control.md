---
title: "Droop Control"
category: concepts
created: 2026-04-10
updated: 2026-04-10
sources: ["docs/architecture/market-engine.md", "src/smart_meter_simulator/core/frequency.py"]
tags: [frequency, control, stability, inverter]
related: [[Frequency Regulator]], [[aFRR]], [[VPP Orchestrator]]
---

# Droop Control

Droop control is the primary frequency response mechanism for grid-tied inverters. It autonomously adjusts power output in response to grid frequency deviations, without requiring external communication.

## Summary

In the Smart Meter Simulator, every inverter-based resource (solar prosumer, battery, EV) implements a frequency-power droop curve with 5% droop and ±20 mHz deadband, centered on 50 Hz nominal.

## The Droop Curve

```
Power Output
    ↑
100% |        .
     |       .
     |      .
     |     .
 50% |----·----  (Nominal operating point)
     |   .
     |  .
     | .
  0% |.
     +------------------→ Frequency
     49.0  49.98 50.0 50.02 51.0
           ←deadband→
```

## Mathematical Model

```
ΔP = -(f - f₀) / (R × f₀) × P_rated

Where:
  ΔP = power adjustment (positive = increase generation)
  f = measured frequency (Hz)
  f₀ = nominal frequency (50.0 Hz)
  R = droop coefficient (5% = 0.05)
  P_rated = inverter rated power
```

### Deadband

```
If |f - f₀| < 0.02 Hz → ΔP = 0 (no response)
```

The 20 mHz deadband prevents unnecessary response to normal frequency fluctuations.

### Example

Grid frequency drops to 49.95 Hz (50 mHz deviation):

```
ΔP = -(49.95 - 50.0) / (0.05 × 50.0) × P_rated
   = 0.05 / 2.5 × P_rated
   = 0.02 × P_rated
   = 2% increase in generation
```

For a 5 kW inverter: ΔP = 0.1 kW increase

## Implementation in Simulator

Each `SmartMeter` with inverter capability applies droop locally:

```python
def apply_droop(self, frequency_hz):
    deviation = frequency_hz - 50.0
    if abs(deviation) < 0.02:
        return 0.0  # Deadband

    droop_gain = 1.0 / (0.05 * 50.0)  # 0.4 pu/pu
    adjustment = -deviation * droop_gain * self.inverter_capacity
    return adjustment
```

## Relationship to aFRR

| Property | Droop Control | aFRR |
|----------|--------------|------|
| **Response time** | Instantaneous (< 100 ms) | Seconds to minutes |
| **Control** | Local, autonomous | Centralized, dispatched |
| **Duration** | Sustained | Limited by energy (SoC) |
| **Deadband** | ±20 mHz | ±20 mHz |
| **Droop** | 5% | 5% (equivalent) |

Droop is the **primary** frequency response; aFRR is the **secondary** response that restores frequency to nominal.

## Relationships

- **Implemented in:** [[Smart Meter]] (frequency-watt droop)
- **Monitored by:** [[Frequency Regulator]]
- **Complemented by:** [[aFRR]] (secondary response)
- **Dispatched by:** [[VPP Orchestrator]]

## Known Issues

- Droop response is bounded by available headroom (solar curtailment or battery discharge)
- Inverters at max output cannot increase further (saturation)
- Deadband tuning affects trade-off: tighter = more responsive, wider = less wear
