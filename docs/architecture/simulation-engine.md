# Simulation Engine

The **Simulation Engine** is the core orchestrator of the GridTokenX Smart Meter Simulator. It manages the simulation tick loop, meter updates, grid integration, and data flow.

## ⚙️ Core Responsibilities

The `SimulationEngine` class (located in `backend/src/smart_meter_simulator/core/engine.py`) is responsible for:

1.  **Simulation Life-cycle**: Manages the starting, pausing, and stopping of simulations.
2.  **Tick Synchronization**: Orchestrates simulation steps ("ticks"), ensuring that all components (meters, grid, VPP) update their states correctly.
3.  **Grid State Orchestration**: Interfaces with the `PandapowerAdapter` (or `IslandHubTopology`) to build and solve grid models derived from active meters.
4.  **VPP & Frequency Modeling**: Coordinates aFRR response, load shedding logic, frequency-watt droop control, and bottleneck game resolution.
5.  **Edge Forecasting**: Runs the `EdgeForecastingEngine` to generate 24-hour load forecasts for island hub nodes.
6.  **Multi-Modal Operation**: Supports both **Real-Time (Async Loop)** and **Co-Simulation (External Clock)** modes.

## 🔄 Tick Cycle Breakdown

Each simulation tick follows a rigorous sequence of operations:

1.  **Reading Generation**:
    *   Iterates through all `SmartMeter` objects to calculate generation (solar), consumption, and battery state.
    *   **Optimization Path**: If enabled, uses the **Rust Batch Engine** to generate 1,000+ readings in one call.
2.  **Edge Forecasting**:
    *   The `EdgeForecastingEngine` (node `SAMUI-HUB-01`) generates a 24-step hourly forecast vector.
    *   Forecast incorporates temperature sensitivity, cloud cover, and weekend/holiday tourism boost (+15%).
    *   Target accuracy: **<10% MAPE** for 24-hour lookahead.
3.  **VPP Dispatch**:
    *   Checks system frequency and calculates the required aFRR response.
    *   Resolves bottleneck constraints (115 kV KMB line) using the financial optimization game.
    *   Dispatches setpoints to individual meters based on their priority and flexibility.
4.  **Grid Analysis (Digital Twin)**:
    *   Transforms meter readings into Nodal Measurements (MW/MVar).
    *   Runs **Weighted Least Squares (WLS)** State Estimation via Pandapower.
    *   Detects and removes "Bad Data" using normalized residuals (Standard test: $r_N > 3.0$).
5.  **Transport & Persistence**:
    *   Broadcasts signed meter readings to the configured transport layers (gRPC, HTTP, Kafka).
    *   Persists grid state and session metadata to the PostgreSQL and InfluxDB databases.

## 🔮 EdgeForecastingEngine

The `EdgeForecastingEngine` (in `backend/src/smart_meter_simulator/core/forecaster.py`) is a decentralized forecasting component designed for deployment on substation controllers.

```python
from smart_meter_simulator.core.forecaster import EdgeForecastingEngine

engine = EdgeForecastingEngine(node_id="SAMUI-HUB-01")
forecast = engine.generate_24h_forecast(
    current_load_mw=15.0,
    weather_data={"temp_c": 32.0, "cloud_cover": 20.0}
)
schedule = engine.get_recommended_schedule(forecast, capacity_mw=40.0)
```

The recommended schedule identifies bottleneck hours and calculates potential savings from BESS dispatch (9 THB/kWh shifted from diesel to BESS).

## 🏝️ Island Mode

When running the island scenario (`run_islands_sim.sh`), the engine uses `IslandHubTopology` instead of the generic `PandapowerAdapter`. Meters are assigned to island zones (`Samui`, `Phangan`, `Tao`, `Mainland`) via the `initial_locations_islands.json` config.

## ⚡ Performance: Rust Acceleration

The `SimulationEngine` integrates `RustAcceleratedMeter` via PyO3 to bypass the Python GIL and take advantage of native SIMD instructions for reading generation.

| Implementation | 100 Meters | 1,000 Meters | 5,000 Meters |
| :--- | :--- | :--- | :--- |
| **Pure Python** | ~300 ms | ~3,000 ms | ~15,000 ms |
| **Rust (PyO3)** | **0.02 ms** | **0.28 ms** | **1.15 ms** |

---
_Next: [Smart Meter Model](smart-meter.md)_
