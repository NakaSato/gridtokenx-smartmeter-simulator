# Running Simulations

The **GridTokenX Smart Meter Simulator** provides multiple ways to execute and manage power systems simulations. All commands are run from the `backend/` directory.

## 🏃 Running Modes

### 1. Server Mode (Interactive)

The recommended mode for production-like environments where you need to interact via the web dashboard or external APIs.

```bash
cd backend
uv run uvicorn smart_meter_simulator.app:app --host 0.0.0.0 --port 8082
```

In this mode, the simulator exposes a **FastAPI** server that allows you to:
-   Start/Stop simulations via REST.
-   Monitor real-time telemetry via **WebSocket**.
-   Interact with the **Swagger UI** at `http://localhost:8082/docs`.

### 2. Island Microgrid Scenario (Khanom–Samui–Phangan–Tao)

Runs the Gulf of Thailand island hub simulation with 60 meters across all island zones:

```bash
cd backend
./run_islands_sim.sh
```

This script sets:
- `LOCATIONS_FILE=initial_locations_islands.json`
- `BASE_LATITUDE=9.45`, `BASE_LONGITUDE=100.0`
- `NUM_METERS=60`
- `TRANSPORT_TYPE=no-db`

### 3. Khanom Power Station Scenario

Runs a focused simulation of the Khanom mainland power station (5 meters):

```bash
cd backend
./run_khanom_sim.sh
```

### 4. Standalone Mode (Direct)

Ideal for quick testing, benchmarks, and direct data output.

```bash
cd backend
uv run start-simulator --mode standalone --meters 50 --api-url http://localhost:4000
```

## 🛠️ Simulation Controls

### Using the CLI

The `start-simulator` command supports several CLI flags to override configuration:

| Flag | Argument | Description |
| :--- | :--- | :--- |
| `--meters` | `int` | Number of meters to simulate. |
| `--interval` | `int` | Simulation interval in seconds (e.g. 900 for 15m). |
| `--purchase-rate` | `float` | Grid purchase rate (Baht/kWh). |
| `--solar-ratio` | `float` | Ratio of solar prosumer meters (0.0 - 1.0). |

### Using the REST API

When in **Server Mode**, you can control the simulation using these endpoints:

1.  **Start Simulation**: `POST /api/v1/simulation/actions/start`
2.  **Stop Simulation**: `POST /api/v1/simulation/actions/stop`
3.  **Update Environment**: `PATCH /api/v1/simulation/environment`
    *   Example: `{"weather": "Rainy", "grid_stress": 1.5}`

## 🗺️ Grid Map API

Render the Thai grid (EGAT transmission + island distribution + meters) as GeoJSON or MVT:

```bash
# All layers as GeoJSON
curl http://localhost:8082/api/v1/grid/map?format=geojson&layers=all

# EGAT transmission only, South region
curl "http://localhost:8082/api/v1/grid/map?format=geojson&layers=egat&region=South"

# Bounding box filter (Gulf of Thailand islands)
curl "http://localhost:8082/api/v1/grid/map?format=geojson&layers=all&bbox=99.5,8.5,101.0,10.0"
```

## 🌓 Interactive Scenarios

The simulator supports real-time scenario injection to test grid resilience.

### Islanding (Microgrid Formation)

Test how the Virtual Power Plant handles a sudden loss of the main grid:

```bash
curl -X POST http://localhost:8082/api/v1/simulation/scenarios/island
```

### Grid Stress Testing

Simulate a high-load or "brownout" condition by increasing the consumption multiplier:

```bash
curl -X PATCH http://localhost:8082/api/v1/simulation/environment \
  -H "Content-Type: application/json" \
  -d '{"grid_stress": 2.0}'
```

## 🧪 Running Tests

```bash
cd backend

# All tests
uv run pytest

# Bottleneck game tests
uv run pytest tests/test_bottleneck_game.py -v

# EGAT transmission tests
uv run pytest tests/test_egat_transmission.py -v

# Financial VPP optimization
python scripts/test_financial_vpp.py

# Island bottleneck scenario
python scripts/test_island_bottleneck.py
```

---
_Next: [Docker Deployment](docker-deployment.md)_
