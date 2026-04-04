# Thai Grid Map Viewer Guide

Interactive web-based map visualization for Thai distribution networks, similar to [Open Infrastructure Map](https://openinframap.org/).

![Map Viewer Example](https://via.placeholder.com/800x400?text=Thai+Grid+Map+Viewer+Screenshot)

---

## Overview

The GridTokenX Smart Meter Simulator now includes an interactive web map viewer for visualizing Thai electrical distribution networks. Features include:

- **Interactive Leaflet-based map** with OpenStreetMap base layer
- **Layer controls** for MV/LV networks, substations, and transformers
- **GeoJSON export** for integration with GIS tools
- **Real-time statistics** display
- **Popup information** for network elements
- **Drag-and-drop** file loading

---

## Quick Start

### 1. Generate GeoJSON Data

```bash
# Export Thai networks to GeoJSON
uv run python examples/export_thai_grid_geojson.py
```

This creates GeoJSON files in the `data/` directory:
- `bangkok_urban.geojson` - Bangkok urban network
- `central_thailand_rural.geojson` - Central Thailand rural feeder
- `combined_demo.geojson` - Combined network demo

### 2. Open Map Viewer

```bash
# Open in browser (macOS)
open static/grid_map_viewer.html

# Or open manually in any browser
# File path: static/grid_map_viewer.html
```

### 3. Load Network Data

The viewer will automatically load `static/data/thai_network.geojson` if available.

**Or drag-and-drop** any GeoJSON file onto the map.

---

## Map Viewer Features

### Layer Controls

Located in the bottom-right corner:

| Layer | Description | Color |
|-------|-------------|-------|
| **MV Network (22 kV)** | Medium voltage distribution lines | Orange (#ff6600) |
| **LV Network (0.4 kV)** | Low voltage distribution lines | Yellow (#ffcc00) |
| **Substations** | MV/LV substations and buses | Orange/Yellow circles |
| **Transformers** | Distribution transformers | Purple (#9933ff) |

Toggle layers on/off to focus on specific network components.

### Network Statistics

Top-right panel displays real-time statistics:
- Total buses
- Total lines
- Total transformers
- MV line count
- LV line count

### Interactive Popups

Click on any network element to view details:

**Lines:**
- Voltage level (kV)
- Length (km)
- Cable type
- In-service status

**Substations/Buses:**
- Voltage level (kV)
- Zone/district
- Name

**Transformers:**
- Capacity (kVA)
- Voltage ratio (HV/LV kV)
- Name

### Legend

Bottom-left corner shows map symbology reference.

---

## GeoJSON Export

### Python API

```python
from smart_meter_simulator.adapters.thai_grid_topology import ThaiGridBuilder
from smart_meter_simulator.adapters.geojson_exporter import NetworkGeoJSONExporter

# Create network
builder = ThaiGridBuilder(region=ThaiRegion.BANGKOK)
net = builder.build_urban_network(num_households=100)

# Export to GeoJSON
exporter = NetworkGeoJSONExporter()
geojson = exporter.to_geojson(net)

# Save to file
exporter.save_to_file(net, "my_network.geojson")

# Export as string
geojson_string = exporter.to_geojson_string(net)
```

### Export Options

```python
exporter = NetworkGeoJSONExporter(
    include_properties=True  # Include pandapower properties
)

geojson = exporter.to_geojson(
    net,
    include_buses=True,        # Include bus markers
    include_lines=True,        # Include line routes
    include_transformers=True, # Include transformer markers
    voltage_threshold_kv=1.0   # MV/LV threshold (default 1.0 kV)
)
```

### Layered Export

Export separate GeoJSON files for each layer:

```python
layers = exporter.create_layered_geojson(net)

# Access individual layers
mv_lines = layers['MV_lines']
lv_lines = layers['LV_lines']
substations = layers['substations']
transformers = layers['transformers']

# Save each layer separately
import json
for layer_name, geojson in layers.items():
    with open(f"{layer_name}.geojson", 'w') as f:
        json.dump(geojson, f, indent=2)
```

---

## GeoJSON Schema

The exported GeoJSON follows this structure:

```json
{
  "type": "FeatureCollection",
  "metadata": {
    "network_name": "Thai Distribution Network",
    "num_buses": 106,
    "num_lines": 104,
    "num_transformers": 1,
    "generator": "Thai Grid Topology - GridTokenX"
  },
  "features": [
    {
      "type": "Feature",
      "geometry": {
        "type": "Point",
        "coordinates": [100.6025, 13.8788]
      },
      "properties": {
        "name": "สถานีไฟฟ้าย่อย Bang Khen",
        "type": "substation",
        "voltage_level_kv": 22.0,
        "layer": "MV",
        "color": "#ff9933",
        "radius": 6,
        "zone": "Bangkok_MV"
      }
    },
    {
      "type": "Feature",
      "geometry": {
        "type": "LineString",
        "coordinates": [
          [100.6025, 13.8788],
          [100.6030, 13.8790]
        ]
      },
      "properties": {
        "name": "Line_0",
        "type": "line",
        "voltage_level_kv": 0.4,
        "layer": "LV",
        "length_km": 0.05,
        "std_type": "NAYY 4x50 SE",
        "color": "#ffcc00",
        "width": 2
      }
    }
  ]
}
```

### Feature Properties

| Property | Type | Description |
|----------|------|-------------|
| `name` | string | Element name |
| `type` | string | `line`, `substation`, `bus`, or `transformer` |
| `voltage_level_kv` | number | Voltage in kV |
| `layer` | string | `MV` or `LV` |
| `color` | string | Hex color code for rendering |
| `in_service` | boolean | Operational status |

**Line-specific:**
- `length_km`: Line length in kilometers
- `std_type`: Cable type standard

**Transformer-specific:**
- `sn_mva`: Rated power in MVA
- `vn_hv_kv`: High voltage side (kV)
- `vn_lv_kv`: Low voltage side (kV)

---

## Integration with Other Tools

### QGIS

1. Open QGIS
2. Drag-and-drop GeoJSON file
3. Style by `layer` or `voltage_level_kv` properties

### ArcGIS

```python
# Use ArcGIS Python API
from arcgis.gis import GIS
from arcgis.features import FeatureLayerCollection

# Add GeoJSON as feature layer
gis = GIS("https://www.arcgis.com", "username", "password")
feature_layer = gis.content.add({
    "title": "Thai Distribution Network",
    "type": "GeoJSON",
    "path": "my_network.geojson"
})
```

### Leaflet Web Map

```html
<script>
// Load GeoJSON directly
fetch('my_network.geojson')
  .then(response => response.json())
  .then(data => {
    L.geoJSON(data, {
      style: function(feature) {
        return {
          color: feature.properties.color,
          weight: feature.properties.width
        };
      },
      onEachFeature: function(feature, layer) {
        layer.bindPopup(feature.properties.name);
      }
    }).addTo(map);
  });
</script>
```

### Mapbox GL JS

```javascript
map.on('load', () => {
  map.addSource('thai-grid', {
    type: 'geojson',
    data: 'my_network.geojson'
  });
  
  // Add MV lines layer
  map.addLayer({
    id: 'mv-lines',
    type: 'line',
    source: 'thai-grid',
    filter: ['==', 'layer', 'MV'],
    paint: {
      'line-color': '#ff6600',
      'line-width': 3
    }
  });
});
```

---

## Customization

### Change Map Base Layer

Edit `static/grid_map_viewer.html`:

```javascript
// Replace OpenStreetMap with other tile providers
L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
  attribution: 'Tiles © Esri'
}).addTo(map);
```

### Custom Styling

Modify the `OIM_STYLE_MAP` in `geojson_exporter.py`:

```python
OIM_STYLE_MAP = {
    'line_mv': {
        'color': '#your_color',  # Change line color
        'width': 4,              # Change line width
        'opacity': 0.9           # Change opacity
    },
    'transformer': {
        'color': '#your_color',
        'radius': 8              # Change marker size
    }
}
```

### Add Custom Popup Content

Edit `createPopup()` in `grid_map_viewer.html`:

```javascript
function createPopup(feature) {
    let content = '<div class="popup-content">';
    
    // Add custom properties
    if (feature.properties.custom_field) {
        content += `<div>${feature.properties.custom_field}</div>`;
    }
    
    // ... existing code ...
    return content;
}
```

---

## API Endpoint (Future)

To serve GeoJSON via FastAPI endpoint:

```python
from fastapi import APIRouter
from smart_meter_simulator.adapters.geojson_exporter import NetworkGeoJSONExporter

router = APIRouter()

@router.get("/api/grid/geojson")
async def get_grid_geojson(network_id: str = "bangkok"):
    """Get network GeoJSON."""
    # Load or generate network
    builder = ThaiGridBuilder()
    net = builder.build_urban_network(num_households=100)
    
    # Export to GeoJSON
    exporter = NetworkGeoJSONExporter()
    geojson = exporter.to_geojson(net)
    
    return geojson
```

Then fetch from the map viewer:

```javascript
fetch('/api/grid/geojson?network_id=bangkok')
  .then(response => response.json())
  .then(data => loadGeoJSON(data));
```

---

## Troubleshooting

### No Features Displayed

**Problem:** GeoJSON loads but no features appear on map.

**Solutions:**
1. Check browser console for errors
2. Verify GeoJSON has valid coordinates: `features[].geometry.coordinates`
3. Ensure coordinates are in [longitude, latitude] format
4. Check layer visibility toggles

### Coordinates Wrong

**Problem:** Features appear in wrong location.

**Solutions:**
1. Verify coordinate order: GeoJSON uses [lon, lat], not [lat, lon]
2. Check if coordinates are in degrees (not meters or other units)
3. Ensure latitude is between -90 to 90, longitude -180 to 180

### Performance Issues

**Problem:** Map is slow with large networks.

**Solutions:**
1. Reduce number of features (simplify network)
2. Use layer filtering to show only visible layers
3. Enable clustering for dense bus markers
4. Consider server-side tiling for very large networks

### JSON Serialization Error

**Problem:** `Object of type NAType is not JSON serializable`

**Solution:** Update to latest version with `PandasNAEncoder` or clean NA values:

```python
# Clean NA values before export
net.bus = net.bus.fillna(None)
net.line = net.line.fillna(None)
```

---

## Examples

### Bangkok Urban Network

```bash
uv run python examples/export_thai_grid_geojson.py
# Opens: data/bangkok_urban.geojson

# Features:
# - 206 buses
# - 204 lines
# - 1 transformer
# - Underground cables (NAYY)
```

### Central Thailand Rural Feeder

```bash
# File: data/central_thailand_rural.geojson

# Features:
# - 111 buses
# - 105 lines
# - 5 transformers
# - Overhead AAC cables
# - 5 villages along 25 km feeder
```

### Custom Network from Coordinates

```python
from smart_meter_simulator.adapters.thai_grid_topology import ThaiGridBuilder

builder = ThaiGridBuilder()

# Create substation at specific location
mv_bus = builder.create_thai_substation(
    location_name="ลำลูกกา",
    province="Pathum Thani",
    latitude=13.9425,
    longitude=100.7142
)

# Build custom network
# ... add feeders, transformers, etc.

# Export
exporter = NetworkGeoJSONExporter()
exporter.save_to_file(net, "custom_network.geojson")
```

---

## References

- [GeoJSON Specification](https://geojson.org/)
- [Leaflet Documentation](https://leafletjs.com/)
- [Open Infrastructure Map](https://openinframap.org/)
- [pandapower Geo Documentation](https://pandapower.readthedocs.io/)

---

## License

Part of the GridTokenX Ecosystem - Proprietary

---

_Maintained by the GridTokenX Engineering Team._
