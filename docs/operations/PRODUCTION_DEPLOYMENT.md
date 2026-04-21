# Production Deployment Guide

## Production-Grade Features

### Error Handling
- ✓ Custom exception hierarchy (AIServiceError, ForecastError, ValidationError)
- ✓ HTTP status codes (400 for validation, 500 for server errors)
- ✓ Detailed error logging with stack traces
- ✓ Graceful degradation

### Input Validation
- ✓ Load range validation (0-100,000 kW)
- ✓ Timestamp validation and normalization
- ✓ Query parameter constraints (FastAPI validators)

### Performance
- ✓ LRU caching for forecast results (5-minute TTL)
- ✓ Performance tracking and metrics
- ✓ Execution time logging
- ✓ Configurable timeouts

### Monitoring
- ✓ Metrics endpoint (`/api/v1/forecast/metrics`)
- ✓ Health check endpoint (`/api/v1/forecast/health`)
- ✓ Request/error counters
- ✓ Average response time tracking

### Configuration
- ✓ Environment-based configuration
- ✓ Pydantic validation
- ✓ Configurable cache, timeouts, buffers
- ✓ Log level control

## Environment Variables

```bash
# AI Service Configuration
AI_MODEL_PATH=/path/to/model.pkl
AI_FORECAST_HORIZON=24
AI_CACHE_ENABLED=true
AI_CACHE_TTL=300
AI_LOG_LEVEL=INFO
AI_ENABLE_METRICS=true

# Load Limits
AI_MIN_LOAD_KW=0
AI_MAX_LOAD_KW=100000

# Performance
AI_MAX_CONCURRENT_FORECASTS=10
AI_FORECAST_TIMEOUT_SECONDS=30

# BESS Buffers
AI_BESS_CAPACITY_BUFFER=1.2
AI_BESS_POWER_BUFFER=1.1
```

## Production Checklist

### Pre-Deployment
- [ ] All environment variables configured
- [ ] Model files deployed (if using LightGBM)
- [ ] Database connections tested
- [ ] InfluxDB configured for metrics storage
- [ ] Log aggregation configured (ELK/Loki)

### Deployment
- [ ] Docker images built with production tag
- [ ] Health checks configured in orchestrator
- [ ] Resource limits set (CPU/Memory)
- [ ] Auto-scaling policies configured
- [ ] Load balancer configured

### Post-Deployment
- [ ] Health endpoint returns 200
- [ ] Metrics endpoint accessible
- [ ] Error rates < 1%
- [ ] Response times < 200ms (p95)
- [ ] Logs flowing to aggregator

## Monitoring Endpoints

### Health Check
```bash
curl http://localhost:8082/api/v1/forecast/health
```

**Response**:
```json
{
  "status": "healthy",
  "service": "ai_forecasting",
  "metrics": {
    "total_forecasts": 1234,
    "total_errors": 5,
    "constraint_detections": 456,
    "avg_forecast_time_ms": 87.23,
    "error_rate": 0.0041
  },
  "timestamp": "2026-04-20T05:30:00.000000"
}
```

### Metrics
```bash
curl http://localhost:8082/api/v1/forecast/metrics
```

**Response**:
```json
{
  "total_forecasts": 1234,
  "total_errors": 5,
  "constraint_detections": 456,
  "avg_forecast_time_ms": 87.23,
  "error_rate": 0.0041
}
```

## Error Handling Examples

### Validation Error (400)
```bash
curl "http://localhost:8082/api/v1/forecast/dual-target?current_load_kw=999999"
```

**Response**:
```json
{
  "detail": "Invalid load: 999999.0 kW (must be 0-100000)"
}
```

### Invalid Timestamp (400)
```bash
curl "http://localhost:8082/api/v1/forecast/dual-target?start_time=invalid"
```

**Response**:
```json
{
  "detail": "Invalid timestamp format: Invalid isoformat string: 'invalid'"
}
```

### Server Error (500)
```json
{
  "detail": "Internal server error"
}
```

## Performance Tuning

### Cache Configuration
```python
# Increase cache size for high-traffic deployments
AI_CACHE_MAX_SIZE=256
AI_CACHE_TTL=600  # 10 minutes
```

### Concurrency Limits
```python
# Limit concurrent forecasts to prevent overload
AI_MAX_CONCURRENT_FORECASTS=20
```

### Timeout Configuration
```python
# Adjust timeout for slower systems
AI_FORECAST_TIMEOUT_SECONDS=60
```

## Logging

### Log Levels
- **DEBUG**: Detailed execution traces
- **INFO**: Normal operations, forecast completions
- **WARNING**: Validation errors, constraint detections
- **ERROR**: Forecast failures, exceptions

### Log Format
```
2026-04-20 05:30:00 - ai_service - INFO - Forecast generated: 12/24 constraint hours, avg_load=21267.50kW
2026-04-20 05:30:01 - ai_service - WARNING - Constraints detected: 12 hours, max_deficit=78949.36kW
2026-04-20 05:30:02 - forecast_v1 - ERROR - Forecast error: Failed to generate forecast
```

## Alerting Rules

### Critical Alerts
- Error rate > 5%
- Response time p95 > 500ms
- Service health check fails
- Constraint detection rate > 80%

### Warning Alerts
- Error rate > 1%
- Response time p95 > 200ms
- Cache hit rate < 50%
- Constraint detection rate > 50%

## Scaling Guidelines

### Vertical Scaling
- **CPU**: 2-4 cores recommended
- **Memory**: 2-4 GB recommended
- **Disk**: Minimal (logs only)

### Horizontal Scaling
- Stateless service (scales horizontally)
- Load balancer with round-robin
- Shared cache (Redis) recommended
- 3-5 replicas for high availability

## Backup & Recovery

### Model Backups
```bash
# Backup trained models
cp /data/pea_lgbm_model.pkl /backup/models/pea_lgbm_model_$(date +%Y%m%d).pkl
```

### Configuration Backups
```bash
# Backup environment configuration
env | grep AI_ > /backup/config/ai_config_$(date +%Y%m%d).env
```

### Recovery Procedure
1. Stop affected service
2. Restore model from backup
3. Restore configuration
4. Restart service
5. Verify health check
6. Monitor metrics for 15 minutes

## Security

### API Security
- [ ] Rate limiting configured (100 req/min per IP)
- [ ] API key authentication enabled
- [ ] HTTPS/TLS configured
- [ ] CORS properly configured

### Data Security
- [ ] No PII in logs
- [ ] Sensitive data encrypted at rest
- [ ] Secure model storage
- [ ] Access controls on metrics endpoints

## Maintenance

### Daily
- Check error rates
- Review constraint detection trends
- Monitor response times

### Weekly
- Review logs for anomalies
- Check cache hit rates
- Validate forecast accuracy (MAPE)

### Monthly
- Retrain models with new data
- Review and update configuration
- Performance optimization review
- Security audit

## Troubleshooting

### High Error Rate
1. Check logs for error patterns
2. Verify input data quality
3. Check model file integrity
4. Review recent configuration changes

### Slow Response Times
1. Check cache hit rate
2. Review concurrent request count
3. Check database connection pool
4. Profile forecast execution

### High Constraint Detection
1. Review load patterns
2. Check demographic calculations
3. Verify thermal derating logic
4. Validate upstream load data

## Support Contacts

- **DevOps**: devops@gridtokenx.com
- **AI Team**: ai@gridtokenx.com
- **On-Call**: +66-xxx-xxx-xxxx
