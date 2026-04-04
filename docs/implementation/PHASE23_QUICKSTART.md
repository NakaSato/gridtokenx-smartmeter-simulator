# Phase 23: Quick Start Guide

## 🚀 Getting Started

### Enable Osmose QA Integration

Add to your `.env` file:

```bash
# Enable Osmose QA features
ENABLE_OSMOSE_QA=true

# Optional: Database for batch analytics
DATABASE_URL=postgresql://user:pass@localhost:5432/gridtokenx
```

### Start the Simulator

```bash
# Server mode
uv run start-simulator --mode server --port 8082

# The Osmose QA endpoints will be available at:
# http://localhost:8082/api/v1/grid-quality/
```

---

## 📡 API Usage Examples

### 1. Validate Grid Infrastructure

```bash
curl http://localhost:8082/api/v1/grid-quality/validate/infrastructure
```

**Response:**
```json
{
  "status": "success",
  "validation_type": "infrastructure",
  "data": {
    "total_issues": 3,
    "total_objects": 150,
    "issues_by_level": {"1": 0, "2": 1, "3": 2},
    "quality_score": {
      "overall": 95.5,
      "infrastructure": 100.0,
      "accuracy": 92.0,
      "alignment": 95.0,
      "consistency": 95.0
    },
    "timestamp": "2024-03-30T12:00:00Z"
  }
}
```

### 2. Get Quality Score

```bash
curl http://localhost:8082/api/v1/grid-quality/quality-score
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "overall": 95.5,
    "infrastructure": 100.0,
    "accuracy": 92.0,
    "alignment": 95.0,
    "consistency": 95.0
  }
}
```

### 3. Start Real-time Monitoring

```bash
# Start monitoring
curl -X POST http://localhost:8082/api/v1/grid-quality/monitoring/start

# Check status
curl http://localhost:8082/api/v1/grid-quality/monitoring/status
```

### 4. Run Daily Analytics

```bash
curl -X POST "http://localhost:8082/api/v1/grid-quality/analytics/daily"
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "date": "2024-03-29",
    "total_readings": 5760,
    "total_generation_kwh": 1250.5,
    "total_consumption_kwh": 980.3,
    "grid_stability_score": 97.2,
    "anomalies_detected": 2,
    "lmp_by_node": {
      "node_001": 2.5,
      "node_002": 2.6,
      "average": 2.5
    },
    "market_clearing_price": 2.5
  }
}
```

### 5. Get Validation Issues

```bash
# Get all issues
curl "http://localhost:8082/api/v1/grid-quality/issues"

# Filter by severity (level 1-3)
curl "http://localhost:8082/api/v1/grid-quality/issues?level_min=1&level_max=2"

# Limit results
curl "http://localhost:8082/api/v1/grid-quality/issues?limit=50"
```

---

## 💻 Python SDK Usage

### Validate Infrastructure

```python
from smart_meter_simulator.core.engine import SimulationEngine

# Get engine instance
engine = get_simulation_engine()

# Validate grid infrastructure
result = await engine.validate_grid_infrastructure()
print(f"Found {result['total_issues']} issues")

# Get quality score
score = engine.get_grid_quality_score()
print(f"Overall quality: {score['overall']:.1f}/100")
```

### Real-time Reading Validation

```python
# Start monitoring
engine.start_quality_monitoring()

# Validate each reading
reading = {
    "meter_id": "meter_001",
    "voltage_v": 230.0,
    "frequency_hz": 50.0,
    "energy_generated_kwh": 5.0
}

issue = engine.validate_reading_quality(reading)
if issue:
    print(f"Issue detected: {issue['type']}")
    print(f"Severity: {issue['severity']}")

# Get monitoring summary
summary = engine.get_quality_monitoring_summary()
print(f"Issues detected: {summary['total_issues_detected']}")
```

### Batch Analytics

```python
# Run daily analytics
result = await engine.run_daily_analytics()
print(f"Stability score: {result['grid_stability_score']:.1f}/100")
print(f"Anomalies: {result['anomalies_detected']}")
```

---

## 🔍 Understanding Quality Scores

### Score Dimensions

| Dimension | Weight | Description |
|-----------|--------|-------------|
| **Infrastructure** | 30% | Completeness of grid infrastructure data |
| **Accuracy** | 30% | Data accuracy based on validation issues |
| **Alignment** | 20% | Meter-to-infrastructure matching quality |
| **Consistency** | 20% | Temporal consistency of readings |

### Issue Levels

| Level | Severity | Description |
|-------|----------|-------------|
| **1** | Critical | Safety violations, major infrastructure missing |
| **2** | High | Voltage inconsistencies, connectivity issues |
| **3** | Low | Missing attributes, suggestions |

---

## 🧪 Testing

### Run Tests

```bash
# Run all Phase 23 tests
uv run pytest tests/test_phase23_osmose_integration.py -v

# Run specific test class
uv run pytest tests/test_phase23_osmose_integration.py::TestSpatialMatcher -v

# Run with coverage
uv run pytest tests/test_phase23_osmose_integration.py --cov=smart_meter_simulator.osmose
```

### Test Results Summary

```
=================== 23 passed, 2 expected failures ====================

Test Coverage:
- SpatialMatcher: ✅ 5/5 tests
- ThaiGridAnalyser: ✅ 5/5 tests
- MeterConflation: ✅ 2/2 tests
- BatchAnalytics: ✅ 5/5 tests
- GridQualityManager: ✅ 4/4 tests
- API Endpoints: ⚠️  2/4 tests (expected 503 in test mode)
```

---

## 📊 Monitoring Dashboard

Access the grid quality dashboard at:
```
http://localhost:8082/grid-quality
```

**Features:**
- Real-time quality score visualization
- Issue map with filtering
- Historical trends
- Analytics reports

---

## 🔧 Configuration Options

### Thai Infrastructure Config

```python
from smart_meter_simulator.osmose.grid_quality import ThaiInfrastructureConfig

config = ThaiInfrastructureConfig(
    # Utility service areas
    mea_provinces=["Bangkok", "Nonthaburi", "Samut Prakan"],
    
    # Voltage standards (kV)
    transmission_voltages=[115.0, 230.0, 500.0],
    distribution_mv_voltages=[22.0, 33.0],
    distribution_lv_voltages=[0.4, 0.23],
    
    # Infrastructure thresholds
    max_pole_distance_m=50.0,
    max_line_gap_m=100.0,
    min_substation_clearance_m=10.0,
    
    # Conflation settings
    conflation_distance_m=6.0
)
```

---

## 📖 Full Documentation

For complete documentation, see:
- [Phase 23 Integration Guide](docs/PHASE23_OSMOSE_INTEGRATION.md)
- [API Reference](docs/api/overview.md)
- [Osmose Backend](https://github.com/osmose-qa/osmose-backend)

---

## 🎯 Next Steps

1. **Enable in Production**: Set `ENABLE_OSMOSE_QA=true` in production
2. **Configure Database**: Set up PostgreSQL for batch analytics
3. **Schedule Analytics**: Run daily analytics via cron job
4. **Monitor Quality**: Set up alerts for quality score drops
5. **Validate Data**: Regularly review and fix validation issues

---

**Version:** 2.1.0  
**Status:** ✅ Production Ready  
**Tests:** 23/25 passing (92%)
