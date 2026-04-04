# OSMOSE Backend Integration

This directory contains the complete integration of the **OSMOSE Quality Assurance** system into the Smart Meter Simulator.

## 📁 Directory Structure

```
osmose/
├── README.md                    # This file - overview and quick reference
├── __init__.py                  # Module exports (v2.1.0)
├── analysers/                   # Validation analysers
│   └── thai_grid_analyser.py    # Thai infrastructure validation
├── core/                        # Core OSMOSE components
│   ├── analyser.py              # Base analyser classes (existing)
│   ├── issue.py                 # Issue data models (existing)
│   ├── plugin.py                # Plugin system (existing)
│   └── batch_analytics.py       # Batch processing pipeline (NEW)
├── utils/                       # Utility modules
│   └── spatial.py               # Spatial matching & conflation (NEW)
├── database.py                  # PostgreSQL/PostGIS integration (existing)
├── dataset.py                   # Dataset management (existing)
├── fetcher.py                   # Data fetching (existing)
├── grid_quality.py              # Quality management (NEW)
├── runner.py                    # Analyser orchestration (existing)
└── tile_server.py               # Vector tile server (existing)
```

## 🎯 What is OSMOSE?

**OSMOSE** (OpenStreetMap Sanity Checker) is a quality assurance tool for OpenStreetMap that:
- Detects mapping errors and inconsistencies
- Validates infrastructure data against official sources
- Provides fix suggestions for mappers
- Runs on a scheduled basis (daily/weekly)

**Reference:** https://github.com/osmose-qa/osmose-backend

## 🔧 Our Implementation

### Phase 23: Grid Quality Assurance

We've adapted OSMOSE patterns for smart meter and grid infrastructure validation:

| OSMOSE Feature | Our Adaptation | Status |
|----------------|----------------|--------|
| Infrastructure Analysers | Thai Grid Analyser | ✅ Complete |
| Spatial Conflation | Meter-to-Pole Matching | ✅ Complete |
| Batch Processing | Daily Analytics Pipeline | ✅ Complete |
| Issue Tracking | Quality Scoring System | ✅ Complete |
| MapCSS Validation | (Future) | 📋 Planned |
| Vector Tiles | (Future) | 📋 Planned |

## 📖 Key Concepts

### 1. Analyser Pattern

OSMOSE analysers validate specific aspects of data:

```python
from smart_meter_simulator.osmose.core.analyser import Analyser
from smart_meter_simulator.osmose.core.issue import OsmoseIssue, IssueLevel

class AnalyserThaiGridInfrastructure(Analyser):
    def __init__(self, config):
        super().__init__("thai_grid_infrastructure", "th")
        self.config = config
    
    def run(self, osm_data):
        issues = []
        
        # Validate power poles
        poles = self._extract_power_poles(osm_data)
        for pole in poles:
            if self._is_missing_voltage(pole):
                issues.append(OsmoseIssue(
                    item=8290,
                    id=1071,
                    level=IssueLevel.LOW,
                    title="Power pole missing voltage",
                    tags=["merge", "power", "fix:chair"],
                    osm_type="node",
                    osm_id=pole["id"],
                    lat=pole["lat"],
                    lon=pole["lon"],
                    detail="Power pole on line without voltage tagging",
                    text=f"Power pole {pole['id']} needs voltage attribute"
                ))
        
        return OsmoseValidationResult(
            analyser=self.analyser_id,
            country=self.country,
            timestamp=datetime.utcnow().isoformat(),
            issues=issues,
            total_objects=len(poles),
            total_issues=len(issues),
            issues_by_level={"1": 0, "2": 0, "3": len(issues)},
            issues_by_item={"8290": len(issues)},
            issues_by_tag={"power": len(issues)}
        )
```

### 2. Issue Levels

```python
class IssueLevel(int, Enum):
    HIGH = 1      # Critical errors - break data integrity
    NORMAL = 2    # Common mistakes - reduce data quality
    LOW = 3       # Suggestions - improvements
```

### 3. Spatial Conflation

Matching objects from different sources based on location:

```python
from smart_meter_simulator.osmose.utils.spatial import SpatialMatcher, ConflationConfig

matcher = SpatialMatcher()

# Match meters to poles
config = ConflationConfig(
    max_distance_m=10.0,           # Maximum matching distance
    confidence_threshold=0.7,      # Minimum confidence for matches
    use_tags=True,                 # Consider tags in matching
    tag_weight=0.3,                # Weight for tag similarity
    distance_weight=0.7            # Weight for distance
)

matches = matcher.match_meters_to_poles(meters, poles, config)
```

### 4. Quality Scoring

Multi-dimensional quality assessment:

```python
from smart_meter_simulator.osmose.grid_quality import GridQualityScore

score = GridQualityScore()

# Dimensions (weights in parentheses)
score.infrastructure_score = 95.0    # Infrastructure completeness (30%)
score.accuracy_score = 92.0          # Data accuracy (30%)
score.alignment_score = 98.0         # Meter alignment (20%)
score.consistency_score = 96.0       # Temporal consistency (20%)

overall = score.calculate_overall()  # Weighted average
```

## 🚀 Quick Start

### Enable Osmose QA

```bash
# Add to .env
ENABLE_OSMOSE_QA=true
DATABASE_URL=postgresql://user:pass@localhost:5432/gridtokenx
```

### Use in Code

```python
from smart_meter_simulator.osmose.grid_quality import GridQualityManager

# Create manager
manager = GridQualityManager()

# Validate infrastructure
result = await manager.validate_infrastructure()
print(f"Found {result.total_issues} issues")

# Get quality score
score = manager.get_quality_score()
print(f"Overall: {score['overall']:.1f}/100")
```

### API Endpoints

```bash
# Quality score
curl http://localhost:8082/api/v1/grid-quality/quality-score

# Validate infrastructure
curl http://localhost:8082/api/v1/grid-quality/validate/infrastructure

# Run daily analytics
curl -X POST http://localhost:8082/api/v1/grid-quality/analytics/daily
```

## 📚 Reference Materials

### OSMOSE Backend Patterns

Key patterns we've adopted from OSMOSE:

1. **Analyser Execution Model**
   - Load OSM data → Run analysers → Store results → Upload to frontend
   - See: `osmose/runner.py`

2. **Issue Classification**
   - Hierarchical: item → id → level → tags
   - Structured fix suggestions
   - See: `osmose/core/issue.py`

3. **Conflation Engine**
   - Distance-based matching
   - Tag similarity scoring
   - Confidence calculation
   - See: `osmose/utils/spatial.py`

4. **Batch Processing**
   - Daily/weekly/monthly analytics
   - Incremental updates
   - Result caching
   - See: `osmose/core/batch_analytics.py`

### Thai Grid Specifics

Our implementation adds Thai-specific validation:

- **Voltage Standards:** 115kV, 230kV, 500kV (transmission), 22kV, 33kV (distribution), 400V (LV)
- **Utility Boundaries:** MEA (Bangkok metro), PEA (provincial)
- **Infrastructure Types:** Thai-standard poles, transformers, substations

## 🧪 Testing

```bash
# Run all Osmose tests
uv run pytest tests/test_phase23_osmose_integration.py -v

# Run specific component tests
uv run pytest tests/test_phase23_osmose_integration.py::TestSpatialMatcher -v
uv run pytest tests/test_phase23_osmose_integration.py::TestThaiGridAnalyser -v
uv run pytest tests/test_phase23_osmose_integration.py::TestBatchAnalytics -v
```

## 📊 Test Coverage

```
=================== 23 passed, 2 expected failures ====================

Component Tests:
- SpatialMatcher:       ✅ 5/5 (100%)
- ThaiGridAnalyser:     ✅ 5/5 (100%)
- MeterConflation:      ✅ 2/2 (100%)
- BatchAnalytics:       ✅ 5/5 (100%)
- GridQualityManager:   ✅ 4/4 (100%)
- API Endpoints:        ⚠️  2/4 (50% - expected 503 in test mode)

Overall: 92% pass rate
```

## 🔗 External Resources

- **OSMOSE Backend:** https://github.com/osmose-qa/osmose-backend
- **OSMOSE Frontend:** https://osmose.openstreetmap.fr/
- **OSMOSE Docs:** https://osmose-qa.readthedocs.io/
- **MapCSS:** https://josm.openstreetmap.de/wiki/Help/Styles/MapCSSImplementation

## 📈 Roadmap

### Phase 23 (Current) ✅
- [x] Thai Grid Infrastructure Analyser
- [x] Spatial Conflation Module
- [x] Batch Analytics Pipeline
- [x] Grid Quality Manager
- [x] API Endpoints
- [x] Test Suite

### Future Enhancements 📋
- [ ] MapCSS rule-based validation
- [ ] Vector tile generation
- [ ] Overpass API integration
- [ ] JOSM validator export
- [ ] ML-based anomaly detection
- [ ] Historical trend analysis

## 🤝 Contributing

### Adding New Analysers

1. Create analyser in `osmose/analysers/`
2. Inherit from `Analyser` base class
3. Define issue classes in `_define_issue_classes()`
4. Implement validation logic in `run()`
5. Add tests in `tests/test_phase23_osmose_integration.py`
6. Update `osmose/__init__.py` exports

### Example Analyser

```python
from smart_meter_simulator.osmose.core.analyser import Analyser
from smart_meter_simulator.osmose.core.issue import OsmoseIssue, IssueLevel

class AnalyserExample(Analyser):
    def __init__(self):
        super().__init__("example_analyser", "th")
        self._define_issue_classes()
    
    def _define_issue_classes(self):
        self.class_example = {
            "item": 9000,
            "id": 1,
            "level": IssueLevel.LOW,
            "title": "Example issue",
            "tags": ["example", "test"],
            "fix": "Fix the example issue"
        }
    
    def run(self, osm_data):
        issues = []
        # Validation logic here
        return self._create_result(issues)
```

## 📞 Support

- **Documentation:** `docs/PHASE23_OSMOSE_INTEGRATION.md`
- **Quick Start:** `docs/PHASE23_QUICKSTART.md`
- **API Reference:** `/api/v1/grid-quality/` (when running)
- **Issues:** Report via project issue tracker

---

**Version:** 2.1.0  
**Last Updated:** 2024-03-30  
**Status:** ✅ Production Ready
