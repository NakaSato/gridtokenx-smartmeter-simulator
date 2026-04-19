# Grid Integration (Pandapower + EGAT)

The **Grid Integration** layer acts as the "Digital Twin" of the physical electrical network. It uses the **Pandapower** library to translate individual meter readings into a unified grid state, and models the full EGAT transmission backbone down to island distribution networks.

## 🏗️ Architecture

The integration is managed by several adapters (located in `backend/src/smart_meter_simulator/adapters/`):

| Adapter | File | Purpose |
| :--- | :--- | :--- |
| `PandapowerAdapter` | `pandapower_adapter.py` | Generic distribution network builder and state estimator |
| `IslandHubTopology` | `island_hub_topology.py` | Khanom–Samui–Phangan–Tao island network |
| `EGATTransmissionBuilder` | `egat_transmission.py` | National 500/230/115/69 kV transmission model |
| `ThaiGridBuilder` | `thai_grid_topology.py` | MEA/PEA regional distribution topologies |
| `StateEstimator` | `state_estimator.py` | WLS state estimation and bad data detection |
| `TopologyBuilder` | `topology_builder.py` | Base class for all topology builders |

## 🏝️ IslandHubTopology

The `IslandHubTopology` builds the **Gulf of Thailand Island Hub** network in Pandapower:

```
EGAT Khanom 115 kV (ext_grid)
    │
    115 kV KMB Circuit 3 (20 km, max_i_ka=0.25 — Bottleneck)
    │
Samui Main 115 kV
    │ (25 MVA transformer)
Samui Dist 33 kV ── 50 MWh BESS, 25 MW EGAT Gen
    │
    33 kV Submarine XLPE (15 km)
    │
Phangan Dist 33 kV
    │
    33 kV Submarine XLPE (40 km)
    │
Tao Dist 33 kV ── 10 MW Diesel Gen
```

Meters are mapped to buses by their `zone` config field (`Samui`, `Phangan`, `Tao`, `Mainland`).

## ⚡ EGAT Transmission Model

The `EGATTransmissionBuilder` (in `egat_transmission.py`) provides a realistic model of Thailand's national transmission system:

- **500 kV**: Main backbone (HVDC/HVAC inter-regional)
- **230 kV**: Regional interconnection
- **115 kV**: Sub-transmission (connects to MEA/PEA substations)
- **69 kV**: Legacy system (being phased out)

It exposes substations and lines as structured data objects, filterable by region and voltage level.

## 🗺️ Map API

The `GET /api/v1/grid/map` endpoint renders the Thai grid on a map, combining multiple data sources:

| Layer | Description |
| :--- | :--- |
| `egat` | EGAT transmission substations and lines |
| `grid` | Active Pandapower distribution network |
| `meters` | Simulator meter positions |
| `substations` | Substation locations |
| `all` | All layers combined |

**Formats**: `geojson` (for Leaflet/MapLibre) or `mvt` (Mapbox Vector Tiles).

```bash
# GeoJSON all layers
GET /api/v1/grid/map?format=geojson&layers=all

# Regional filter
GET /api/v1/grid/map?format=geojson&layers=egat&region=South

# MVT tile
GET /api/v1/grid/map?format=mvt&layers=egat&z=8&x=196&y=119
```

## 🔄 State Estimation Workflow

Each simulation tick triggers the following grid analysis cycle:

1.  **Ingestion**: Aggregate latest generation/consumption from all `SmartMeter` objects.
2.  **Mapping**: Convert kWh (energy) into average P (active) and Q (reactive) power (MW/MVar).
3.  **WLS Estimation**: Solve non-linear estimation equations; verify against ANSI C12.20 accuracy standards.
4.  **Bad Data Detection**: Identify and remove outlier measurements using the $r_N$ (Normalized Residual) test ($r_N > 3.0$).
5.  **Analytics**: Calculate grid losses, average voltage deviation, and thermal line loading.

## 🗺️ Spatial Modeling (PostGIS)

The simulator integrates with a **PostGIS** spatial database to retrieve realistic grid topologies for MEA/PEA (Thailand) distribution networks.

```python
net, meter_to_bus = self.adapter.build_network_from_meters(self.meters)
```

## 📐 Observability

A network is considered **Observable** if there are enough measurement points to uniquely determine the state at every node. The simulator handles low-observability scenarios by:
-   Injecting **Pseudo-measurements** derived from Standard Load Profiles (SLP).
-   Using **Geo-SAM** estimates for distributed solar capacity.

---
_Next: [Market & VPP Engine](market-engine.md)_
