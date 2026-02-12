# Smart Meter Simulator for P2P Energy Trading

**Version: 2.0.0**

## Overview
Advanced AMI (Advanced Metering Infrastructure) simulator designed specifically for Peer-to-Peer Solar Energy Trading systems using Solana blockchain and University PoA (Proof-of-Authority) consensus.

### Project Scope

**Current Focus (Phase 1):** Blockchain-focused P2P energy trading platform simulator that generates realistic meter readings with cryptographic signatures for Solana token minting.

**Future Vision (Phase 2+):** Comprehensive AMI modeling framework with power-system analysis capabilities including State Estimation, pandapower integration, and co-simulation architectures.

See [Implementation Roadmap](#roadmap) for detailed phases and [meter_spec.md](meter_spec.md) for complete technical specification.

## Features

### Enhanced Energy Simulation
- Multiple Meter Types: Solar Prosumers, Grid Consumers, Hybrid Systems, Battery Storage, EV Chargers
- Real-time Weather Impact: Dynamic weather simulation affecting solar generation
- Battery Management: Intelligent battery charging/discharging simulation
- Grid Integration: Bi-directional energy flow with feed-in tariffs

### P2P Trading Capabilities
- Trading Opportunities: Real-time surplus/deficit matching
- Dynamic Pricing: Configurable buy/sell price preferences
- Trading Strategies: Conservative, Moderate, Aggressive trading behaviors
- Market Analytics: Comprehensive trading opportunity analysis

### Renewable Energy Certificates (REC)
- REC Generation: Automatic REC eligibility determination
- Carbon Offset Calculation: CO2 offset tracking for renewable generation
- Environmental Impact: Weather condition impact on renewable energy

### Advanced Analytics
- Real-time Monitoring: Live energy balance tracking
- Trading Analytics: Opportunity identification and efficiency scoring
- Weather Impact Analysis: Generation performance under different conditions
- Battery Performance: Storage system efficiency monitoring

### WebSocket Streaming
- Real-time Data Broadcasting: Live meter readings via WebSocket
- Multi-client Support: Serve multiple concurrent clients
- Batch Broadcasting: Efficient batch message delivery
- Web Dashboard: Built-in HTML client for visualization

## Project Structure

```
smart-meter-simulator/
├── src/
│   └── smart_meter_simulator/
│       ├── __init__.py
│       ├── app.py                  # FastAPI application
│       ├── cli.py                  # CLI interface
│       ├── meter_generator.py      # Meter generation logic
│       ├── config/
│       │   └── __init__.py
│       ├── core/
│       │   ├── engine.py           # Core simulation engine
│       │   ├── meter.py            # Meter models
│       │   ├── analytics.py        # Analytics and statistics
│       │   ├── attacker.py         # Cyber-security simulation
│       │   ├── data_source.py      # Data source management
│       │   ├── db.py               # Database integration
│       │   ├── adr.py              # Automated Demand Response
│       │   ├── frequency.py        # Frequency regulation
│       │   ├── island.py           # Island/microgrid mode
│       │   ├── market.py           # Market dynamics
│       │   ├── optimizer.py        # Optimization algorithms
│       │   ├── settlement.py       # Energy settlement
│       │   └── vpp.py              # Virtual Power Plant
│       ├── models/
│       │   └── reading.py          # Reading data models
│       ├── transport/
│       │   ├── base.py             # Base transport interface
│       │   ├── composite.py        # Composite transport
│       │   ├── http.py             # HTTP transport
│       │   ├── kafka.py            # Kafka producer transport
│       │   ├── websocket.py        # WebSocket transport
│       │   └── influxdb.py         # InfluxDB transport
│       ├── adapters/
│       │   ├── pandapower_adapter.py  # pandapower integration
│       │   ├── state_estimator.py     # State estimation
│       │   ├── topology_builder.py    # Network topology
│       │   ├── cim_adapter.py         # CIM interoperability
│       │   ├── mosaik_shim.py         # Mosaik shim layer
│       │   └── mosaik_adapter.py      # Mosaik co-simulation
│       └── utils/
│           ├── crypto.py           # Cryptographic utilities
│           └── zk_worker.py        # Zero-knowledge proofs
├── tests/                          # Unit and integration tests
├── scripts/                        # Application runner scripts
├── templates/                      # Jinja2 templates and code templates
├── docs/                           # Documentation
├── data/                           # Data files and outputs
├── static/                         # Static web assets
├── pyproject.toml                  # Project configuration
├── requirements.txt                # Python dependencies
├── Dockerfile                      # Application container
└── README.md                       # This file
```

## Architecture

```
Smart Meter Simulator
├── Core Simulation Engine
│   ├── Weather Simulation (Dynamic conditions)
│   ├── Solar Generation (Time/weather dependent)
│   ├── Consumption Patterns (User-type specific)
│   └── Battery Management (Charge/discharge cycles)
├── P2P Trading Engine
│   ├── Surplus/Deficit Detection
│   ├── Price Matching Algorithm
│   ├── Trading Opportunity Scoring
│   └── Market Dynamics Simulation
├── Data Pipeline
│   ├── Kafka Producer (Real-time streaming)
│   ├── InfluxDB Storage (Time-series data)
│   ├── PostgreSQL Integration (Relational data)
│   └── File Backup (JSONL format)
└── Analytics Engine
  ├── Trading Opportunity Analyzer
  ├── Energy Balance Reporter
  ├── REC Generation Tracker
  └── Visualization Generator
```

## Installation

### Prerequisites
- Python 3.11+
- Docker and Docker Compose (for full setup with dependencies)

### Quick Setup with Docker
```bash
# Clone the repository
git clone <repository-url>
cd smart-meter-simulator

# Start all services
docker-compose up -d

# Access the application at http://localhost:8000
```

### Manual Setup
```bash
# Clone the repository
git clone <repository-url>
cd smart-meter-simulator

# Install Python dependencies
pip install -e .

# Copy and configure environment (optional)
cp .env.example .env
# Edit .env with your configuration

# Run the simulator
python scripts/run.py
```

## Configuration

### Environment Variables

#### Simulation Settings
```bash
NUM_METERS=100              # Number of meters to simulate
SIMULATION_INTERVAL=5       # Seconds between readings
STANDALONE_MODE=true        # Run without external dependencies
```

#### Database Configuration
```bash
DB_HOST=localhost
DB_PORT=5432
DB_NAME=smart_meter_db
DB_USER=postgres
DB_PASSWORD=password
```

#### Kafka Configuration
```bash
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
KAFKA_TOPIC=meter_readings
```

#### InfluxDB Configuration
```bash
INFLUXDB_URL=http://localhost:8086
INFLUXDB_TOKEN=my-super-secret-auth-token
INFLUXDB_ORG=smart_meter_org
INFLUXDB_BUCKET=meter_data
```

#### Trading Configuration
```bash
MIN_SELL_PRICE=0.15         # USD per kWh
MAX_SELL_PRICE=0.35         # USD per kWh
MIN_BUY_PRICE=0.20          # USD per kWh
MAX_BUY_PRICE=0.40          # USD per kWh
GRID_FEED_IN_RATE=0.12      # Grid feed-in rate
GRID_PURCHASE_RATE=0.28     # Grid purchase rate
```

#### Weather Simulation
```bash
WEATHER_SUNNY_WEIGHT=0.4           # 40% sunny weather
WEATHER_PARTLY_CLOUDY_WEIGHT=0.3   # 30% partly cloudy
WEATHER_CLOUDY_WEIGHT=0.15         # 15% cloudy
WEATHER_OVERCAST_WEIGHT=0.1        # 10% overcast
WEATHER_RAINY_WEIGHT=0.05          # 5% rainy
```

### Meter Type Distribution
- Solar Prosumers (35%): Residential with solar panels
- Grid Consumers (30%): Traditional grid-connected consumers
- Hybrid Prosumers (20%): Solar + battery storage systems
- Battery Storage (5%): Dedicated storage providers
- EV Chargers (10%): Electric vehicle charging stations

## Usage Examples

### Basic Simulation
```bash
# Run with default settings
python scripts/run.py

# Run with custom configuration
NUM_METERS=50 SIMULATION_INTERVAL=10 python scripts/run.py
```

### Web Dashboard & API
```bash
# Run FastAPI web application with dashboard
uvicorn smart_meter_simulator.app:app --host 0.0.0.0 --port 8000 --reload

# Access the web dashboard at: http://localhost:8000
# API documentation at: http://localhost:8000/docs
```

### WebSocket Real-time Streaming
```bash
# Run simulator with WebSocket enabled (default)
python scripts/run.py

# Or run FastAPI app which includes WebSocket support
uvicorn smart_meter_simulator.app:app --host 0.0.0.0 --port 8000

# Connect to WebSocket programmatically:
# ws = new WebSocket('ws://localhost:8000/ws')
# ws.onmessage = (event) => console.log(JSON.parse(event.data))
```

### Docker Deployment
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f app

# Stop services
docker-compose down
```

## Data Outputs

### Energy Readings Format
```json
{
  "timestamp": "2024-01-01T12:00:00Z",
  "meter_id": "AMI_METER_001",
  "meter_type": "Solar_Prosumer",
  "location": "Zone_1_Building_1",
  "user_type": "Prosumer",
  "energy_generated": 5.234,
  "energy_consumed": 2.145,
  "energy_available_for_sale": 2.487,
  "battery_level": 75.2,
  "surplus_energy": 3.089,
  "trading_preference": "Moderate",
  "max_sell_price": 0.28,
  "max_buy_price": 0.32,
  "rec_eligible": true,
  "carbon_offset": 3.664,
  "weather_condition": "Sunny"
}
```

### Kafka Topics
- energy-readings: Raw meter data
- trading-opportunities: P2P trading matches
- renewable-certificates: REC generation data

### Database Tables
- energy_readings_enhanced: Main time-series data
- trading_opportunities_summary: Hourly trading summaries
- rec_generation_summary: REC generation reports
- weather_impact_analysis: Weather performance analysis

## Analytics & Monitoring

### Real-time Metrics
- Energy balance (generation vs consumption)
- Trading opportunity detection
- Battery performance monitoring
- Weather impact assessment
- REC generation tracking

### Generated Reports
- Trading Opportunities: Current buy/sell matches
- Energy Balance: System-wide energy flow analysis
- REC Reports: Renewable energy certificate generation
- Weather Impact: Generation performance by weather condition

### Visualizations
- Energy supply vs demand trends
- Trading price movements
- Battery utilization patterns
- Weather impact on generation

## Integration with GridTokenX

### Solana Blockchain Integration
- Compatible with GridTokenX Anchor programs
- REC data feeds to Energy Token program
- Trading signals for P2P marketplace
- University PoA validator integration

### Program Compatibility
- Registry Program: Meter registration data
- Energy Token Program: REC certificate validation
- Trading Program: P2P trading opportunities
- Oracle Program: AMI data validation
- Governance Program: University authority verification

## Development

### Testing
```bash
# Run unit tests
pytest tests/

# Install in development mode first
pip install -e .
```

### Custom Extensions
```python
from smart_meter_simulator.simulator import SmartMeterSimulator

# Extend the simulator
class CustomSimulator(SmartMeterSimulator):
    def custom_trading_logic(self):
        # Add custom trading algorithms
        pass
```

## Monitoring & Alerts

### Health Checks
- Database connectivity
- Kafka producer health
- Data quality validation
- Generation anomaly detection

### API Endpoints
- GET /health/ready: Health check endpoint
- GET /api/status: Simulator status
- POST /api/control/start: Start simulation
- POST /api/control/stop: Stop simulation

## Roadmap

### Phase 1: P2P Trading Platform (✅ Current)
**Status:** Active  
**Focus:** Blockchain-ready meter reading generation with cryptographic signing

**Delivered:**
- ✅ Core simulation engine with async meter orchestration
- ✅ Ed25519 cryptographic signing for blockchain integration
- ✅ WebSocket/HTTP transport layer
- ✅ 5 meter types (Solar Prosumer, Grid Consumer, Hybrid, Battery Storage, EV Charger)
- ✅ Basic weather simulation and energy modeling
- ✅ REST API with FastAPI

### Phase 2: AMI Foundation (✅ Completed)
**Status:** Completed
**Focus:** Power-system analysis foundation with pandapower integration

**Delivered Components:**
- Pandapower integration for `net.measurement` tables
- Accuracy class modeling (CLASS_0_2, CLASS_0_5, CLASS_1_0, CLASS_2_0)
- Measurement channel filtering per meter type
- Gaussian error models and σ derivation
- Sign convention mapping (Load vs. Generator reference frames)
- Topology Builder for radial and multi-voltage networks
- State Estimator with WLS and Iwamoto algorithms
- Measurement Validator for range and consistency checks

**Success Metrics:**
- Generate valid pandapower measurement tables from 50+ meters
- Accuracy class mapping matches ANSI C12.20 standard ±2%
- Test coverage: 60%+

### Phase 3: Grid Integration & Analytics (⏳ In Progress)
**Status:** Planned
**Focus:** SCADA system integration and real-time monitoring

**Planned Components:**
- Newton-Raphson WLS and Iwamoto SE algorithms
- Pseudo-measurement generation for observability
- Chi-squared test and normalized residuals for bad data detection
- Virtual measurements for zero-injection buses
- Time-series SE loop with feedback control

**Success Metrics:**
- SE convergence >95% on IEEE 123-node feeder
- Bad data detection: 95%+ true positive rate
- Reduce required meter coverage from 100% to 30%

### Phase 4: Data Source Management (⏳ Planned - 4-6 weeks)
**Status:** Proposed  
**Focus:** Historical and synthetic profile management

**Planned Components:**
- CSV/HDF5/Parquet profile loading
- Standard Load Profile (SLP) generation (H0, G0 profiles)
- Data pre-processing pipeline (timestamp alignment, gap filling)
- Vectorized ConstControl for performance optimization

**Success Metrics:**
- Profile generation <5% RMS error vs. target consumption
- 1000-meter simulation completes 365 days in <5 minutes
- Test coverage: 80%+

### Phase 5: Co-Simulation & Advanced Features (⏳ Future - 8-12 weeks)
**Status:** Proposed  
**Focus:** External simulator integration and advanced modeling

**Planned Components:**
- Mosaik integration for multi-domain co-simulation
- OPEN platform integration for Smart Local Energy Systems
- Cyber-security simulation (False Data Injection attacks)
- CIM (Common Information Model) interoperability
- PMU integration for hybrid state estimation

**Success Metrics:**
- Mosaik adapter with sub-second synchronization
- FDI attack detection: 99%+ stealth detection rate
- CIM lossless round-trip import/export

**Timeline:** 6-9 months total | **Budget:** ~$29k-$46k (~4-4.25 FTE)

See [.github/prompts/plan-alignSpecificationWithImplementation.prompt.md](.github/prompts/plan-alignSpecificationWithImplementation.prompt.md) for detailed implementation plan.

## License
This project is part of the GridTokenX P2P Energy Trading System.

## Support
For technical support and questions, please refer to the main GridTokenX documentation.

---

Note: This simulator is designed for the University PoA (Proof-of-Authority) blockchain environment and integrates with the complete GridTokenX ecosystem for comprehensive P2P energy trading simulation.