# Thai Infrastructure Map - Quick Start Guide

## 🗺️ Open the Map

```bash
# Method 1: Using open command (macOS)
open static/thai_infrastructure_map.html

# Method 2: Double-click the file
# Navigate to: static/thai_infrastructure_map.html

# Method 3: Drag to browser
# Drag the file to Chrome, Firefox, Safari, or Edge
```

## 📊 Features

### Sidebar Controls (Left Panel)

**Network Statistics:**
- Real-time counts of buses, lines, substations, transformers

**Voltage Layers:**
- ⚡ MV 500 kV (Red) - Transmission
- ⚡ MV 230 kV (Orange) - Transmission  
- ⚡ MV 115 kV (Yellow) - Sub-transmission
- ⚡ MV 22 kV (Orange) - Distribution
- ⚡ LV 0.4 kV (Yellow) - LV Distribution
- 🏢 Substations (Purple)
- 🔌 Transformers (Blue)

**Power Generation:**
- ☀️ Solar Farms
- 💨 Wind Farms
- 💧 Hydro Plants

### Map Controls

- **Base Maps:** Click layers icon (top-right) to switch between:
  - OpenStreetMap
  - Satellite Imagery
  - Dark Matter (dark theme)
  
- **Zoom:** Use mouse wheel or +/- buttons (bottom-right)
- **Pan:** Click and drag the map
- **Identify:** Click on any element for details popup

### Load Your Data

1. **Drag & Drop:** Drag any GeoJSON file onto the map
2. **Click Upload:** Click the "Data" section in sidebar
3. **Auto-load:** Place file at `static/data/thai_network.geojson`

## 🚀 Generate Sample Data

```bash
# Export Thai grid networks to GeoJSON
uv run python examples/export_thai_grid_geojson.py

# Then refresh the map - it will auto-load!
```

## 🎨 Voltage Color Scheme

| Voltage | Color | Usage |
|---------|-------|-------|
| 500 kV | 🔴 Red | EGAT Transmission |
| 230 kV | 🟠 Orange | EGAT Transmission |
| 115 kV | 🟡 Yellow | Sub-transmission |
| 22 kV | 🟠 Orange | MEA/PEA Distribution |
| 0.4 kV | 🟡 Yellow | LV Distribution |
| Substation | 🟣 Purple | MV/LV substations |
| Transformer | 🔵 Blue | Distribution transformers |

## 📍 Navigation

- **Zoom Level:** Displayed bottom-right
- **Coordinates:** Real-time lat/lon display
- **Fit to Data:** Automatically zooms to network bounds on load

## 🔧 Customization

### Change Default Location

Edit `static/thai_infrastructure_map.html`, line ~417:

```javascript
const map = L.map('map', {
    center: [13.7563, 100.5018],  // Change to your location
    zoom: 12,                      // Change zoom level
    zoomControl: false
});
```

### Add Custom Base Maps

Add more tile layers in the map script:

```javascript
const tileLayers = {
    'OpenStreetMap': L.tileLayer('...'),
    'Satellite': L.tileLayer('...'),
    'Dark Matter': L.tileLayer('...'),
    'Your Custom Map': L.tileLayer('YOUR_TILE_URL')
};
```

## 📥 Export Data

Click **Export** in the header to download current view as GeoJSON.

## 🐛 Troubleshooting

**Map doesn't load:**
- Ensure JavaScript is enabled
- Check browser console for errors
- Try a different browser

**No features displayed:**
- Check if GeoJSON file exists at `static/data/thai_network.geojson`
- Verify GeoJSON format is valid
- Toggle layers on/off in sidebar

**Features in wrong location:**
- Check coordinate order in GeoJSON (should be [lon, lat])
- Verify coordinates are in decimal degrees

## 📚 Related Files

| File | Purpose |
|------|---------|
| `static/thai_infrastructure_map.html` | Main map viewer |
| `static/grid_map_viewer.html` | Simple viewer (alternative) |
| `src/smart_meter_simulator/adapters/geojson_exporter.py` | GeoJSON export |
| `examples/export_thai_grid_geojson.py` | Export example script |
| `data/*.geojson` | Exported network data |

## 💡 Tips

1. **Performance:** For large networks, toggle off LV layer to improve rendering
2. **Focus:** Use layer checkboxes to isolate specific voltage levels
3. **Analysis:** Click elements to view detailed properties
4. **Presentation:** Use "Dark Matter" base map for demos/presentations
5. **Collaboration:** Share GeoJSON files with team members

---

**Part of the GridTokenX Smart Meter Simulator**

For more information, see `docs/GRID_MAP_VIEWER.md`
