#!/usr/bin/env python3
"""
Thai Grid Topology Examples

Demonstrates how to create realistic Thai distribution networks
for the GridTokenX Smart Meter Simulator.

Examples:
1. Bangkok Urban Network (MEA - Metropolitan Electricity Authority)
2. Central Thailand Rural Network (PEA - Provincial Electricity Authority)
3. Commercial District Network (High-density urban)
4. Custom Network with Specific Locations

Usage:
    python examples/thai_grid_examples.py
    
    Or import in your code:
    from examples.thai_grid_examples import create_bangkok_network
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

try:
    import pandapower as pp
    import pandapower.plotting as pp_plotting
    import matplotlib.pyplot as plt
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    print("Note: matplotlib not available. Skipping visualization.")

from smart_meter_simulator.adapters.thai_grid_topology import (
    ThaiGridBuilder,
    ThaiRegion,
    TransformerType,
    create_bangkok_test_network,
    create_central_thailand_test_network,
)


def example_1_bangkok_urban():
    """
    Example 1: Bangkok Urban Residential Network
    
    Characteristics:
    - Underground cables (XLPE MV, NAYY LV)
    - 200 households
    - 630 kVA transformer
    - MEA service area (Bangkok Metro)
    """
    print("\n" + "="*60)
    print("Example 1: Bangkok Urban Residential Network")
    print("="*60)
    
    builder = ThaiGridBuilder(region=ThaiRegion.BANGKOK)
    
    net = builder.build_urban_network(
        num_households=200,
        transformer_capacity_kva=630,
        underground=True,
        province="Bangkok",
        district="Bang Khen",
        latitude=13.8788,  # Bang Khen area
        longitude=100.6025
    )
    
    # Print network summary
    summary = builder.get_network_summary()
    print(f"\nNetwork: {summary['name']}")
    print(f"Region: {summary['region']}")
    print(f"Buses: {summary['buses']}")
    print(f"Lines: {summary['lines']}")
    print(f"Transformers: {summary['distribution_transformers']}")
    print(f"Total Capacity: {summary['total_transformer_capacity_kva']:.0f} kVA")
    print(f"Voltage Levels: MV={summary['mv_voltage_kv']} kV, LV={summary['lv_voltage_kv']} kV")
    
    if summary.get('cable_types'):
        print("\nCable Types:")
        for cable_type, count in summary['cable_types'].items():
            print(f"  - {cable_type}: {count} lines")
    
    # Visualize if matplotlib available
    if MATPLOTLIB_AVAILABLE:
        ax = pp_plotting.simple_plot(net, show_plot=False)
        if isinstance(ax, tuple):
            fig, ax = ax
        else:
            fig = ax.get_figure()
        ax.set_title("Bangkok Urban Network (MEA)")
        plt.savefig("data/bangkok_urban_network.png", dpi=150, bbox_inches='tight')
        print("\n✓ Saved visualization: data/bangkok_urban_network.png")
    
    return net, builder


def example_2_central_thailand_rural():
    """
    Example 2: Central Thailand Rural Feeder
    
    Characteristics:
    - Overhead AAC cables (MV and LV)
    - 5 villages along 25 km feeder
    - 20 households per village
    - 160-315 kVA transformers per village
    - PEA service area (Provincial)
    """
    print("\n" + "="*60)
    print("Example 2: Central Thailand Rural Feeder (Ayutthaya)")
    print("="*60)
    
    builder = ThaiGridBuilder(region=ThaiRegion.CENTRAL)
    
    net = builder.build_rural_feeder(
        num_villages=5,
        households_per_village=20,
        province="Ayutthaya",
        latitude=14.3532,  # Ayutthaya area
        longitude=100.5775
    )
    
    # Print network summary
    summary = builder.get_network_summary()
    print(f"\nNetwork: {summary['name']}")
    print(f"Region: {summary['region']}")
    print(f"Buses: {summary['buses']}")
    print(f"Lines: {summary['lines']}")
    print(f"Transformers: {summary['distribution_transformers']}")
    print(f"Total Capacity: {summary['total_transformer_capacity_kva']:.0f} kVA")
    
    if summary.get('cable_types'):
        print("\nCable Types:")
        for cable_type, count in summary['cable_types'].items():
            print(f"  - {cable_type}: {count} lines")
    
    # Visualize
    if MATPLOTLIB_AVAILABLE:
        ax = pp_plotting.simple_plot(net, show_plot=False)
        if isinstance(ax, tuple):
            fig, ax = ax
        else:
            fig = ax.get_figure()
        ax.set_title("Central Thailand Rural Feeder (PEA - Ayutthaya)")
        plt.savefig("data/central_thailand_rural.png", dpi=150, bbox_inches='tight')
        print("\n✓ Saved visualization: data/central_thailand_rural.png")
    
    return net, builder


def example_3_commercial_district():
    """
    Example 3: Bangkok Commercial District
    
    Characteristics:
    - High-density commercial loads
    - 800 kVA transformer
    - Underground cables
    - Pathum Wan area (shopping district)
    """
    print("\n" + "="*60)
    print("Example 3: Bangkok Commercial District (Pathum Wan)")
    print("="*60)
    
    builder = ThaiGridBuilder(region=ThaiRegion.BANGKOK)
    
    net = builder.build_commercial_network(
        num_shops=50,
        transformer_capacity_kva=800,
        province="Bangkok",
        district="Pathum Wan",
        latitude=13.7465,  # Siam/Pathum Wan area
        longitude=100.5347
    )
    
    # Print network summary
    summary = builder.get_network_summary()
    print(f"\nNetwork: {summary['name']}")
    print(f"Region: {summary['region']}")
    print(f"Buses: {summary['buses']}")
    print(f"Lines: {summary['lines']}")
    print(f"Transformers: {summary['distribution_transformers']}")
    print(f"Total Capacity: {summary['total_transformer_capacity_kva']:.0f} kVA")
    
    # Visualize
    if MATPLOTLIB_AVAILABLE:
        ax = pp_plotting.simple_plot(net, show_plot=False)
        if isinstance(ax, tuple):
            fig, ax = ax
        else:
            fig = ax.get_figure()
        ax.set_title("Bangkok Commercial District (Pathum Wan)")
        plt.savefig("data/bangkok_commercial.png", dpi=150, bbox_inches='tight')
        print("\n✓ Saved visualization: data/bangkok_commercial.png")
    
    return net, builder


def example_4_custom_location():
    """
    Example 4: Custom Location (Lam Lukka, Pathum Thani)
    
    Demonstrates building a network for a specific location
    with custom parameters.
    """
    print("\n" + "="*60)
    print("Example 4: Custom Location (Lam Lukka, Pathum Thani)")
    print("="*60)
    
    builder = ThaiGridBuilder(region=ThaiRegion.CENTRAL)
    
    # Create substation at specific location
    mv_bus_idx = builder.create_thai_substation(
        location_name="ลำลูกกา",
        province="Pathum Thani",
        latitude=13.9425,  # Lam Lukka coordinates
        longitude=100.7142
    )
    
    # Build custom LV network
    # Create LV bus
    lv_bus_id = "LV_LamLukka"
    from smart_meter_simulator.adapters.topology_builder import BusConfig, VoltageLevel
    
    builder.add_bus(BusConfig(
        bus_id=lv_bus_id,
        voltage_level=VoltageLevel.LV,
        vn_kv=0.4,
        name="Bus LV - ลำลูกกา",
        zone="PathumThani_LV",
        geo_data={'latitude': 13.9420, 'longitude': 100.7142}
    ))
    
    # Add transformer
    builder.create_distribution_transformer(
        mv_bus_id="MV_SUB_ลำลูกกา",
        lv_bus_id=lv_bus_id,
        capacity_kva=500,
        location_name="ลำลูกกา"
    )
    
    # Add residential feeders
    for feeder_idx in range(3):
        feeder_houses = 30
        builder.add_feeder(
            parent_bus_id=lv_bus_id,
            feeder_name=f"LamLukka_F{feeder_idx}",
            num_buses=feeder_houses,
            voltage_kv=0.4,
            line_length_km=0.03,
            zone_id=f"PathumThani_F{feeder_idx}"
        )
    
    # Print summary
    summary = builder.get_network_summary()
    print(f"\nNetwork: {summary['name']}")
    print(f"Buses: {summary['buses']}")
    print(f"Lines: {summary['lines']}")
    print(f"Transformers: {summary['distribution_transformers']}")
    print(f"Total Capacity: {summary['total_transformer_capacity_kva']:.0f} kVA")
    
    return builder.net, builder


def example_5_quick_test():
    """
    Example 5: Quick Test Networks
    
    Convenience functions for rapid prototyping.
    """
    print("\n" + "="*60)
    print("Example 5: Quick Test Networks")
    print("="*60)
    
    # Bangkok test network
    print("\nCreating Bangkok test network...")
    net_bkk = create_bangkok_test_network(num_meters=50)
    print(f"✓ Bangkok: {len(net_bkk.bus)} buses, {len(net_bkk.line)} lines")
    
    # Central Thailand test network
    print("\nCreating Central Thailand test network...")
    net_central = create_central_thailand_test_network(num_villages=3)
    print(f"✓ Central: {len(net_central.bus)} buses, {len(net_central.line)} lines")
    
    return net_bkk, net_central


def run_power_flow(net, network_name: str = "Network"):
    """
    Run power flow analysis on the network.
    
    Args:
        net: Pandapower network
        network_name: Network identifier for output
    """
    print(f"\nRunning power flow for: {network_name}")
    
    try:
        pp.runpp(net)
        
        # Check voltage profile
        if len(net.res_bus) > 0:
            min_vm = net.res_bus['vm_pu'].min()
            max_vm = net.res_bus['vm_pu'].max()
            print(f"  Voltage range: {min_vm:.4f} - {max_vm:.4f} p.u.")
            
            # Check for voltage violations (Thai standard: ±5%)
            violations = ((net.res_bus['vm_pu'] < 0.95) | (net.res_bus['vm_pu'] > 1.05)).sum()
            if violations > 0:
                print(f"  ⚠️  Voltage violations: {violations} buses outside ±5%")
            else:
                print(f"  ✓ Voltage within limits (±5%)")
        
        # Check line loading
        if len(net.res_line) > 0:
            max_loading = (net.res_line['loading_percent'].max() 
                          if 'loading_percent' in net.res_line.columns else 0)
            print(f"  Max line loading: {max_loading:.1f}%")
        
        # Check transformer loading
        if len(net.res_trafo) > 0:
            max_trafo_loading = (net.res_trafo['loading_percent'].max()
                                if 'loading_percent' in net.res_trafo.columns else 0)
            print(f"  Max transformer loading: {max_trafo_loading:.1f}%")
        
    except Exception as e:
        print(f"  ⚠️  Power flow failed: {e}")


def main():
    """Run all examples."""
    print("\n" + "="*60)
    print("Thai Grid Topology Examples")
    print("GridTokenX Smart Meter Simulator")
    print("="*60)
    
    # Ensure data directory exists
    data_dir = Path(__file__).parent.parent / "data"
    data_dir.mkdir(exist_ok=True)
    
    # Run examples
    examples = [
        ("Bangkok Urban", example_1_bangkok_urban),
        ("Central Thailand Rural", example_2_central_thailand_rural),
        ("Bangkok Commercial", example_3_commercial_district),
        ("Custom Location", example_4_custom_location),
        ("Quick Test", example_5_quick_test),
    ]
    
    results = []
    for name, example_func in examples:
        try:
            net, builder = example_func()
            results.append((name, net, builder))
        except Exception as e:
            print(f"\n❌ {name} failed: {e}")
            import traceback
            traceback.print_exc()
    
    # Run power flow on successful examples
    print("\n" + "="*60)
    print("Power Flow Analysis")
    print("="*60)
    
    for name, net, _ in results:
        run_power_flow(net, name)
    
    # Summary
    print("\n" + "="*60)
    print("Summary")
    print("="*60)
    print(f"\nSuccessfully created {len(results)} networks:")
    for name, net, _ in results:
        print(f"  ✓ {name}: {len(net.bus)} buses, {len(net.line)} lines, {len(net.trafo)} transformers")
    
    if MATPLOTLIB_AVAILABLE:
        print(f"\nVisualizations saved to: {data_dir}/")
    
    print("\n" + "="*60)


if __name__ == "__main__":
    main()
