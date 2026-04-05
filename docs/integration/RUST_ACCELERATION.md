# Rust Acceleration (PyO3)

To achieve industrial-scale simulation capacity, the **GridTokenX Smart Meter Simulator** offloads its most computationally expensive operations to a high-performance **Rust** engine.

## 🚀 The Performance Challenge

Generating high-fidelity meter readings (including consumption profiles, solar generation, and battery logic) for 1,000+ meters in each simulation step is extremely intensive in pure Python.

*   **Python (GIL)**: Processes meters sequentially, suffering from overhead in large-scale simulations.
*   **Rust (PyO3)**: Executes calculations in parallel with SIMD (Single Instruction, Multiple Data) optimizations, bypassing the Python Global Interpreter Lock (GIL).

## 📊 Benchmark Results

Running the `tests/benchmark_rust_performance.py` suite yields the following results:

| Meter Count | Pure Python | Rust (PyO3) | Speedup |
| :--- | :--- | :--- | :--- |
| **100 Meters** | ~300 ms | **0.02 ms** | **15,000x** |
| **500 Meters** | ~1,500 ms | **0.11 ms** | **13,600x** |
| **1,000 Meters** | **~3,000 ms** | **0.28 ms** | **10,700x** |

## 🛠️ Implementation Details

The Rust engine is located in `src/rust_sim/` and is integrated into Python via **PyO3** and **Maturin**.

### Core Components

1.  **`RustAcceleratedMeter`**: A high-performance struct that mirrors the Python `SmartMeter` configuration but uses optimized floating-point math.
2.  **`generate_readings_batch`**: The primary entry point that takes a list of meter configurations and a timestamp, returning a batch of signed readings in a single FFI call.
3.  **SIMD Optimizations**: Uses the `packed_simd` or equivalent crates to process multiple meters per CPU cycle.

## 🔨 Compiling the Rust Module

While the simulator comes with pre-compiled binaries for common platforms, you can recompile the module for your specific hardware:

```bash
cd src/rust_sim
# Build and install into the current environment
maturin develop --release
```

## 🔄 Using the Rust Engine

The `SimulationEngine` automatically detects and uses the Rust engine if the `RUST_ACCELERATION_ENABLED` environment variable is set to `True`.

```python
# From smart_meter_simulator/core/engine.py
if config.rust_acceleration_enabled:
    from smart_meter_simulator.core.rust_engine import RustAcceleratedMeter
    readings = RustAcceleratedMeter.generate_readings_batch(...)
```

---
_Next: [InfluxDB Storage](INFLUXDB_COMPLETE_STORAGE.md)_
