# OSM Power Infrastructure Tagging Reference

Reference: https://wiki.openstreetmap.org/wiki/Key:power

This document maps OpenStreetMap `power=*` tags to GridTokenX simulator format for pandapower integration.

---

## Power Values

| OSM `power=*` | Geometry | Simulator Mapping | Description |
|---------------|----------|-------------------|-------------|
| `line` | Way | `power_lines` | Overhead transmission/distribution line |
| `cable` | Way | `power_lines` (type=underground) | Underground, submarine, or indoor power cable |
| `minor_line` | Way | `power_lines` | Minor distribution line |
| `tower` | Node | `grid_topology.towers` | Steel/concrete pylon for transmission lines |
| `pole` | Node | `grid_topology.poles` | Wooden/concrete pole for distribution lines |
| `substation` | Node/Area | `substations` | Voltage transformation facility |
| `transformer` | Node | `transformers` | Individual voltage transformer device |
| `generator` | Node/Area | `meters` (as generation source) | Single generation unit |
| `plant` | Area | `meters` (as plant) | Entire generation facility/site |
| `switch` | Node | `grid_topology.switches` | Manual/automatic circuit disconnect |
| `switchgear` | Node/Area | `grid_topology.switchgear` | Enclosed switch assembly |
| `terminal` | Node | `grid_topology.terminals` | Electrical endpoint/junction |
| `portal` | Node | `grid_topology.portals` | Overhead-to-underground transition point |
| `insulator` | Node | — | Insulating component (detail, not modeled) |
| `converter` | Node/Area | — | AC/DC conversion facility (HVDC) |

---

## Voltage Tagging

OSM uses **Volts** (no unit suffix):

| OSM Tag | Example Values | Simulator Usage |
|---------|----------------|-----------------|
| `voltage=*` | `230000`, `115000`, `22000`, `380` | Primary voltage for lines, substations, transformers |
| `line_voltage=*` | Same as `voltage=*` | Preferred for `power=line` and `power=cable` |
| `voltage:primary=*` | `230000` | Transformer primary winding |
| `voltage:secondary=*` | `22000` | Transformer secondary winding |

Multi-voltage (semicolon-separated): `voltage=33000;230000`

### Thailand Grid Voltage Levels

| Utility | Transmission | Distribution | Low Voltage |
|---------|-------------|--------------|-------------|
| **EGAT** | 500kV, 230kV, 115kV | — | — |
| **MEA** | — | 22kV | 0.4kV (400V) |
| **PEA** | — | 22kV, 11kV | 0.4kV (400V) |

---

## Electrical Tags for Lines/Cables

| Tag | Format | Example | Meaning |
|-----|--------|---------|---------|
| `cables` | Integer | `6` | Total physical conductors (e.g., 6 = 3 per circuit × 2) |
| `circuits` | Integer | `2` | Independent electrical circuits on same infrastructure |
| `frequency` | Hz | `50`, `60`, `0` (DC) | AC system frequency |
| `wires` | Enum | `single`, `bundled` | Conductor configuration |

### Typical Configurations

| Voltage | Circuits | Cables | Wires | Notes |
|---------|----------|--------|-------|-------|
| 500kV | 2 | 6 | single | EGAT main transmission |
| 230kV | 2 | 6 | single | EGAT regional transmission |
| 115kV | 1-2 | 3-6 | single | EGAT sub-transmission |
| 22kV | 1 | 3 | single | MEA/PEA distribution |

---

## Substation Types

| `substation=*` | Voltage Range | Operator | Description |
|----------------|---------------|----------|-------------|
| `transmission` | ≥69kV | EGAT | High voltage transmission substations |
| `distribution` | ≤69kV | MEA/PEA | Medium/low voltage distribution |
| `traction` | 25kV AC or 16.7Hz | SRT | Railway power supply |
| `industrial` | Variable | Private | Factory/dedicated facility |
| `converter` | HVDC | — | AC/DC conversion |

---

## Metadata Tags

| Tag | Required | Example | Notes |
|-----|----------|---------|-------|
| `operator` | Yes | `การไฟฟ้าฝ่ายผลิตแห่งประเทศไทย` | Thai name preferred |
| `operator:en` | Recommended | `Electricity Generating Authority of Thailand` | English name |
| `operator:wikidata` | Optional | `Q3050569` | Wikidata ID |
| `name` | Recommended | `ท่าตะโก-อ่างทอง1` | Official name (Thai) |
| `name:en` | Optional | `Tha Tako-Ang Thong 1` | English name |
| `ref` | Recommended | `LINE-230-001` | Reference/designation code |
| `location` | Optional | `overhead`, `underground`, `indoor` | Physical installation type |

---

## Lifecycle Tags

| Tag | Usage |
|-----|-------|
| `construction:power=*` | Under construction (ground work started) |
| `planned:power=*` | Approved, pre-construction |
| `disused:power=*` | No longer in operation |
| `disused=yes` | Retain `power=line/cable` for rendering |
| `demolished:power=*` | Being demolished (delete after removal) |

---

## Thailand Utilities Reference

### EGAT (การไฟฟ้าฝ่ายผลิตแห่งประเทศไทย)
- **Wikidata**: Q3050569
- **Role**: Generation & transmission
- **Voltages**: 500kV, 230kV, 115kV
- **Coverage**: Nationwide transmission grid

### MEA (การไฟฟ้านครหลวง)
- **Role**: Metropolitan distribution
- **Voltages**: 22kV, 0.4kV
- **Coverage**: Bangkok, Nonthaburi, Samut Prakan

### PEA (การไฟฟ้าส่วนภูมิภาค)
- **Role**: Provincial distribution
- **Voltages**: 22kV, 11kV, 0.4kV
- **Coverage**: All provinces outside MEA area

---

## OSM → Simulator Conversion Rules

### Power Lines
```json
// OSM
{"power": "line", "voltage": "230000", "cables": "6", "circuits": "2"}

// Simulator
{
  "code": "LINE-OSM-{id}",
  "osm_power": "line",
  "voltage": 230000,
  "type": "overhead",
  "circuits": 2,
  "cables": 6,
  "coordinates": [[lon, lat], ...]
}
```

### Substations
```json
// OSM
{"power": "substation", "substation": "transmission", "voltage": "230000;115000"}

// Simulator
{
  "code": "SUB-OSM-{id}",
  "osm_power": "substation",
  "substation_type": "transmission",
  "voltage": 230000,
  "voltages": [230000, 115000],
  "location": {"latitude": ..., "longitude": ...}
}
```

---

## Files

| File | Purpose |
|------|---------|
| `backend/power_lines_template.json` | Power line template with OSM tagging conventions |
| `backend/substations_template.json` | Substation template with OSM tagging conventions |
| `backend/convert_osm_to_simulator.py` | Converter script: OSM → Simulator format |
| `backend/fetch_korat_power_grid.py` | Fetch script for targeted OSM queries |
| `backend/data/korat/` | Converted OSM data for Korat area |

---

## Overpass Query Examples

### Fetch Single Way
```
[out:json];way(402761973);out tags geom;
```

### Fetch All Power Infrastructure in Bounding Box
```overpass
[out:json][timeout:120];
(
  way["power"="line"]({{bbox}});
  way["power"="cable"]({{bbox}});
  node["power"="substation"]({{bbox}});
  way["power"="substation"]({{bbox}});
  node["power"="tower"]({{bbox}});
  node["power"="pole"]({{bbox}});
);
out body geom;
>;
out skel qt;
```

Run via: `backend/fetch_korat_power_grid.py`
