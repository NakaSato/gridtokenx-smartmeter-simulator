# Power Infrastructure Validation API

OSMOSE-style power infrastructure validation for the GridTokenX Smart Meter Simulator.

## Overview

This module implements power infrastructure validation rules based on the [OSMOSE QA](https://github.com/osmose-qa/osmose-backend) project. It validates power grid data for common tagging errors and topology issues.

## Features

### Validation Rules

Based on OSMOSE Power.py and related analyzers:

| Issue ID | Category | Level | Description |
|----------|----------|-------|-------------|
| **91001** | Transformer Geometry | 2 | Power transformers should always be on a node |
| **91002** | Transformer Tagging | 2 | Use voltage:primary=* and voltage:secondary=* |
| **91101** | Power Line Tagging | 3 | Power line missing voltage tag |
| **91102** | Power Line Format | 2 | Voltage format should be numeric (volts) |
| **91103** | Power Line Tagging | 3 | Power line missing cables tag |
| **91201** | Tower Tagging | 3 | Tower missing type |
| **91202** | Support Tagging | 3 | Missing line_management tag |
| **91301** | Substation Tagging | 3 | Substation missing voltage |
| **91302** | Substation Tagging | 3 | Substation missing type |
| **91401** | Line Management | 3 | Unknown line_management value |
| **91402** | Line Arrangement | 3 | Unknown line_arrangement value |

### Validation Levels

- **Level 1 (High)**: Critical errors that break data integrity
- **Level 2 (Normal)**: Common mistakes that reduce data quality
- **Level 3 (Low)**: Suggestions for improvement

## API Endpoints

### GET /api/power/validate

Validate power infrastructure with sample data.

```bash
curl http://localhost:8082/api/power/validate
```

**Query Parameters:**
- `voltage_min` (int): Minimum voltage to validate (in volts)
- `voltage_max` (int): Maximum voltage to validate (in volts)
- `include_level_3` (bool): Include low-priority issues (default: true)

**Response:**
```json
{
  "total_objects": 7,
  "total_issues": 12,
  "issues_by_level": {
    "1": 0,
    "2": 5,
    "3": 7
  },
  "issues_by_category": {
    "power": 12,
    "fix:chair": 2,
    "geom": 1,
    "tag": 8,
    "voltage": 4,
    "cables": 2,
    "tower:type": 1,
    "line_management": 3
  },
  "transformers_validated": 1,
  "power_lines_validated": 2,
  "towers_validated": 1,
  "poles_validated": 1,
  "substations_validated": 1,
  "issues": [
    {
      "id": 91002,
      "item": 9100,
      "level": 2,
      "tags": ["power", "fix:chair", "tag"],
      "title": "On Power Transformers use voltage:primary=* and voltage:secondary=* in place of voltage",
      "detail": "Transformers have multiple voltage levels...",
      "fix": "Replace voltage=* with voltage:primary=* and voltage:secondary=* tags.",
      "osm_type": "node",
      "osm_id": 1001,
      "text": "voltage=115000"
    }
  ]
}
```

### POST /api/power/validate

Validate custom power infrastructure data.

```bash
curl -X POST http://localhost:8082/api/power/validate \
  -H "Content-Type: application/json" \
  -d '{
    "nodes": [
      {
        "id": 123456,
        "lat": 13.7563,
        "lon": 100.5018,
        "tags": {
          "power": "transformer",
          "voltage": "115000"
        }
      }
    ],
    "ways": [
      {
        "id": 789012,
        "nodes": [111, 222, 333],
        "tags": {
          "power": "line",
          "voltage": "115000",
          "cables": "6"
        }
      }
    ]
  }'
```

### GET /api/power/issues/{issue_id}

Get details about a specific validation issue type.

```bash
curl http://localhost:8082/api/power/issues/91002
```

### GET /api/power/issues

List all available validation issue types.

```bash
curl http://localhost:8082/api/power/issues
```

### GET /api/power/statistics

Get validation statistics.

```bash
curl http://localhost:8082/api/power/statistics
```

## Usage Examples

### Python Client

```python
import requests

# Validate power infrastructure
response = requests.get('http://localhost:8082/api/power/validate')
result = response.json()

print(f"Found {result['total_issues']} issues")
print(f"  - Level 1 (High): {result['issues_by_level']['1']}")
print(f"  - Level 2 (Normal): {result['issues_by_level']['2']}")
print(f"  - Level 3 (Low): {result['issues_by_level']['3']}")

# Show issues by category
for category, count in result['issues_by_category'].items():
    print(f"  {category}: {count} issues")
```

### JavaScript Client

```javascript
// Fetch validation results
const response = await fetch('http://localhost:8082/api/power/validate');
const result = await response.json();

// Display issues
result.issues.forEach(issue => {
  console.log(`[${issue.level}] ${issue.title}`);
  console.log(`  Object: ${issue.osm_type} ${issue.osm_id}`);
  console.log(`  Fix: ${issue.fix}`);
});
```

## Integration with OSMOSE

This validator implements a subset of OSMOSE's power validation rules:

- **OSMOSE Backend**: https://github.com/osmose-qa/osmose-backend
- **Power.py Plugin**: `/plugins/Power.py`
- **Power.validator.mapcss**: `/plugins/Power.validator.mapcss`

### OSMOSE Issue Codes

The issue codes match OSMOSE's classification system:
- **Item 9100**: Transformer issues
- **Item 9110**: Power line issues
- **Item 9120**: Tower/pole issues
- **Item 9130**: Substation issues
- **Item 9140**: Line management issues

## Fix Suggestions

The API provides structured fix suggestions:

```json
{
  "fix_suggestions": [
    {
      "-": ["voltage"],
      "+": {
        "voltage:primary": "115000",
        "voltage:secondary": "22000"
      }
    }
  ]
}
```

**Actions:**
- `+` : Add tag
- `-` : Delete tag
- `~` : Modify tag value

## Future Enhancements

- [ ] Database integration for persistent validation results
- [ ] Real-time validation on data import
- [ ] Thai grid-specific validation rules (MEA/PEA standards)
- [ ] Line management topology visualization
- [ ] Automatic fix application
- [ ] Batch validation for large datasets
- [ ] Integration with OSMOSE backend for advanced SQL analyzers

## References

- [OSMOSE QA Documentation](https://github.com/osmose-qa/osmose-backend/tree/master/doc)
- [OSM Power Tagging](https://wiki.openstreetmap.org/wiki/Tag:power=line)
- [Line Management Key](https://wiki.openstreetmap.org/wiki/Key:line_management)
- [Thai Grid Topology](../../../docs/THAI_GRID_TOPOLOGY.md)
