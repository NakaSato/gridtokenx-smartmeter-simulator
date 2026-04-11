---
title: "Thai Grid Topology"
category: integration
created: 2026-04-10
updated: 2026-04-10
sources: ["docs/integration/THAI_GRID_INTEGRATION.md", "docs/reference/thai-grid-topology.md", "src/smart_meter_simulator/adapters/thai_grid_topology.py"]
tags: [thai, grid, topology, mea, pea]
related: [[PostGIS Integration]], [[Thai Electricity Market]], [[CIM RDF/XML]], [[Pandapower Adapter]]
---

# Thai Grid Topology

The Thai Grid Topology module models distribution networks according to MEA (Metropolitan Electricity Authority) and PEA (Provincial Electricity Authority) standards, with region-specific parameters for Bangkok urban, central plains, and rural northeast networks.

## Summary

Thai distribution networks follow a radial topology: Substation (22 kV) → Primary Feeder → Transformer (22kV/400V) → Secondary Grid → Customers. The `ThaiGridBuilder` constructs these networks programmatically with region-appropriate equipment sizing.

## Network Hierarchy

```
Level 0: Substation (115/22 kV)
    │
    ├── Primary Feeder (22 kV MV)
    │     ├── Conductor: AAC/ACSR (overhead) or XLPE/NAYY (underground)
    │     └── Length: 5-30 km
    │
    ├── Distribution Transformer
    │     ├── Rating: 160, 250, 400, 630, 1000 kVA
    │     └── Ratio: 22 kV / 400 V (3-phase)
    │
    ├── Secondary Grid (400V LV)
    │     └── Length: 200-800 m
    │
    └── Customers (Smart Meters)
          ├── Residential (230V single-phase)
          ├── Commercial (400V three-phase)
          └── Industrial (400V three-phase)
```

## Regional Models

| Region | Authority | Voltage | Density | Characteristics |
|--------|-----------|---------|---------|-----------------|
| Bangkok Central | MEA | 22 kV / 400V | High | Underground cables, short feeders, high load density |
| Samut Prakan | MEA | 22 kV / 400V | Medium-High | Mix of overhead and underground |
| Central Plains | PEA | 22 kV / 400V | Medium | Overhead AAC conductors, medium feeders |
| Rural Northeast | PEA | 22 kV / 400V | Low | Long feeders, ACSR conductors, scattered loads |
| Phuket | PEA | 22 kV / 400V | Medium | Islanded network, tourism load profile |
| Chiang Mai | PEA | 22 kV / 400V | Medium | Mountainous terrain, seasonal hydro |

## Equipment Standards

### Conductors

| Type | Full Name | Use Case | Ampacity |
|------|-----------|----------|----------|
| AAC | All Aluminum Conductor | MV overhead | 140-680 A |
| ACSR | Aluminum Conductor Steel Reinforced | Long-span MV | 200-900 A |
| XLPE | Cross-Linked Polyethylene | Underground MV | 200-500 A |
| NAYY | Aluminum XLPE PVC | Underground LV | 100-300 A |

### Transformers

| Rating (kVA) | Typical Use | No-Load Loss (W) | Full-Load Loss (W) |
|--------------|-------------|-------------------|---------------------|
| 160 | Rural, small village | 340 | 2,150 |
| 250 | Residential feeder | 460 | 3,050 |
| 400 | Urban feeder | 650 | 4,400 |
| 630 | Commercial area | 900 | 6,200 |
| 1000 | Industrial zone | 1,200 | 8,800 |

### Voltage Levels

| Level | Voltage | Tolerance |
|-------|---------|-----------|
| HV (Transmission) | 115 kV, 230 kV, 500 kV | ±5% |
| MV (Distribution) | 22 kV | ±5% |
| LV (Consumer) | 400V (3-phase), 230V (1-phase) | ±10% |

## ThaiGridBuilder

```python
from smart_meter_simulator.adapters.thai_grid_topology import ThaiGridBuilder

builder = ThaiGridBuilder(region="bangkok_central")
builder.add_substation(name="Samut_Prakan", lat=13.6, lon=100.6)
builder.add_feeder(voltage_kv=22, conductor_type="XLPE", length_km=5)
builder.add_transformers(rating_kva=400, count=10)
builder.add_meters(count=55, type_distribution="mixed")

grid = builder.build()  # Returns pandapower net
```

## Islanding Nodes

Microgrid isolators are placed at strategic points in the topology:

| Node Type | Location | Function |
|-----------|----------|----------|
| **Islanding Node** | Feeder midpoint | Disconnect from main grid |
| **Microgrid Isolator** | Transformer secondary | Isolate LV network |
| **Black Start Point** | Substation backup | Restore after outage |

## PostGIS Mapping

Spatial elements stored in [[PostGIS Integration]]:

| Element | Geometry | Table |
|---------|----------|-------|
| Substation | POINT | `substations` |
| Power Line | LINESTRING | `power_lines` |
| Transformer | POINT | `transformers` |
| Meter | POINT | `meters` |
| Feeder Area | POLYGON | `feeders` |

## Relationships

- **Built with:** [[Pandapower Adapter]] (pandapower net)
- **Stored in:** [[PostGIS Integration]]
- **Market context:** [[Thai Electricity Market]]
- **Standard format:** [[CIM RDF/XML]]

## Known Issues

- Regional models are simplified — not based on actual utility GIS data
- Conductor parameters are typical values — not specific manufacturer data
- Transformer loss values are estimates — not tested units
- No underground routing algorithm (straight-line placement)
