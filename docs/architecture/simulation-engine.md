# Simulation Engine

The **Simulation Engine** is the core orchestrator of the GridTokenX Smart Meter Simulator. It manages the simulation tick loop, meter updates, grid integration, and data flow.

## ⚙️ Core Responsibilities

The `SimulationEngine` class (located in `src/smart_meter_simulator/core/engine.py`) is responsible for:

1.  **Simulation Life-cycle**: Manages the starting, pausing, and stopping of simulations.
2.  **Tick Synchronization**: Orchestrates simulation steps ("ticks"), ensuring that all components (meters, grid, VPP) update their states correctly.
3.  **Grid State Orchestration**: Interfaces with the `PandapowerAdapter` to build and solve grid models derived from active meters.
4.  **VPP & Frequency Modeling**: Coordinates AFRR response, load shedding logic, and frequency-watt droop control.
5.  **Multi-Modal Operation**: Supports both **Real-Time (Async Loop)** and **Co-Simulation (External Clock)** modes.

## 🔄 Tick Cycle Breakdown

Each simulation tick follows a rigorous sequence of operations:

1.  **Reading Generation**:
    *   Iterates through all `SmartMeter` objects to calculate generation (solar), consumption, and battery state.
    *   **Optimization Path**: If enabled, uses the **Rust Batch Engine** to generate 1,000+ readings in one call.
2.  **VPP Dispatch**:
    *   Checks system frequency and calculates the required AFRR response.
    *   Dispatches setpoints to individual meters based on their priority and flexibility.
3.  **Grid Analysis (Digital Twin)**:
    *   Transforms meter readings into Nodal Measurements (MW/MVar).
    *   Runs **Weighted Least Squares (WLS)** State Estimation via Pandapower.
    *   Detects and removes "Bad Data" using normalized residuals (Standard test: $r_N > 3.0$).
4.  **Transport & Persistence**:
    *   Broadcasts signed meter readings to the configured transport layers (gRPC, HTTP, Kafka).
    *   Persists grid state and session metadata to the PostgreSQL and InfluxDB databases.

## ⚡ Performance: Rust Acceleration

The `SimulationEngine` integrates `RustAcceleratedMeter` via PyO3 to bypass the Python GIL and take advantage of native SIMD instructions for reading generation.

| Implementation | 100 Meters | 1,000 Meters | 5,000 Meters |
| :--- | :--- | :--- | :--- |
| **Pure Python** | ~300 ms | ~3,000 ms | ~15,000 ms |
| **Rust (PyO3)** | **0.02 ms** | **0.28 ms** | **1.15 ms** |

---
_Next: [Smart Meter Model](smart-meter.md)_
