# Smart Meter Simulator - Development Context

## Project Overview

**Smart Meter Simulator** is an Advanced Metering Infrastructure (AMI) and Grid Orchestration simulator for the GridTokenX P2P energy trading platform. It provides high-fidelity simulation of smart meters with cryptographic signing for Solana blockchain integration, advanced grid modeling via pandapower, and comprehensive market dynamics.

**Current Version:** 3.0.0
**Python Version:** 3.11+
**Package Manager:** `uv`
**Implementation Status:** Phase 27 (InfluxDB Real-Time Database)

### Core Capabilities

| Category | Features |
|----------|----------|
| **AMI Foundation** | 10+ meter types, Ed25519 signing, ANSI C12.20 accuracy classes |
| **Grid Modeling** | Pandapower integration, State Estimation (WLS/Iwamoto), Bad Data Detection |
| **Market Engine** | P2P trading, Locational Marginal Pricing (LMP), Double auction mechanism |
| **Grid Stability** | Frequency regulation (droop control), VPP orchestration, Islanding detection |
| **Data Management** | Polars/Parquet profiles, Standard Load Profiles (SLP), Time-series storage |
| **Interoperability** | CIM (IEC 61970) RDF/XML, Mosaik co-simulation, Kafka event streaming |
| **Security** | FDI attack simulation, Ed25519 signatures, Anomaly detection |
| **Thai Market** | TOU tariffs, Thai wheeling costs, ERC ladder billing |

---

## Building and Running

### Prerequisites

- **Python 3.11** (via `uv` or system)
- **uv** - Python package manager
- **Bun** - For UI build (optional)
- **Docker** - For databases and services (optional)
- **PostgreSQL, InfluxDB, Kafka** - Optional integrations

### Installation

```bash
# Install dependencies
uv sync

# Development mode (includes test tools)
uv sync --dev
```

### Running the Simulator

```bash
# Server mode (FastAPI on port 8082)
uv run start-simulator --mode server --port 8082

# Standalone mode (direct API Gateway submission)
uv run start-simulator --mode standalone --meters 20

# Custom configuration
uv run start-simulator --mode server --meters 100 --api-url http://localhost:4000
```

**CLI Options:**
- `--interval` - Simulation interval in seconds
- `--purchase-rate` / `--feed-in-rate` - Grid tariff rates
- `--base-gen-min/max` - Generation capacity bounds
- `--base-cons-min/max` - Consumption bounds
- `--solar-ratio`, `--consumer-ratio`, `--hybrid-ratio`, `--battery-ratio`, `--ev-ratio` - Meter distribution

### Environment Configuration

Copy `.env.example` to `.env` and configure:

```bash
# Core Settings
SIMULATION_INTERVAL=15        # Seconds between readings
NUM_METERS=55                 # Number of meters
AUTOSTART_SIMULATION=true     # Auto-start on launch

# API Gateway
API_GATEWAY_URL=http://localhost:4000
API_KEY=your-api-key

# Kafka (optional)
KAFKA_BOOTSTRAP_SERVERS=localhost:29092
KAFKA_TOPIC=meter_readings

# InfluxDB (optional)
INFLUXDB_URL=http://localhost:8086
INFLUXDB_TOKEN=your-token
INFLUXDB_ORG=gridtokenx
INFLUXDB_BUCKET=energy_readings

# Database (optional)
DATABASE_URL=postgresql://user:pass@localhost:5432/gridtokenx

# WebSocket
WS_ENABLED=true
WS_PORT=8765
```

### Docker Deployment

```bash
# Build and start all services
make up

# Development mode
make dev

# View logs
make logs

# Health check
make health
```

### Running Tests

```bash
# Run all tests with coverage
uv run pytest

# Run specific test file
uv run pytest tests/test_phase5.py -v

# Run without coverage
uv run pytest --no-cov

# Run with coverage report
uv run pytest --cov-report=html
```

### Building the UI

```bash
cd ui
bun install
bun run build
```

---

## Project Structure

```
gridtokenx-smartmeter-simulator/
├── src/smart_meter_simulator/
│   ├── app.py                  # FastAPI application (REST API + WebSocket)
│   ├── cli.py                  # CLI entry point (server/standalone modes)
│   ├── meter_generator.py      # Meter configuration generation
│   ├── database/               # NEW: PostGIS database integration
│   │   ├── __init__.py         # Database module exports
│   │   ├── models.py           # SQLAlchemy ORM models with GeoAlchemy2
│   │   └── repository.py       # Async repository for spatial queries
│   ├── config/
│   │   ├── __init__.py         # Module exports, backward compatibility
│   │   ├── enums.py            # MeterType, AccuracyClass, WeatherCondition
│   │   ├── channels.py         # METER_TYPE_CHANNELS mapping
│   │   ├── settings.py         # SimulatorConfig (Pydantic BaseSettings)
│   │   ├── thai_market.py      # Thai market constants (wheeling, tariffs)
│   │   └── config_template.yaml
│   ├── core/                   # Core simulation modules
│   │   ├── engine.py           # Simulation orchestration (1000+ lines)
│   │   ├── meter.py            # SmartMeter class with signed readings
│   │   ├── market.py           # P2P trading, tariff management
│   │   ├── vpp.py              # Virtual Power Plant orchestration
│   │   ├── frequency.py        # Frequency regulation (droop control)
│   │   ├── island.py           # Islanding detection, black start
│   │   ├── adr.py              # Automated Demand Response
│   │   ├── optimizer.py        # Optimization engine
│   │   ├── settlement.py       # Settlement engine
│   │   ├── billing.py          # Billing calculations
│   │   ├── thai_tariff.py      # Thai utility tariff (ERC ladder)
│   │   ├── analytics.py        # Grid analytics
│   │   ├── attacker.py         # FDI attack simulation
│   │   ├── data_source.py      # Profile data loading (Polars/Parquet)
│   │   ├── db.py               # PostgreSQL integration
│   │   ├── app_state.py        # Global application state
│   │   ├── constants.py        # Shared constants
│   │   ├── price_provider.py   # ToU price provider abstraction
│   │   ├── price_history.py    # Price history storage & analytics
│   │   ├── price_streamer.py   # Real-time price broadcasting
│   │   └── price_comparison.py # Price comparison engine
│   ├── adapters/               # External system adapters
│   │   ├── pandapower_adapter.py   # Grid topology, measurement tables
│   │   ├── state_estimator.py      # WLS/Iwamoto SE, Chi-squared test
│   │   ├── topology_builder.py     # Programmatic grid construction
│   │   ├── thai_grid_topology.py   # Thai distribution networks (MEA/PEA)
│   │   ├── cim_adapter.py          # CIM RDF/XML import/export
│   │   ├── mosaik_adapter.py       # Co-simulation integration
│   │   └── mosaik_shim.py          # Mosaik compatibility layer
│   ├── models/
│   │   └── reading.py          # EnergyReading, MeasurementChannel
│   ├── transport/              # Data delivery layer
│   │   ├── base.py             # Abstract transport (retry logic)
│   │   ├── composite.py        # Multi-transport aggregator
│   │   ├── http.py             # HTTP REST API client
│   │   ├── websocket.py        # WebSocket real-time streaming
│   │   ├── kafka.py            # Kafka producer (event streaming)
│   │   └── influxdb.py         # InfluxDB time-series storage
│   ├── routers/
│   │   └── router.py           # API router (endpoints)
│   ├── utils/
│   │   ├── crypto.py           # Ed25519 key management, signing
│   │   └── mapbox_matcher.py   # Geographic route matching
│   └── templates/              # Jinja2 HTML templates
├── ui/                         # React frontend (Bun build system)
├── tests/                      # pytest test suite (30+ test files)
├── scripts/                    # Utility scripts
├── data/                       # Simulation output data
├── docker/                     # Docker configuration
├── docker-compose.yml          # NEW: Docker Compose with PostGIS
├── pyproject.toml              # UV-managed dependencies
├── pytest.ini                  # Pytest configuration
├── Dockerfile                  # Multi-stage container build
├── Makefile                    # Docker management commands
└── QWEN.md                     # This file (development context)
```

---

## Documentation

### User Documentation

| Document | Description |
|----------|-------------|
| [`README.md`](README.md) | User-facing project overview |
| [`docs/index.md`](docs/index.md) | Documentation index |
| [`docs/guides/getting-started.md`](docs/guides/getting-started.md) | Quick start guide |
| [`docs/guides/configuration.md`](docs/guides/configuration.md) | Configuration settings |
| [`docs/guides/running-simulations.md`](docs/guides/running-simulations.md) | Simulation management |
| [`docs/guides/docker-deployment.md`](docs/guides/docker-deployment.md) | Docker deployment |

### Technical Documentation

| Document | Description |
|----------|-------------|
| [`docs/architecture/overview.md`](docs/architecture/overview.md) | System architecture |
| [`docs/architecture/simulation-engine.md`](docs/architecture/simulation-engine.md) | Engine internals |
| [`docs/api/overview.md`](docs/api/overview.md) | REST API & WebSocket reference |
| [`docs/reference/thai-grid-topology.md`](docs/reference/thai-grid-topology.md) | Thai distribution network models (MEA/PEA) |

### Reference Documentation

| Document | Description |
|----------|-------------|
| [`docs/reference/meter-spec.md`](docs/reference/meter-spec.md) | AMI specification (Phases 1-22) |
| [`docs/reference/pandapower.md`](docs/reference/pandapower.md) | Pandapower integration guide |
| [`docs/reference/thai-tariffs.md`](docs/reference/thai-tariffs.md) | Thai TOU tariff rates (2026) |
| [`docs/reference/thai-market.md`](docs/reference/thai-market.md) | Thai electricity market analysis |
| [`docs/reference/economic-models.md`](docs/reference/economic-models.md) | Single Buyer vs. P2P pricing |

### Development Documentation

| Document | Description |
|----------|-------------|
| [`QWEN.md`](QWEN.md) | Development context (this file) |
| [`ui/README.md`](ui/README.md) | Frontend documentation |
| [`docs/integration/POSTGIS_INTEGRATION.md`](docs/integration/POSTGIS_INTEGRATION.md) | PostGIS database setup & usage guide |
| [`docs/integration/POSTGIS_SUMMARY.md`](docs/integration/POSTGIS_SUMMARY.md) | PostGIS quick reference & examples |
| [`docs/reference/thai-grid-topology.md`](docs/reference/thai-grid-topology.md) | Thai grid topology module |
| [`docs/reference/grid-map-viewer.md`](docs/reference/grid-map-viewer.md) | Map viewer technical docs |
| [`docs/integration/THAI_INFRASTRUCTURE_MAP_QUICKSTART.md`](docs/integration/THAI_INFRASTRUCTURE_MAP_QUICKSTART.md) | Map viewer quickstart |
| [`docs/integration/THAI_INFRASTRUCTURE_MAP_INTEGRATION.md`](docs/integration/THAI_INFRASTRUCTURE_MAP_INTEGRATION.md) | React integration guide |

---

## Key Architecture Concepts

### Simulation Engine ([`core/engine.py`](src/smart_meter_simulator/core/engine.py))

The `SimulationEngine` orchestrates the entire simulation:

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

**Key Responsibilities:**
1. Manages meter lifecycle and reading generation
2. Coordinates weather simulation updates
3. Dispatches readings through transport layers
4. Integrates pandapower for grid state estimation
5. Handles VPP dispatch commands
6. Runs market matching and settlement
7. Implements bad data detection (Chi-squared, normalized residuals)

### Smart Meter ([`core/meter.py`](src/smart_meter_simulator/core/meter.py))

Each `SmartMeter` instance:

```python
class SmartMeter:
    """
    Represents a single smart meter with:
    - Ed25519 keypair for cryptographic signing
    - Accuracy class modeling (ANSI C12.20)
    - Frequency-watt droop control
    - VPP dispatch setpoint handling
    - Battery/EV logic
    """
```

**Key Features:**
- Generates signed energy readings (generation, consumption, battery, voltage, current)
- Implements frequency-watt droop control (5% droop, ±0.05 Hz deadband)
- Supports VPP dispatch setpoints
- Applies measurement noise based on accuracy class: `σ = (Class / 300) × |Value|`
- Maintains Ed25519 keypair for Solana-compatible signing

### Pandapower Integration ([`adapters/pandapower_adapter.py`](src/smart_meter_simulator/adapters/pandapower_adapter.py))

Converts meter readings to pandapower `net.measurement` tables:

```python
class PandapowerAdapter:
    """
    Maps smart meters to pandapower measurements:
    - element_type: 'bus', 'line', 'load', 'sgen', 'trafo'
    - meas_type: 'v', 'p', 'q', 'i'
    - std_dev: Calculated from accuracy class
    """
```

**Sign Convention:**
- **Load:** Positive P = consumption (draws from grid)
- **Static Generator (sgen):** Positive P = injection (exports to grid)
- **Net Power at Bus:** `P_net = P_sgen - P_load`

### State Estimation ([`adapters/state_estimator.py`](src/smart_meter_simulator/adapters/state_estimator.py))

Implements Weighted Least Squares (WLS) and Iwamoto algorithms:

```python
class StateEstimator:
    """
    State Estimation with:
    - WLS algorithm (Newton-Raphson)
    - Iwamoto method (divergence handling)
    - Chi-squared test for bad data detection
    - Normalized residuals analysis
    - Virtual measurements (zero-injection buses)
    """
```

**Bad Data Detection:**
1. **Chi-squared test:** `J(x̂) > χ²(ν, α)` where ν = m - n (redundancy)
2. **Normalized residuals:** `|r_N| > 3.0` (3-sigma threshold)
3. **Largest normalized residual test** for identification

### Transport Layer ([`transport/`](src/smart_meter_simulator/transport/))

Abstracted transport interface with shared base class:

```python
class TransportLayer(ABC):
    """
    Abstract base with:
    - Connection state management
    - Retry logic (configurable attempts, delay)
    - Reading conversion helpers
    """
```

**Available Transports:**
- **HTTP:** REST API submission to API Gateway
- **WebSocket:** Real-time broadcasting (`ws://localhost:8765/ws`)
- **Kafka:** Event streaming for distributed systems
- **InfluxDB:** Time-series data persistence
- **Composite:** Aggregates multiple transports

### Price System ([`core/price_*.py`](src/smart_meter_simulator/core/))

ToU-based pricing with real-time streaming:

| Module | Purpose |
|--------|---------|
| `price_provider.py` | ToUPriceProvider abstraction for Thai TOU tariffs |
| `price_history.py` | PriceHistoryManager for storage & analytics |
| `price_streamer.py` | PriceStreamer for WebSocket broadcasting |
| `price_comparison.py` | Compare utility vs P2P prices |

---

## API Endpoints

### Core Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/api/status` | Simulator status and meter list |
| GET | `/api/meters` | List all meters |
| GET | `/api/meters/{meter_id}` | Get specific meter details |
| GET | `/api/grid/status` | Grid topology summary |
| GET | `/api/grid/topology` | Detailed grid topology |
| GET | `/api/grid/geojson` | Grid topology in GeoJSON format |
| GET | `/api/grid/measurements` | Current SE measurements |
| GET | `/api/grid/estimation` | Latest SE results |
| GET | `/api/market/orders` | Active market orders |
| GET | `/api/market/clearing` | Market clearing results |
| GET | `/api/vpp/status` | VPP cluster status |
| GET | `/api/vpp/dispatch` | VPP dispatch commands |
| GET | `/api/frequency` | Grid frequency metrics |
| GET | `/api/island/status` | Islanding detection status |
| WS | `/ws` | WebSocket for real-time readings |

### Price & Revenue Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/price/compare` | Compare utility vs P2P prices |
| GET | `/api/v1/price/utility-rates` | Get utility rates |
| GET | `/api/v1/price/p2p-dynamic` | Get dynamic P2P price |
| POST | `/api/v1/revenue/compare` | Compare revenue models |
| GET | `/api/v1/revenue/optimize` | Optimize revenue configuration |
| GET | `/api/v1/p2p/market-prices` | Get market prices |
| POST | `/api/v1/p2p/calculate-cost` | Calculate P2P transaction cost |

### WebSocket Protocol

Connect to `ws://localhost:8765/ws` for real-time meter readings:

```json
{
  "timestamp": "2024-01-01T12:00:00Z",
  "meter_id": "AMI_METER_001",
  "energy_generated_kwh": 5.234,
  "energy_consumed_kwh": 2.145,
  "battery_level_kwh": 7.5,
  "voltage_v": 239.8,
  "current_a": 12.3,
  "frequency_hz": 50.02,
  "signature": "base64-encoded-signature",
  "public_key": "base64-encoded-public-key"
}
```

---

## Configuration Reference

### Meter Type Distribution (Default)

| Type | Ratio | Accuracy Class | Channels |
|------|-------|----------------|----------|
| Solar Prosumer | 40% | CLASS_1_0 | P, Q, V |
| Grid Consumer | 35% | CLASS_2_0 | P, Q, V |
| Hybrid Prosumer | 20% | CLASS_1_0 | P, Q, V, Battery |
| Battery Storage | 5% | CLASS_0_5 | P, Q, V, Battery |
| EV Charger | 10% | CLASS_1_0 | P, Q, V |

### Accuracy Classes (ANSI C12.20)

| Class | Error Range | Typical Use |
|-------|-------------|-------------|
| CLASS_0_2 | ±0.2% | Substation metering |
| CLASS_0_5 | ±0.5% | Feeder head meters |
| CLASS_1_0 | ±1.0% | Commercial/Prosumer |
| CLASS_2_0 | ±2.0% | Residential meters |

### Standard Deviation Calculation

```python
# From accuracy class to measurement std_dev
sigma = (accuracy_class.value / 300.0) * abs(value)
# Example: CLASS_1_0 (1.0) with 5.0 kW reading
# sigma = (1.0 / 300) * 5000 = 16.67 W
```

### Weather Simulation Weights

| Condition | Weight | Solar Impact |
|-----------|--------|--------------|
| Sunny | 40% | 100% generation |
| Partly Cloudy | 30% | 60-80% generation |
| Cloudy | 15% | 30-50% generation |
| Overcast | 10% | 10-20% generation |
| Rainy | 5% | 5-10% generation |

### Thai TOU Tariffs (2026)

| Category | Voltage | On-Peak | Off-Peak | Service Charge |
|----------|---------|---------|----------|----------------|
| Residential (1.2) | < 22 kV | 5.7982 | 2.6369 | 33.29 Baht |
| Small Business (2.2) | < 22 kV | 5.7982 | 2.6369 | 33.29 Baht |

**Time Schedule:**
- **On-Peak:** Mon-Fri 09:00-22:00
- **Off-Peak:** Mon-Fri 22:00-09:00, Weekends & Holidays (all day)

**Additional Charges:**
- Ft (Fuel Adjustment): 0.0972 Baht/kWh
- VAT: 7%

---

## Development Conventions

### Code Style

- **Formatter:** Black (line length 88)
- **Imports:** isort (Black profile)
- **Linting:** flake8
- **Type Hints:** Used throughout codebase
- **Documentation:** Google-style docstrings

### Testing Practices

- **Framework:** pytest with pytest-asyncio
- **Coverage Target:** 50% minimum (configured in `pytest.ini`)
- **Test Markers:**
  - `unit` - Unit tests
  - `integration` - Integration tests
  - `slow` - Long-running tests
  - `phase1` through `phase5` - Roadmap phase tests
  - `vpp`, `market`, `grid`, `crypto` - Feature-specific tests

### Import Organization

Standard order: stdlib → third-party → local

```python
# Standard library
import asyncio
import logging
from typing import Optional

# Third-party
import numpy as np
import pandapower as pp
from fastapi import FastAPI

# Local
from smart_meter_simulator.core.engine import SimulationEngine
from smart_meter_simulator.config import get_config
```

### Error Handling

- Use structured logging with `logger` objects
- Catch specific exceptions, avoid bare `except:`
- Log warnings for recoverable errors (database unavailable, etc.)
- Use `anyhow`-style context for error chaining (via exception causes)

---

## Implementation Roadmap

### Phase 1-2: AMI Foundation ✅ Complete
- Core simulation engine with async meter orchestration
- Ed25519 cryptographic signing
- WebSocket/HTTP transport
- 10+ meter types
- Pandapower integration for measurement tables
- Accuracy class modeling (ANSI C12.20)

### Phase 3: Grid Integration ✅ Complete
- State Estimation (WLS, Iwamoto algorithms)
- Bad data detection (Chi-squared, normalized residuals)
- Geo-SAM integration for solar mapping
- Virtual measurements for zero-injection buses

### Phase 4: Data Source Management ✅ Complete
- Polars/Parquet profile loading
- Standard Load Profile (SLP) generation
- Time-series data handling
- Vectorized operations for performance

### Phase 5: Co-Simulation ✅ Complete
- Mosaik integration adapter
- CIM (IEC 61970) RDF/XML import/export
- Cyber-security simulation (FDI attacks)
- Interoperability testing

### Phase 6-22: Advanced Grid Intelligence ✅ Complete
- Locational Marginal Pricing (LMP)
- Virtual Power Plant (VPP) orchestration
- Frequency regulation (droop control)
- Islanding detection and black start
- Automated Demand Response (ADR)
- Carbon intensity tracking
- Nodal pricing based on congestion
- Market dynamics (double auction)
- Grid resilience modeling

### Phase 23: OpenStreetMap Integration ✅ Complete
- OSM data extraction and parsing
- Electrical infrastructure mapping
- GIS database integration
- Spatial data validation

### Phase 24: Thai Grid Integration & Spatial Analytics ✅ Complete
- PostGIS spatial database with Docker Compose
- EGAT/MEA/PEA grid topology modeling
- Thai electrical infrastructure mapping
- React map viewer with Leaflet
- Real-time meter visualization
- Geographic route matching
- Power plant and solar installation datasets

### Phase 25: Rust Acceleration ✅ Complete
- PyO3-based performance boost (3,655-7,500x speedup)
- Reading generation in Rust
- VPP dispatch in Rust
- Maturin build system

### Phase 26: API Consolidation ✅ Complete
- 67+ endpoints under `/api/v1/` namespace
- Consistent response formats
- Comprehensive API documentation

### Phase 27: InfluxDB Real-Time Database ✅ Complete
- Complete time-series storage for all simulation data
- Real-time query service
- Dashboard integration

### Phase 28: Grafana Dashboards ✅ Complete
- Grafana service in Docker Compose
- Automated provisioning of InfluxDB (Flux) datasource
- Pre-configured Grid Observability dashboard
- Real-time visualization of load and voltage

---

## Common Tasks

### Add a New Meter Type

1. Add meter type to [`config/enums.py`](src/smart_meter_simulator/config/enums.py):
   ```python
   class MeterType(Enum):
       NEW_TYPE = "new_type"
   ```

2. Define measurement channels in [`config/channels.py`](src/smart_meter_simulator/config/channels.py):
   ```python
   METER_TYPE_CHANNELS[MeterType.NEW_TYPE] = {"p", "q", "v"}
   ```

3. Add accuracy class default in [`core/meter.py`](src/smart_meter_simulator/core/meter.py):
   ```python
   accuracy_defaults[MeterType.NEW_TYPE] = AccuracyClass.CLASS_1_0
   ```

4. Update `MeterGenerator` to create the new type

### Modify State Estimation

1. Edit [`adapters/state_estimator.py`](src/smart_meter_simulator/adapters/state_estimator.py) for algorithm changes
2. Update [`adapters/pandapower_adapter.py`](src/smart_meter_simulator/adapters/pandapower_adapter.py) for measurement mapping
3. Add tests in `tests/` with appropriate phase marker

### Add Transport Layer

1. Create new transport class inheriting from [`transport/base.py`](src/smart_meter_simulator/transport/base.py):
   ```python
   class NewTransport(TransportLayer):
       async def connect(self) -> bool: ...
       async def send_reading(self, reading: EnergyReading) -> bool: ...
   ```

2. Register in [`app.py`](src/smart_meter_simulator/app.py) lifespan context

### Debug State Estimation

```bash
# Check estimation results
curl http://localhost:8082/api/grid/estimation

# View measurements
curl http://localhost:8082/api/grid/measurements

# Inspect grid topology
curl http://localhost:8082/api/grid/topology
```

**Common Issues:**
- **Divergence:** Check R/X ratio, try Iwamoto algorithm
- **High Chi²:** Verify accuracy class std_dev calculation
- **Bad Data:** Check for measurement outliers using normalized residuals

---

## Performance Considerations

- **Numba JIT:** Enabled for pandapower Jacobian construction (10-50x speedup)
- **Polars:** Fast DataFrame operations for profile loading
- **Vectorized Controllers:** Use single `ConstControl` for multiple loads
- **Async I/O:** All transports use async operations
- **Recycling:** Reuse Ybus matrices in time-series simulations

**Scalability Targets:**
- 1000+ meters for 365 days in <5 minutes
- State Estimation convergence >98% on IEEE 123-node feeders
- FDI attack detection rate >99%

---

## Security Notes

- **Key Management:** Each meter generates Ed25519 keypair on initialization
- **API Keys:** Required for API Gateway integration (configured via `API_KEY`)
- **FDI Simulation:** Attack injection via `core/attacker.py`
- **No Secrets in Code:** Use environment variables for sensitive configuration

---

## External Integrations

### GridTokenX Ecosystem

- **Solana Blockchain:** Ed25519 signatures compatible with Solana
- **Energy Token Program:** REC (Renewable Energy Certificate) data feeds
- **API Gateway:** HTTP transport submits readings to `API_GATEWAY_URL`

### Co-Simulation Frameworks

- **Mosaik:** Adapter for multi-domain co-simulation (Phase 5)
- **CIM:** IEC 61968/61970 Common Information Model (RDF/XML)
- **OPEN Platform:** Smart Local Energy Systems modeling

---

## Troubleshooting

### Pandapower Import Error

```bash
# Ensure pandapower is installed
uv sync
```

### Database Connection Failed

The simulator continues without database if PostgreSQL is unavailable:
```
Database initialization failed, continuing without persistence
```

### UI Not Loading

```bash
# Build the UI
cd ui
bun install
bun run build
```

### WebSocket Disconnections

- Check if multiple clients are connecting
- Verify `WS_ENABLED=true` in environment
- Check firewall/proxy settings

### State Estimation Divergence

1. Check grid topology for unrealistic R/X ratios
2. Switch to Iwamoto algorithm in [`state_estimator.py`](src/smart_meter_simulator/adapters/state_estimator.py)
3. Increase measurement redundancy (add pseudo-measurements)
4. Verify accuracy class std_dev calculations

---

## Key Files

### Configuration Files

| File | Purpose |
|------|---------|
| [`pyproject.toml`](pyproject.toml) | Project configuration, dependencies, build system |
| [`.env.example`](.env.example) | Environment variable template |
| [`pytest.ini`](pytest.ini) | Pytest configuration |

### Documentation Files

| File | Purpose |
|------|---------|
| [`README.md`](README.md) | User-facing documentation |
| [`QWEN.md`](QWEN.md) | Development context (this file) |
| [`docs/index.md`](docs/index.md) | Documentation index |
| [`docs/integration/`](docs/integration/) | Integration guides (PostGIS, Thai Grid) |
| [`docs/datasets/`](docs/datasets/) | Dataset documentation |
| [`docs/implementation/`](docs/implementation/) | Implementation reports |

### Reference Specifications

| File | Purpose |
|------|---------|
| [`docs/reference/meter-spec.md`](docs/reference/meter-spec.md) | Comprehensive AMI specification (Phases 1-22) |
| [`docs/reference/pandapower.md`](docs/reference/pandapower.md) | Pandapower integration guide |
| [`docs/reference/economic-models.md`](docs/reference/economic-models.md) | Economic model (Single Buyer vs. P2P) |
| [`docs/reference/thai-tariffs.md`](docs/reference/thai-tariffs.md) | Thai TOU tariff rates |
| [`docs/reference/thai-market.md`](docs/reference/thai-market.md) | Thai electricity market analysis |
| [`docs/reference/thai-grid-topology.md`](docs/reference/thai-grid-topology.md) | Thai grid topology module |

### Build & Deployment

| File | Purpose |
|------|---------|
| [`Dockerfile`](Dockerfile) | Container build instructions |
| [`Makefile`](Makefile) | Docker management commands |
| [`uv.lock`](uv.lock) | UV lock file |

---

## License

Part of the GridTokenX Ecosystem - Proprietary

---

_Maintained by the GridTokenX Engineering Team._
