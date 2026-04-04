# Configuration Guide

This guide covers all configuration options for the Smart Meter Simulator.

## Environment Variables

### Core Settings

| Variable | Default | Required | Description |
|----------|---------|----------|-------------|
| `SIMULATION_INTERVAL` | 15 | No | Seconds between meter readings |
| `NUM_METERS` | 55 | No | Number of meters to simulate |
| `AUTOSTART_SIMULATION` | true | No | Auto-start simulation on launch |
| `SIMULATION_SPEED_MULTIPLIER` | 1.0 | No | Time acceleration factor |
| `RANDOM_SEED` | 42 | No | Random seed for reproducibility |

### API Gateway

| Variable | Default | Required | Description |
|----------|---------|----------|-------------|
| `API_GATEWAY_URL` | http://localhost:4000 | Yes | Target API endpoint |
| `API_KEY` | sim-secret-key | Yes | Authentication key |

### WebSocket

| Variable | Default | Required | Description |
|----------|---------|----------|-------------|
| `WS_ENABLED` | true | No | Enable WebSocket streaming |
| `WS_HOST` | localhost | No | WebSocket bind host |
| `WS_PORT` | 8765 | No | WebSocket port |

### Kafka (Optional)

| Variable | Default | Required | Description |
|----------|---------|----------|-------------|
| `KAFKA_BOOTSTRAP_SERVERS` | - | No | Kafka brokers (comma-separated) |
| `KAFKA_TOPIC` | meter_readings | No | Kafka topic name |

### InfluxDB (Optional)

| Variable | Default | Required | Description |
|----------|---------|----------|-------------|
| `INFLUXDB_URL` | http://localhost:8086 | No | InfluxDB server URL |
| `INFLUXDB_TOKEN` | - | No | InfluxDB authentication token |
| `INFLUXDB_ORG` | gridtoken | No | InfluxDB organization |
| `INFLUXDB_BUCKET` | energy_readings | No | InfluxDB bucket name |

### PostgreSQL (Optional)

| Variable | Default | Required | Description |
|----------|---------|----------|-------------|
| `DATABASE_URL` | postgresql://... | No | PostgreSQL connection string |

### Solar & Generation

| Variable | Default | Required | Description |
|----------|---------|----------|-------------|
| `SOLAR_PANEL_EFFICIENCY_MIN` | 0.85 | No | Minimum solar panel efficiency |
| `SOLAR_PANEL_EFFICIENCY_MAX` | 0.95 | No | Maximum solar panel efficiency |
| `BASE_GENERATION_MIN` | 3.0 | No | Minimum base generation (kW) |
| `BASE_GENERATION_MAX` | 15.0 | No | Maximum base generation (kW) |

### Consumption & Pricing

| Variable | Default | Required | Description |
|----------|---------|----------|-------------|
| `BASE_CONSUMPTION_MIN` | 1.5 | No | Minimum base consumption (kW) |
| `BASE_CONSUMPTION_MAX` | 8.0 | No | Maximum base consumption (kW) |
| `MIN_SELL_PRICE` | 0.15 | No | Minimum sell price (Baht/kWh) |
| `MAX_SELL_PRICE` | 0.35 | No | Maximum sell price (Baht/kWh) |
| `GRID_FEED_IN_RATE` | 0.12 | No | Grid feed-in tariff (Baht/kWh) |
| `GRID_PURCHASE_RATE` | 0.28 | No | Grid purchase rate (Baht/kWh) |

### Weather Simulation

| Variable | Default | Required | Description |
|----------|---------|----------|-------------|
| `WEATHER_SUNNY_WEIGHT` | 0.40 | No | Sunny weather probability |
| `WEATHER_PARTLY_CLOUDY_WEIGHT` | 0.30 | No | Partly cloudy probability |
| `WEATHER_CLOUDY_WEIGHT` | 0.15 | No | Cloudy weather probability |
| `WEATHER_OVERCAST_WEIGHT` | 0.10 | No | Overcast probability |
| `WEATHER_RAINY_WEIGHT` | 0.05 | No | Rainy weather probability |
| `WEATHER_CHANGE_FREQUENCY` | 5 | No | Weather update interval (minutes) |

### Meter Type Distribution

| Variable | Default | Required | Description |
|----------|---------|----------|-------------|
| `SOLAR_PROSUMER_RATIO` | 0.40 | No | Solar prosumer meter ratio |
| `GRID_CONSUMER_RATIO` | 0.35 | No | Grid consumer meter ratio |
| `HYBRID_PROSUMER_RATIO` | 0.20 | No | Hybrid prosumer meter ratio |
| `BATTERY_STORAGE_RATIO` | 0.05 | No | Battery storage meter ratio |
| `EV_CHARGER_RATIO` | 0.00 | No | EV charger meter ratio |

### Battery Configuration

| Variable | Default | Required | Description |
|----------|---------|----------|-------------|
| `BATTERY_CAPACITY_MIN` | 10.0 | No | Minimum battery capacity (kWh) |
| `BATTERY_CAPACITY_MAX` | 30.0 | No | Maximum battery capacity (kWh) |
| `BATTERY_EFFICIENCY_MIN` | 0.90 | No | Minimum battery efficiency |
| `BATTERY_EFFICIENCY_MAX` | 0.95 | No | Maximum battery efficiency |

### Market Dynamics

| Variable | Default | Required | Description |
|----------|---------|----------|-------------|
| `ENABLE_MARKET_DYNAMICS` | true | No | Enable P2P market dynamics |

### Logging & Metrics

| Variable | Default | Required | Description |
|----------|---------|----------|-------------|
| `LOG_LEVEL` | INFO | No | Logging level (DEBUG, INFO, WARNING, ERROR) |
| `METRICS_PORT` | 9090 | No | Prometheus metrics port |
| `PROMETHEUS_METRICS_ENABLED` | true | No | Enable Prometheus metrics |
| `HEALTH_CHECK_INTERVAL` | 60 | No | Health check interval (seconds) |

### University Validator (Optional)

| Variable | Default | Required | Description |
|----------|---------|----------|-------------|
| `UNIVERSITY_VALIDATOR_ENDPOINT` | http://localhost:8899 | No | REC certification endpoint |
| `ENGINEERING_DEPT_AUTHORITY` | true | No | Enable engineering dept authority |
| `REC_CERTIFICATION_ENABLED` | true | No | Enable REC certification |
| `CARBON_OFFSET_RATE` | 0.7 | No | Carbon offset rate |

### Mapbox (Optional)

| Variable | Default | Required | Description |
|----------|---------|----------|-------------|
| `VITE_MAPBOX_ACCESS_TOKEN` | - | No | Mapbox access token for geo-features |

## Configuration File

The simulator also supports YAML configuration via `config_template.yaml`:

```yaml
simulation:
  interval: 15
  num_meters: 55
  autostart: true

api:
  gateway_url: http://localhost:4000
  api_key: your-api-key

websocket:
  enabled: true
  port: 8765

meter_distribution:
  solar_prosumer: 0.40
  grid_consumer: 0.35
  hybrid_prosumer: 0.20
  battery_storage: 0.05
  ev_charger: 0.00
```

## CLI Configuration

Override environment variables via CLI:

```bash
# Custom interval and meter count
uv run start-simulator --mode server --interval 30 --meters 100

# Custom pricing
uv run start-simulator --purchase-rate 0.28 --feed-in-rate 0.12

# Custom meter distribution
uv run start-simulator \
  --solar-ratio 0.50 \
  --consumer-ratio 0.30 \
  --hybrid-ratio 0.15 \
  --battery-ratio 0.05
```

## Best Practices

### Development

```bash
# Use lower meter count for faster iteration
NUM_METERS=10 uv run start-simulator

# Enable debug logging
LOG_LEVEL=DEBUG uv run start-simulator
```

### Production

```bash
# Use fixed random seed for reproducibility
RANDOM_SEED=42 uv run start-simulator

# Enable all persistence layers
DATABASE_URL=postgresql://... INFLUXDB_TOKEN=... uv run start-simulator
```

### Testing

```bash
# Disable autostart for manual control
AUTOSTART_SIMULATION=false uv run start-simulator
```

## Related Documents

- [Getting Started](getting-started.md)
- [Running Simulations](running-simulations.md)
- [Thai Tariffs Reference](../reference/thai-tariffs.md)
