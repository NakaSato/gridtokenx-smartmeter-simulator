# Running Simulations

The **GridTokenX Smart Meter Simulator** provides multiple ways to execute and manage power systems simulations.

## 🏃 Running Modes

You can run the simulator in two distinct modes:

### 1. Server Mode (Interactive)

The recommended mode for production-like environments where you need to interact via the web dashboard or external APIs.

```bash
uv run start-simulator --mode server --port 8082
```

In this mode, the simulator exposes a **FastAPI** server that allows you to:
-   Start/Stop simulations via REST.
-   Monitor real-time telemetry via **WebSocket**.
-   Interact with the **Swagger UI** at `http://localhost:8082/docs`.

### 2. Standalone Mode (Direct)

Ideal for quick testing, benchmarks, and direct data output to standard storage.

```bash
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
curl -X PATCH http://localhost:8082/api/v1/simulation/environment -d '{"grid_stress": 2.0}'
```

---
_Next: [Docker Deployment](docker-deployment.md)_
