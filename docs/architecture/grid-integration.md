# Grid Integration (Pandapower + EGAT)

The **Grid Integration** layer acts as the "Digital Twin" of the physical electrical network. It uses the **Pandapower** library to solve real-time power flow equations, translating individual meter readings into a unified grid state based on the national EGAT transmission backbone or local PostGIS topologies.

## 🏗️ Architecture

The integration is managed by a unified adapter that interfaces with the simulation engine:

| Component | File | Purpose |
| :--- | :--- | :--- |
| `PandapowerAdapter` | `pandapower_adapter.py` | Core engine for building networks from GeoJSON or DB and running power flow. |
| `GridManager` | `grid_manager.py` | Orchestrates the lifecycle of the grid model during simulation ticks. |
| `StateEstimator` | `state_estimator.py` | (Planned) WLS state estimation and bad data detection. |

## 🛠️ Data-Driven Topologies

The `PandapowerAdapter` supports multiple loading mechanisms to ensure the grid matches the physical environment:

1.  **Dynamic Database (PostGIS)**: The primary mode. Fetches substations, power lines, and transformers from the `grid` schema using spatial SQL.
2.  **EGAT National Grid**: Loads optimized GeoJSON data (300+ substations, 80+ lines) for the Thailand transmission backbone.
3.  **Island Hub Scenario**: A specialized topology builder for the Khanom–Samui–Phangan–Tao island network, used for bottleneck simulation.

## ⚡ Real-Time Physics (Power Flow)

Each simulation tick triggers a physical analysis cycle:

1.  **Ingestion**: Aggregate latest generation/consumption from all `SmartMeter` objects.
2.  **Mapping**: Spatially snap meters to the nearest substation or transformer bus using a **KD-Tree** index.
3.  **WLS/NR Solver**: Run the Newton-Raphson power flow solver (`pp.runpp`) using the **Numba** JIT-accelerated backend.
4.  **Analytics**: Extract real-time metrics including bus voltage magnitude (`vm_pu`), line thermal loading (`loading_percent`), and system-wide losses.

## 🗺️ Map API & GeoJSON

The `GET /api/v1/grid/map` endpoint serves a live, physics-annotated GeoJSON `FeatureCollection`. This data allows frontends to visualize the grid with real-world coordinates and dynamic health indicators.

```bash
# Get live grid state as GeoJSON
GET /api/v1/grid/map?format=geojson
```

**Payload includes**:
- **Buses (Substations)**: Name, Nominal Voltage (kV), Magnitude (pu).
- **Lines (Cables)**: Geographic route, Thermal Loading (%).

## 📐 Observability & Spatial Snapping

The simulator ensures grid connectivity even with sparse data through:
-   **Spatial Snapping**: Automatically connecting GeoJSON LineStrings to the nearest Point features within a ~1.1km threshold.
-   **Slack Management**: Automatically designating a high-voltage reference bus to ensure solver convergence.
-   **Pseudo-measurements**: Injecting standard load profiles when physical meters are missing.

---
_Next: [Market & VPP Engine](market-engine.md)_
