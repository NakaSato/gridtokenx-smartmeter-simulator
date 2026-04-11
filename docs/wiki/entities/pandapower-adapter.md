---
title: "Pandapower Adapter"
category: entities
created: 2026-04-10
updated: 2026-04-10
sources: ["src/smart_meter_simulator/adapters/pandapower_adapter.py", "docs/reference/pandapower.md"]
tags: [grid, pandapower, measurement, topology]
related: [[State Estimator]], [[Thai Grid Topology]], [[Smart Meter]], [[EnergyReading Model]]
---

# Pandapower Adapter

The `PandapowerAdapter` converts `SmartMeter` instances and their `EnergyReading` objects into pandapower `net.measurement` tables, bridging the AMI simulation layer with the power system analysis engine.

## Summary

The adapter maps signed meter readings to pandapower measurement elements (load, sgen, bus) with proper sign conventions, accuracy-class-based standard deviations, and spatial topology construction using Delaunay triangulation plus minimum spanning tree optimization.

## Architecture

```
SmartMeter (energy reading)
    ↓
┌──────────────────────────────┐
│  PandapowerAdapter           │
│  ┌────────────────────────┐  │
│  │ MeasurementTableBuilder│  │
│  │  - add_voltage()       │  │
│  │  - add_active_power()  │  │
│  │  - add_reactive_power()│  │
│  └────────────────────────┘  │
│  ┌────────────────────────┐  │
│  │ TopologyBuilder        │  │
│  │  - Delaunay + MST      │  │
│  └────────────────────────┘  │
└──────────────────────────────┘
    ↓
pandapower net (buses, lines, loads, sgens, measurements)
```

## Sign Convention

| Element | pandapower Element | Sign | Meaning |
|---------|-------------------|------|---------|
| Consumption | `net.load` | P > 0 | Draws power from grid |
| Generation | `net.sgen` | P > 0 | Injects power to grid |
| Battery charge | `net.storage` | P > 0 | Draws from grid |
| Battery discharge | `net.storage` | P < 0 | Injects to grid |

**Net power at bus:** `P_net = P_sgen - P_load`

## Standard Deviation Calculation

```python
def calculate_std_dev(self, accuracy_class, nominal_value):
    # 3-sigma bound: 99.7% confidence
    sigma = (accuracy_class / (100 * sigma_factor)) * abs(nominal_value)
    return max(sigma, 0.001)  # Floor at 1 kW
```

| Parameter | Multiplier | Reasoning |
|-----------|-----------|-----------|
| Active power (P) | 2.0× | Base std_dev |
| Reactive power (Q) | 3.0× | Higher uncertainty |
| Voltage (V) | 1.0× | Direct measurement |

### Accuracy Class Mapping

| Meter Type | Accuracy Class | Std_dev at 5 kW |
|------------|---------------|-----------------|
| SUBSTATION | CLASS_0_2 | 0.0033 kW |
| BATTERY_STORAGE | CLASS_0_5 | 0.0083 kW |
| SOLAR_PROSUMER | CLASS_1_0 | 0.0167 kW |
| HYBRID_PROSUMER | CLASS_1_0 | 0.0167 kW |
| GRID_CONSUMER | CLASS_2_0 | 0.0333 kW |
| EV_CHARGER | CLASS_1_0 | 0.0167 kW |

## Topology Building

The adapter builds grid topology from meter coordinates using:

1. **Delaunay triangulation** — connects nearby meters
2. **Minimum spanning tree (MST)** — removes redundant edges
3. **Street alignment** — uses OpenStreetMap road data when available

```python
adapter = PandapowerAdapter(sigma_factor=3, topology_builder=topology_builder)
net, meter_to_bus = adapter.build_network_from_meters(meters)
```

## Measurement Table Format

The `net.measurement` DataFrame:

| Column | Type | Description |
|--------|------|-------------|
| `name` | str | Meter identifier |
| `measurement_type` | str | Current, power, voltage |
| `element_type` | str | Bus, line, load, sgen, trafo |
| `element` | int | Element index in net |
| `value` | float | Measured value |
| `std_dev` | float | Standard deviation |
| `std_type` | str | Calculation basis |

## Key Methods

| Method | Description |
|--------|-------------|
| `build_network_from_meters(meters)` | Create pandapower net from meter list |
| `add_meter_to_network(net, meter, reading, bus_index)` | Add single meter's elements |
| `get_measurement_table()` | Return net.measurement DataFrame |
| `create_simple_network(num_buses)` | Deprecated — simple test network |

## Relationships

- **Input from:** [[Smart Meter]] (readings), [[Meter Generator]] (configs)
- **Grid model:** [[Thai Grid Topology]] (equipment standards)
- **Feeds:** [[State Estimator]] (measurement table)
- **Topology:** [[PostGIS Integration]] (spatial queries)
- **Standard:** [[CIM RDF/XML]] (import/export)

## Known Issues

- Spatial topology uses straight-line connections — not actual cable routes
- Reactive power std_dev multiplier (3.0×) is heuristic
- No transformer impedance modeling in meter-to-grid mapping
- Delaunay triangulation may create unrealistic long lines at edges
