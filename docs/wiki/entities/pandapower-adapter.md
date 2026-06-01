---
title: "Pandapower Adapter"
category: entities
created: 2026-04-10
updated: 2026-05-27
sources: ["src/smart_meter_simulator/adapters/pandapower_adapter.py", "docs/reference/pandapower.md"]
tags: [grid, pandapower, measurement, topology]
related: [[State Estimator]], [[Thai Grid Topology]], [[Smart Meter]], [[EnergyReading Model]]
---

# Pandapower Adapter

The `PandapowerAdapter` converts `SmartMeter` instances and their `EnergyReading` objects into pandapower `net.measurement` tables, bridging the AMI simulation layer with the power system analysis engine. It supports multiple methods for constructing the electrical grid from external data sources.

## Summary

The adapter maps signed meter readings to pandapower measurement elements (load, sgen, bus) with proper sign conventions and accuracy-class-based standard deviations. It can programmatically build grid topologies from **PostGIS storage**, **EGAT GeoJSON files**, or specialized scenario templates.

## Architecture

```
SmartMeter (energy reading)
    ↓
┌──────────────────────────────────────┐
│  PandapowerAdapter                   │
│  ┌────────────────────────────────┐  │
│  │ Grid Building Methods          │  │
│  │  - build_from_db(subs, lines)  │  │
│  │  - load_egat_grid(data_dir)    │  │
│  │  - build_island_hub()          │  │
│  └────────────────────────────────┘  │
│  ┌────────────────────────────────┐  │
│  │ Mapping Engine                 │  │
│  │  - Spatial Snapping (KD-Tree)  │  │
│  │  - Reading-to-Element Mapping  │  │
│  └────────────────────────────────┘  │
└──────────────────────────────────────┘
    ↓
pandapower net (buses, lines, loads, sgens, measurements)
```

## Key Methods

| Method | Description |
|--------|-------------|
| `build_from_db(subs, lines, trafos)` | Construct network on-the-fly from PostGIS records. |
| `load_egat_grid(data_dir)` | Build Thailand transmission backbone from optimized GeoJSON. |
| `build_island_hub()` | Build Khanom–Samui–Phangan–Tao template for bottleneck tests. |
| `map_meters_to_buses_spatial(meters)` | Use KD-Tree to snap meters to nearest grid nodes. |
| `update_measurements(readings)` | Inject readings into net.load and net.sgen tables. |
| `run_power_flow()` | Execute the Newton-Raphson solver (`pp.runpp`). |
| `get_grid_geojson()` | Export current electrical state (voltage, loading) as GeoJSON. |

## Spatial Snapping

For real-world data (EGAT/DB), the adapter ensures connectivity via:
1. **Node Snapping**: Line endpoints are automatically snapped to substations within a 0.01 degree (~1.1km) radius.
2. **Meter Snapping**: Meters are snapped to the geographically closest bus, ensuring consistent power flow paths.

## Sign Convention

| Element | pandapower Element | Sign | Meaning |
|---------|-------------------|------|---------|
| Consumption | `net.load` | P > 0 | Draws power from grid |
| Generation | `net.sgen` | P > 0 | Injects power to grid |
| Battery charge | `net.storage` | P > 0 | Draws from grid |
| Battery discharge | `net.storage` | P < 0 | Injects to grid |

## Relationships

- **Input from:** [[Smart Meter]] (readings), [[Database Manager]] (storage records)
- **Grid model:** [[Thai Grid Topology]] (standard equipment types)
- **Feeds:** [[State Estimator]] (for WLS analysis)
- **Topology:** [[PostGIS Integration]] (spatial queries)
