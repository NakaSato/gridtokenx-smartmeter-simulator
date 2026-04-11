---
title: "Performance Benchmarks"
category: reference
created: 2026-04-10
updated: 2026-04-10
sources: ["docs/integration/RUST_ACCELERATION.md", "tests/benchmark_rust_performance.py", "tests/benchmark_vpp_performance.py"]
tags: [performance, benchmarks, rust, comparison]
related: [[Rust Acceleration]], [[Simulation Engine]], [[VPP Orchestrator]]
---

# Performance Benchmarks

Comprehensive performance measurements for the Smart Meter Simulator's hotspots: reading generation and VPP dispatch, comparing Python and Rust implementations.

## Summary

Rust acceleration via PyO3 delivers 3,655-7,500x speedup for reading generation and sub-microsecond VPP dispatch for small clusters. The bottleneck for large-scale simulation is no longer computation but I/O (database writes, network transport).

## Reading Generation Benchmarks

### Single-Thread Performance

| Meters | Python (ms) | Rust (ms) | Speedup | Rust (µs/reading) |
|--------|-------------|-----------|---------|-------------------|
| 100 | ~300 | 0.02 | 15,000x | 0.2 |
| 500 | ~1,500 | 0.11 | 13,636x | 0.22 |
| 1,000 | ~3,000 | 0.28 | 10,714x | 0.28 |

### Scaling

| Meters | Python O(n) | Rust O(n) |
|--------|-------------|-----------|
| 100 | 3.0 ms/reading | 0.2 µs/reading |
| 500 | 3.0 ms/reading | 0.22 µs/reading |
| 1,000 | 3.0 ms/reading | 0.28 µs/reading |

Per-reading cost is constant in both implementations (~0.2-0.3 µs for Rust, ~3,000 µs for Python).

### Breakdown (Python)

| Operation | Time (1,000 meters) | % |
|-----------|---------------------|---|
| Solar curve calculation | 1,200 ms | 40% |
| Consumption profile | 900 ms | 30% |
| Battery logic | 300 ms | 10% |
| Electrical params + noise | 600 ms | 20% |

### Breakdown (Rust)

| Operation | Time (1,000 meters) | % |
|-----------|---------------------|---|
| Solar curve calculation | 80 µs | 29% |
| Consumption profile | 70 µs | 25% |
| Battery logic | 50 µs | 18% |
| Electrical params + noise | 80 µs | 29% |

## VPP Dispatch Benchmarks

### Multi-Objective Dispatch

| Meters | Rust Direct (µs) | Rust PyO3 FFI (µs) | FFI Overhead |
|--------|------------------|--------------------|--------------|
| 50 | 15 | 33 | 2.2x |
| 100 | 33 | 1,380 | 41.8x |

The FFI overhead is significant — crossing the Python-Rust boundary dominates for small dispatches.

### aFRR Calculation

| Implementation | Time (ns) |
|----------------|-----------|
| Rust (direct) | ~50 |
| Python (equivalent) | ~500 |
| Speedup | 10x |

## System-Level Performance

### End-to-End Tick Time (1,000 meters, 15s interval)

| Component | Time (ms) | % of Tick |
|-----------|-----------|-----------|
| Reading generation (Rust) | 0.28 | <0.01% |
| VPP dispatch (Rust) | 1.4 | <0.01% |
| State estimation (pandapower) | 50-200 | 0.3-1.3% |
| Market clearing | 10-50 | 0.07-0.3% |
| Transport dispatch (HTTP) | 100-500 | 0.7-3.3% |
| InfluxDB write | 50-200 | 0.3-1.3% |
| **Total** | **212-952** | **1.4-6.3%** |

The simulation uses ~6% of the 15-second tick for 1,000 meters — headroom for 15,000+ meters at this interval.

### Bottleneck Analysis

At scale (> 5,000 meters), the bottleneck shifts:

| Bottleneck | Threshold | Mitigation |
|------------|-----------|------------|
| Reading generation | Solved (Rust) | Already optimized |
| State estimation | ~2,000 meters | Partition grid, parallel SE |
| Transport I/O | ~5,000 meters | Batch writes, async |
| InfluxDB write | ~10,000 meters | Batch API, buffering |
| Database write | ~10,000 meters | Connection pooling |

## Benchmark Commands

```bash
# Reading generation benchmarks
uv run pytest tests/benchmark_rust_performance.py -v

# VPP dispatch benchmarks
uv run pytest tests/benchmark_vpp_performance.py -v

# Full system profiling
python -m cProfile -o profile.stats src/smart_meter_simulator/app.py
```

## Relationships

- **Rust module:** [[Rust Acceleration]]
- **Engine:** [[Simulation Engine]]
- **VPP:** [[VPP Orchestrator]]

## Known Issues

- Benchmarks run on macOS (Apple Silicon) — Linux/x86 may differ
- No warm-up runs — first-run JIT cost may be included
- Network latency not measured (localhost only)
- InfluxDB batch write not benchmarked vs individual writes
