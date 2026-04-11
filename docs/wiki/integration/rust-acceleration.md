---
title: "Rust Acceleration"
category: integration
created: 2026-04-10
updated: 2026-04-10
sources: ["docs/integration/RUST_ACCELERATION.md", "src/rust_sim/src/lib.rs", "src/rust_sim/Cargo.toml"]
tags: [performance, rust, pyo3, maturin]
related: [[Simulation Engine]], [[VPP Orchestrator]], [[Performance Benchmarks]]
---

# Rust Acceleration

Critical simulation hotspots — reading generation and VPP dispatch — are implemented in Rust and exposed to Python via PyO3, delivering 3,655-7,500x speedup over pure Python.

## Summary

The `gridtokenx_sim` PyO3 module provides two main capabilities: `generate_readings()` for batch meter reading generation, and `VPPDispatchEngine` for multi-objective dispatch optimization. Both are transparently called from Python with automatic fallback if Rust is unavailable.

## Architecture

```
┌──────────────────────────────┐
│  Python (smart_meter_sim)    │
│  ┌────────────────────────┐  │
│  │  SimulationEngine      │  │
│  │    ┌──────────────────┐│  │
│  │    │ rust_engine.py   ││  │
│  │    │  → import        ││  │
│  │    │    gridtokenx_sim││  │
│  │    └────────┬─────────┘│  │
│  └─────────────┼──────────┘  │
└────────────────┼──────────────┘
                 │ PyO3 FFI
┌────────────────┼──────────────┐
│  Rust (rust_sim)              │
│  ┌────────────▼────────────┐  │
│  │  generate_readings()    │  │
│  │  VPPDispatchEngine      │  │
│  │    - calculate_afrr()   │  │
│  │    - dispatch()         │  │
│  │    - batch_dispatch()   │  │
│  └─────────────────────────┘  │
│                               │
│  Dependencies:                │
│  - pyo3                       │
│  - rand, rand_distr           │
│  - numpy (via ndarray)        │
└───────────────────────────────┘
```

## PyO3 Module API

### `generate_readings(meters, hour, weekday, weather_factor, is_peak, interval_seconds)`

Batch reading generation for all meters in a single call.

| Argument | Type | Description |
|----------|------|-------------|
| `meters` | Vec<MeterConfig> | Meter configurations |
| `hour` | f64 | Simulation hour (0-24) |
| `weekday` | bool | Is weekday |
| `weather_factor` | f64 | Solar irradiance multiplier (0-1) |
| `is_peak` | bool | Is on-peak period |
| `interval_seconds` | f64 | Reading interval (default 900) |

Returns: `Vec<EnergyReading>`

### `VPPDispatchEngine`

| Method | Description |
|--------|-------------|
| `new(seed)` | Create engine with RNG seed |
| `calculate_afrr(freq, flex_up, flex_down)` | Compute aFRR response |
| `dispatch(resources, target, prices, carbon, interval)` | Multi-objective dispatch |
| `batch_dispatch(clusters, interval)` | Dispatch multiple clusters |

## Building

```bash
# Development build
cd src/rust_sim
maturin develop --release

# Production wheel
maturin build --release
pip install target/wheels/*.whl
```

The Python package auto-detects and imports the Rust module:

```python
try:
    import gridtokenx_sim
    RUST_AVAILABLE = True
except ImportError:
    RUST_AVAILABLE = False
```

## Performance Benchmarks

### Reading Generation

| Meters | Python | Rust | Speedup |
|--------|--------|------|---------|
| 100 | ~300 ms | 0.02 ms | 15,000x |
| 500 | ~1,500 ms | 0.11 ms | 13,636x |
| 1,000 | ~3,000 ms | 0.28 ms | 10,714x |

### VPP Dispatch

| Meters | Rust (direct) | Rust (PyO3 FFI) |
|--------|---------------|-----------------|
| 50 | 15 µs | 33 µs |
| 100 | 33 µs | 1,380 µs |

The FFI overhead is significant for small dispatches — pure Rust is 40× faster at 100 meters.

## Rust Dependencies

| Crate | Purpose |
|-------|---------|
| `pyo3` | Python bindings |
| `rand` | Random number generation |
| `rand_distr` | Statistical distributions (Normal) |

## SIMD Optimization

The Rust code uses `rand`'s SIMD-optimized RNG (StdRng), which auto-vectorizes on supported CPUs. No explicit SIMD intrinsics are used, but the compiler may auto-vectorize the batch operations.

## Relationships

- **Used by:** [[Simulation Engine]] (reading generation)
- **Used by:** [[VPP Orchestrator]] (dispatch optimization)
- **Build system:** Maturin
- **Benchmarks:** [[Performance Benchmarks]]

## Known Issues

- FFI overhead dominates for small clusters (< 100 meters)
- No GIL-free parallelism (PyO3 holds GIL during FFI)
- Rust module is optional — Python fallback always available
- Maturin build requires Rust toolchain (`rustup`)
