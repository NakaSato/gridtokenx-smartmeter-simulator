---
title: "Brownian Motion Simulation"
category: concepts
created: 2026-04-10
updated: 2026-04-10
sources: ["src/rust_sim/src/lib.rs", "src/smart_meter_simulator/core/meter.py"]
tags: [simulation, noise, time-series, autocorrelation]
related: [[Measurement Noise Model]], [[Standard Load Profiles]], [[Smart Meter]]
---

# Brownian Motion Simulation

Brownian motion with mean reversion is used to generate realistic autocorrelated noise in generation and consumption time series, producing smooth, natural-looking patterns instead of independent white noise.

## Summary

Each meter maintains a running noise state that evolves as an Ornstein-Uhlenbeck process: 80% mean reversion to the previous state plus a Gaussian innovation. This creates time-correlated fluctuations that mimic real-world load behavior.

## Model

### Ornstein-Uhlenbeck Process

```
noise_t = θ × noise_{t-1} + ε_t

Where:
  θ = mean reversion coefficient (0.8 for generation, 0.85 for consumption)
  ε_t = innovation ~ N(0, σ_innovation)
  σ_innovation = base_value × noise_factor
```

### Generation Noise

```python
# Solar generation
innovation = random.normal(0, base_gen × 0.02)
new_noise = 0.8 × last_gen_noise + innovation
generation = base_gen × weather_factor + new_noise
```

| Parameter | Value | Description |
|-----------|-------|-------------|
| Mean reversion | 0.8 | Moderate persistence |
| Innovation σ | 2% of base_gen | Small fluctuations |
| Typical effect | ±2-3% of base | Smooth variation |

### Consumption Noise

```python
# Consumption
innovation = random.normal(0, base_cons × 0.015)
new_noise = 0.85 × last_cons_noise + innovation
consumption = base_cons × slp_factor + new_noise
```

| Parameter | Value | Description |
|-----------|-------|-------------|
| Mean reversion | 0.85 | Higher persistence than generation |
| Innovation σ | 1.5% of base_cons | Smaller relative noise |
| Typical effect | ±1-2% of base | Very smooth |

### Rust Implementation

In `src/rust_sim/src/lib.rs`, the same logic uses `rand_distr::Normal`:

```rust
if let Ok(normal) = Normal::new(0.0, base_gen * 0.02) {
    let innovation = normal.sample(rng);
    let new_noise = 0.8 * last_gen_noise + innovation;
    return (generation.max(0.0), new_noise);
}
```

## Why Brownian Motion?

| Property | White Noise | Brownian Motion |
|----------|------------|-----------------|
| **Autocorrelation** | Zero | High (θ = 0.8-0.85) |
| **Visual appearance** | Jittery | Smooth |
| **Realism** | Poor (real loads don't jump) | Good (loads change gradually) |
| **Spectral content** | Flat (all frequencies) | Low-pass (smooth) |

Real consumption changes gradually — appliances turn on/off, temperature changes slowly. White noise would create unrealistic tick-to-tick jumps.

## Parameter Tuning

| Parameter | Effect of Increasing |
|-----------|---------------------|
| Mean reversion (θ) | Smoother, more persistent noise |
| Innovation σ | Larger amplitude fluctuations |
| Base value | Scales both proportionally |

## Noise State Management

Each meter maintains its own noise state:
- **Generation noise:** Reset each tick, carried forward
- **Consumption noise:** Reset each tick, carried forward
- **Initialization:** Zero at simulation start

This ensures each meter has unique, persistent noise characteristics.

## Relationships

- **Generation:** [[Smart Meter]] (solar curve)
- **Consumption:** [[Standard Load Profiles]]
- **Measurement noise:** [[Measurement Noise Model]] (per-tick, not autocorrelated)

## Known Issues

- Parameters (0.8, 0.85, 2%, 1.5%) are heuristic — not calibrated to real data
- No seasonal variation in noise characteristics
- Innovation is Gaussian — real loads may have skewed distributions
- No correlation between meters (each has independent noise process)
