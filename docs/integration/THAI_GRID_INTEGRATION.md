# Thai Grid Integration (MEA/PEA/EGAT)

The **GridTokenX Smart Meter Simulator** provides high-fidelity modeling of Thailand's electrical infrastructure at all levels: EGAT national transmission, MEA metropolitan distribution, and PEA provincial distribution — with support for both optimized GeoJSON assets and dynamic PostGIS storage.

## 🏗️ Grid Infrastructure Layers

### EGAT Transmission (National)

The `PandapowerAdapter` can build the national transmission system by loading optimized EGAT GeoJSON data (derived from official GIS sources):

| Voltage | Role |
| :--- | :--- |
| **500 kV** | Main backbone (HVDC/HVAC inter-regional) |
| **230 kV** | Regional interconnection |
| **115 kV** | Sub-transmission (connects to MEA/PEA substations) |

Grid structure:
- **EGAT** operates the national transmission network (300+ substations simulated).
- **MEA** serves Bangkok Metro (Bangkok, Nonthaburi, Samut Prakan).
- **PEA** serves 74 other provinces.

### MEA/PEA Distribution (Dynamic)

The simulator can load specific regional distribution topologies directly from a **PostGIS** database:

| Region | Source | Feeder Characteristics |
| :--- | :--- | :--- |
| **Dynamic Grid** | `grid` DB Schema | Real-time loading of substations, lines, and transformers from storage. |
| **Bangkok Urban** | PostGIS | Dense load, underground XLPE/NAYY, 630–1000 kVA transformers. |
| **Central Thailand** | GeoJSON | Mixed urban/rural, long overhead AAC feeders, 250–400 kVA transformers. |

## 🏝️ Island Hub Topology (Khanom–Samui–Phangan–Tao)

A specialized scenario for the Gulf of Thailand island network is available in the adapter (`build_island_hub`):

```
EGAT Khanom 115 kV (External Grid Supply)
    │
    115 kV KMB Circuit 3 — 20 km, max_i_ka=0.25 (BOTTLENECK)
    │
Koh Samui 115 kV
    │ (25 MVA 115/22 kV transformer)
Koh Samui 22 kV
    ├── 50 MWh BESS (±20 MW)
    ├── 25 MW EGAT Generator
    │
    22 kV Submarine XLPE — 15 km (Samui → Phangan)
    │
Koh Phangan 22 kV
    │
    22 kV Submarine XLPE — 40 km (Phangan → Tao)
    │
Koh Tao 22 kV
    └── 10 MW Diesel Generator
```

### Bottleneck Constraint

The 115 kV KMB Circuit 3 line is modeled with a reduced thermal limit to simulate the real-world capacity constraint. The simulator uses this bottleneck to test **VPP Bottleneck Games** and predictive dispatch.

## 📐 Spatial Snapping & Mapping

Meters are assigned to grid buses using geographic proximity:

1.  **KD-Tree Mapping**: Each `SmartMeter` is snapped to the nearest substation or transformer bus.
2.  **Zone-based Mapping**: (Legacy) Meters are assigned to island zones (`Samui`, `Phangan`, `Tao`).
3.  **Real-world Snapping**: Transmission lines are automatically connected to substations if their endpoints are within ~1.1km.

## 🗺️ Map Visualization

The `GET /api/v1/grid/map` endpoint renders the optimized Thai grid as a GeoJSON `FeatureCollection`, consumable by the Next.js frontend. Payload size has been optimized by 98.6% (from 1.5GB to ~21MB) for fast web delivery.

---
_See [Grid Integration Architecture](../architecture/grid-integration.md) for technical details._
