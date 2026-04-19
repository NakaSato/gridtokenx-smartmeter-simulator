# Thai Grid Integration (MEA/PEA/EGAT)

The **GridTokenX Smart Meter Simulator** provides high-fidelity modeling of Thailand's electrical infrastructure at all levels: EGAT national transmission, MEA metropolitan distribution, and PEA provincial distribution — with specialized support for the **Gulf of Thailand Island Hub** (Khanom–Samui–Phangan–Tao).

## 🏗️ Grid Infrastructure Layers

### EGAT Transmission (National)

The `EGATTransmissionBuilder` (in `backend/src/smart_meter_simulator/adapters/egat_transmission.py`) models the national transmission system:

| Voltage | Role |
| :--- | :--- |
| **500 kV** | Main backbone (HVDC/HVAC inter-regional) |
| **230 kV** | Regional interconnection |
| **115 kV** | Sub-transmission (connects to MEA/PEA substations) |
| **69 kV** | Legacy system (being phased out) |

Grid structure:
- **EGAT** operates the national transmission network.
- **MEA** serves Bangkok Metro (Bangkok, Nonthaburi, Samut Prakan).
- **PEA** serves 74 other provinces.

### MEA/PEA Distribution

The `ThaiGridBuilder` (in `thai_grid_topology.py`) creates representative distribution topologies:

| Region | Utility | Feeder Characteristics |
| :--- | :--- | :--- |
| **Bangkok Urban** | MEA | Dense load, underground XLPE/NAYY, 630–1000 kVA transformers |
| **Central Thailand** | PEA | Mixed urban/rural, long overhead AAC feeders, 250–400 kVA transformers |
| **Rural (Northeast)** | PEA | Long-distance radial feeders, low load density, 160 kVA transformers |

Standard voltage levels: **22 kV** (MV distribution), **400 V** (3-phase LV), **230 V** (phase-to-neutral).

## 🏝️ Island Hub Topology (Khanom–Samui–Phangan–Tao)

The `IslandHubTopology` (in `backend/src/smart_meter_simulator/adapters/island_hub_topology.py`) builds the Gulf of Thailand island network in Pandapower:

```
EGAT Khanom 115 kV (External Grid Supply)
    │
    115 kV KMB Circuit 3 — 20 km, max_i_ka=0.25 (BOTTLENECK)
    │
Koh Samui 115 kV
    │ (25 MVA 115/33 kV transformer)
Koh Samui 33 kV
    ├── 50 MWh BESS (±20 MW)
    ├── 25 MW EGAT Generator
    │
    33 kV Submarine XLPE — 15 km (Samui → Phangan)
    │
Koh Phangan 33 kV
    │
    33 kV Submarine XLPE — 40 km (Phangan → Tao)
    │
Koh Tao 33 kV
    └── 10 MW Diesel Generator
```

### Bottleneck Constraint

The 115 kV KMB Circuit 3 line is modeled with a reduced thermal limit (`max_i_ka=0.25`) to simulate the real-world capacity constraint between the mainland and Koh Samui. When this line approaches saturation, the **Bottleneck Game** is activated to resolve congestion via BESS dispatch.

### Running the Island Simulation

```bash
cd backend
./run_islands_sim.sh
```

Or manually:

```bash
cd backend
export LOCATIONS_FILE="initial_locations_islands.json"
export BASE_LATITUDE=9.45
export BASE_LONGITUDE=100.0
export NUM_METERS=60
export TRANSPORT_TYPE="no-db"
uv run uvicorn smart_meter_simulator.app:app --host 0.0.0.0 --port 8082
```

### Meter Zone Mapping

Meters are assigned to island zones via the `zone` field in `initial_locations_islands.json`:

| Zone | Bus | Assets |
| :--- | :--- | :--- |
| `Mainland` | Khanom 115 kV | EGAT supply |
| `Samui` | Samui 33 kV | 50 MWh BESS, 25 MW Gen |
| `Phangan` | Phangan 33 kV | — |
| `Tao` | Tao 33 kV | 10 MW Diesel |

## 📐 Grid Health & ANSI Standards

The simulator validates the Thai grid state against local regulatory limits:
-   **Voltage Tolerance**: $\pm 5\%$ for MEA/PEA (0.95–1.05 pu).
-   **Line Loading**: Alerts triggered if thermal capacity exceeds 90%.
-   **Phase Balance**: Monitoring for neutrality current in 3-phase, 4-wire configurations.

## 🗺️ Map Visualization

The `GET /api/v1/grid/map` endpoint renders the full Thai grid (EGAT + island distribution + meters) as GeoJSON or MVT tiles, consumable by the Next.js frontend (Leaflet/MapLibre).

```bash
# Gulf of Thailand island view
curl "http://localhost:8082/api/v1/grid/map?format=geojson&layers=all&bbox=99.5,8.5,101.0,10.0"
```

---
_See [Grid Integration Architecture](../architecture/grid-integration.md) for technical details._
