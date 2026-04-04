# Docker Deployment Guide

This guide covers Docker-based deployment of the Smart Meter Simulator.

## Prerequisites

- **Docker** 20.10+
- **Docker Compose** 2.0+
- **Make** (optional, for convenience commands)

## Quick Start

### Using Make (Recommended)

```bash
# Build and start all services
make up

# View logs
make logs

# Stop all services
make down

# Health check
make health
```

### Using Docker Compose

```bash
# Build images
docker-compose build

# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## Make Commands

| Command | Description |
|---------|-------------|
| `make up` | Start all services (detached) |
| `make down` | Stop all services |
| `make restart` | Restart all services |
| `make logs` | View logs (follow mode) |
| `make ps` | Show running containers |
| `make clean` | Remove containers and volumes |
| `make build` | Build all Docker images |
| `make ui-build` | Build UI only |
| `make test` | Run tests |
| `make lint` | Run linter |
| `make shell` | Shell access to simulator |
| `make health` | Health check |
| `make metrics` | View Prometheus metrics |

## Services

### Core Services

| Service | Port | Description |
|---------|------|-------------|
| `simulator` | 8082 | FastAPI simulator server |
| `ui` | 3000 | React frontend |
| `influxdb` | 8086 | Time-series database |
| `kafka` | 9092 | Event streaming |
| `zookeeper` | 2181 | Kafka coordination |
| `postgres` | 5432 | PostgreSQL database |

### Optional Services

| Service | Port | Description |
|---------|------|-------------|
| `redis` | 6379 | Caching and pub/sub |
| `prometheus` | 9090 | Metrics collection |
| `grafana` | 3001 | Metrics visualization |

## Configuration

### Environment Variables

Create `.env` file (copy from `.env.example`):

```bash
cp .env.example .env
```

Edit `.env` with your settings:

```bash
# Core Settings
SIMULATION_INTERVAL=15
NUM_METERS=55
AUTOSTART_SIMULATION=true

# API Gateway
API_GATEWAY_URL=http://localhost:4000
API_KEY=your-api-key

# InfluxDB
INFLUXDB_URL=http://influxdb:8086
INFLUXDB_TOKEN=your-influxdb-token
INFLUXDB_ORG=gridtoken
INFLUXDB_BUCKET=energy_readings

# Kafka
KAFKA_BOOTSTRAP_SERVERS=kafka:9092
KAFKA_TOPIC=meter_readings

# Database
DATABASE_URL=postgresql://gridtokenx_user:gridtokenx_password@postgres:5432/gridtokenx
```

### Docker Compose Override

Create `docker-compose.override.yml` for customizations:

```yaml
version: '3.8'

services:
  simulator:
    environment:
      - NUM_METERS=100
      - LOG_LEVEL=DEBUG
    ports:
      - "8082:8082"
  
  ui:
    environment:
      - VITE_API_URL=http://localhost:8082
```

## Data Persistence

### Volume Management

```bash
# Backup data volumes
make backup

# Restore from backup
make restore BACKUP_FILE=./backup/influxdb-backup-20240101-120000.tar.gz
```

### Volume Locations

| Volume | Data |
|--------|------|
| `influxdb-data` | InfluxDB time-series data |
| `postgres-data` | PostgreSQL database |
| `kafka-data` | Kafka message logs |

## Development Mode

```bash
# Start development environment
make dev

# Or with docker-compose
docker-compose -f docker-compose.dev.yml up -d
```

**Features:**
- Hot reload enabled
- Debug logging
- Additional development tools

## Production Mode

```bash
# Start production environment
make prod

# Or with docker-compose
docker-compose up -d
```

**Features:**
- Optimized images
- Resource limits
- Health checks enabled

## Scaling

### Scale Simulator

```bash
# Scale to 3 instances
make scale COUNT=3

# Or using docker-compose
docker-compose up -d --scale simulator=3
```

### Resource Limits

Edit `docker-compose.yml`:

```yaml
services:
  simulator:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 2G
        reservations:
          cpus: '0.5'
          memory: 512M
```

## Monitoring

### Prometheus Metrics

```bash
# View metrics
curl http://localhost:9090/metrics

# Or using make
make metrics
```

### Health Checks

```bash
# Check all services
make health

# Individual health checks
curl http://localhost:8082/health  # Simulator
curl http://localhost:8086/health  # InfluxDB
```

### Logs

```bash
# All services
make logs

# Specific service
docker-compose logs simulator

# Follow logs
docker-compose logs -f simulator

# Last 100 lines
docker-compose logs --tail=100 simulator
```

## Troubleshooting

### Container Won't Start

```bash
# Check logs
docker-compose logs simulator

# Inspect container
docker-compose exec simulator bash

# Check resource usage
docker stats
```

### Port Conflicts

```bash
# Check port usage
lsof -i :8082

# Change port in docker-compose.yml
ports:
  - "8083:8082"  # Use 8083 externally
```

### Database Connection Issues

```bash
# Check database status
docker-compose ps postgres

# Reset database
make reset-db

# View database logs
docker-compose logs postgres
```

### Clean Restart

```bash
# Stop and remove everything
make clean

# Rebuild from scratch
docker-compose build --no-cache

# Start fresh
docker-compose up -d
```

## CI/CD Integration

### Build Image

```bash
docker build -t gridtokenx/smartmeter-simulator:latest .
```

### Run Tests

```bash
docker-compose run simulator pytest
```

### Deploy

```bash
# Tag image
docker tag gridtokenx/smartmeter-simulator:latest registry.example.com/simulator:v1.0

# Push to registry
docker push registry.example.com/simulator:v1.0
```

## Security Considerations

### Non-root User

The Docker image runs as non-root user `appuser` (UID 1000).

### Secrets Management

Use Docker secrets or environment files:

```bash
# Create secrets file
echo "MY_SECRET_KEY" > secrets/api_key

# Mount in docker-compose.yml
secrets:
  - api_key

secrets:
  api_key:
    file: ./secrets/api_key
```

### Network Isolation

```yaml
# Create internal network
networks:
  internal:
    driver: bridge

services:
  simulator:
    networks:
      - internal
      - public  # Only if external access needed
```

## Related Documents

- [Getting Started](getting-started.md)
- [Configuration Guide](configuration.md)
- [Running Simulations](running-simulations.md)
