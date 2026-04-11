---
title: "Meter Generator"
category: entities
created: 2026-04-10
updated: 2026-04-10
sources: ["src/smart_meter_simulator/meter_generator.py", "src/smart_meter_simulator/config/settings.py"]
tags: [meter, config, generation, spatial]
related: [[Smart Meter]], [[Meter Type Distribution]], [[PostGIS Integration]]
---

# Meter Generator

The `MeterGenerator` creates smart meter configurations by reading spatial location data, calculating type distributions, and producing type-specific configuration dictionaries with geographic, electrical, and behavioral attributes.

## Summary

Given a target meter count, the MeterGenerator reads location data from `initial_locations.json`, distributes meters across types (solar prosumer, grid consumer, hybrid prosumer, battery storage, EV charger), and creates complete configuration objects including UUIDs, Ed25519 keys, capacity parameters, and feeder assignments.

## Meter Type Distribution

| Type | Default Ratio | Description |
|------|--------------|-------------|
| Solar Prosumer | 0.35 | Rooftop solar with export capability |
| Grid Consumer | 0.30 | Pure consumption, no generation |
| Hybrid Prosumer | 0.20 | Solar + battery, bidirectional |
| Battery Storage | 0.05 | Dedicated storage system |
| EV Charger | 0.10 | Electric vehicle charging (V2G capable) |

Ratios are configurable via environment variables (`SOLAR_PROSUMER_RATIO`, etc.) and rounded to ensure the total matches `num_meters`.

## Location Data

Locations are loaded from `src/smart_meter_simulator/config/initial_locations.json`:

```json
{
  "latitude": 13.758252,
  "longitude": 100.687455,
  "address": "...",
  "type": "residential|commercial|industrial"
}
```

Default fallback: Bangkok coordinates with random offset.

## Configuration Structure

Each generated meter configuration:

```python
{
    "meter_id": "AMI_METER_001",          # Sequential ID
    "uuid": "...",                         # UUID4
    "meter_type": "Solar_Prosumer",        # Type enum
    "user_type": "Prosumer",               # Prosumer/Consumer/Producer
    "manufacturer": "KMP",                 # KMP/LGZ/MSK/ELS/GXT
    "location": {                           # GPS coordinates
        "latitude": 13.758,
        "longitude": 100.687,
        "address": "..."
    },
    "electrical_params": {                  # Type-specific
        "solar_capacity_kw": 8.5,
        "battery_capacity_kwh": 15.0,
        "battery_soc": 0.45,
        "accuracy_class": "CLASS_1_0"
    },
    "behavioral_params": {                  # Price response
        "price_elasticity": 0.15,
        "priority": 2                       # 1=critical, 2=normal, 3=flexible
    },
    "feeder_id": "ZONE-A-ST",              # Phase-based assignment
    "phase": "A"
}
```

## Manufacturer IDs

| Code | Manufacturer | Origin |
|------|-------------|--------|
| KMP | Kamstrup | Denmark |
| LGZ | Landis+Gyr | Switzerland |
| MSK | Mitsubishi | Japan |
| ELS | Elster (Honeywell) | Germany/USA |
| GXT | GridTokenX | Custom |

## Feeder Assignment

Meters are assigned to feeders by phase rotation:

| Phase | Feeder ID | Description |
|-------|-----------|-------------|
| A | ZONE-A-ST | Street-level feed |
| B | ZONE-B-MT | Medium-tier feed |
| C | ZONE-C-HP | High-priority feed |

## Priority Mapping

| Priority | Types | Description |
|----------|-------|-------------|
| 1 (Critical) | Substation, Feeder head, Commercial | Never shed |
| 2 (Normal) | Solar Prosumer, Grid Consumer, Hybrid | Standard service |
| 3 (Flexible) | EV Charger, Battery Storage | First to shed |

## Capacity Ranges

| Type | Solar (kW) | Battery (kWh) | Initial SoC |
|------|-----------|---------------|-------------|
| Solar Prosumer | 5-15 | — | — |
| Hybrid Prosumer | 5-15 | 10-30 | 20-80% |
| Battery Storage | — | 10-30 | 20-80% |
| EV Charger | — | 40-80 | 20-80% |

## Key Methods

```python
generator = MeterGenerator(num_meters=55)
configs = generator.generate_meters()  # List[Dict]
```

| Method | Description |
|--------|-------------|
| `generate_meters()` | Main entry point — creates all configs |
| `_load_locations()` | Read from initial_locations.json |
| `_calculate_meter_counts(ratios)` | Distribute by type, round |
| `_create_meter_config(id, type, location)` | Full config dict |

## Relationships

- **Output:** [[Smart Meter]] (configuration dicts)
- **Location source:** [[PostGIS Integration]]
- **Ratios from:** [[Meter Type Distribution]]
- **Settings:** `config/settings.py`

## Known Issues

- Location file may not exist — fallback to random placement
- Rounding may cause small deviations from configured ratios
- No real-world address geocoding (uses template data)
- Manufacturer assignment is random, not based on actual deployment
