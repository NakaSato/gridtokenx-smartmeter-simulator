# Getting Started Guide

This guide will help you get the Smart Meter Simulator up and running quickly.

## Prerequisites

- **Python 3.11** (via `uv` or system)
- **uv** - Python package manager
- **Bun** - For UI build (optional)
- **Docker** - For databases and services (optional)

## Installation

### Option 1: UV (Recommended)

```bash
# Clone the repository
git clone https://github.com/gridtokenx/gridtokenx-smartmeter-simulator.git
cd gridtokenx-smartmeter-simulator

# Install dependencies
uv sync

# Development mode (includes test tools)
uv sync --dev
```

### Option 2: Docker

```bash
# Build and start all services
make up

# Or using docker-compose directly
docker-compose up -d
```

## Quick Start

### Server Mode

Run the simulator as a FastAPI server:

```bash
# Default server on port 8082
uv run start-simulator --mode server --port 8082

# With custom configuration
uv run start-simulator --mode server --meters 50 --api-url http://localhost:4000
```

### Standalone Mode

Run standalone simulation without API server:

```bash
# Direct submission to API Gateway
uv run start-simulator --mode standalone --meters 20
```

### Docker Deployment

```bash
# Start all services
make up

# View logs
make logs

# Health check
make health
```

## Configuration

### Environment Variables

Copy the example environment file:

```bash
cp .env.example .env
```

Edit `.env` with your settings:

```bash
# Core Settings
SIMULATION_INTERVAL=15        # Seconds between readings
NUM_METERS=55                 # Number of meters
AUTOSTART_SIMULATION=true     # Auto-start on launch

# API Gateway
API_GATEWAY_URL=http://localhost:4000
API_KEY=your-api-key

# WebSocket
WS_ENABLED=true
WS_PORT=8765
```

### Required Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `SIMULATION_INTERVAL` | 15 | Seconds between meter readings |
| `NUM_METERS` | 55 | Number of meters to simulate |
| `API_GATEWAY_URL` | http://localhost:4000 | Target API endpoint |
| `API_KEY` | sim-secret-key | Authentication key |

### Optional Variables

| Variable | Description |
|----------|-------------|
| `KAFKA_BOOTSTRAP_SERVERS` | Kafka brokers for event streaming |
| `INFLUXDB_URL` | InfluxDB for time-series storage |
| `DATABASE_URL` | PostgreSQL for persistence |
| `WS_ENABLED` | Enable WebSocket streaming |

## Verification

### Check Health

```bash
curl http://localhost:8082/health
```

Expected response:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

### View Status

```bash
curl http://localhost:8082/api/status
```

### Connect WebSocket

```javascript
const ws = new WebSocket('ws://localhost:8082/ws');
ws.onmessage = (event) => {
  console.log('Reading:', JSON.parse(event.data));
};
```

## Next Steps

- [Configuration Guide](configuration.md) - Detailed configuration options
- [Running Simulations](running-simulations.md) - Advanced simulation features
- [API Reference](../api/overview.md) - Complete API documentation
- [Architecture Overview](../architecture/overview.md) - System architecture details

## Troubleshooting

### Common Issues

**Port Already in Use:**
```bash
# Change the port
uv run start-simulator --mode server --port 8083
```

**Database Connection Failed:**
The simulator continues without database if PostgreSQL is unavailable.

**UI Not Loading:**
```bash
cd ui
bun install
bun run build
```

For more help, see [Troubleshooting Guide](reference/troubleshooting.md).
