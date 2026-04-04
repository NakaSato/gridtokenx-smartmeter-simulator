# Power Infrastructure - Complete Reference

Comprehensive guide to power infrastructure mapping, validation, and integration in GridTokenX.

---

## Table of Contents

1. [OSM Power Tagging Standards](#1-osm-power-tagging-standards)
2. [Line Management Topology](#2-line-management-topology)
3. [Voltage Classification](#3-voltage-classification)
4. [Thai Power Grid Standards](#4-thai-power-grid-standards)
5. [OSMOSE Validation Rules](#5-osmose-validation-rules)
6. [API Reference](#6-api-reference)
7. [Use Cases](#7-use-cases)

---

## 1. OSM Power Tagging Standards

### 1.1 Power Infrastructure Elements

| Element | Tag | Description | Typical Use |
|---------|-----|-------------|-------------|
| **Transmission Line** | `power=line` | High-voltage lines (>150kV) on towers | 115kV, 230kV, 500kV |
| **Distribution Line** | `power=minor_line` | Lower voltage lines on poles | 22kV, 33kV |
| **Underground Cable** | `power=cable` | Buried or underwater cables | Urban areas |
| **Transformer** | `power=transformer` | Voltage conversion equipment | Substations |
| **Tower** | `power=tower` | Large steel lattice structures | Transmission |
| **Pole** | `power=pole` | Wooden/concrete poles | Distribution |
| **Substation** | `power=substation` | Major switching facility | Transmission/Distribution |
| **Minor Substation** | `power=minor_substation` | Small distribution node | Local distribution |
| **Switch** | `power=switch` | Circuit control equipment | All levels |
| **Generator** | `power=generator` | Power production unit | Plants, solar, wind |
| **Plant** | `power=plant` | Entire power generation facility | Multi-unit |

### 1.2 Required Tags by Element

#### Power Lines
```
power=line OR power=minor_line
voltage=*                    # Operating voltage in volts
cables=*                     # Number of conductors (3, 6, 9, 12)
circuits=*                   # Number of circuits (cables/3)
frequency=*                  # Hz (50 for Thailand)
location=overhead            # Default, or underground/underwater
```

#### Towers
```
power=tower
tower:type=*                 # lattice, tubular, guyed, etc.
line_management=*            # straight, branch, termination, etc.
line_arrangement=*           # horizontal, vertical, triangle
voltage=*                    # Operating voltage
```

#### Poles
```
power=pole
pole:type=*                  # distribution, transmission, street_light
line_management=*            # straight, branch, termination, etc.
line_arrangement=*           # horizontal, vertical
material=*                   # wood, concrete, steel
```

#### Transformers
```
power=transformer
voltage:primary=*            # Input voltage
voltage:secondary=*          # Output voltage
voltage:tertiary=*           # Optional third winding
rating=*                     # Power rating (e.g., "50 MVA")
windings=*                   # Number of windings
```

#### Substations
```
power=substation OR power=minor_substation
substation=*                 # transmission, distribution, minor_distribution
voltage=*                    # Highest voltage level
location=*                   # indoor, outdoor, underground
```

### 1.3 Optional but Recommended Tags

```
operator=*                   # Grid operator (e.g., "MEA", "PEA", "EGAT")
owner=*                      # Asset owner
name=*                       # Facility name
ref=*                        # Equipment reference number
start_date=*                 # Commissioning date
frequency=*                  # Grid frequency (50 in Thailand)
wires=*                      # Conductor bundle (single, double, triple)
layer=*                      # Vertical position (for crossings)
```

---

## 2. Line Management Topology

### 2.1 What is Line Management?

Line management describes **how power lines connect to support structures** (towers/poles). This is critical for:
- Understanding grid topology
- Network analysis and tracing
- Identifying critical infrastructure points
- Power flow modeling

### 2.2 Standard Line Management Values

| Value | Icon | Description | Visual Example |
|-------|------|-------------|----------------|
| **straight** | │ | Simple support, lines continue straight | `────●────` |
| **branch** | ┣ | Y-connection where lines split off | `────●───`<br>`      │` |
| **split** | ┳ | Lines divide into separate paths | `───●───`<br>`    │` |
| **termination** | ┫ | End of line (anchor point) | `────●│` |
| **transpose** | ╳ | Phase transposition (swap positions) | `╳` |
| **transition** | ╔ | Change in line configuration | `┌────` |
| **cross** | ╋ | Lines crossing (no connection) | `─┼─` |

### 2.3 Line Arrangement

Describes how conductors are arranged on the support:

| Value | Description | Typical Use |
|-------|-------------|-------------|
| **horizontal** | Conductors in horizontal line | Single-circuit towers |
| **vertical** | Conductors stacked vertically | Narrow right-of-way |
| **semi_vertical** | Partially vertical arrangement | Double-circuit towers |
| **triangle** | Triangular arrangement | Compact designs |

### 2.4 Real-World Examples

#### Transmission Tower (500kV)
```
power=tower
tower:type=lattice
line_management=straight
line_arrangement=horizontal
voltage=500000
cables=3
operator=EGAT
```

#### Distribution Pole (22kV)
```
power=pole
pole:type=distribution
line_management=branch
line_arrangement=horizontal
voltage=22000
cables=3
material=concrete
operator=PEA
```

#### Termination Tower
```
power=tower
tower:type=lattice
line_management=termination
line_arrangement=horizontal
voltage=115000
```

---

## 3. Voltage Classification

### 3.1 Standard Voltage Levels

#### Thailand (MEA/PEA/EGAT)

| Level | Voltage (kV) | Usage | Color Code |
|-------|--------------|-------|------------|
| **Ultra High** | 500 kV | National transmission (EGAT) | Red (#e6194B) |
| **Extra High** | 230 kV | Regional transmission | Orange (#f58231) |
| **High** | 115 kV | Provincial distribution | Yellow (#ffe119) |
| **Medium** | 33 kV | Industrial distribution | Orange (#ff6600) |
| **Medium** | 22 kV | Commercial distribution | Orange (#ff6600) |
| **Low** | 0.4 kV (400V) | Residential (3-phase) | Yellow (#ffcc00) |
| **Low** | 0.23 kV (230V) | Residential (1-phase) | Yellow (#ffcc00) |

#### International Standards

| Region | Transmission | Distribution | Residential |
|--------|--------------|--------------|-------------|
| **Thailand** | 500/230/115 kV | 33/22 kV | 400/230 V |
| **Europe** | 400/220 kV | 110/20 kV | 400/230 V |
| **North America** | 500/345/230 kV | 138/69/34.5 kV | 208/120 V |
| **Japan** | 500/275 kV | 154/77/66 kV | 400/200 V |

### 3.2 Voltage Tagging Format

**Always use volts (not kV):**
```
✅ voltage=115000      # Correct
❌ voltage=115kV       # Wrong
❌ voltage=115         # Wrong (ambiguous)
```

**Multiple voltages (semicolon-separated):**
```
voltage=115000;22000   # Transformer with multiple windings
```

**Transformer-specific tagging:**
```
power=transformer
voltage:primary=115000
voltage:secondary=22000
# NOT: voltage=115000 (ambiguous for transformers)
```

### 3.3 Voltage-Based Styling

For map visualization:

```css
/* 500+ kV - Ultra High */
stroke: #e6194B;
stroke-width: 6px;

/* 230-499 kV - Extra High */
stroke: #f58231;
stroke-width: 4px;

/* 115-229 kV - High */
stroke: #ffe119;
stroke-width: 3px;

/* 22-114 kV - Medium */
stroke: #ff6600;
stroke-width: 2px;

/* < 22 kV - Low */
stroke: #ffcc00;
stroke-width: 1px;
```

---

## 4. Thai Power Grid Standards

### 4.1 Grid Operators

| Operator | Coverage | Voltage Levels |
|----------|----------|----------------|
| **EGAT** (การไฟฟ้าฝ่ายผลิต) | National | 500 kV, 230 kV, 115 kV |
| **MEA** (การไฟฟ้านครหลวง) | Bangkok & vicinity | 115 kV, 33 kV, 22 kV |
| **PEA** (การไฟฟ้าส่วนภูมิภาค) | Rest of Thailand | 115 kV, 33 kV, 22 kV |

### 4.2 Thai Grid Topology

```
EGAT Generation Plants
    │
    ├─ 500 kV Transmission ──────┐
    │                             │
    ├─ 230 kV Transmission ──── Substations
    │                             │
    ├─ 115 kV Transmission ──── MEA/PEA Handover
                                │
                    ┌───────────┴───────────┐
                    │                       │
                MEA Area              PEA Area
                (Bangkok)            (Provinces)
                    │                       │
              33 kV / 22 kV           33 kV / 22 kV
              Distribution            Distribution
                    │                       │
                400/230 V             400/230 V
                Residential           Residential
```

### 4.3 Thai-Specific Tags

```
operator=EGAT              # Electricity Generating Authority of Thailand
operator=MEA               # Metropolitan Electricity Authority
operator=PEA               # Provincial Electricity Authority

substation=transmission    # EGAT substations
substation=distribution    # MEA/PEA substations

power_line=ac              # AC lines (default)
power_line=dc              # DC lines (rare, for specific projects)
```

### 4.4 Thai Infrastructure Examples

#### EGAT 500kV Tower
```
power=tower
tower:type=lattice
line_management=straight
line_arrangement=horizontal
voltage=500000
cables=3
circuits=1
operator=EGAT
name=สายส่งไฟฟ้า 500 kV
```

#### MEA Distribution Pole
```
power=pole
pole:type=distribution
line_management=branch
line_arrangement=horizontal
voltage=22000
cables=3
material=concrete
operator=MEA
location=urban
```

#### PEA Substation
```
power=substation
substation=distribution
voltage=115000
location=outdoor
operator=PEA
name=สถานีไฟฟ้าแรงสูง...
```

---

## 5. OSMOSE Validation Rules

### 5.1 What is OSMOSE?

**OSMOSE QA** (OpenStreetMap Quality Assurance) is an automated validation system that checks OSM data for errors.

- **Backend**: https://github.com/osmose-qa/osmose-backend
- **Frontend**: https://osmose.openstreetmap.fr
- **Coverage**: 30+ countries, 300+ validation rules

### 5.2 Power Validation Rules

#### Rule 91001: Transformer Geometry
```
Issue: Power transformers should always be on a node
Level: 2 (Normal)
Tags: power, fix:chair, geom

Wrong:
  way[power=transformer]
  relation[power=transformer]

Correct:
  node[power=transformer]
```

#### Rule 91002: Transformer Voltage Tagging
```
Issue: Use voltage:primary=* and voltage:secondary=* instead of voltage=*
Level: 2 (Normal)
Tags: power, fix:chair, tag

Wrong:
  node[power=transformer][voltage=115000]

Correct:
  node[power=transformer][voltage:primary=115000][voltage:secondary=22000]
```

#### Rule 91101: Power Line Voltage
```
Issue: Power line missing voltage tag
Level: 3 (Low)
Tags: power, voltage

Required:
  way[power=line][voltage=*]
```

#### Rule 91102: Voltage Format
```
Issue: Voltage format should be numeric (in volts)
Level: 2 (Normal)
Tags: power, voltage, tag

Wrong:
  voltage=115kV
  voltage=115

Correct:
  voltage=115000
```

#### Rule 91103: Cables Tag
```
Issue: Power line missing cables tag
Level: 3 (Low)
Tags: power, cables

Required:
  way[power=line][cables=*]
  
Typical values: 3, 6, 9, 12 (multiples of 3)
```

#### Rule 91201: Tower Type
```
Issue: Tower missing type
Level: 3 (Low)
Tags: power, tower:type

Required:
  node[power=tower][tower:type=*]
  
Common values: lattice, tubular, guyed, portal
```

#### Rule 91202: Line Management
```
Issue: Support structure missing line_management tag
Level: 3 (Low)
Tags: power, line_management

Required:
  node[power=tower][line_management=*]
  node[power=pole][line_management=*]
  
Valid values: straight, branch, split, termination, transpose, transition, cross
```

#### Rule 91301: Substation Voltage
```
Issue: Substation missing voltage
Level: 3 (Low)
Tags: power, substation

Required:
  node[power=substation][voltage=*]
```

#### Rule 91302: Substation Type
```
Issue: Substation missing type
Level: 3 (Low)
Tags: power, substation

Required:
  node[power=substation][substation=*]
  
Valid values: transmission, distribution, minor_distribution
```

### 5.3 Fix Suggestions Format

OSMOSE provides structured fix suggestions:

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

---

## 6. API Reference

### 6.1 Power Validation API

Base URL: `http://localhost:8082/api/power`

#### GET /validate

Validate power infrastructure with sample data.

```bash
curl http://localhost:8082/api/power/validate
```

**Query Parameters:**
- `voltage_min` (int): Minimum voltage to validate
- `voltage_max` (int): Maximum voltage to validate
- `include_level_3` (bool): Include low-priority issues

**Response:**
```json
{
  "total_objects": 6,
  "total_issues": 9,
  "issues_by_level": {"1": 0, "2": 3, "3": 6},
  "issues_by_category": {"power": 9, "tag": 2},
  "transformers_validated": 1,
  "power_lines_validated": 2,
  "towers_validated": 1,
  "poles_validated": 1,
  "substations_validated": 1,
  "issues": [...]
}
```

#### POST /validate

Validate custom power data.

```bash
curl -X POST http://localhost:8082/api/power/validate \
  -H "Content-Type: application/json" \
  -d '{
    "nodes": [{"id": 1, "tags": {"power": "transformer"}}],
    "ways": [{"id": 2, "tags": {"power": "line"}}]
  }'
```

#### GET /issues/{issue_id}

Get issue type details.

```bash
curl http://localhost:8082/api/power/issues/91002
```

#### GET /issues

List all issue types.

```bash
curl http://localhost:8082/api/power/issues
```

#### GET /statistics

Get validation statistics.

```bash
curl http://localhost:8082/api/power/statistics
```

### 6.2 OSMOSE Public API

Base URL: `https://osmose.openstreetmap.fr/api/0.3`

#### Vector Tiles (MVT)

```
GET /issues/{z}/{x}/{y}.mvt?tags=power
```

Returns power validation issues as Mapbox Vector Tiles.

#### Issue Details

```
GET /issue/{issue_id}
```

Get detailed information about a specific issue.

#### Tags Taxonomy

```
GET /tags
```

List all issue classification tags.

---

## 7. Use Cases

### 7.1 Grid Quality Assurance

**Problem**: Ensure OSM power data meets quality standards before import.

**Solution**:
```python
import requests

# Validate power data
response = requests.post(
    'http://localhost:8082/api/power/validate',
    json=osm_data
)
result = response.json()

# Check for critical issues
if result['issues_by_level']['1'] > 0:
    print("❌ Critical errors found - fix before import")
elif result['issues_by_level']['2'] > 0:
    print("⚠️ Common mistakes found - review recommended")
else:
    print("✅ Data quality acceptable")
```

### 7.2 Thai Grid Visualization

**Problem**: Display Thai power grid with proper voltage styling.

**Solution**:
```typescript
// Voltage-based line coloring
const getVoltageColor = (voltageKv: number) => {
  if (voltageKv >= 500) return '#e6194B';  // EGAT 500kV
  if (voltageKv >= 230) return '#f58231';  // EGAT 230kV
  if (voltageKv >= 115) return '#ffe119';  // MEA/PEA 115kV
  if (voltageKv >= 22)  return '#ff6600';  // Distribution
  return '#ffcc00';                         // Low voltage
};

// Operator-based filtering
const filterByOperator = (operator: string) => {
  return [
    '==',
    ['get', 'operator'],
    operator  // 'EGAT', 'MEA', or 'PEA'
  ];
};
```

### 7.3 Network Topology Analysis

**Problem**: Trace power flow from generation to consumer.

**Solution**:
```python
def trace_power_flow(start_node, graph):
    """
    Trace power network from substation to end users
    using line_management topology tags
    """
    visited = set()
    queue = [start_node]
    
    while queue:
        current = queue.pop(0)
        if current in visited:
            continue
        visited.add(current)
        
        # Get connected lines
        lines = graph.get_lines(current)
        for line in lines:
            # Check line management at next tower
            next_tower = line.end_tower
            topology = next_tower.get('line_management')
            
            if topology == 'termination':
                # End of line - consumer connection
                record_consumer(next_tower)
            elif topology == 'branch':
                # Branch point - add to queue
                queue.extend(next_tower.connected_lines)
            else:
                # Continue along main line
                queue.append(next_tower)
    
    return visited
```

### 7.4 Smart Meter Integration

**Problem**: Link smart meters to grid infrastructure.

**Solution**:
```python
class MeterGridIntegration:
    def __init__(self):
        self.validator = PowerValidator()
    
    def register_meter(self, meter_data):
        """
        Register smart meter and validate grid connection
        """
        # Find nearest pole/tower
        nearest_support = self.find_nearest_support(
            meter_data.lat, 
            meter_data.lon
        )
        
        # Validate connection point
        issues = self.validator.validate_support(nearest_support)
        
        if issues:
            logger.warning(f"Grid connection issues: {issues}")
        
        # Link meter to grid node
        meter_record = {
            **meter_data,
            'grid_connection': {
                'support_id': nearest_support.id,
                'support_type': nearest_support.type,
                'voltage': nearest_support.voltage,
                'operator': nearest_support.operator,
            }
        }
        
        return meter_record
```

### 7.5 OSMOSE Integration

**Problem**: Display real-time validation issues on map.

**Solution**:
```typescript
// Fetch OSMOSE vector tiles
const osmoseSource = {
  type: 'vector',
  tiles: [
    'https://osmose.openstreetmap.fr/api/0.3/issues/{z}/{x}/{y}.mvt?tags=power'
  ],
  minzoom: 10,
  maxzoom: 18,
};

// Style validation markers
const osmoseLayer = {
  id: 'osmose-power-issues',
  type: 'circle',
  source: 'osmose-issues',
  'source-layer': 'issues',
  paint: {
    'circle-radius': 8,
    'circle-color': [
      'case',
      ['==', ['get', 'severity'], 'error'], '#ff0000',
      ['==', ['get', 'severity'], 'warning'], '#ffa500',
      '#0080ff'
    ],
  }
};
```

---

## Quick Reference Card

### Essential Tags

```
# Power Lines
power=line|minor_line|cable
voltage=* (in volts!)
cables=* (3, 6, 9, 12)

# Supports
power=tower|pole
tower:type=* | pole:type=*
line_management=*
line_arrangement=*

# Transformers (NODES ONLY!)
power=transformer
voltage:primary=*
voltage:secondary=*

# Substations
power=substation|minor_substation
substation=transmission|distribution|minor_distribution
voltage=*
```

### Common Mistakes

```
❌ power=transformer on way/relation → ✅ Must be node
❌ voltage=115kV → ✅ voltage=115000
❌ voltage=115 on transformer → ✅ voltage:primary=115000
❌ Missing line_management → ✅ Add topology tag
❌ Missing cables → ✅ Add conductor count
```

### Thai Grid Quick Reference

```
EGAT:  500kV, 230kV, 115kV (National transmission)
MEA:   115kV, 33kV, 22kV (Bangkok distribution)
PEA:   115kV, 33kV, 22kV (Provincial distribution)

Residential: 400V (3-phase), 230V (1-phase)
Frequency: 50 Hz
```

---

## Resources

- **OSM Power Tagging**: https://wiki.openstreetmap.org/wiki/Tag:power=line
- **Line Management**: https://wiki.openstreetmap.org/wiki/Key:line_management
- **OSMOSE Backend**: https://github.com/osmose-qa/osmose-backend
- **OSMOSE Live**: https://osmose.openstreetmap.fr
- **Thai Grid Info**: https://www.egat.co.th, https://www.mea.or.th, https://www.pea.co.th

---

_Document Version: 1.0_  
_Last Updated: 2026-03-30_  
_Author: GridTokenX Engineering Team_
