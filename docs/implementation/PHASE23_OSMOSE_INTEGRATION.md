# Phase 23: Osmose QA Integration

## Overview

Phase 23 integrates the **Osmose Quality Assurance** system into the Smart Meter Simulator, providing comprehensive grid infrastructure validation, spatial conflation, and batch analytics capabilities.

Based on: [Osmose Backend](https://github.com/osmose-qa/osmose-backend)

---

## 🎯 Implementation Summary

### Completed Features

| Feature | Status | Location |
|---------|--------|----------|
| **Thai Grid Infrastructure Analyser** | ✅ Complete | `osmose/analysers/thai_grid_analyser.py` |
| **Spatial Conflation Module** | ✅ Complete | `osmose/utils/spatial.py` |
| **Batch Analytics Pipeline** | ✅ Complete | `osmose/core/batch_analytics.py` |
| **Grid Quality Manager** | ✅ Complete | `osmose/grid_quality.py` |
| **API Endpoints** | ✅ Complete | `routers/grid_quality_router.py` |
| **Test Suite** | ✅ Complete | `tests/test_phase23_osmose_integration.py` |

---

## 📁 New Files Created

### Core Modules

```
src/smart_meter_simulator/osmose/
├── analysers/
│   └── thai_grid_analyser.py        # Thai infrastructure validation
├── utils/
│   └── spatial.py                   # Spatial matching & conflation
├── core/
│   └── batch_analytics.py           # Batch processing pipeline
├── grid_quality.py                  # Quality management
└── __init__.py                      # Updated exports (v2.1.0)
```

### Integration

```
src/smart_meter_simulator/
├── core/
│   └── engine.py                    # Updated with Osmose methods
├── routers/
│   └── grid_quality_router.py       # REST API endpoints
└── app.py                           # Updated with new router
```

### Tests

```
tests/
└── test_phase23_osmose_integration.py  # Comprehensive test suite
```

---

## 🔧 Key Components

### 1. Thai Grid Infrastructure Analyser

**Purpose:** Validate grid infrastructure against Thai standards

**Validates:**
- Power pole placement and attributes
- Power line connectivity and voltage consistency
- Substation locations and clearances
- Transformer placements
- Utility service area boundaries (MEA vs PEA)

**Thai Voltage Standards:**
- Transmission: 115kV, 230kV, 500kV (EGAT)
- Distribution MV: 22kV, 33kV (MEA/PEA)
- Distribution LV: 400V, 230V

**Usage:**
```python
from smart_meter_simulator.osmose.analysers.thai_grid_analyser import (
    AnalyserThaiGridInfrastructure,
    ThaiInfrastructureConfig
)

config = ThaiInfrastructureConfig(
    conflation_distance_m=6.0,
    max_pole_distance_m=50.0
)

analyser = AnalyserThaiGridInfrastructure(config)
result = analyser.run(osm_data)

print(f"Found {result.total_issues} issues")
```

---

### 2. Spatial Conflation Module

**Purpose:** Match smart meters to power infrastructure using spatial analysis

**Features:**
- Haversine distance calculation
- Tag similarity scoring
- Confidence-based matching
- Bounding box filtering

**Usage:**
```python
from smart_meter_simulator.osmose.utils.spatial import (
    SpatialMatcher,
    ConflationConfig
)

matcher = SpatialMatcher()

# Match meters to poles
meters = [
    {"id": "m1", "lat": 13.7563, "lon": 100.5018, "tags": {}},
]

poles = [
    {"id": "p1", "lat": 13.7565, "lon": 100.5020, "tags": {}},
]

config = ConflationConfig(
    max_distance_m=10.0,
    confidence_threshold=0.7
)

matches = matcher.match_meters_to_poles(meters, poles, config)
```

**Distance Calculation:**
```python
distance = matcher.haversine_distance(lat1, lon1, lat2, lon2)
# Returns distance in meters
```

---

### 3. Batch Analytics Pipeline

**Purpose:** Offline analytics for historical grid data

**Analytics Types:**
- **Daily:** Aggregate metrics, LMP, anomalies, stability
- **Weekly:** Aggregated daily results with trends
- **Monthly:** Comprehensive reports with breakdown

**Metrics Calculated:**
- Total generation/consumption
- Average voltage/frequency
- Peak demand/generation
- Locational Marginal Prices (LMP)
- Grid stability score (0-100)
- Anomaly detection count

**Usage:**
```python
from smart_meter_simulator.osmose.core.batch_analytics import (
    BatchAnalyticsPipeline
)

pipeline = BatchAnalyticsPipeline(db_url="postgresql://...")

# Run daily analytics
result = await pipeline.run_daily_analytics(target_date=date.today())

print(f"Readings: {result.total_readings}")
print(f"Stability: {result.grid_stability_score:.1f}/100")
print(f"Anomalies: {result.anomalies_detected}")
```

---

### 4. Grid Quality Manager

**Purpose:** Central management for grid quality validation

**Features:**
- Infrastructure validation
- Meter alignment validation
- Quality scoring (0-100)
- Real-time monitoring
- Batch analytics orchestration

**Quality Score Dimensions:**
- Infrastructure completeness (30%)
- Data accuracy (30%)
- Meter alignment (20%)
- Temporal consistency (20%)

**Usage:**
```python
from smart_meter_simulator.osmose.grid_quality import (
    GridQualityManager,
    create_quality_manager
)

manager = create_quality_manager(db_url="postgresql://...")

# Validate infrastructure
result = await manager.validate_infrastructure()

# Get quality score
score = manager.get_quality_score()
print(f"Overall: {score['overall']:.1f}/100")

# Validate meter alignment
meter_data = [...]  # List of meter locations
result = await manager.validate_meter_alignment(meter_data)
```

---

### 5. Real-time Quality Monitoring

**Purpose:** Monitor meter readings in real-time for quality issues

**Monitors:**
- Voltage out of range (<207V or >253V)
- Frequency deviation (<49.5Hz or >50.5Hz)
- Negative energy values
- Communication failures

**Usage:**
```python
from smart_meter_simulator.osmose.grid_quality import GridQualityMonitor

monitor = GridQualityMonitor(manager)
monitor.start_monitoring()

# Validate each reading
reading = {...}
issue = monitor.validate_reading(reading)

if issue:
    print(f"Issue detected: {issue['type']}")
    print(f"Severity: {issue['severity']}")

# Get summary
summary = monitor.get_monitoring_summary()
```

---

## 🌐 API Endpoints

### Infrastructure Validation

```bash
# Validate grid infrastructure
curl http://localhost:8082/api/v1/grid-quality/validate/infrastructure

# Validate meter alignment
curl http://localhost:8082/api/v1/grid-quality/validate/meter-alignment
```

### Quality Scoring

```bash
# Get quality score
curl http://localhost:8082/api/v1/grid-quality/quality-score

# Get quality summary
curl http://localhost:8082/api/v1/grid-quality/quality-summary
```

### Batch Analytics

```bash
# Run daily analytics
curl -X POST "http://localhost:8082/api/v1/grid-quality/analytics/daily"

# Get historical analytics
curl http://localhost:8082/api/v1/grid-quality/analytics/daily/2024-03-30
```

### Real-time Monitoring

```bash
# Start monitoring
curl -X POST http://localhost:8082/api/v1/grid-quality/monitoring/start

# Stop monitoring
curl -X POST http://localhost:8082/api/v1/grid-quality/monitoring/stop

# Get monitoring status
curl http://localhost:8082/api/v1/grid-quality/monitoring/status
```

### Issues & Configuration

```bash
# Get issues with filtering
curl "http://localhost:8082/api/v1/grid-quality/issues?level_min=1&level_max=2&limit=50"

# Get configuration
curl http://localhost:8082/api/v1/grid-quality/config
```

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

### Test Coverage

| Component | Tests | Coverage |
|-----------|-------|----------|
| SpatialMatcher | 6 | ✅ Complete |
| ThaiGridAnalyser | 5 | ✅ Complete |
| MeterConflation | 2 | ✅ Complete |
| BatchAnalytics | 6 | ✅ Complete |
| GridQualityManager | 4 | ✅ Complete |
| API Endpoints | 2 | ✅ Complete |

---

## ⚙️ Configuration

### Enable Osmose QA

Add to `.env`:

```bash
# Enable Osmose QA integration
ENABLE_OSMOSE_QA=true

# Database for batch analytics (optional)
DATABASE_URL=postgresql://user:pass@localhost:5432/gridtokenx

# Conflation settings
OSMOSE_CONFLATION_DISTANCE_M=6.0
OSMOSE_MAX_POLE_DISTANCE_M=50.0
```

### Programmatic Configuration

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

## 📊 Integration with Simulation Engine

### Access from Engine

```python
from smart_meter_simulator.core.engine import SimulationEngine

engine = SimulationEngine(...)

# Validate infrastructure
result = await engine.validate_grid_infrastructure()

# Get quality score
score = engine.get_grid_quality_score()

# Run daily analytics
analytics = await engine.run_daily_analytics()

# Start monitoring
engine.start_quality_monitoring()

# Validate reading in real-time
issue = engine.validate_reading_quality(reading)
```

### Engine Configuration

The Osmose integration is automatically enabled if:
1. Osmose module is available
2. `enable_osmose_qa` config is `True`

```python
# In engine.py initialization
self.osmose_enabled = OSMOSE_AVAILABLE and config.get("enable_osmose_qa", False)
```

---

## 🔍 Issue Classification

### Issue Levels

| Level | Severity | Description |
|-------|----------|-------------|
| 1 | Critical | Safety violations, major infrastructure missing |
| 2 | High | Voltage inconsistencies, connectivity issues |
| 3 | Low | Missing attributes, suggestions |

### Issue Categories

| Category | Description | Examples |
|----------|-------------|----------|
| `merge` | Infrastructure not integrated | Missing poles, lines |
| `topology` | Grid topology issues | Voltage mismatch, gaps |
| `safety` | Safety violations | Clearance violations |
| `alignment` | Meter-infrastructure misalignment | Meter not near pole |
| `utility` | Utility boundary issues | MEA/PEA mismatch |

---

## 📈 Performance Considerations

### Spatial Matching

- **Haversine Distance:** O(1) per pair
- **Batch Matching:** O(n×m) for n meters, m poles
- **Optimization:** Use spatial indexing (R-tree) for large datasets

### Batch Analytics

- **Daily Run:** ~1-5 seconds for 1000 meters
- **Weekly Run:** ~10-30 seconds (7 daily runs + aggregation)
- **Monthly Run:** ~1-2 minutes (4 weekly runs + trends)

### Recommendations

1. **Use Database:** Configure PostgreSQL for persistent analytics
2. **Schedule Off-Peak:** Run batch analytics during low-load periods
3. **Index Spatial Data:** Add PostGIS indexes for faster queries
4. **Cache Results:** Cache validation results for repeated queries

---

## 🚀 Future Enhancements

### Planned Features

- [ ] **OSM Data Fetching:** Integrate Overpass API for live OSM data
- [ ] **MapCSS Validation:** Add MapCSS rule-based validation
- [ ] **Vector Tiles:** Generate vector tiles for visualization
- [ ] **Historical Trends:** Long-term trend analysis and forecasting
- [ ] **Machine Learning:** Anomaly detection using ML models
- [ ] **Thai-specific Analysers:** More Thai infrastructure patterns

### Integration Opportunities

- [ ] **Osmose Frontend:** Direct integration with Osmose frontend
- [ ] **JOSM Validator:** Export to JOSM validator format
- [ ] **Tasking Manager:** Create validation tasks for mappers
- [ ] **EGAT/MEA/PEA Data:** Import official infrastructure data

---

## 📚 References

### Osmose Backend

- **Repository:** https://github.com/osmose-qa/osmose-backend
- **License:** GPL v3
- **Documentation:** https://osmose-qa.readthedocs.io/

### Thai Grid Standards

- **EGAT:** https://www.egat.co.th/
- **MEA:** https://www.mea.or.th/
- **PEA:** https://www.pea.co.th/

### Related Phases

- **Phase 3:** Geo-SAM Integration (solar mapping)
- **Phase 5:** Co-Simulation (Mosaik, CIM)
- **Phase 21:** Locational Marginal Pricing
- **Phase 22:** Advanced Grid Intelligence
- **Phase 23:** OpenStreetMap Integration ✅ Complete
- **Phase 24:** Thai Grid Integration & Spatial Analytics ✅ Complete

---

## 🤝 Contributing

### Adding New Analysers

1. Create analyser in `osmose/analysers/`
2. Inherit from `Analyser` base class
3. Implement `run()` method
4. Define issue classes
5. Add tests
6. Update `__init__.py` exports

### Example Analyser

```python
from smart_meter_simulator.osmose.core.analyser import Analyser
from smart_meter_simulator.osmose.core.issue import OsmoseIssue

class AnalyserCustom(Analyser):
    def __init__(self):
        super().__init__("custom_analyser", "th")
    
    def run(self, osm_data):
        issues = []
        # Validation logic here
        return OsmoseValidationResult(
            analyser=self.analyser_id,
            country=self.country,
            timestamp=datetime.utcnow(),
            issues=issues,
            total_objects=len(osm_data)
        )
```

---

## ✅ Checklist

- [x] Thai Grid Infrastructure Analyser
- [x] Spatial Conflation Module
- [x] Batch Analytics Pipeline
- [x] Grid Quality Manager
- [x] Real-time Monitoring
- [x] API Endpoints
- [x] Test Suite
- [x] Documentation
- [x] Engine Integration
- [x] Configuration Support

---

**Phase 23 Status:** ✅ **Complete**

**Version:** 2.1.0  
**Last Updated:** 2024-03-30
