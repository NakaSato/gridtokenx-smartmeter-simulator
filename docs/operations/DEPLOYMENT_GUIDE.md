# Deployment & Operations Guide

This guide covers the deployment, configuration, and operation of the **GridTokenX Smart Meter Simulator** in both development and production environments.

## Quick Start (Development)

### 1. Start Infrastructure
Start the required databases (PostgreSQL, Redis, InfluxDB) using Docker Compose:
```bash
docker compose up -d
```

### 2. Start Simulator
Run the simulator using `uv` (recommended):
```bash
# Server mode (REST API + gRPC)
uv run uvicorn smart_meter_simulator.app:app --host 0.0.0.0 --port 8082

# Standalone mode (Direct telemetry output)
uv run start-simulator --mode standalone --meters 20
```

### 3. Verify
```bash
curl http://localhost:8082/health
```

---

## Production Deployment

### Pre-Deployment Checklist
- [ ] All files compile and tests pass (`uv run pytest`)
- [ ] Copy `.env.production.template` to `.env.production`
- [ ] Set strong passwords for PostgreSQL and InfluxDB
- [ ] Configure `API_KEY` for authentication
- [ ] Ensure Docker (v20.10+) and Docker Compose (v2.0+) are installed

### Deployment Steps
1. **Build Images**:
   ```bash
   docker-compose -f docker-compose.production.yml build
   ```
2. **Start Services**:
   ```bash
   docker-compose -f docker-compose.production.yml up -d
   ```
3. **Verify Status**:
   ```bash
   docker-compose -f docker-compose.production.yml ps
   docker-compose -f docker-compose.production.yml logs simulator
   ```

### Access Points
| Service | URL |
|---------|-----|
| **API Gateway** | http://localhost:8082 |
| **API Docs** | http://localhost:8082/docs |
| **Grafana** | http://localhost:3000 |
| **InfluxDB** | http://localhost:8086 |

---

## Service Management

### Check Status
```bash
curl http://localhost:8082/health
```

### Test AI Endpoints
```bash
# Dual-target forecast
curl "http://localhost:8082/api/v1/forecast/dual-target?current_load_kw=15000"

# Constraint analysis
curl "http://localhost:8082/api/v1/forecast/constraints?current_load_kw=15000"

# Demographics
curl "http://localhost:8082/api/v1/forecast/demographics"
```

### View Logs
```bash
# Docker
docker compose logs -f simulator

# Bare metal
tail -f /tmp/simulator.log
```

### Stop Services
```bash
# Docker
docker compose down

# Bare metal
pkill -f "uvicorn smart_meter_simulator"
```

---

## Monitoring & Alerting

### Metrics to Monitor
- **Request Rate**: Number of API calls per second.
- **Error Rate**: Percentage of 4xx and 5xx responses.
- **Response Time**: p95 latency for forecasting endpoints (Target: < 200ms).
- **Resource Usage**: CPU and Memory consumption of the AI engine.

### Alerting Thresholds
- **Critical**: Error rate > 5% or Service down.
- **Warning**: p95 latency > 500ms or Memory usage > 80%.

---

## Troubleshooting

### Common Issues
1. **Database Connection Refused**: Ensure Docker services are running and the `DATABASE_URL` in `.env` matches the container names.
2. **AI Forecast Timeout**: Check CPU usage. Rust acceleration should be enabled for large meter counts.
3. **InfluxDB Token Invalid**: Verify the `INFLUXDB_TOKEN` matches the one generated during the first run of InfluxDB.

### Rollback Procedure
If a deployment fails:
1. Stop the current deployment: `docker compose down`
2. Revert to the last known stable git tag.
3. Restart services: `docker compose up -d`
