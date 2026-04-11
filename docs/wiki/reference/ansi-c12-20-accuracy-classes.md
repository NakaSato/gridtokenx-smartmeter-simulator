---
title: "ANSI C12.20 Accuracy Classes"
category: reference
created: 2026-04-10
updated: 2026-04-10
sources: ["docs/reference/meter-spec.md", "docs/architecture/smart-meter.md", "src/smart_meter_simulator/config/enums.py"]
tags: [spec, meter, accuracy, standard]
related: [[Smart Meter]], [[Measurement Noise Model]], [[Pandapower Adapter]], [[EnergyReading Model]]
---

# ANSI C12.20 Accuracy Classes

ANSI C12.20 defines accuracy classes for watt-hour meters, specifying the maximum permissible error in energy measurement. The simulator models four accuracy classes to represent different meter grades from substation-quality to residential.

## Summary

Each accuracy class determines the standard deviation of measurement noise applied to every electrical parameter reading. Lower class numbers indicate higher precision meters used at critical grid points.

## Accuracy Classes

| Class | Max Error | Typical Use | Std_dev at 5 kW | Std_dev at 10 kW |
|-------|-----------|-------------|-----------------|-----------------|
| **CLASS_0_2** | ±0.2% | Substation metering | 3.3 W | 6.7 W |
| **CLASS_0_5** | ±0.5% | Feeder head meters | 8.3 W | 16.7 W |
| **CLASS_1_0** | ±1.0% | Commercial/Prosumer | 16.7 W | 33.3 W |
| **CLASS_2_0** | ±2.0% | Residential meters | 33.3 W | 66.7 W |

## Std_dev Formula

The simulator uses a 3-sigma bound (99.7% confidence) rather than the ANSI maximum:

```python
sigma = (accuracy_class_value / (100 × sigma_factor)) × |nominal_value|

Where:
  sigma_factor = 3  (3-sigma = 99.7% confidence)
  accuracy_class_value = 0.2, 0.5, 1.0, or 2.0
```

This produces a tighter distribution than the ANSI maximum — the ANSI spec defines the **maximum** error, while the simulator models the **typical** error (σ).

## Meter Type Assignment

| Meter Type | Accuracy Class | Rationale |
|------------|---------------|-----------|
| Substation | CLASS_0_2 | Revenue-grade accuracy |
| Battery Storage | CLASS_0_5 | High-value asset monitoring |
| Solar Prosumer | CLASS_1_0 | Commercial-grade |
| Hybrid Prosumer | CLASS_1_0 | Commercial-grade |
| Grid Consumer | CLASS_2_0 | Residential-grade |
| EV Charger | CLASS_1_0 | Billing accuracy needed |

## Error at Different Load Points

### Active Energy (5 kW reading)

| Class | σ (W) | ±1σ Range | ±3σ Range |
|-------|-------|-----------|-----------|
| 0.2 | 3.3 | 4,996.7-5,003.3 | 4,990-5,010 |
| 0.5 | 8.3 | 4,991.7-5,008.3 | 4,975-5,025 |
| 1.0 | 16.7 | 4,983.3-5,016.7 | 4,950-5,050 |
| 2.0 | 33.3 | 4,966.7-5,033.3 | 4,900-5,100 |

### Voltage (240V reading)

| Class | σ (V) | ±1σ Range | ±3σ Range |
|-------|-------|-----------|-----------|
| 0.2 | 0.16 | 239.84-240.16 | 239.5-240.5 |
| 0.5 | 0.40 | 239.60-240.40 | 238.8-241.2 |
| 1.0 | 0.80 | 239.20-240.80 | 237.6-242.4 |
| 2.0 | 1.60 | 238.40-241.60 | 235.2-244.8 |

## Impact on State Estimation

Measurement weight in WLS state estimation:

```
W_ii = 1 / σ_i²
```

| Class | σ (5 kW) | Weight | Relative to Class 2.0 |
|-------|----------|--------|----------------------|
| 0.2 | 0.0033 kW | 91,743 | 100× |
| 0.5 | 0.0083 kW | 14,519 | 16× |
| 1.0 | 0.0167 kW | 3,589 | 4× |
| 2.0 | 0.0333 kW | 902 | 1× |

Higher accuracy meters have much greater influence on the state estimate.

## Implementation

In `src/smart_meter_simulator/config/enums.py`:

```python
class AccuracyClass(Enum):
    CLASS_0_2 = 0.2   # Substation
    CLASS_0_5 = 0.5   # Feeder
    CLASS_1_0 = 1.0   # Commercial
    CLASS_2_0 = 2.0   # Residential
```

## Relationships

- **Noise model:** [[Measurement Noise Model]]
- **State estimation:** [[State Estimator]], [[Pandapower Adapter]]
- **Meter types:** [[Smart Meter]], [[Meter Type Distribution]]

## Known Issues

- ANSI C12.20 defines error at specific test conditions — real-world error may differ
- Simulator uses single accuracy value — ANSI defines different errors at different load points (light load vs. full load)
- Temperature effects on accuracy not modeled
- Aging/degradation of meter accuracy not modeled
