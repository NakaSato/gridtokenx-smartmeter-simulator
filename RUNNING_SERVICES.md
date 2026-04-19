# Services Running in Background ✅

## Status

**Simulator**: ✅ Running on http://localhost:8082  
**PID**: 9003  
**Started**: 2026-04-20 05:36:11

## Quick Commands

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
tail -f /tmp/simulator.log
```

### Stop Services
```bash
pkill -f "uvicorn smart_meter_simulator"
```

### Restart Services
```bash
cd backend && nohup uv run uvicorn smart_meter_simulator.app:app --host 0.0.0.0 --port 8082 > /tmp/simulator.log 2>&1 &
```

## Access Points

- **API**: http://localhost:8082
- **Swagger Docs**: http://localhost:8082/docs
- **Health Check**: http://localhost:8082/health
- **Logs**: /tmp/simulator.log

## Available Endpoints

✅ `/api/v1/forecast/dual-target` - 24h dual-target forecast  
✅ `/api/v1/forecast/constraints` - Constraint analysis  
✅ `/api/v1/forecast/demographics` - Population metrics  
✅ `/api/v1/forecast/24h` - Edge forecasting  
✅ `/api/v1/optimize/schedule` - Optimal dispatch  
✅ `/api/v1/optimize/savings` - Cost savings  
✅ `/api/v1/ews/status` - EWS status  
✅ `/api/v1/ews/simulate` - Simulate incident  

## Notes

- Docker daemon not running, using direct uvicorn
- Database connections may be limited without Docker services
- For full stack, start Docker first: `docker compose up -d`
