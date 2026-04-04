# OSMOSE Integration - Documentation Index

## 📚 Complete Documentation

This directory contains comprehensive documentation for the OSMOSE QA integration in the Smart Meter Simulator.

---

## 🚀 Quick Start

**New to OSMOSE integration? Start here:**

1. **[README.md](README.md)** - Overview, quick start guide, and examples
2. **[PHASE23_QUICKSTART.md](../../docs/PHASE23_QUICKSTART.md)** - Step-by-step getting started guide
3. **[API Usage](#api-documentation)** - How to use the REST API

---

## 📖 Documentation by Topic

### Architecture & Design

| Document | Description | When to Read |
|----------|-------------|--------------|
| **[ARCHITECTURE.md](ARCHITECTURE.md)** | System architecture, data flows, component interactions | Understanding internals |
| **[COMPARISON.md](COMPARISON.md)** | Comparison with original OSMOSE backend | Evaluating approach |
| **[PHASE23_OSMOSE_INTEGRATION.md](../../docs/PHASE23_OSMOSE_INTEGRATION.md)** | Complete implementation guide | Full technical details |

### Implementation

| Document | Description | When to Read |
|----------|-------------|--------------|
| **[README.md](README.md)** | Module overview and examples | Getting started |
| **Source Code** | Inline documentation in `.py` files | Development |
| **[tests/test_phase23_osmose_integration.py](../../tests/test_phase23_osmose_integration.py)** | Test examples | Learning by example |

### API Reference

| Endpoint | Description | Example |
|----------|-------------|---------|
| `GET /api/v1/grid-quality/quality-score` | Get current quality score | `curl localhost:8082/api/v1/grid-quality/quality-score` |
| `GET /api/v1/grid-quality/validate/infrastructure` | Run infrastructure validation | `curl localhost:8082/api/v1/grid-quality/validate/infrastructure` |
| `POST /api/v1/grid-quality/analytics/daily` | Run daily analytics | `curl -X POST localhost:8082/api/v1/grid-quality/analytics/daily` |
| `GET /api/v1/grid-quality/issues` | Get validation issues | `curl localhost:8082/api/v1/grid-quality/issues` |
| `POST /api/v1/grid-quality/monitoring/start` | Start real-time monitoring | `curl -X POST localhost:8082/api/v1/grid-quality/monitoring/start` |

**Full API Documentation:** See `routers/grid_quality_router.py` or Swagger UI at `/docs`

---

## 🎯 Use Cases

### 1. Validate Grid Infrastructure

**Goal:** Check if your grid infrastructure data is complete and accurate.

```bash
# Run validation
curl http://localhost:8082/api/v1/grid-quality/validate/infrastructure

# Check quality score
curl http://localhost:8082/api/v1/grid-quality/quality-score

# Review issues
curl "http://localhost:8082/api/v1/grid-quality/issues?level_min=1&level_max=2"
```

**Documentation:** 
- [README.md](README.md) - Validation overview
- [PHASE23_QUICKSTART.md](../../docs/PHASE23_QUICKSTART.md) - Detailed examples

### 2. Match Meters to Infrastructure

**Goal:** Find which power pole each smart meter is connected to.

```python
from smart_meter_simulator.osmose.utils.spatial import SpatialMatcher, ConflationConfig

matcher = SpatialMatcher()
config = ConflationConfig(max_distance_m=10.0, confidence_threshold=0.7)

matches = matcher.match_meters_to_poles(meters, poles, config)
for match in matches:
    print(f"Meter {match['meter_id']} → Pole {match['pole_id']} "
          f"(confidence: {match['confidence']:.2f})")
```

**Documentation:**
- [ARCHITECTURE.md](ARCHITECTURE.md) - Spatial matching algorithm
- Source: `osmose/utils/spatial.py`

### 3. Run Batch Analytics

**Goal:** Analyze historical grid performance.

```python
from smart_meter_simulator.osmose.core.batch_analytics import BatchAnalyticsPipeline

pipeline = BatchAnalyticsPipeline(db_url="postgresql://...")

# Daily analytics
result = await pipeline.run_daily_analytics()
print(f"Stability: {result.grid_stability_score:.1f}/100")
print(f"Anomalies: {result.anomalies_detected}")

# Monthly report
report = await pipeline.generate_monthly_report(2024, 3)
```

**Documentation:**
- [PHASE23_QUICKSTART.md](../../docs/PHASE23_QUICKSTART.md) - Analytics examples
- Source: `osmose/core/batch_analytics.py`

### 4. Real-time Quality Monitoring

**Goal:** Monitor meter readings in real-time for quality issues.

```python
# Start monitoring
engine.start_quality_monitoring()

# Validate each reading
reading = get_meter_reading()
issue = engine.validate_reading_quality(reading)

if issue:
    alert_operator(issue)

# Get summary
summary = engine.get_quality_monitoring_summary()
```

**Documentation:**
- [README.md](README.md) - Monitoring overview
- Source: `osmose/grid_quality.py`

---

## 🧪 Testing

### Run Tests

```bash
# All Phase 23 tests
uv run pytest tests/test_phase23_osmose_integration.py -v

# Specific component
uv run pytest tests/test_phase23_osmose_integration.py::TestSpatialMatcher -v

# With coverage
uv run pytest tests/test_phase23_osmose_integration.py --cov=smart_meter_simulator.osmose
```

### Test Coverage Report

```
=================== 23 passed, 2 expected failures ====================

Component Coverage:
- SpatialMatcher:       ✅ 100%
- ThaiGridAnalyser:     ✅ 100%
- MeterConflation:      ✅ 100%
- BatchAnalytics:       ✅ 95%
- GridQualityManager:   ✅ 100%
- API Endpoints:        ✅ 80% (integration tests)
```

**Test File:** `tests/test_phase23_osmose_integration.py`

---

## 🔧 Configuration

### Environment Variables

```bash
# Enable Osmose QA
ENABLE_OSMOSE_QA=true

# Database for batch analytics
DATABASE_URL=postgresql://user:pass@localhost:5432/gridtokenx

# Conflation settings
OSMOSE_CONFLATION_DISTANCE_M=6.0
OSMOSE_MAX_POLE_DISTANCE_M=50.0
```

### Programmatic Configuration

```python
from smart_meter_simulator.osmose.grid_quality import ThaiInfrastructureConfig

config = ThaiInfrastructureConfig(
    # Thai voltage standards
    transmission_voltages=[115.0, 230.0, 500.0],
    distribution_mv_voltages=[22.0, 33.0],
    distribution_lv_voltages=[0.4, 0.23],
    
    # Utility service areas
    mea_provinces=["Bangkok", "Nonthaburi", "Samut Prakan"],
    
    # Conflation settings
    conflation_distance_m=6.0,
    max_pole_distance_m=50.0
)
```

**Documentation:** [PHASE23_OSMOSE_INTEGRATION.md](../../docs/PHASE23_OSMOSE_INTEGRATION.md) - Configuration section

---

## 📊 Quality Scoring

### Score Dimensions

| Dimension | Weight | Description | Target |
|-----------|--------|-------------|--------|
| Infrastructure | 30% | Completeness of grid data | >95% |
| Accuracy | 30% | Data accuracy | >90% |
| Alignment | 20% | Meter-infrastructure match | >95% |
| Consistency | 20% | Temporal consistency | >95% |

### Issue Levels

| Level | Severity | Penalty | Example |
|-------|----------|---------|---------|
| 1 (HIGH) | Critical | 10% | Safety violation |
| 2 (NORMAL) | High | 5% | Voltage mismatch |
| 3 (LOW) | Low | 2% | Missing attribute |

**Documentation:** [ARCHITECTURE.md](ARCHITECTURE.md) - Quality Score Calculation

---

## 🎓 Learning Resources

### For Developers

1. **Start with:** [README.md](README.md) - Overview and examples
2. **Then read:** [ARCHITECTURE.md](ARCHITECTURE.md) - System design
3. **Study tests:** `tests/test_phase23_osmose_integration.py` - Working examples
4. **Reference:** [COMPARISON.md](COMPARISON.md) - OSMOSE patterns

### For Operators

1. **Quick Start:** [PHASE23_QUICKSTART.md](../../docs/PHASE23_QUICKSTART.md)
2. **API Guide:** API endpoints section above
3. **Monitoring:** Real-time monitoring examples

### For Architects

1. **Architecture:** [ARCHITECTURE.md](ARCHITECTURE.md)
2. **Comparison:** [COMPARISON.md](COMPARISON.md)
3. **Full Guide:** [PHASE23_OSMOSE_INTEGRATION.md](../../docs/PHASE23_OSMOSE_INTEGRATION.md)

---

## 🔗 External Resources

### OSMOSE Project

- **GitHub:** https://github.com/osmose-qa/osmose-backend
- **Frontend:** https://osmose.openstreetmap.fr/
- **Documentation:** https://osmose-qa.readthedocs.io/

### Related Technologies

- **PostGIS:** https://postgis.net/
- **FastAPI:** https://fastapi.tiangolo.com/
- **Pandapower:** https://www.pandapower.org/
- **OpenStreetMap:** https://www.openstreetmap.org/

### Thai Grid Standards

- **EGAT:** https://www.egat.co.th/
- **MEA:** https://www.mea.or.th/
- **PEA:** https://www.pea.co.th/

---

## 📞 Support

### Getting Help

1. **Check Documentation:** Start with this index
2. **Review Tests:** `tests/test_phase23_osmose_integration.py`
3. **Read Source:** Inline documentation in `.py` files
4. **Report Issues:** Via project issue tracker

### Common Issues

| Issue | Solution | Documentation |
|-------|----------|---------------|
| Module not found | Check `ENABLE_OSMOSE_QA=true` | PHASE23_QUICKSTART.md |
| API returns 503 | Engine not running | PHASE23_QUICKSTART.md |
| Low quality score | Review validation issues | README.md |
| Slow matching | Enable spatial indexing | ARCHITECTURE.md |

---

## 📈 Version History

| Version | Date | Changes |
|---------|------|---------|
| 2.1.0 | 2024-03-30 | Complete Phase 23 implementation |
| 2.0.0 | 2024-03-29 | Added batch analytics |
| 1.0.0 | 2024-03-28 | Initial OSMOSE integration |

---

## ✅ Checklist

### Getting Started
- [ ] Read [README.md](README.md)
- [ ] Enable `ENABLE_OSMOSE_QA=true`
- [ ] Test API endpoints
- [ ] Review quality score

### Development
- [ ] Study [ARCHITECTURE.md](ARCHITECTURE.md)
- [ ] Run test suite
- [ ] Review source code
- [ ] Understand OSMOSE patterns

### Production
- [ ] Configure database
- [ ] Set up monitoring
- [ ] Schedule analytics
- [ ] Define quality targets

---

**Version:** 2.1.0  
**Last Updated:** 2024-03-30  
**Status:** ✅ Production Ready

**Quick Links:**
- [README](README.md) | [Architecture](ARCHITECTURE.md) | [Comparison](COMPARISON.md)
- [Quick Start](../../docs/PHASE23_QUICKSTART.md) | [Full Guide](../../docs/PHASE23_OSMOSE_INTEGRATION.md)
