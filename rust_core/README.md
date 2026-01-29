# Smart Meter Rust Core

High-performance Rust implementation of the smart meter simulation engine with Python bindings via PyO3.

## Architecture

The Rust core replaces Python implementations for all performance-critical calculations:

```
┌─────────────────────────────────────────────────────────────────┐
│                         Python Layer                            │
│    (FastAPI, Web UI, pandapower integration, orchestration)     │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     smartmeter_core (Rust)                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │  MeterSim    │  │WeatherSystem │  │MatchingEngine│          │
│  │  (Complete   │  │  (Markov     │  │  (P2P Trade  │          │
│  │   Meter)     │  │   Chain)     │  │   Matching)  │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ PowerQuality │  │ZoningService │  │EmissionCalc  │          │
│  │  (THD Calc)  │  │  (K-Means)   │  │  (Carbon)    │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │SolarCalculator│ │LoadCalculator│  │ BatteryState │          │
│  │  (PV Model)  │  │(Load Profile)│  │  (SOC/SoH)   │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│  ┌──────────────┐  ┌──────────────┐                            │
│  │  GridPhysics │  │MarketCalculator│                          │
│  │  (V, f, PF)  │  │  (Pricing)   │                            │
│  └──────────────┘  └──────────────┘                            │
└─────────────────────────────────────────────────────────────────┘
```

## Modules

| Module | File | Description |
|--------|------|-------------|
| `MeterSim` | [meter_sim.rs](src/meter_sim.rs) | Complete smart meter simulation with all components |
| `SimReading` | [meter_sim.rs](src/meter_sim.rs) | Output data structure for meter readings |
| `WeatherSystem` | [weather.rs](src/weather.rs) | Markov chain weather simulation |
| `MatchingEngine` | [trading.rs](src/trading.rs) | P2P energy trading matching engine |
| `TradeBid/TradeAsk` | [trading.rs](src/trading.rs) | Trade order data structures |
| `TradeMatch` | [trading.rs](src/trading.rs) | Matched trade result |
| `ZoningService` | [zoning.rs](src/zoning.rs) | K-Means clustering for microgrid zones |
| `ZoneInfo` | [zoning.rs](src/zoning.rs) | Zone information data |
| `PowerQuality` | [power_quality.rs](src/power_quality.rs) | THD (Total Harmonic Distortion) calculation |
| `SolarCalculator` | [solar.rs](src/solar.rs) | Photovoltaic power generation model |
| `LoadCalculator` | [load.rs](src/load.rs) | Load profile with user type patterns |
| `BatteryState` | [battery.rs](src/battery.rs) | Battery SOC, SOH, charge/discharge model |
| `GridPhysics` | [grid.rs](src/grid.rs) | Voltage, frequency, power factor calculations |
| `EmissionCalculator` | [emission.rs](src/emission.rs) | Carbon emissions and REC eligibility |
| `MarketCalculator` | [market.rs](src/market.rs) | Dynamic pricing model |

## Performance

Benchmarks on Apple M-series (arm64):

| Operation | Performance |
|-----------|-------------|
| `MeterSim.generate_reading()` | ~590,000 ops/sec |
| `WeatherSystem.step()` | ~2,300,000 ops/sec |
| `PowerQuality.estimate_thd()` | ~1,300,000 ops/sec |
| `ZoningService.fit()` (500 meters) | ~5,400 ops/sec |
| `MatchingEngine.match_greedy()` (100×100) | ~4,100 ops/sec |

## Building

```bash
# Install maturin
pip install maturin

# Build and install in development mode
cd rust_core
maturin develop --release

# Build release wheel
maturin build --release
```

## Usage

```python
import smartmeter_core as core

# 1. Weather simulation
weather = core.WeatherSystem()
irradiance, temp, state = weather.step()

# 2. Power quality
pq = core.PowerQuality()
thd_v, thd_i = pq.estimate_thd(has_ev_charger=True, ev_power_kw=7.0)

# 3. P2P Trading
engine = core.MatchingEngine()
bids = [core.TradeBid('buyer1', zone=1, amount_kwh=100, price=3.5, wallet='0x...')]
asks = [core.TradeAsk('seller1', zone=1, amount_kwh=80, price=3.0, wallet='0x...')]
matches, welfare = engine.match_greedy(bids, asks)

# 4. Zoning
zoning = core.ZoningService(num_zones=5)
zone_ids = zoning.fit([(lat1, lon1), (lat2, lon2), ...])

# 5. Complete meter simulation
meter = core.MeterSim(
    meter_id='meter-001',
    meter_type='Prosumer',
    user_type='Residential',
    has_solar=True,
    solar_capacity_kw=5.0,
    has_battery=True,
    battery_capacity_kwh=10.0,
)
meter.update_weather('Sunny', 0.9, 2.0)
reading = meter.generate_reading('2024-01-15T12:00:00Z')
print(f"Generated: {reading.energy_generated} kWh")
print(f"Consumed: {reading.energy_consumed} kWh")
```

## Dependencies

- `pyo3` 0.21 - Python bindings
- `chrono` 0.4 - Date/time handling  
- `rand` 0.8 - Random number generation
- `serde` 1.0 - Serialization (for JSON output)

## Python Compatibility

- Python 3.9+ (ABI3 stable ABI)
- Works on macOS, Linux, Windows
