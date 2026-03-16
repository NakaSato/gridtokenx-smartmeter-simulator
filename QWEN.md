# Smart Meter Simulator - Development Context

## Project Overview

**Smart Meter Simulator** is an Advanced Metering Infrastructure (AMI) simulator for Peer-to-Peer (P2P) Solar Energy Trading systems. It generates realistic meter readings with cryptographic signatures for Solana blockchain integration and provides power-system analysis capabilities via pandapower.

**Current Version:** 2.0.0  
**Python Version:** 3.11+  
**Package Manager:** `uv`

### Core Capabilities

- **Multiple Meter Types:** Solar Prosumers, Grid Consumers, Hybrid Systems, Battery Storage, EV Chargers, Feeders, Substations
- **P2P Trading Simulation:** Surplus/deficit detection, dynamic pricing, trading strategies
- **Cryptographic Signing:** Ed25519 signatures for blockchain integration (Solana-compatible)
- **Power System Analysis:** Pandapower integration with State Estimation (WLS, Iwamoto algorithms)
- **Real-time Streaming:** WebSocket and HTTP transports for live data broadcasting
- **Weather Modeling:** Dynamic weather simulation affecting solar generation

---

## Project Structure

```
gridtokenx-smartmeter-simulator/
├── src/smart_meter_simulator/
│   ├── app.py                  # FastAPI application with REST API & WebSocket
│   ├── cli.py                  # Command-line interface
│   ├── meter_generator.py      # Meter configuration generation
│   ├── config/
│   │   └── __init__.py         # SimulatorConfig, environment variables
│   ├── core/
│   │   ├── engine.py           # Core simulation orchestration
│   │   ├── meter.py            # SmartMeter class with reading generation
│   │   ├── analytics.py        # Trading and energy analytics
│   │   ├── market.py           # P2P trading logic, tariff management
│   │   ├── data_source.py      # Time-series profile management
│   │   ├── db.py               # PostgreSQL integration
│   │   ├── adr.py              # Automated Demand Response
│   │   ├── frequency.py        # Frequency regulation (droop control)
│   │   ├── vpp.py              # Virtual Power Plant orchestration
│   │   └── ...                 # Additional modules (island, optimizer, settlement)
│   ├── adapters/
│   │   ├── pandapower_adapter.py   # Pandapower measurement table generation
│   │   ├── state_estimator.py      # WLS/Iwamoto State Estimation
│   │   ├── topology_builder.py     # Programmatic grid topology creation
│   │   ├── cim_adapter.py          # Common Information Model interoperability
│   │   └── mosaik_adapter.py       # Co-simulation integration
│   ├── models/
│   │   └── reading.py          # EnergyReading, MeasurementChannel data models
│   ├── transport/
│   │   ├── base.py             # Abstract transport interface
│   │   ├── composite.py        # Multi-transport aggregator
│   │   ├── http.py             # HTTP REST API client
│   │   ├── websocket.py        # WebSocket real-time streaming
│   │   ├── kafka.py            # Kafka producer for event streaming
│   │   └── influxdb.py         # InfluxDB time-series storage
│   └── utils/
│       ├── crypto.py           # Ed25519 key management, signing
│       ├── zk_worker.py        # Zero-knowledge proof generation
│       └── mapbox_matcher.py   # Geographic route matching
├── tests/                      # pytest test suite
├── ui/                         # React frontend (Bun build system)
├── templates/                  # Jinja2 HTML templates
├── static/                     # Static web assets
├── data/                       # Simulation output data
└── docs/                       # Documentation
```

---

## Building and Running

### Installation

```bash
# Install dependencies using uv
uv sync

# Install in development mode
uv sync --dev
```

### Running the Simulator

```bash
# Start the FastAPI application (default port 8080)
uv run start-simulator

# Or using uvicorn directly
uv run uvicorn smart_meter_simulator.app:app --host 0.0.0.0 --port 8080 --reload
```

### Environment Configuration

Copy `.env.example` to `.env` and configure:

```bash
# Core Settings
SIMULATION_INTERVAL=15        # Seconds between readings
NUM_METERS=20                 # Number of meters to simulate
AUTOSTART_SIMULATION=true     # Auto-start on launch

# API Gateway (optional)
API_GATEWAY_URL=http://localhost:8000
API_KEY=your-api-key

# Database (optional)
DATABASE_URL=postgresql://user:pass@localhost:5432/dbname

# Kafka (optional)
KAFKA_SERVERS=localhost:9092
KAFKA_TOPIC=meter_readings

# InfluxDB (optional)
INFLUXDB_URL=http://localhost:8086
INFLUXDB_TOKEN=your-token
INFLUXDB_ORG=your-org
INFLUXDB_BUCKET=your-bucket
```

### Running Tests

```bash
# Run all tests with coverage
uv run pytest

# Run specific test phase
uv run pytest tests/test_phase5.py -v

# Run without coverage
uv run pytest --no-cov
```

### Building the UI

```bash
cd ui
bun install
bun run build
```

---

## Key Architecture Concepts

### Simulation Engine (`core/engine.py`)

The `SimulationEngine` orchestrates the simulation loop:
1. Manages meter lifecycle and reading generation
2. Coordinates weather simulation updates
3. Dispatches readings through transport layers
4. Integrates pandapower for grid state estimation
5. Handles VPP (Virtual Power Plant) dispatch commands

### Smart Meter (`core/meter.py`)

Each `SmartMeter` instance:
- Generates signed energy readings (generation, consumption, battery level)
- Implements frequency-watt droop control for grid stability
- Supports VPP dispatch setpoints
- Applies measurement noise based on accuracy class (ANSI C12.20)
- Maintains Ed25519 keypair for cryptographic signing

### Pandapower Integration (`adapters/pandapower_adapter.py`)

Converts meter readings to pandapower `net.measurement` tables:
- Maps meter types to accuracy classes (CLASS_0_2, CLASS_0_5, CLASS_1_0, CLASS_2_0)
- Handles sign conventions (load consumption positive, generation negative)
- Calculates standard deviation from accuracy class: `σ = (Class / 300) × |Value|`
- Supports State Estimation with WLS and Iwamoto algorithms

### Transport Layer (`transport/`)

Abstracted transport interface supporting:
- **HTTP:** REST API submission to API Gateway
- **WebSocket:** Real-time broadcasting to connected clients
- **Kafka:** Event streaming for distributed systems
- **InfluxDB:** Time-series data persistence
- **Composite:** Aggregates multiple transports

---

## Development Conventions

### Code Style

- **Formatter:** Black (line length 88)
- **Imports:** isort (Black profile)
- **Linting:** flake8
- **Type Hints:** Used throughout codebase

### Testing Practices

- **Framework:** pytest with pytest-asyncio for async tests
- **Coverage Target:** 50% minimum (configured in `pytest.ini`)
- **Test Markers:**
  - `unit` - Unit tests
  - `integration` - Integration tests
  - `phase1` through `phase5` - Roadmap phase tests
  - `slow` - Long-running tests

### Commit Conventions

- Use conventional commits format
- Reference issues and roadmap phases
- Include test coverage in commits

---

## Implementation Roadmap

### Phase 1: P2P Trading Platform ✅ Complete
- Core simulation engine with async meter orchestration
- Ed25519 cryptographic signing
- WebSocket/HTTP transport
- 5 meter types (Solar Prosumer, Grid Consumer, Hybrid, Battery Storage, EV Charger)

### Phase 2: AMI Foundation ✅ Complete
- Pandapower integration for `net.measurement` tables
- Accuracy class modeling (ANSI C12.20)
- State Estimator (WLS, Iwamoto algorithms)
- Topology Builder for radial/multi-voltage networks
- Measurement Validator for quality checks

### Phase 3: Grid Integration & Analytics 🔄 In Progress
- SCADA system integration
- Newton-Raphson WLS with bad data detection
- Chi-squared test and normalized residuals
- Virtual measurements for zero-injection buses
- Time-series SE loop with feedback control

### Phase 4: Data Source Management ⏳ Planned
- CSV/HDF5/Parquet profile loading
- Standard Load Profile (SLP) generation
- Data pre-processing (timestamp alignment, gap filling)
- Vectorized ConstControl for performance

### Phase 5: Co-Simulation & Advanced Features ⏳ Future
- Mosaik integration for multi-domain co-simulation
- Cyber-security simulation (False Data Injection attacks)
- CIM (Common Information Model) interoperability
- PMU integration for hybrid state estimation

---

## API Endpoints

### Core Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check for API Gateway |
| GET | `/api/status` | Simulator status and meter list |
| GET | `/api/meters` | List all meters with serial numbers |
| GET | `/api/meters/{meter_id}` | Get specific meter details |
| GET | `/api/grid/status` | Grid topology summary |
| GET | `/api/grid/topology` | Detailed grid topology |
| GET | `/api/grid/geojson` | Grid topology in GeoJSON format |
| GET | `/api/grid/measurements` | Current state estimation measurements |
| GET | `/api/grid/estimation` | Latest state estimation results |
| WS | `/ws` | WebSocket for real-time readings |

### WebSocket Protocol

Connect to `ws://localhost:8080/ws` for real-time meter readings. Messages are JSON-formatted:

```json
{
  "timestamp": "2024-01-01T12:00:00Z",
  "meter_id": "AMI_METER_001",
  "energy_generated": 5.234,
  "energy_consumed": 2.145,
  "battery_level": 75.2,
  "signature": "base64-encoded-signature"
}
```

---

## Configuration Reference

### Meter Type Distribution

| Type | Default Ratio | Accuracy Class |
|------|---------------|----------------|
| Solar Prosumer | 40% | CLASS_1_0 |
| Grid Consumer | 35% | CLASS_2_0 |
| Hybrid Prosumer | 20% | CLASS_1_0 |
| Battery Storage | 5% | CLASS_0_5 |
| EV Charger | 10% | CLASS_1_0 |

### Accuracy Classes (ANSI C12.20)

| Class | Error Range | Typical Use |
|-------|-------------|-------------|
| CLASS_0_2 | ±0.2% | Substation metering |
| CLASS_0_5 | ±0.5% | Feeder head meters |
| CLASS_1_0 | ±1.0% | Commercial/Prosumer |
| CLASS_2_0 | ±2.0% | Residential meters |

### Weather Simulation

Default weights for weather conditions:
- Sunny: 40%
- Partly Cloudy: 30%
- Cloudy: 15%
- Overcast: 10%
- Rainy: 5%

---

## Key Files

| File | Purpose |
|------|---------|
| `pyproject.toml` | Project configuration, dependencies, build system |
| `.env.example` | Environment variable template |
| `meter_spec.md` | Comprehensive AMI specification (Phases 1-5) |
| `pandapower.md` | Pandapower integration guide |
| `README.md` | User-facing documentation |
| `pytest.ini` | Pytest configuration |
| `Dockerfile` | Container build instructions |
| `QWEN.md` | Development context and refactoring documentation |

---

## Refactoring Summary (March 2026)

### Completed Refactoring

#### Config Module Restructuring
**Problem:** Circular import risk with `METER_TYPE_CHANNELS` defined in main config module.

**Solution:** Split into three modules:
- `config/enums.py` - MeterType, AccuracyClass, WeatherCondition, GridConnectionStatus
- `config/channels.py` - METER_TYPE_CHANNELS mapping
- `config/settings.py` - SimulatorConfig with Pydantic BaseSettings

**Benefits:**
- Type-safe configuration with validation
- Clear separation of concerns
- Eliminated circular import risk
- Backward-compatible property aliases for legacy code

#### Transport Layer Refactoring
**Problem:** Code duplication across HTTP, Kafka, and InfluxDB transports (connection management, retry logic).

**Solution:** Enhanced `transport/base.py` with:
- Shared connection state management (`_connected`, `_set_connected()`)
- Common retry logic (`_retry_operation()`)
- Reading conversion helper (`_convert_reading_to_dict()`)
- Configurable retry parameters

**Updated Transports:**
- `transport/http.py` - Now inherits from enhanced base class
- `transport/kafka.py` - Uses common connection management
- `transport/influxdb.py` - Uses common conversion helpers

**Benefits:**
- Reduced code duplication by ~40%
- Consistent error handling across transports
- Easier to add new transport implementations

#### Import Organization
**Problem:** Duplicate imports, inconsistent ordering, unused imports.

**Solution:**
- Fixed duplicate imports in `app.py`, `pandapower_adapter.py`, `engine.py`
- Organized imports: stdlib → third-party → local
- Removed unused imports (e.g., `from pydantic import BaseModel`)
- Fixed type hints (`Optional[any]` → `Optional[Any]`)

**Benefits:**
- Cleaner code
- Faster import times
- Easier to maintain

#### Constants Extraction
**Problem:** Magic numbers scattered throughout codebase.

**Solution:** Created `core/constants.py` with:
- Time constants (SIMULATION_INTERVAL_SECONDS, REAL_TIME_TICK_SECONDS)
- Frequency constants (FREQUENCY_NOMINAL_HZ, DROOP_GAIN)
- Accuracy constants (ACCURACY_SIGMA_FACTOR, MIN_STD_DEV_FLOOR)
- Bad data thresholds (BAD_DATA_NORM_RESIDUAL_THRESHOLD)
- Grid analytics limits (VOLTAGE_UPPER_LIMIT_PU, LINE_LOADING_CRITICAL_PERCENT)

**Benefits:**
- Centralized configuration
- Easier to tune parameters
- Self-documenting code

---

## Common Tasks

### Add a New Meter Type

1. Add meter type to `config/__init__.py` `MeterType` enum
2. Define measurement channels in `METER_TYPE_CHANNELS`
3. Add accuracy class mapping in `core/meter.py`
4. Update `MeterGenerator` to create the new type

### Modify State Estimation

1. Edit `adapters/state_estimator.py` for algorithm changes
2. Update `adapters/pandapower_adapter.py` for measurement mapping
3. Add tests in `tests/` with `phase3` marker

### Add Transport Layer

1. Create new transport class inheriting from `transport/base.py`
2. Implement `send_reading()` and `connect()` methods
3. Register in `app.py` lifespan context

### Debug State Estimation Convergence

```python
# Check estimation results
GET /api/grid/estimation

# View measurements
GET /api/grid/measurements

# Inspect grid topology
GET /api/grid/topology
```

Common issues:
- **Divergence:** Check R/X ratio, try Iwamoto algorithm
- **High Chi²:** Verify accuracy class std_dev calculation
- **Bad Data:** Check for measurement outliers using normalized residuals

---

## Troubleshooting

### Pandapower Import Error

```bash
# Ensure pandapower is installed
uv sync
```

### Database Connection Failed

The simulator continues without database if PostgreSQL is unavailable. Check logs for:
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

---

## External Integrations

### GridTokenX Ecosystem

- **Solana Blockchain:** Ed25519 signatures compatible with Solana
- **Energy Token Program:** REC (Renewable Energy Certificate) data feeds
- **University PoA:** Validator integration for academic blockchain
- **API Gateway:** HTTP transport submits readings to `API_GATEWAY_URL`

### Co-Simulation Frameworks

- **Mosaik:** Adapter for multi-domain co-simulation (Phase 5)
- **OPEN Platform:** Smart Local Energy Systems modeling
- **CIM Adapter:** IEC 61968/61970 Common Information Model

---

## Performance Considerations

- **Numba JIT:** Enabled for pandapower Jacobian construction (10-50x speedup)
- **Vectorized Controllers:** Use single `ConstControl` for multiple loads
- **Recycling:** Reuse Ybus matrices in time-series simulations
- **Async I/O:** All transports use async operations for non-blocking I/O

---

## Security Notes

- **Key Management:** Each meter generates Ed25519 keypair on initialization
- **API Keys:** Required for API Gateway integration (configured via `API_KEY`)
- **Zero-Knowledge Proofs:** Optional ZK proof generation in `utils/zk_worker.py`
- **No Secrets in Code:** Use environment variables for sensitive configuration

---

## Contact & Support

- **Repository:** gridtokenx-platform-infa/gridtokenx-smartmeter-simulator
- **Documentation:** See `README.md`, `meter_spec.md`, `pandapower.md`
- **Issues:** Track via project issue tracker
