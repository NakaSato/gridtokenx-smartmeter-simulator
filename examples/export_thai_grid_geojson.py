#!/usr/bin/env python3
"""
Thai Grid GeoJSON Export Example

Exports Thai distribution networks to GeoJSON format for visualization
in the web map viewer (similar to Open Infrastructure Map).

Usage:
    python examples/export_thai_grid_geojson.py
    
    Then open: static/grid_map_viewer.html in a browser
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from smart_meter_simulator.adapters.thai_grid_topology import (
    ThaiGridBuilder,
    ThaiRegion,
    create_bangkok_test_network,
)
from smart_meter_simulator.adapters.geojson_exporter import (
    NetworkGeoJSONExporter,
    export_network_to_geojson,
)


def export_bangkok_urban():
    """Export Bangkok urban network to GeoJSON."""
    print("\n" + "="*60)
    print("Exporting Bangkok Urban Network")
    print("="*60)
    
    # Create network
    builder = ThaiGridBuilder(region=ThaiRegion.BANGKOK)
    net = builder.build_urban_network(
        num_households=100,
        transformer_capacity_kva=630,
        province="Bangkok",
        district="Bang Khen",
        latitude=13.8788,
        longitude=100.6025
    )
    
    # Export to GeoJSON
    exporter = NetworkGeoJSONExporter(include_properties=True)
    
    # Save combined GeoJSON
    output_file = Path(__file__).parent.parent / "data" / "bangkok_urban.geojson"
    exporter.save_to_file(net, str(output_file))
    print(f"✓ Saved: {output_file}")
    
    # Also create layered export
    layers = exporter.create_layered_geojson(net)
    layers_dir = Path(__file__).parent.parent / "data" / "layers"
    layers_dir.mkdir(exist_ok=True)
    
    for layer_name, geojson in layers.items():
        layer_file = layers_dir / f"{layer_name}.geojson"
        with open(layer_file, 'w') as f:
            import json
            json.dump(geojson, f, indent=2)
        print(f"✓ Saved layer: {layer_file}")
    
    # Print statistics
    stats = builder.get_network_summary()
    print(f"\nNetwork Statistics:")
    print(f"  Buses: {stats['buses']}")
    print(f"  Lines: {stats['lines']}")
    print(f"  Transformers: {stats['distribution_transformers']}")
    print(f"  Total Capacity: {stats['total_transformer_capacity_kva']:.0f} kVA")
    
    return str(output_file)


def export_central_thailand_rural():
    """Export Central Thailand rural network to GeoJSON."""
    print("\n" + "="*60)
    print("Exporting Central Thailand Rural Network")
    print("="*60)
    
    # Create network
    builder = ThaiGridBuilder(region=ThaiRegion.CENTRAL)
    net = builder.build_rural_feeder(
        num_villages=5,
        households_per_village=20,
        province="Ayutthaya",
        latitude=14.3532,
        longitude=100.5775
    )
    
    # Export to GeoJSON
    exporter = NetworkGeoJSONExporter(include_properties=True)
    
    output_file = Path(__file__).parent.parent / "data" / "central_thailand_rural.geojson"
    exporter.save_to_file(net, str(output_file))
    print(f"✓ Saved: {output_file}")
    
    # Print statistics
    stats = builder.get_network_summary()
    print(f"\nNetwork Statistics:")
    print(f"  Buses: {stats['buses']}")
    print(f"  Lines: {stats['lines']}")
    print(f"  Transformers: {stats['distribution_transformers']}")
    print(f"  Total Capacity: {stats['total_transformer_capacity_kva']:.0f} kVA")
    
    return str(output_file)


def export_combined_network():
    """Export a combined network for demonstration."""
    print("\n" + "="*60)
    print("Exporting Combined Network (Bangkok + Rural)")
    print("="*60)
    
    # Create Bangkok network
    builder_bkk = ThaiGridBuilder(region=ThaiRegion.BANGKOK)
    net_bkk = builder_bkk.build_urban_network(
        num_households=50,
        province="Bangkok",
        district="Bang Khen",
        latitude=13.8788,
        longitude=100.6025
    )
    
    # Create rural network
    builder_rural = ThaiGridBuilder(region=ThaiRegion.CENTRAL)
    net_rural = builder_rural.build_rural_feeder(
        num_villages=3,
        households_per_village=15,
        province="Ayutthaya",
        latitude=14.3532,
        longitude=100.5775
    )
    
    # Merge networks (create combined GeoJSON)
    exporter = NetworkGeoJSONExporter(include_properties=True)
    
    # Export separately
    data_dir = Path(__file__).parent.parent / "data"
    data_dir.mkdir(exist_ok=True)
    
    bkk_file = data_dir / "demo_bangkok.geojson"
    rural_file = data_dir / "demo_rural.geojson"
    
    exporter.save_to_file(net_bkk, str(bkk_file))
    exporter.save_to_file(net_rural, str(rural_file))
    
    print(f"✓ Saved Bangkok: {bkk_file}")
    print(f"✓ Saved Rural: {rural_file}")
    
    # Create combined GeoJSON manually
    import json
    
    with open(bkk_file, 'r') as f:
        bkk_geojson = json.load(f)
    
    with open(rural_file, 'r') as f:
        rural_geojson = json.load(f)
    
    # Combine features
    combined = {
        'type': 'FeatureCollection',
        'features': bkk_geojson['features'] + rural_geojson['features'],
        'metadata': {
            'name': 'Combined Demo Network',
            'bangkok_features': len(bkk_geojson['features']),
            'rural_features': len(rural_geojson['features']),
            'total_features': len(bkk_geojson['features']) + len(rural_geojson['features'])
        }
    }
    
    combined_file = data_dir / "combined_demo.geojson"
    with open(combined_file, 'w') as f:
        json.dump(combined, f, indent=2)
    
    print(f"✓ Saved Combined: {combined_file}")
    
    return str(combined_file)


def create_sample_for_viewer():
    """Create a sample GeoJSON file for the map viewer."""
    print("\n" + "="*60)
    print("Creating Sample for Map Viewer")
    print("="*60)
    
    # Create a nice network centered in Bangkok
    builder = ThaiGridBuilder(region=ThaiRegion.BANGKOK)
    net = builder.build_urban_network(
        num_households=80,
        transformer_capacity_kva=500,
        province="Bangkok",
        district="Lat Phrao",
        latitude=13.8050,
        longitude=100.6140
    )
    
    exporter = NetworkGeoJSONExporter(include_properties=True)
    
    # Save to static folder for easy access
    static_dir = Path(__file__).parent.parent / "static" / "data"
    static_dir.mkdir(exist_ok=True, parents=True)
    
    output_file = static_dir / "thai_network.geojson"
    exporter.save_to_file(net, str(output_file))
    
    print(f"✓ Saved: {output_file}")
    print(f"\nView in browser: static/grid_map_viewer.html")
    
    # Print GeoJSON preview
    with open(output_file, 'r') as f:
        import json
        data = json.load(f)
    
    print(f"\nGeoJSON Preview:")
    print(f"  Type: {data['type']}")
    print(f"  Features: {len(data['features'])}")
    print(f"  Metadata: {data.get('metadata', {})}")
    
    return str(output_file)


def main():
    """Run all exports."""
    print("\n" + "="*60)
    print("Thai Grid GeoJSON Export")
    print("GridTokenX Smart Meter Simulator")
    print("="*60)
    
    # Ensure data directory exists
    data_dir = Path(__file__).parent.parent / "data"
    data_dir.mkdir(exist_ok=True)
    
    # Run exports
    exports = [
        ("Bangkok Urban", export_bangkok_urban),
        ("Central Thailand Rural", export_central_thailand_rural),
        ("Combined Network", export_combined_network),
        ("Sample for Viewer", create_sample_for_viewer),
    ]
    
    results = []
    for name, export_func in exports:
        try:
            filepath = export_func()
            results.append((name, filepath))
        except Exception as e:
            print(f"\n❌ {name} failed: {e}")
            import traceback
            traceback.print_exc()
    
    # Summary
    print("\n" + "="*60)
    print("Export Summary")
    print("="*60)
    print(f"\nSuccessfully exported {len(results)} networks:")
    for name, filepath in results:
        print(f"  ✓ {name}: {filepath}")
    
    print("\n" + "="*60)
    print("Next Steps:")
    print("="*60)
    print("""
1. Open the map viewer in your browser:
   
   open static/grid_map_viewer.html
   
   Or drag-and-drop any exported GeoJSON file onto the map.

2. View specific networks:
   - data/bangkok_urban.geojson
   - data/central_thailand_rural.geojson
   - data/combined_demo.geojson

3. Integrate with web applications:
   - Use the GeoJSON files directly with Leaflet
   - Import into QGIS or ArcGIS
   - Display on Open Infrastructure Map style viewers
    """)
    
    print("="*60)


if __name__ == "__main__":
    main()
