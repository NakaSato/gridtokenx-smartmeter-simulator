# Enhanced Smart Meter Simulator for P2P Energy Trading

## Overview
Advanced AMI (Advanced Metering Infrastructure) simulator designed specifically for **Peer-to-Peer Solar Energy Trading** systems using Solana blockchain and University PoA (Proof-of-Authority) consensus.

## Features

### 🔋 **Enhanced Energy Simulation**
- **Multiple Meter Types**: Solar Prosumers, Grid Consumers, Hybrid Systems, Battery Storage
- **Real-time Weather Impact**: Dynamic weather simulation affecting solar generation
- **Battery Management**: Intelligent battery charging/discharging simulation
- **Grid Integration**: Bi-directional energy flow with feed-in tariffs

### 💱 **P2P Trading Capabilities**
- **Trading Opportunities**: Real-time surplus/deficit matching
- **Dynamic Pricing**: Configurable buy/sell price preferences
- **Trading Strategies**: Conservative, Moderate, Aggressive trading behaviors
- **Market Analytics**: Comprehensive trading opportunity analysis

### 🌱 **Renewable Energy Certificates (REC)**
- **REC Generation**: Automatic REC eligibility determination
- **Carbon Offset Calculation**: CO2 offset tracking for renewable generation
- **Environmental Impact**: Weather condition impact on renewable energy

### 📊 **Advanced Analytics**
- **Real-time Monitoring**: Live energy balance tracking
- **Trading Analytics**: Opportunity identification and efficiency scoring
- **Weather Impact Analysis**: Generation performance under different conditions
- **Battery Performance**: Storage system efficiency monitoring

### 🌐 **WebSocket Streaming**
- **Real-time Data Broadcasting**: Live meter readings via WebSocket
- **Multi-client Support**: Serve multiple concurrent clients
- **Batch Broadcasting**: Efficient batch message delivery
- **Web Dashboard**: Built-in HTML client for visualization

## Architecture

```
Enhanced Smart Meter Simulator
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
│   ├── TimescaleDB Storage (Time-series optimization)
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
- Python 3.9+
- PostgreSQL 13+
- TimescaleDB 2.0+
- Apache Kafka (optional)
- Redis (optional)

### Setup
```bash
# Clone the repository
git clone <repository-url>
cd docker/smart-meter-simulator

# Install dependencies
uv install -r requirements.txt

# Copy and configure environment
cp .env.example .env
# Edit .env with your configuration

# Initialize database schema
psql -f schema/timescaledb_schema.sql

# Run the enhanced simulator
python simulator.py
```

## Configuration

### Environment Variables

#### Simulation Settings
```bash
SIMULATION_INTERVAL=15      # Seconds between readings
NUM_METERS=20              # Number of meters to simulate
OUTPUT_FILE=./data/meter_readings.jsonl
```

#### Trading Configuration
```bash
MIN_SELL_PRICE=0.15        # USD per kWh
MAX_SELL_PRICE=0.35        # USD per kWh  
MIN_BUY_PRICE=0.20         # USD per kWh
MAX_BUY_PRICE=0.40         # USD per kWh
GRID_FEED_IN_RATE=0.12     # Grid feed-in rate
GRID_PURCHASE_RATE=0.28    # Grid purchase rate
```

#### Weather Simulation
```bash
WEATHER_SUNNY_WEIGHT=0.4          # 40% sunny weather
WEATHER_PARTLY_CLOUDY_WEIGHT=0.3  # 30% partly cloudy
WEATHER_CLOUDY_WEIGHT=0.15        # 15% cloudy
WEATHER_OVERCAST_WEIGHT=0.1       # 10% overcast
WEATHER_RAINY_WEIGHT=0.05         # 5% rainy
```

#### WebSocket Configuration
```bash
WS_ENABLED=true                    # Enable WebSocket server (default: true)
WS_HOST=localhost                  # WebSocket server host (default: localhost)
WS_PORT=8765                       # WebSocket server port (default: 8765)
```

### Meter Type Distribution
- **Solar Prosumers (40%)**: Residential with solar panels
- **Grid Consumers (35%)**: Traditional grid-connected consumers
- **Hybrid Prosumers (20%)**: Solar + battery storage systems
- **Battery Storage (5%)**: Dedicated storage providers

## Usage Examples

### Basic Simulation
```bash
# Run with default settings
python enhanced_simulator.py

# Run with custom configuration
NUM_METERS=50 SIMULATION_INTERVAL=10 python enhanced_simulator.py
```

### Analytics Dashboard
```bash
# Generate trading analytics
python analytics/trading_analyzer.py

# View generated reports
ls data/analytics/
```

### Web Dashboard & API
```bash
# Run FastAPI web application with dashboard
uvicorn app:app --host 0.0.0.0 --port 8000 --reload

# Access the web dashboard at: http://localhost:8000
# API documentation at: http://localhost:8000/docs
```

### WebSocket Real-time Streaming
```bash
# Run simulator with WebSocket enabled (default)
python simulator.py

# Or run FastAPI app which includes WebSocket support
uvicorn app:app --host 0.0.0.0 --port 8000

# Connect to WebSocket programmatically:
# ws = new WebSocket('ws://localhost:8000/ws')
# ws.onmessage = (event) => console.log(JSON.parse(event.data))
```

### Docker Deployment
```bash
# Build image
docker build -t meter-simulator .

# Run container with WebSocket exposed
docker run -d \
  --name meter-simulator \
  -e NUM_METERS=30 \
  -e SIMULATION_INTERVAL=15 \
  -e WS_HOST=0.0.0.0 \
  -e WS_PORT=8765 \
  -p 8765:8765 \
  -v $(pwd)/data:/app/data \
  meter-simulator
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
- **energy-readings**: Raw meter data
- **trading-opportunities**: P2P trading matches
- **renewable-certificates**: REC generation data

### Database Tables
- **energy_readings_enhanced**: Main time-series data
- **trading_opportunities_summary**: Hourly trading summaries
- **rec_generation_summary**: REC generation reports
- **weather_impact_analysis**: Weather performance analysis

## Analytics & Monitoring

### Real-time Metrics
- Energy balance (generation vs consumption)
- Trading opportunity detection
- Battery performance monitoring
- Weather impact assessment
- REC generation tracking

### Generated Reports
- **Trading Opportunities**: Current buy/sell matches
- **Energy Balance**: System-wide energy flow analysis
- **REC Reports**: Renewable energy certificate generation
- **Weather Impact**: Generation performance by weather condition

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
- **Registry Program**: Meter registration data
- **Energy Token Program**: REC certificate validation
- **Trading Program**: P2P trading opportunities
- **Oracle Program**: AMI data validation
- **Governance Program**: University authority verification

## Development

### Testing
```bash
# Run unit tests
pytest tests/

# Run integration tests with Docker
docker-compose -f docker-compose.test.yml up --build
```

### Custom Extensions
```python
from enhanced_simulator import EnhancedSmartMeterSimulator

# Extend the simulator
class CustomSimulator(EnhancedSmartMeterSimulator):
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

### Prometheus Metrics
- Meter reading rates
- Trading opportunities count
- Energy balance metrics
- System performance indicators

## License
This project is part of the GridTokenX P2P Energy Trading System.

## Support
For technical support and questions, please refer to the main GridTokenX documentation.

---

**Note**: This enhanced simulator is designed for the University PoA (Proof-of-Authority) blockchain environment and integrates with the complete GridTokenX ecosystem for comprehensive P2P energy trading simulation.