# Configuration Guide

This document describes all configuration options for the Smart Meter Simulator.

## Configuration Methods

The simulator can be configured through:

1. **Environment Variables** - Primary configuration method
2. **`.env` File** - Local development configuration
3. **Docker Environment** - Container deployment
4. **Code Configuration** - Programmatic overrides

---

## Environment Variables Reference

### Simulation Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `NUM_METERS` | `20` | Number of virtual meters to simulate |
| `SIMULATION_INTERVAL` | `30` | Seconds between readings (simulated time) |
| `SIMULATION_SPEED_MULTIPLIER` | `1.0` | Speed multiplier for stress testing |
| `RANDOM_SEED` | `42` | Random seed for reproducibility |

### Infrastructure

#### Kafka Configuration
| Variable | Default | Description |
|----------|---------|-------------|
| `KAFKA_BOOTSTRAP_SERVERS` | None | Kafka broker addresses (comma-separated) |
| `KAFKA_TOPIC` | `meter_readings` | Topic for meter readings |

#### Database Configuration
| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql://p2p_user:p2p_password@localhost:5432/p2p_energy_trading` | PostgreSQL connection string |

#### InfluxDB Configuration
| Variable | Default | Description |
|----------|---------|-------------|
| `INFLUXDB_URL` | `http://localhost:8086` | InfluxDB server URL |
| `INFLUXDB_TOKEN` | None | Authentication token |
| `INFLUXDB_ORG` | `gridtoken` | Organization name |
| `INFLUXDB_BUCKET` | `energy_readings` | Bucket for time-series data |

#### WebSocket Configuration
| Variable | Default | Description |
|----------|---------|-------------|
| `WS_ENABLED` | `true` | Enable WebSocket server |
| `WS_HOST` | `localhost` | WebSocket host |
| `WS_PORT` | `8765` | WebSocket port |

#### API Gateway Configuration
| Variable | Default | Description |
|----------|---------|-------------|
| `API_GATEWAY_URL` | `http://localhost:4000` | API Gateway endpoint |
| `API_KEY` | `gridtokenx_secret_key_2025` | API authentication key |

### Energy & Market Configuration

#### Solar Configuration
| Variable | Default | Description |
|----------|---------|-------------|
| `SOLAR_PANEL_EFFICIENCY_MIN` | `0.85` | Minimum panel efficiency |
| `SOLAR_PANEL_EFFICIENCY_MAX` | `0.95` | Maximum panel efficiency |
| `BASE_GENERATION_MIN` | `3.0` | Minimum base generation (kW) |
| `BASE_GENERATION_MAX` | `12.0` | Maximum base generation (kW) |

#### Consumption Configuration
| Variable | Default | Description |
|----------|---------|-------------|
| `BASE_CONSUMPTION_MIN` | `1.5` | Minimum base consumption (kW) |
| `BASE_CONSUMPTION_MAX` | `8.0` | Maximum base consumption (kW) |
| `NOISE_FACTOR_MIN` | `0.05` | Minimum noise factor |
| `NOISE_FACTOR_MAX` | `0.15` | Maximum noise factor |

#### Trading Configuration
| Variable | Default | Description |
|----------|---------|-------------|
| `MIN_SELL_PRICE` | `0.15` | Minimum sell price ($/kWh) |
| `MAX_SELL_PRICE` | `0.35` | Maximum sell price ($/kWh) |
| `MIN_BUY_PRICE` | `0.20` | Minimum buy price ($/kWh) |
| `MAX_BUY_PRICE` | `0.40` | Maximum buy price ($/kWh) |
| `GRID_FEED_IN_RATE` | `0.12` | Grid feed-in tariff ($/kWh) |
| `GRID_PURCHASE_RATE` | `0.28` | Grid purchase rate ($/kWh) |
| `ENABLE_MARKET_DYNAMICS` | `true` | Enable dynamic pricing |

#### Battery Configuration
| Variable | Default | Description |
|----------|---------|-------------|
| `BATTERY_CAPACITY_MIN` | `10.0` | Minimum battery capacity (kWh) |
| `BATTERY_CAPACITY_MAX` | `30.0` | Maximum battery capacity (kWh) |
| `BATTERY_EFFICIENCY_MIN` | `0.90` | Minimum battery efficiency |
| `BATTERY_EFFICIENCY_MAX` | `0.95` | Maximum battery efficiency |

#### EV Configuration
| Variable | Default | Description |
|----------|---------|-------------|
| `EV_BATTERY_CAPACITY_MIN` | `40.0` | Minimum EV battery capacity (kWh) |
| `EV_BATTERY_CAPACITY_MAX` | `80.0` | Maximum EV battery capacity (kWh) |
| `EV_CHARGE_RATE_KW` | `7.4` | EV charge rate (kW) |
| `EV_V2G_DISCHARGE_RATE_KW` | `5.0` | EV vehicle-to-grid discharge rate (kW) |
| `EV_V2G_THRESHOLD_SOC` | `0.4` | Minimum state-of-charge before V2G export |

### Meter Distribution

| Variable | Default | Description |
|----------|---------|-------------|
| `SOLAR_PROSUMER_RATIO` | `0.35` | Fraction of solar prosumer meters |
| `GRID_CONSUMER_RATIO` | `0.30` | Fraction of grid consumer meters |
| `HYBRID_PROSUMER_RATIO` | `0.20` | Fraction of hybrid prosumer meters |
| `BATTERY_STORAGE_RATIO` | `0.05` | Fraction of battery storage meters |
| `EV_CHARGER_RATIO` | `0.10` | Fraction of EV charger meters |

### Weather Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `WEATHER_CHANGE_FREQUENCY` | `5` | Intervals between weather changes |
| `WEATHER_SUNNY_WEIGHT` | `0.4` | Probability weight for sunny weather |
| `WEATHER_PARTLY_CLOUDY_WEIGHT` | `0.3` | Probability weight for partly cloudy |
| `WEATHER_CLOUDY_WEIGHT` | `0.15` | Probability weight for cloudy |
| `WEATHER_OVERCAST_WEIGHT` | `0.1` | Probability weight for overcast |
| `WEATHER_RAINY_WEIGHT` | `0.05` | Probability weight for rainy |

### REC Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `REC_CERTIFICATION_ENABLED` | `true` | Enable REC certification |
| `CARBON_OFFSET_RATE` | `0.7` | kg CO2 offset per kWh solar |

### Logging & Monitoring

| Variable | Default | Description |
|----------|---------|-------------|
| `LOG_LEVEL` | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR) |
| `METRICS_PORT` | `9091` | Prometheus metrics port |
| `HEALTH_CHECK_INTERVAL` | `60` | Health check interval (seconds) |

### Server Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `HOST` | `0.0.0.0` | Server bind address |
| `PORT` | `8000` | Server port |

---

## Enumerations

### MeterType

Available meter types for simulation:

```python
class MeterType(Enum):
    SOLAR_PROSUMER = "Solar_Prosumer"
    GRID_CONSUMER = "Grid_Consumer"
    HYBRID_PROSUMER = "Hybrid_Prosumer"
    BATTERY_STORAGE = "Battery_Storage"
    RESIDENTIAL = "Residential"
    COMMERCIAL = "Commercial"
    FEEDER = "Feeder"
    SUBSTATION = "Substation"
    EV_CHARGER = "EV_Charger"
```

### AccuracyClass

ANSI C12.20 accuracy class definitions:

```python
class AccuracyClass(Enum):
    CLASS_0_2 = 0.002  # ±0.2% (substation meters)
    CLASS_0_5 = 0.005  # ±0.5% (feeder head meters)
    CLASS_1_0 = 0.010  # ±1.0% (commercial meters)
    CLASS_2_0 = 0.020  # ±2.0% (residential meters)
```

### WeatherCondition

Weather conditions affecting solar generation:

```python
class WeatherCondition(Enum):
    SUNNY = "Sunny"
    PARTLY_CLOUDY = "Partly_Cloudy"
    CLOUDY = "Cloudy"
    OVERCAST = "Overcast"
    RAINY = "Rainy"
```

---

## Meter Type to Channel Mapping

Each meter type has specific measurement channels:

| Meter Type | Channels |
|------------|----------|
| Grid Consumer | v, p, q |
| Residential | v, p, q |
| Solar Prosumer | v, p, q |
| Hybrid Prosumer | v, p, q |
| Battery Storage | v, p, q |
| EV Charger | v, p, q |
| Commercial | v, p, q, i |
| Feeder | v, p, q, i |
| Substation | v, p, q, i, ia, va |

**Channel Descriptions**:
- `v` - Voltage magnitude
- `p` - Active power
- `q` - Reactive power
- `i` - Current magnitude
- `ia` - Current angle
- `va` - Voltage angle

---

## Configuration File Examples

### .env File (Development)

```bash
# Simulation
NUM_METERS=50
SIMULATION_INTERVAL=15
SIMULATION_SPEED_MULTIPLIER=2.0

# Database
DATABASE_URL=postgresql://p2p_user:p2p_password@localhost:5432/p2p_energy_trading

# Kafka (comment out for console-only mode)
# KAFKA_BOOTSTRAP_SERVERS=localhost:9092
# KAFKA_TOPIC=meter_readings

# InfluxDB (optional)
# INFLUXDB_URL=http://localhost:8086
# INFLUXDB_TOKEN=your-token
# INFLUXDB_ORG=gridtoken
# INFLUXDB_BUCKET=energy_readings

# API Gateway
API_GATEWAY_URL=http://localhost:3000/api
API_KEY=development-key

# WebSocket
WS_ENABLED=true

# Logging
LOG_LEVEL=DEBUG

# Meter Distribution (must sum to 1.0)
SOLAR_PROSUMER_RATIO=0.35
GRID_CONSUMER_RATIO=0.30
HYBRID_PROSUMER_RATIO=0.20
BATTERY_STORAGE_RATIO=0.05
EV_CHARGER_RATIO=0.10
```

### Docker Compose Environment

```yaml
# docker-compose.yml
version: '3.8'

services:
  simulator:
    build: .
    ports:
      - "8000:8000"
    environment:
      - NUM_METERS=100
      - SIMULATION_INTERVAL=30
      - DATABASE_URL=postgresql://p2p_user:p2p_password@postgres:5432/p2p_energy_trading
      - KAFKA_BOOTSTRAP_SERVERS=kafka:9092
      - INFLUXDB_URL=http://influxdb:8086
      - INFLUXDB_TOKEN=${INFLUXDB_TOKEN}
      - API_GATEWAY_URL=http://api-gateway:3000/api
      - LOG_LEVEL=INFO
    depends_on:
      - postgres
      - kafka
      - influxdb
```

### Production Configuration

```bash
# Production .env
NUM_METERS=1000
SIMULATION_INTERVAL=60
SIMULATION_SPEED_MULTIPLIER=1.0

# Database (use connection pooling)
DATABASE_URL=postgresql://user:password@db.production.com:5432/production_db?sslmode=require

# Kafka (multi-broker)
KAFKA_BOOTSTRAP_SERVERS=kafka1:9092,kafka2:9092,kafka3:9092
KAFKA_TOPIC=production-meter-readings

# InfluxDB (cloud)
INFLUXDB_URL=https://influxdb.production.com:8086
INFLUXDB_TOKEN=production-token
INFLUXDB_ORG=production-org
INFLUXDB_BUCKET=production-readings

# API Gateway
API_GATEWAY_URL=https://api.gridtokenx.com/api
API_KEY=${PRODUCTION_API_KEY}

# Logging
LOG_LEVEL=WARNING
```

---

## Programmatic Configuration

Override configuration in code:

```python
from smart_meter_simulator.config import SimulatorConfig

# Create custom config
config = SimulatorConfig()

# Override values
config.NUM_METERS = 100
config.SIMULATION_INTERVAL = 15

# Or set before import
import os
os.environ['NUM_METERS'] = '100'

# Then import
from smart_meter_simulator.config import SimulatorConfig
```

---

## Configuration Best Practices

1. **Use .env files** for local development
2. **Use environment variables** in production (K8s secrets, Docker secrets)
3. **Never commit** sensitive values (API keys, tokens)
4. **Validate** meter ratios sum to 1.0
5. **Monitor** resource usage when increasing `NUM_METERS`
6. **Use appropriate** `SIMULATION_SPEED_MULTIPLIER` for testing vs production
