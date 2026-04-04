# OSMOSE Architecture Reference

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Smart Meter Simulator                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              OSMOSE QA Integration Layer                 │   │
│  ├─────────────────────────────────────────────────────────┤   │
│  │                                                          │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │   │
│  │  │  Analysers   │  │   Spatial    │  │    Batch     │  │   │
│  │  │              │  │  Conflation  │  │  Analytics   │  │   │
│  │  │ - Thai Grid  │  │              │  │              │  │   │
│  │  │ - Meter Align│  │ - Haversine  │  │ - Daily      │  │   │
│  │  │              │  │ - Tag Match  │  │ - Weekly     │  │   │
│  │  │              │  │ - Confidence │  │ - Monthly    │  │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘  │   │
│  │                                                          │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │   │
│  │  │   Quality    │  │    Core      │  │   Database   │  │   │
│  │  │   Manager    │  │  Components  │  │   Adapter    │  │   │
│  │  │              │  │              │  │              │  │   │
│  │  │ - Scoring    │  │ - Issue      │  │ - PostGIS    │  │   │
│  │  │ - Monitoring │  │ - Analyser   │  │ - Results    │  │   │
│  │  │ - Validation │  │ - Plugin     │  │ - History    │  │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘  │   │
│  │                                                          │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                    Simulation Engine                            │
│  - Meter Generation  - Grid Topology  - Market Dynamics        │
└─────────────────────────────────────────────────────────────────┘
```

## Data Flow

### 1. Infrastructure Validation Flow

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  OSM Data   │────▶│  Analyser   │────▶│   Issues    │
│  (Nodes,    │     │  (Thai Grid │     │  (Osmose    │
│   Ways,     │     │   Infrastructure)│   Issue)     │
│   Relations)│     │               │     │             │
└─────────────┘     └─────────────┘     └─────────────┘
                                              │
                                              ▼
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Quality   │◀────│   Result    │◀────│  Validation │
│   Score     │     │  (Summary)  │     │  Engine     │
└─────────────┘     └─────────────┘     └─────────────┘
```

### 2. Spatial Conflation Flow

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Meters    │     │   Spatial   │     │  Matches    │
│  (Lat/Lon)  │────▶│   Matcher   │────▶│  (Confidence│
│             │     │               │     │   Score)    │
└─────────────┘     └─────────────┘     └─────────────┘
                           │
                           │
                    ┌─────────────┐
                    │   Poles     │
                    │  (Lat/Lon,  │
                    │   Tags)     │
                    └─────────────┘
```

### 3. Batch Analytics Flow

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Historical │────▶│  Analytics  │────▶│   Metrics   │
│  Readings   │     │   Pipeline  │     │  (Aggregates│
│             │     │               │     │   LMP, etc) │
└─────────────┘     └─────────────┘     └─────────────┘
                           │
                           ▼
                    ┌─────────────┐
                    │   Anomaly   │
                    │  Detection  │
                    └─────────────┘
                           │
                           ▼
                    ┌─────────────┐
                    │  Stability  │
                    │   Score     │
                    └─────────────┘
```

## Component Interactions

### Engine Integration

```python
# Simulation Engine (core/engine.py)
class SimulationEngine:
    def __init__(self):
        # Osmose QA Integration
        self.osmose_enabled = OSMOSE_AVAILABLE
        if self.osmose_enabled:
            self.grid_quality_manager = create_quality_manager()
            self.grid_quality_monitor = GridQualityMonitor(...)
            self.batch_analytics = BatchAnalyticsPipeline(...)
    
    async def validate_grid_infrastructure(self):
        """Delegate to Osmose analyser"""
        return await self.grid_quality_manager.validate_infrastructure()
    
    def validate_reading_quality(self, reading):
        """Real-time validation"""
        return self.grid_quality_monitor.validate_reading(reading)
```

### API Layer

```python
# API Router (routers/grid_quality_router.py)
@router.get("/quality-score")
async def get_quality_score():
    engine = get_simulation_engine()
    return {"status": "success", "data": engine.get_grid_quality_score()}

@router.post("/analytics/daily")
async def run_daily_analytics():
    engine = get_simulation_engine()
    result = await engine.run_daily_analytics()
    return {"status": "success", "data": result}
```

## Issue Lifecycle

```
┌─────────────┐
│  Detected   │  Analyser finds issue in data
└─────────────┘
       │
       ▼
┌─────────────┐
│ Classified  │  Assign level, tags, category
└─────────────┘
       │
       ▼
┌─────────────┐
│  Stored     │  Save to database with metadata
└─────────────┘
       │
       ▼
┌─────────────┐
│  Reported   │  Include in validation result
└─────────────┘
       │
       ▼
┌─────────────┐
│   Fixed     │  User corrects issue
└─────────────┘
       │
       ▼
┌─────────────┐
│  Verified   │  Re-validation confirms fix
└─────────────┘
```

## Quality Score Calculation

```
Overall Score = Σ(Dimension Score × Weight)

┌──────────────────────┬────────┬─────────┬──────────┐
│     Dimension        │ Weight │  Score  │ Weighted │
├──────────────────────┼────────┼─────────┼──────────┤
│ Infrastructure       │  30%   │  95.0   │  28.5    │
│ Accuracy             │  30%   │  92.0   │  27.6    │
│ Alignment            │  20%   │  98.0   │  19.6    │
│ Consistency          │  20%   │  96.0   │  19.2    │
├──────────────────────┴────────┴─────────┼──────────┤
│                              OVERALL     │  94.9    │
└─────────────────────────────────────────┴──────────┘
```

### Score Update Formula

```python
def update_from_issues(self, validation_result):
    total = validation_result.total_objects
    if total == 0:
        return
    
    # Count issues by severity
    level1_count = validation_result.issues_by_level.get('1', 0)
    level2_count = validation_result.issues_by_level.get('2', 0)
    level3_count = validation_result.issues_by_level.get('3', 0)
    
    # Weighted penalty
    penalty = (
        level1_count * 0.1 +   # Critical: 10% penalty each
        level2_count * 0.05 +  # High: 5% penalty each
        level3_count * 0.02    # Low: 2% penalty each
    ) / total * 100
    
    # Update accuracy score
    self.accuracy_score = max(0, 100 - penalty)
```

## Spatial Matching Algorithm

### Haversine Distance

```python
def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate great-circle distance in meters"""
    R = 6371.0  # Earth radius in km
    
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)
    
    a = sin²(Δlat/2) + cos(lat1) × cos(lat2) × sin²(Δlon/2)
    c = 2 × atan2(√a, √(1−a))
    
    return R × c × 1000  # Convert to meters
```

### Confidence Calculation

```python
def calculate_confidence(distance, tag_similarity, config):
    # Distance score (exponential decay)
    distance_score = exp(-distance / config.max_distance)
    
    # Combine scores
    if config.use_tags and tag_similarity > 0:
        confidence = (
            config.distance_weight * distance_score +
            config.tag_weight * tag_similarity
        )
    else:
        confidence = distance_score
    
    return min(1.0, max(0.0, confidence))
```

## Database Schema

### Osmose Issues Table

```sql
CREATE TABLE osmose_issues (
    id SERIAL PRIMARY KEY,
    issue_id INTEGER NOT NULL,
    item INTEGER NOT NULL,
    level INTEGER NOT NULL,
    tags TEXT[] NOT NULL,
    title TEXT NOT NULL,
    detail TEXT,
    fix TEXT,
    osm_type VARCHAR(20),
    osm_id BIGINT,
    lat DOUBLE PRECISION,
    lon DOUBLE PRECISION,
    subclass INTEGER,
    text TEXT,
    fix_suggestions JSONB,
    analyser VARCHAR(100),
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    country VARCHAR(10)
);

-- Spatial index for fast bbox queries
CREATE INDEX idx_osmose_issues_geom 
ON osmose_issues USING GIST (
    ST_SetSRID(ST_MakePoint(lon, lat), 4326)
);
```

## Performance Considerations

### Batch Processing

```
Daily Analytics (1000 meters):
- Load readings:    ~0.5s
- Calculate metrics: ~0.2s
- Detect anomalies:  ~0.3s
- Calculate LMP:     ~0.5s
- Generate report:   ~0.1s
─────────────────────────────
Total:              ~1.6s
```

### Spatial Matching

```
Meter-to-Pole Matching:
- Naive O(n×m):     1000 meters × 500 poles = 500,000 comparisons
- With R-tree:      O(n log m) = ~9,000 comparisons
- Optimization:     55× speedup with spatial indexing
```

## Error Handling

### Analyser Errors

```python
try:
    result = analyser.run(osm_data)
except Exception as e:
    logger.error(f"Analyser {analyser.analyser_id} failed: {e}")
    # Continue with next analyser - don't fail entire validation
    continue
```

### Database Errors

```python
try:
    await db_manager.store_result(result)
except Exception as e:
    logger.warning(f"Failed to store result: {e}")
    # Continue - database failure shouldn't stop validation
    pass
```

## Security Considerations

### Input Validation

```python
# Validate coordinates
lat = Field(..., ge=-90, le=90)
lon = Field(..., ge=-180, le=180)

# Validate issue level
level = Field(..., ge=1, le=3)

# Sanitize OSM IDs
osm_id = Field(..., gt=0)
```

### Rate Limiting

```python
# API rate limiting for validation endpoints
@router.post("/validate/infrastructure")
@rate_limit(max_requests=10, window_seconds=60)
async def validate_infrastructure():
    ...
```

---

**Version:** 2.1.0  
**Last Updated:** 2024-03-30
