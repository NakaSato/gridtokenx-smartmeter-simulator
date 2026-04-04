# Running Simulations Guide

This guide covers how to run and manage simulations with the Smart Meter Simulator.

## Simulation Modes

### Server Mode

Runs the simulator as a FastAPI server with REST API and WebSocket support:

```bash
# Basic server mode
uv run start-simulator --mode server --port 8082

# With custom configuration
uv run start-simulator --mode server --meters 100 --api-url http://localhost:4000
```

**Features:**
- REST API endpoints for control and monitoring
- WebSocket real-time streaming
- Multiple transport layers (HTTP, Kafka, InfluxDB)
- Web UI interface

### Standalone Mode

Runs simulation without API server, directly submitting to API Gateway:

```bash
# Basic standalone mode
uv run start-simulator --mode standalone --meters 20

# With custom API endpoint
uv run start-simulator --mode standalone --meters 50 --api-url http://api.example.com
```

**Use Cases:**
- Direct integration with external systems
- Batch processing
- Simplified deployment

## CLI Options

### Basic Options

| Option | Default | Description |
|--------|---------|-------------|
| `--mode` | server | Run mode: `server` or `standalone` |
| `--meters` | 20 | Number of meters to simulate |
| `--port` | 8082 | Server port (server mode only) |
| `--api-url` | http://localhost:3000 | API Gateway URL |
| `--api-key` | sim-secret-key | API authentication key |

### Simulation Parameters

| Option | Description |
|--------|-------------|
| `--interval` | Simulation interval in seconds |
| `--purchase-rate` | Grid purchase rate (Baht/kWh) |
| `--feed-in-rate` | Grid feed-in rate (Baht/kWh) |

### Energy Parameters

| Option | Description |
|--------|-------------|
| `--base-gen-min` | Minimum base generation (kW) |
| `--base-gen-max` | Maximum base generation (kW) |
| `--base-cons-min` | Minimum base consumption (kW) |
| `--base-cons-max` | Maximum base consumption (kW) |

### Meter Distribution

| Option | Description |
|--------|-------------|
| `--solar-ratio` | Ratio of solar prosumer meters |
| `--consumer-ratio` | Ratio of grid consumer meters |
| `--hybrid-ratio` | Ratio of hybrid prosumer meters |
| `--battery-ratio` | Ratio of battery storage meters |
| `--ev-ratio` | Ratio of EV charger meters |

## Advanced Features

### Custom Meter Distribution

Configure specific meter type ratios:

```bash
uv run start-simulator \
  --meters 100 \
  --solar-ratio 0.50 \
  --consumer-ratio 0.25 \
  --hybrid-ratio 0.15 \
  --battery-ratio 0.05 \
  --ev-ratio 0.05
```

**Constraints:**
- All ratios must sum to 1.0
- Each ratio must be between 0.0 and 1.0

### Weather Simulation

The simulator automatically models weather conditions:

| Condition | Weight | Solar Impact |
|-----------|--------|--------------|
| Sunny | 40% | 100% generation |
| Partly Cloudy | 30% | 60-80% generation |
| Cloudy | 15% | 30-50% generation |
| Overcast | 10% | 10-20% generation |
| Rainy | 5% | 5-10% generation |

### Market Dynamics

Enable P2P market dynamics:

```bash
# Via environment variable
ENABLE_MARKET_DYNAMICS=true uv run start-simulator

# Market features:
# - Double auction mechanism
# - Dynamic pricing based on supply/demand
# - Locational Marginal Pricing (LMP)
```

## Monitoring Simulations

### Health Check

```bash
curl http://localhost:8082/health
```

Response:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T12:00:00Z",
  "meters_active": 55,
  "simulation_running": true
}
```

### Status Endpoint

```bash
curl http://localhost:8082/api/status
```

### Meter List

```bash
# List all meters
curl http://localhost:8082/api/meters

# Get specific meter
curl http://localhost:8082/api/meters/AMI_METER_001
```

### Real-time Readings (WebSocket)

```javascript
const ws = new WebSocket('ws://localhost:8082/ws');

ws.onopen = () => {
  console.log('Connected to simulator');
};

ws.onmessage = (event) => {
  const reading = JSON.parse(event.data);
  console.log('Meter reading:', reading);
};
```

**Reading Format:**
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

## Grid Integration

### State Estimation

View state estimation results:

```bash
# Latest estimation
curl http://localhost:8082/api/grid/estimation

# Current measurements
curl http://localhost:8082/api/grid/measurements

# Grid topology
curl http://localhost:8082/api/grid/topology
```

### VPP Status

```bash
# VPP cluster status
curl http://localhost:8082/api/vpp/status

# VPP dispatch commands
curl http://localhost:8082/api/vpp/dispatch
```

### Market Data

```bash
# Active market orders
curl http://localhost:8082/api/market/orders

# Market clearing results
curl http://localhost:8082/api/market/clearing
```

## Stopping Simulations

### Graceful Shutdown

```bash
# Send SIGINT
kill $(cat simulator.pid)

# Or use Ctrl+C if running in foreground
```

### Docker

```bash
# Stop all services
make down

# Or using docker-compose
docker-compose down
```

## Performance Tuning

### Scalability Targets

| Metric | Target |
|--------|--------|
| 1000+ meters × 365 days | <5 minutes |
| State Estimation convergence | >98% |
| FDI detection rate | >99% |

### Optimization Tips

1. **Use Numba JIT:** Enabled by default for pandapower
2. **Vectorized Operations:** Polars for profile loading
3. **Async I/O:** All transports use async operations
4. **Reduce Meter Count:** For development, use fewer meters

```bash
# Development: Fast iteration
NUM_METERS=10 uv run start-simulator

# Production: Full scale
NUM_METERS=1000 uv run start-simulator
```

## Example Workflows

### Development Workflow

```bash
# 1. Start with small simulation
uv run start-simulator --mode server --meters 10

# 2. Test API endpoints
curl http://localhost:8082/api/status

# 3. Monitor WebSocket
# Connect via browser or wscat

# 4. Stop and adjust configuration
kill $(cat simulator.pid)
```

### Production Workflow

```bash
# 1. Set environment variables
export NUM_METERS=500
export API_GATEWAY_URL=https://api.gridtokenx.io
export API_KEY=production-key
export DATABASE_URL=postgresql://...

# 2. Start simulator
uv run start-simulator --mode server

# 3. Monitor via Prometheus
# Metrics available at :9090/metrics
```

### Batch Processing

```bash
# 1. Run standalone simulation
uv run start-simulator --mode standalone --meters 100

# 2. Output to file
# Readings sent directly to API Gateway

# 3. Process results externally
```

## Related Documents

- [Getting Started](getting-started.md)
- [Configuration Guide](configuration.md)
- [API Reference](../api/overview.md)
- [Docker Deployment](docker-deployment.md)
