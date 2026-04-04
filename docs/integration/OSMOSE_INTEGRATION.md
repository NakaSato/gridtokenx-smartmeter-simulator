# Grid Infrastructure Analysis - OSMOSE Integration

**Date:** 2026-04-04
**Status:** ✅ Complete - 4 custom analysers implemented, 22 tests passing

---

## Overview

GridTokenX custom OSMOSE analysers validate electrical infrastructure data for the Thai grid (EGAT/MEA/PEA). They replace the legacy GPL osmose-backend with proprietary, Thailand-specific validation logic.

---

## Analysers

### 1. PowerSubstationValidator

Validates OSM `power=substation` elements.

| Check | Severity | Item Code |
|-------|----------|-----------|
| Missing `voltage=*` tag | HIGH | 9101 |
| Missing `substation=*` type | NORMAL | 9102 |
| Invalid transformer count (≤0) | LOW | 9103 |
| Orphaned substation (not connected to lines) | NORMAL | 9104 |
| Duplicate substations (within 10m) | HIGH | 9105 |

**Example:**
```python
from smart_meter_simulator.osmose import PowerSubstationValidator

analyser = PowerSubstationValidator(country="TH", power_lines=[])
result = analyser.run(osm_data)
print(f"Found {result.total_issues} substation issues")
```

### 2. PowerLineConnectivity

Validates OSM `power=line` and `power=cable` elements.

| Check | Severity | Item Code |
|-------|----------|-----------|
| Dangling line end (not connected to facility) | HIGH | 9201 |
| Missing `voltage=*` on power line | NORMAL | 9202 |
| Self-intersecting power line | NORMAL | 9203 |
| Invalid conductor material | LOW | 9204 |
| Crossing without junction node | LOW | 9205 |

**Example:**
```python
from smart_meter_simulator.osmose import PowerLineConnectivity

analyser = PowerLineConnectivity(country="TH")
result = analyser.run(osm_data)
```

### 3. DuplicateDetection

Finds duplicate electrical infrastructure elements.

| Check | Severity | Default Threshold |
|-------|----------|-------------------|
| Duplicate poles | HIGH | 5m |
| Duplicate transformers | HIGH | 5m |
| Duplicate substations | HIGH | 10m |
| Near-duplicate different types | NORMAL | 15m |

**Example:**
```python
from smart_meter_simulator.osmose import DuplicateDetection

analyser = DuplicateDetection(
    country="TH",
    pole_dist_m=5.0,
    transformer_dist_m=5.0,
    substation_dist_m=10.0,
)
result = analyser.run(osm_data)
```

### 4. MeterConflation

Matches simulator smart meters to OSM power infrastructure.

| Check | Severity |
|-------|----------|
| Unmatched meter (no infrastructure within 50m) | NORMAL |
| Suspicious distance (>200m from infrastructure) | LOW |
| Equidistant to multiple elements | LOW |
| Meter outside grid coverage | HIGH |

**Example:**
```python
from smart_meter_simulator.osmose import MeterConflation, MeterMatch
from smart_meter_simulator.osmose.analysers.meter_conflation import ConflationConfig

analyser = MeterConflation(
    country="TH",
    config=ConflationConfig(max_pole_distance_m=50.0),
)
analyser.load_infrastructure(osm_data)
result = analyser.run([
    {"meter_id": "AMI_001", "lat": 13.7563, "lon": 100.5018},
])
summary = analyser.get_match_summary(...)
print(f"Match rate: {summary['match_rate']}")
```

---

## Grid Quality Manager

The `GridQualityManager` orchestrates all analysers:

```python
from smart_meter_simulator.osmose import create_quality_manager

mgr = create_quality_manager()

# Run all infrastructure validation
result = await mgr.validate_infrastructure(osm_data)
print(f"Total issues: {result.total_issues}")
print(f"By level: {result.issues_by_level}")

# Run meter conflation
meter_result = await mgr.validate_meter_alignment(meters, osm_data)

# Get quality score
score = mgr.get_quality_score()
print(f"Overall: {score['overall']}/100")

# Get suggested matches
matches = mgr.get_suggested_matches(meters, osm_data)
```

---

## API Endpoints

All quality and validation endpoints are consolidated under `/api/v1/quality/`:

### Validation

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/quality/health` | Service health check |
| POST | `/api/v1/quality/validate/infrastructure` | Validate all infrastructure with custom OSM data |
| GET | `/api/v1/quality/validate/infrastructure` | Validate with cached/default data |
| POST | `/api/v1/quality/validate/substation` | Validate substations only |
| POST | `/api/v1/quality/validate/power-line` | Validate power lines only |
| POST | `/api/v1/quality/validate/duplicates` | Detect duplicates only |
| POST | `/api/v1/quality/validate/meter-conflation` | Match meters to infrastructure |
| GET | `/api/v1/quality/validate/meter-alignment` | Validate meter alignment (cached) |
| POST | `/api/v1/quality/validate/power` | Validate custom power data |

### Issues & Rules

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/quality/issues` | Get issues with filtering (analyser, category, level, item) |
| GET | `/api/v1/quality/issues/{issue_id}` | Get specific issue details |
| GET | `/api/v1/quality/issues/{category_id}/class/{class_id}` | Get issues by category and class |
| GET | `/api/v1/quality/rules` | Get validation rule definitions |

### Quality

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/quality/quality-score` | Quality score (0-100) across 5 dimensions |
| GET | `/api/v1/quality/quality-summary` | Comprehensive quality summary |
| GET | `/api/v1/quality/stats` | Validation statistics from last run |
| GET | `/api/v1/quality/dashboard` | Quality dashboard data |
| GET | `/api/v1/quality/categories` | Issue category definitions |

### Monitoring

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/quality/monitoring/start` | Start real-time monitoring |
| POST | `/api/v1/quality/monitoring/stop` | Stop real-time monitoring |
| GET | `/api/v1/quality/monitoring/status` | Monitoring status |

### Analytics & Config

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/quality/analytics/daily` | Run daily analytics |
| GET | `/api/v1/quality/analytics/daily/{target_date}` | Get daily analytics |
| GET | `/api/v1/quality/config` | Get configuration |

### Example: Validate Infrastructure via API

```bash
curl -X POST http://localhost:8082/api/v1/quality/validate/infrastructure \
  -H "Content-Type: application/json" \
  -d '{
    "nodes": [
      {"id": 1, "lat": 13.7563, "lon": 100.5018,
       "tags": {"power": "substation", "voltage": "22000", "substation": "distribution"}}
    ],
    "ways": [],
    "relations": []
  }'
```

### Example: Query Issues with Filters

```bash
# Get all HIGH severity power issues
curl "http://localhost:8082/api/v1/quality/issues?level=1&category=power"

# Get issues from specific analyser
curl "http://localhost:8082/api/v1/quality/issues?analyser=substation"
```

---

## File Structure

```
src/smart_meter_simulator/osmose/
├── analysers/
│   ├── __init__.py
│   ├── power_substation.py          # PowerSubstationValidator
│   ├── power_line_connectivity.py   # PowerLineConnectivity
│   ├── duplicate_detection.py       # DuplicateDetection
│   └── meter_conflation.py          # MeterConflation + MeterMatch + ConflationConfig
├── grid_quality.py                  # GridQualityManager + GridQualityConfig
├── core/
│   ├── analyser.py                  # Base classes (Analyser, AnalyserOsmosis, etc.)
│   └── issue.py                     # OsmoseIssue, IssueLevel, OsmoseValidationResult
├── utils/
│   └── spatial.py                   # SpatialMatcher
└── __init__.py                      # Lazy-loading exports

src/smart_meter_simulator/routers/
└── grid_analysis.py                 # REST API router (8 endpoints)

tests/
└── test_grid_analysers.py           # 22 tests, all passing
```

---

## Test Results

```
22 passed, 0 failed
- TestPowerSubstationValidator: 7 tests
- TestPowerLineConnectivity: 4 tests
- TestDuplicateDetection: 4 tests
- TestMeterConflation: 4 tests
- TestGridQualityManager: 3 tests
```

Run tests:
```bash
uv run pytest tests/test_grid_analysers.py -v
```

---

## Architecture

```
OSM Data (nodes, ways, relations)
    │
    ├──► PowerSubstationValidator ──┐
    ├──► PowerLineConnectivity     ├──► Combined Result
    ├──► DuplicateDetection        ──┘
    │
    ▼
GridQualityManager
    ├──► Quality Score (0-100)
    ├──► Issue Report (by level, tag, item)
    └──► Meter Conflation Results

Meter Data (lat, lon, meter_id)
    │
    └──► MeterConflation ──► Match Results (matched/unmatched/suspicious)
```

---

## Configuration

```python
from smart_meter_simulator.osmose import GridQualityConfig

config = GridQualityConfig(
    conflation_distance_m=50.0,      # Max distance for meter-pole matching
    max_pole_distance_m=50.0,        # Max pole matching distance
    suspicious_distance_m=200.0,     # Threshold for suspicious matches
    pole_duplicate_dist_m=5.0,       # Pole duplicate detection threshold
    transformer_duplicate_dist_m=5.0,
    substation_duplicate_dist_m=10.0,
    country="TH",
)
```

---

_Maintained by the GridTokenX Engineering Team._
