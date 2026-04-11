---
title: "Meter Type Distribution"
category: reference
created: 2026-04-10
updated: 2026-04-10
sources: ["src/smart_meter_simulator/config/settings.py", "src/smart_meter_simulator/meter_generator.py"]
tags: [config, meter, distribution, ratios]
related: [[Meter Generator]], [[Smart Meter]], [[ANSI C12.20 Accuracy Classes]]
---

# Meter Type Distribution

Meter type distribution defines the proportion of each meter class in the simulation, determining the mix of solar prosumers, pure consumers, hybrid systems, battery storage, and EV chargers.

## Summary

The distribution is configurable via environment variables, with defaults tuned to a realistic Thai urban distribution network: predominantly solar-equipped households with growing EV adoption.

## Default Distribution

| Type | Default Ratio | Description | Accuracy Class |
|------|--------------|-------------|----------------|
| Solar Prosumer | 0.35 | Rooftop solar, exports surplus | CLASS_1_0 |
| Grid Consumer | 0.30 | Pure consumption, no generation | CLASS_2_0 |
| Hybrid Prosumer | 0.20 | Solar + battery, bidirectional | CLASS_1_0 |
| Battery Storage | 0.05 | Dedicated storage system | CLASS_0_5 |
| EV Charger | 0.10 | EV charging with V2G | CLASS_1_0 |

**Sum:** 1.00

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `SOLAR_PROSUMER_RATIO` | 0.35 | Fraction of solar-equipped prosumers |
| `GRID_CONSUMER_RATIO` | 0.30 | Fraction of pure consumers |
| `HYBRID_PROSUMER_RATIO` | 0.20 | Fraction of solar+battery prosumers |
| `BATTERY_STORAGE_RATIO` | 0.05 | Fraction of dedicated storage |
| `EV_CHARGER_RATIO` | 0.10 | Fraction of EV chargers |

## Meter Count Calculation

Given `NUM_METERS=N`, the MeterGenerator distributes:

```python
def calculate_counts(ratios, total):
    counts = [int(r * total) for r in ratios]
    # Adjust rounding to ensure sum == total
    remainder = total - sum(counts)
    for i in range(remainder):
        counts[i] += 1
    return counts
```

### Example: 55 Meters

| Type | Ratio | Count |
|------|-------|-------|
| Solar Prosumer | 0.35 | 19 |
| Grid Consumer | 0.30 | 17 |
| Hybrid Prosumer | 0.20 | 11 |
| Battery Storage | 0.05 | 3 |
| EV Charger | 0.10 | 5 |
| **Total** | **1.00** | **55** |

## DER Capability by Type

| Type | Solar | Battery | EV V2G | Export |
|------|-------|---------|--------|--------|
| Solar Prosumer | ✅ | ❌ | ❌ | ✅ |
| Grid Consumer | ❌ | ❌ | ❌ | ❌ |
| Hybrid Prosumer | ✅ | ✅ | ❌ | ✅ |
| Battery Storage | ❌ | ✅ | ❌ | ✅ |
| EV Charger | ❌ | ✅ (V2G) | ✅ | ✅ |

## Typical Parameters by Type

| Parameter | Solar Prosumer | Grid Consumer | Hybrid | Battery | EV |
|-----------|---------------|--------------|--------|---------|-----|
| Solar (kW) | 5-15 | — | 5-15 | — | — |
| Battery (kWh) | — | — | 10-30 | 10-30 | 40-80 |
| Initial SoC | — | — | 20-80% | 20-80% | 20-80% |
| Accuracy | CLASS_1_0 | CLASS_2_0 | CLASS_1_0 | CLASS_0_5 | CLASS_1_0 |
| Priority | 2 | 2 | 2 | 3 | 3 |

## Scenario Presets

### Urban Residential (Default)
```
SOLAR_PROSUMER_RATIO=0.35
GRID_CONSUMER_RATIO=0.30
HYBRID_PROSUMER_RATIO=0.20
BATTERY_STORAGE_RATIO=0.05
EV_CHARGER_RATIO=0.10
```

### High Solar Penetration
```
SOLAR_PROSUMER_RATIO=0.50
GRID_CONSUMER_RATIO=0.20
HYBRID_PROSUMER_RATIO=0.20
BATTERY_STORAGE_RATIO=0.05
EV_CHARGER_RATIO=0.05
```

### EV Fleet Focus
```
SOLAR_PROSUMER_RATIO=0.20
GRID_CONSUMER_RATIO=0.20
HYBRID_PROSUMER_RATIO=0.20
BATTERY_STORAGE_RATIO=0.10
EV_CHARGER_RATIO=0.30
```

### Storage-Heavy
```
SOLAR_PROSUMER_RATIO=0.20
GRID_CONSUMER_RATIO=0.20
HYBRID_PROSUMER_RATIO=0.20
BATTERY_STORAGE_RATIO=0.20
EV_CHARGER_RATIO=0.20
```

## CLI Override

```bash
# Set ratios via CLI
uv run start-simulator \
  --solar-ratio 0.50 \
  --consumer-ratio 0.20 \
  --hybrid-ratio 0.20 \
  --battery-ratio 0.05 \
  --ev-ratio 0.05
```

## Relationships

- **Applied by:** [[Meter Generator]]
- **Meter types:** [[Smart Meter]]
- **Accuracy classes:** [[ANSI C12.20 Accuracy Classes]]
- **Configuration:** `config/settings.py`

## Known Issues

- Ratios must sum to 1.0 — validation is best-effort
- Rounding may cause small deviations (±1 meter)
- No geographic correlation (all meters use same distribution)
- Default ratios based on 2024 Thai solar adoption — may be outdated
