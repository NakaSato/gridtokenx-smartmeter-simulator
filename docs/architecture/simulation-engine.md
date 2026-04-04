# Simulation Engine Architecture

**Location:** [`src/smart_meter_simulator/core/engine.py`](../src/smart_meter_simulator/core/engine.py)

The `SimulationEngine` is the core orchestration component of the Smart Meter Simulator.

## Class Overview

```python
class SimulationEngine:
    """
    Orchestrates simulation of multiple smart meters with:
    - Grid integration (pandapower)
    - Market dynamics (P2P trading, LMP)
    - VPP orchestration
    - Frequency regulation
    - State estimation
    - FDI attack simulation
    """
```

## Core Responsibilities

### 1. Meter Lifecycle Management

```python
def __init__(self, meters: List[SmartMeter], ...):
    self.meters = meters
    self.billing_engines: Dict[str, ThaiBillingEngine] = {}
```

**Features:**
- Manages 1000+ meter instances concurrently
- Tracks meter configuration and state
- Applies meter-type-specific logic
- Handles billing engine per meter

### 2. Reading Generation

```python
async def generate_reading(self, meter: SmartMeter) -> EnergyReading:
    # Apply weather conditions
    weather = self.get_weather_condition()
    
    # Generate base values from profiles
    generation = self.data_source.get_solar_profile(meter, weather)
    consumption = self.data_source.get_load_profile(meter)
    
    # Apply accuracy class noise
    reading = meter.generate_reading(generation, consumption)
    
    return reading
```

**Process:**
1. Load Standard Load Profiles (SLP) via Polars/Parquet
2. Apply weather simulation weights
3. Generate noisy measurements based on accuracy class
4. Sign readings with Ed25519 keypair

### 3. Weather Simulation

```python
WEATHER_WEIGHTS = {
    'Sunny': 0.40,        # 100% solar generation
    'Partly_Cloudy': 0.30, # 60-80% generation
    'Cloudy': 0.15,       # 30-50% generation
    'Overcast': 0.10,     # 10-20% generation
    'Rainy': 0.05         # 5-10% generation
}
```

**Features:**
- Probabilistic weather condition selection
- Solar generation impact modeling
- Configurable change frequency

### 4. Grid Integration

```python
async def update_grid_measurements(self, readings: List[EnergyReading]):
    # Convert to pandapower measurement table
    measurements = self.adapter.create_measurement_table(readings)
    
    # Run state estimation
    estimation = self.estimator.run_estimation(self.net)
    
    # Check for bad data
    if not estimation.bad_data_detected:
        self.update_grid_state(estimation.results)
```

**Integration Points:**
- Pandapower adapter for measurement mapping
- State estimator (WLS/Iwamoto algorithms)
- Bad data detection (Chi-squared, normalized residuals)
- Virtual measurements for zero-injection buses

### 5. Market Operations

```python
async def run_market_clearing(self):
    # Collect buy/sell orders
    orders = self.market.collect_orders(self.meters)
    
    # Calculate LMP based on grid congestion
    lmp = self.market.calculate_lmp(self.grid_state)
    
    # Match orders via double auction
    clearing = self.market.match_orders(orders, lmp)
    
    # Settle transactions
    await self.settlement.process_clearing(clearing)
```

**Market Features:**
- Double auction mechanism
- Locational Marginal Pricing (LMP)
- Supply/demand-based dynamic pricing
- Thai TOU tariff integration

### 6. VPP Orchestration

```python
async def dispatch_vpp(self):
    # Aggregate VPP resources
    vpp_resources = self.vpp.get_available_resources(self.meters)
    
    # Calculate optimal dispatch
    dispatch = self.optimizer.optimize_dispatch(vpp_resources)
    
    # Send setpoints to meters
    for meter_id, setpoint in dispatch.items():
        await self.send_vpp_setpoint(meter_id, setpoint)
```

**VPP Capabilities:**
- Battery storage aggregation
- EV charger coordination
- Solar prosumer curtailment
- Frequency regulation support

### 7. Frequency Regulation

```python
def apply_frequency_response(self, frequency_deviation: float):
    # Droop control: 5% droop, ±0.05 Hz deadband
    for meter in self.meters:
        if meter.supports_frequency_control:
            adjustment = meter.calculate_droop_response(frequency_deviation)
            meter.apply_power_adjustment(adjustment)
```

**Frequency Control:**
- Frequency-watt droop control
- Configurable deadband
- Rate of Change of Frequency (ROCOF) monitoring

### 8. Islanding Detection

```python
async def check_islanding_conditions(self):
    # Monitor grid connection status
    is_islanded = self.island_manager.detect_islanding(self.grid_state)
    
    if is_islanded:
        # Initiate islanding mode
        await self.island_manager.enter_island_mode()
        
        # Balance generation/load within island
        await self.island_manager.balance_island()
```

**Islanding Features:**
- Passive detection methods
- Black start capability
- Island power balance

## Execution Flow

### Main Simulation Loop

```python
async def start(self):
    self.running = True
    
    while self.running:
        if not self.paused:
            # 1. Generate readings for all meters
            readings = await self.generate_all_readings()
            
            # 2. Update grid measurements
            await self.update_grid_measurements(readings)
            
            # 3. Run market clearing
            await self.run_market_clearing()
            
            # 4. Dispatch VPP resources
            await self.dispatch_vpp()
            
            # 5. Send readings through transport
            await self.transport.send_readings(readings)
            
            # 6. Update simulation time
            self.current_sim_time += self.interval
        
        # Wait for next interval
        await asyncio.sleep(self.real_time_interval)
```

### Async Orchestration

```python
# Parallel reading generation
readings = await asyncio.gather(
    *[meter.generate_reading() for meter in self.meters]
)

# Batch transport dispatch
await asyncio.gather(
    self.http_transport.send(readings),
    self.kafka_transport.send(readings),
    self.websocket_transport.broadcast(readings)
)
```

## Component Integration

```
┌────────────────────────────────────────────────────────────┐
│                    SimulationEngine                         │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ SmartMeter[] │  │  GridAdapter │  │ MarketManager│     │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘     │
│         │                 │                 │              │
│         ▼                 ▼                 ▼              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │  Readings    │  │StateEstimator│  │  Clearing    │     │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘     │
│         │                 │                 │              │
│         └─────────────────┼─────────────────┘              │
│                           ▼                                │
│                  ┌──────────────────┐                      │
│                  │ CompositeTransport│                     │
│                  │  - HTTP           │                     │
│                  │  - WebSocket      │                     │
│                  │  - Kafka          │                     │
│                  │  - InfluxDB       │                     │
│                  └──────────────────┘                      │
└────────────────────────────────────────────────────────────┘
```

## Configuration

### Simulation Parameters

```python
self.interval = 15  # Simulation interval (seconds)
self.real_time_interval = 5  # Real seconds between ticks
self.external_clock = False  # Co-simulation mode
```

### Mode Selection

```python
class SimulationMode(Enum):
    RANDOM = "random"      # Stochastic generation
    PLAYBACK = "playback"  # Profile-based playback
```

## Performance Optimization

### Vectorized Operations

```python
# Use Polars for fast profile loading
import polars as pl

def get_load_profiles(self, meter_ids: List[str]) -> pl.DataFrame:
    return self.profile_cache.filter(
        pl.col("meter_id").is_in(meter_ids)
    )
```

### Numba JIT

```python
from numba import jit

@jit(nopython=True)
def calculate_jacobian(net):
    # 10-50x speedup for pandapower Jacobian
    ...
```

### Async Concurrency

```python
# Parallel meter processing
async def generate_all_readings(self):
    tasks = [self.generate_reading(m) for m in self.meters]
    return await asyncio.gather(*tasks, return_exceptions=True)
```

## Error Handling

```python
try:
    readings = await self.generate_all_readings()
except SimulationError as e:
    logger.error(f"Reading generation failed: {e}")
    readings = self.generate_fallback_readings()
finally:
    # Always attempt transport
    await self.transport.send_readings(readings)
```

## Testing

```python
# Unit test example
@pytest.mark.unit
async def test_simulation_engine_initialization(engine):
    assert len(engine.meters) == 55
    assert engine.running == False
    assert engine.paused == False

# Integration test example
@pytest.mark.integration
async def test_full_simulation_cycle(engine):
    await engine.start()
    await asyncio.sleep(30)  # Run for 30 seconds
    readings = engine.get_readings()
    assert len(readings) > 0
```

## Related Documents

- [System Overview](overview.md)
- [Smart Meter Model](smart-meter.md)
- [Grid Integration](grid-integration.md)
- [Market Engine](market-engine.md)
