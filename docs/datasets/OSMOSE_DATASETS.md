# OSMOSE Datasets - Complete Reference

Comprehensive guide to OSMOSE validation datasets, sample data, and test data generation.

---

## Table of Contents

1. [Overview](#overview)
2. [Sample Datasets](#sample-datasets)
3. [Test Data Generation](#test-data-generation)
4. [Real-World Data](#real-world-data)
5. [Data Formats](#data-formats)
6. [Usage Examples](#usage-examples)

---

## Overview

### What is OSMOSE Dataset?

OSMOSE datasets are collections of OpenStreetMap data used for:
- **Validation testing** - Verify analyser correctness
- **Development** - Test new validation rules
- **Demonstration** - Show OSMOSE capabilities
- **Benchmarking** - Measure performance

### Dataset Types

| Type | Description | Use Case |
|------|-------------|----------|
| **Sample** | Pre-defined real-world data | Testing, demos |
| **Generated** | Randomly created data | Stress testing |
| **Real** | Live OSM data (Overpass) | Production validation |
| **Custom** | User-provided data | Specific scenarios |

---

## Sample Datasets

### 1. Thailand Power Infrastructure

**Dataset**: `thailand_power`

Complete power infrastructure sample for Central Thailand.

**Contents:**
- 6 nodes (towers, poles, transformer, substation)
- 4 ways (power lines)
- 1 relation (site)

**Features:**
```python
{
  "nodes": [
    # EGAT 500kV Tower
    {
      "id": 1001,
      "lat": 14.2563,
      "lon": 100.5018,
      "tags": {
        "power": "tower",
        "tower:type": "lattice",
        "line_management": "straight",
        "line_arrangement": "horizontal",
        "voltage": "500000",
        "operator": "EGAT",
      }
    },
    # MEA Distribution Pole
    {
      "id": 1003,
      "lat": 14.2580,
      "lon": 100.5030,
      "tags": {
        "power": "pole",
        "pole:type": "distribution",
        "line_management": "termination",
        "voltage": "22000",
        "material": "concrete",
        "operator": "MEA",
      }
    },
  ],
  "ways": [
    # 500kV Power Line
    {
      "id": 2001,
      "nodes": [1001, 1002],
      "tags": {
        "power": "line",
        "voltage": "500000",
        "cables": "3",
        "circuits": "1",
      }
    },
  ]
}
```

**Usage:**
```python
from smart_meter_simulator.osmose.dataset import get_sample

data = get_sample("thailand_power")
print(f"Nodes: {len(data['nodes'])}")
print(f"Ways: {len(data['ways'])}")
```

---

### 2. Bangkok Substation

**Dataset**: `bangkok_substation`

Sample substation data for Bangkok metropolitan area.

**Contents:**
- 2 nodes (substation, transformer)
- Proper voltage tagging (voltage:primary/secondary)

**Features:**
```python
{
  "nodes": [
    {
      "id": 5001,
      "lat": 13.7563,
      "lon": 100.5018,
      "tags": {
        "power": "substation",
        "substation": "distribution",
        "voltage": "115000",
        "operator": "MEA",
        "name": "สถานีไฟฟ้าชิดลม",
      }
    },
    {
      "id": 5002,
      "lat": 13.7570,
      "lon": 100.5025,
      "tags": {
        "power": "transformer",
        "voltage:primary": "115000",
        "voltage:secondary": "22000",
        "rating": "50 MVA",
      }
    },
  ]
}
```

---

### 3. Power Line Network

**Dataset**: `power_line_network`

5x5 grid of transmission towers with complete connectivity.

**Contents:**
- 25 towers in grid pattern
- 20 power lines connecting towers
- Complete line_management tagging

**Features:**
- Regular spacing (0.05 degrees)
- Varied line_management types
- Consistent voltage (115kV)

**Usage:**
```python
data = get_sample("power_line_network")
print(f"Grid: 5x5 = {len(data['nodes'])} towers")
print(f"Lines: {len(data['ways'])}")
```

---

### 4. Validation Errors Sample

**Dataset**: `validation_errors`

Intentionally flawed data for testing validation rules.

**Contents:**
- 5 nodes with errors
- 4 ways with errors
- 1 relation with errors

**Errors Included:**

| Error ID | Count | Description |
|----------|-------|-------------|
| 91001 | 2 | Transformer as way/relation |
| 91002 | 1 | Wrong transformer voltage tagging |
| 91101 | 1 | Missing voltage on line |
| 91102 | 1 | Wrong voltage format (115kV) |
| 91103 | 1 | Missing cables tag |
| 91201 | 1 | Missing tower:type |
| 91202 | 1 | Missing line_management |
| 91301 | 1 | Missing substation voltage |
| 91302 | 1 | Missing substation type |

**Expected Results:**
```python
{
  "expected_errors": {
    "91001": 2,
    "91002": 1,
    "91101": 1,
    "91102": 1,
    "91103": 1,
    "91201": 1,
    "91202": 1,
    "91301": 1,
    "91302": 1,
  }
}
```

**Usage:**
```python
# Test validation against known errors
data = get_sample("validation_errors")
result = validator.run(data)

# Verify all errors detected
for error_id, expected_count in data["expected_errors"].items():
    actual_count = sum(1 for i in result.issues if i.id == int(error_id))
    assert actual_count == expected_count, f"Error {error_id}: expected {expected_count}, got {actual_count}"
```

---

## Test Data Generation

### Random Data Generator

Generate random test data with configurable error rates.

**Parameters:**
- `count`: Total number of objects
- `error_rate`: Fraction with validation errors (0.0-1.0)

**Usage:**
```python
from smart_meter_simulator.osmose.dataset import generate_test

# Generate 100 objects with 30% error rate
data = generate_test(count=100, error_rate=0.3)

# Generate 1000 objects with 10% error rate
data = generate_test(count=1000, error_rate=0.1)
```

**Generated Objects:**
- Towers (33%) - power=tower
- Poles (33%) - power=pole
- Power lines (33%) - power=line

**Error Types (when error_rate > 0):**
- Missing line_management
- Missing tower:type
- Missing voltage
- Missing cables
- Wrong voltage format

---

## Real-World Data

### Fetch from Overpass API

Get live OSM data for any geographic area.

**Usage:**
```python
from smart_meter_simulator.osmose.fetcher import OSMOSEDataFetcher
import asyncio

async def fetch_real_data():
    fetcher = OSMOSEDataFetcher()
    
    # Define bounding box (Bangkok)
    bbox = {
        "north": 13.9,
        "south": 13.6,
        "east": 100.7,
        "west": 100.4,
    }
    
    # Fetch power infrastructure
    data = await fetcher.fetch_power_infrastructure(bbox)
    
    print(f"Nodes: {len(data.get('elements', []))}")
    return data

asyncio.run(fetch_real_data())
```

**Overpass Query:**
```
[out:json][timeout:120];
(
  way["power"~"line|minor_line|cable"]({{bbox}});
  node["power"~"tower|pole|portal|terminal"]({{bbox}});
  node["power"="substation"]({{bbox}});
  node["power"="transformer"]({{bbox}});
);
out body;
>;
out skel qt;
```

---

## Data Formats

### OSM JSON Format

Standard format from Overpass API:

```json
{
  "version": 0.6,
  "generator": "Overpass API",
  "elements": [
    {
      "type": "node",
      "id": 123456,
      "lat": 13.7563,
      "lon": 100.5018,
      "tags": {
        "power": "tower",
        "voltage": "115000"
      }
    },
    {
      "type": "way",
      "id": 789012,
      "nodes": [123456, 234567],
      "tags": {
        "power": "line",
        "voltage": "115000"
      }
    }
  ]
}
```

### Internal Format

Simplified format for validation:

```json
{
  "metadata": {
    "name": "Dataset Name",
    "country": "th",
    "bbox": {...}
  },
  "nodes": [
    {
      "id": 123456,
      "lat": 13.7563,
      "lon": 100.5018,
      "tags": {...}
    }
  ],
  "ways": [
    {
      "id": 789012,
      "nodes": [123456, 234567],
      "tags": {...}
    }
  ],
  "relations": [...]
}
```

### GeoJSON Format

For map visualization:

```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "geometry": {
        "type": "Point",
        "coordinates": [100.5018, 13.7563]
      },
      "properties": {
        "id": 123456,
        "power": "tower",
        "voltage": "115000"
      }
    }
  ]
}
```

---

## Usage Examples

### Load and Validate Sample Data

```python
from smart_meter_simulator.osmose import (
    OSMOSERunner,
    create_power_runner,
)
from smart_meter_simulator.osmose.dataset import get_sample

# Create runner
runner = create_power_runner(country="th")

# Load sample data
data = get_sample("validation_errors")

# Run validation
import asyncio

async def validate_sample():
    results = await runner.run_all()
    
    # Print results
    summary = runner.get_summary()
    print(f"Total issues: {summary['total_issues']}")
    print(f"Issues by level: {summary['issues_by_level']}")
    
    # Export issues
    issues = runner.get_issues()
    for issue in issues:
        print(f"  - {issue['title']}")

asyncio.run(validate_sample())
```

### Generate Test Report

```python
from smart_meter_simulator.osmose.dataset import dataset, generate_test

# Generate test data
test_data = generate_test(count=500, error_rate=0.25)

# Save to file
dataset.save(test_data, "test_data.json")

# Load and validate
loaded_data = dataset.load("test_data.json")
print(f"Loaded {len(loaded_data['nodes'])} nodes")
print(f"Loaded {len(loaded_data['ways'])} ways")

# Convert to GeoJSON
geojson = dataset.to_geojson(loaded_data)
print(f"Generated {len(geojson['features'])} features")
```

### Compare Datasets

```python
from smart_meter_simulator.osmose.dataset import get_sample

# Load different datasets
thailand = get_sample("thailand_power")
bangkok = get_sample("bangkok_substation")
errors = get_sample("validation_errors")

# Compare statistics
print("Dataset Comparison:")
print(f"Thailand Power: {len(thailand['nodes'])} nodes, {len(thailand['ways'])} ways")
print(f"Bangkok Substation: {len(bangkok['nodes'])} nodes, {len(bangkok['ways'])} ways")
print(f"Validation Errors: {len(errors['nodes'])} nodes, {len(errors['ways'])} ways")
```

### Batch Processing

```python
import asyncio
from smart_meter_simulator.osmose.dataset import dataset

async def process_all_samples():
    runner = create_power_runner(country="th")
    
    for sample_name in dataset.list_samples():
        print(f"\nProcessing {sample_name}...")
        
        data = dataset.load_sample(sample_name)
        results = await runner.run_all()
        
        summary = runner.get_summary()
        print(f"  Objects: {summary['total_objects']}")
        print(f"  Issues: {summary['total_issues']}")
        print(f"  By level: {summary['issues_by_level']}")

asyncio.run(process_all_samples())
```

---

## Dataset API Reference

### OSMOSEDataset Class

```python
class OSMOSEDataset:
    def load_sample(name: str) -> Dict[str, Any]
        """Load sample dataset by name"""
    
    def generate_test_data(
        count: int = 100,
        error_rate: float = 0.3
    ) -> Dict[str, Any]
        """Generate random test data"""
    
    def to_geojson(data: Dict[str, Any]) -> Dict[str, Any]
        """Convert to GeoJSON format"""
    
    def save(data: Dict[str, Any], filepath: str)
        """Save dataset to JSON file"""
    
    def load(filepath: str) -> Dict[str, Any]
        """Load dataset from JSON file"""
    
    def list_samples() -> List[str]
        """List available sample datasets"""
```

### Helper Functions

```python
def get_sample(name: str) -> Dict[str, Any]
    """Get sample dataset by name"""

def generate_test(
    count: int = 100,
    error_rate: float = 0.3
) -> Dict[str, Any]
    """Generate test data"""
```

---

## Sample Data Locations

| Dataset | File | Size |
|---------|------|------|
| Thailand Power | `dataset.thailand_power` | 6 nodes, 4 ways |
| Bangkok Substation | `dataset.bangkok_substation` | 2 nodes |
| Power Line Network | `dataset.power_line_network` | 25 nodes, 20 ways |
| Validation Errors | `dataset.validation_errors` | 5 nodes, 4 ways, 1 relation |

---

## Creating Custom Datasets

### Example: Custom Industrial Area

```python
custom_data = {
    "metadata": {
        "name": "Industrial Area Sample",
        "description": "Factory power infrastructure",
        "bbox": {
            "north": 13.8,
            "south": 13.7,
            "east": 100.6,
            "west": 100.5,
        }
    },
    "nodes": [
        {
            "id": 1,
            "lat": 13.75,
            "lon": 100.55,
            "tags": {
                "power": "substation",
                "substation": "industrial",
                "voltage": "115000",
                "operator": "PEA",
            }
        },
        # Add more nodes...
    ],
    "ways": [
        # Add power lines...
    ],
}

# Save custom dataset
dataset.save(custom_data, "custom_industrial.json")

# Load and use
custom = dataset.load("custom_industrial.json")
```

---

## Best Practices

### 1. Use Appropriate Error Rates

```python
# For testing: high error rate
test_data = generate_test(count=100, error_rate=0.5)

# For benchmarking: realistic error rate
benchmark_data = generate_test(count=1000, error_rate=0.1)

# For production validation: use real data
real_data = await fetcher.fetch_power_infrastructure(bbox)
```

### 2. Validate Sample Data

```python
# Always verify sample data structure
data = get_sample("thailand_power")
assert "nodes" in data
assert "ways" in data
assert "metadata" in data
```

### 3. Save Test Results

```python
# Save validation results for comparison
result = await runner.run_all()
dataset.save({
    "dataset": "thailand_power",
    "timestamp": datetime.utcnow().isoformat(),
    "issues": [i.dict() for i in result.issues],
    "summary": runner.get_summary(),
}, "validation_result.json")
```

---

## Resources

- **Sample Code**: `src/smart_meter_simulator/osmose/dataset.py`
- **Documentation**: `docs/OSMOSE_INTEGRATION_COMPLETE.md`
- **OSM Data Format**: https://wiki.openstreetmap.org/wiki/OSM_JSON
- **GeoJSON Spec**: https://geojson.org/

---

_Document Version: 1.0_  
_Last Updated: 2026-03-30_  
_Author: GridTokenX Engineering Team_
