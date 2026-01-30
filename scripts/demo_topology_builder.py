#!/usr/bin/env python3
"""
Topology Builder - Demonstration Script

Shows how to use TopologyBuilder to create various network topologies.
Run with: python scripts/demo_topology_builder.py
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app.adapters.topology_builder import TopologyBuilder, VoltageLevel, NetworkTopology

try:
    import pandapower as pp
    PANDAPOWER_AVAILABLE = True
except ImportError:
    PANDAPOWER_AVAILABLE = False
    print("❌ pandapower not installed. Install with: pip install pandapower>=2.14.0")
    sys.exit(1)


def demo_radial_network():
    """Demonstrate simple radial network creation."""
    print("\n" + "="*60)
    print("Demo 1: Simple Radial Network")
    print("="*60)
    
    builder = TopologyBuilder(network_name="Radial LV Network")
    net = builder.build_radial_network(
        num_buses=10,
        voltage_kv=0.4,
        line_length_km=0.1,
        add_grid=True
    )
    
    summary = builder.get_network_summary()
    print(f"\nNetwork: {summary['name']}")
    print(f"  Buses: {summary['buses']}")
    print(f"  Lines: {summary['lines']}")
    print(f"  External Grids: {summary['external_grids']}")
    print(f"  Voltage Levels: {summary['voltage_levels']} kV")
    
    # Display bus table
    print("\nBus Table:")
    print(net.bus[['name', 'vn_kv', 'zone']].to_string(index=True))
    
    return builder, net


def demo_feeder_network():
    """Demonstrate multi-feeder network creation."""
    print("\n" + "="*60)
    print("Demo 2: Multi-Feeder Network")
    print("="*60)
    
    builder = TopologyBuilder(network_name="3-Feeder LV Network")
    net = builder.build_feeder_network(
        num_feeders=3,
        buses_per_feeder=5,
        voltage_kv=0.4,
        line_length_km=0.1,
        substation_bus_id="Substation"
    )
    
    summary = builder.get_network_summary()
    print(f"\nNetwork: {summary['name']}")
    print(f"  Buses: {summary['buses']}")
    print(f"  Lines: {summary['lines']}")
    print(f"  External Grids: {summary['external_grids']}")
    print(f"  Voltage Levels: {summary['voltage_levels']} kV")
    
    # Display buses by zone
    print("\nBuses by Zone:")
    for zone in net.bus['zone'].unique():
        buses_in_zone = net.bus[net.bus['zone'] == zone]
        print(f"  {zone}: {len(buses_in_zone)} buses")
    
    return builder, net


def demo_multi_voltage_network():
    """Demonstrate multi-voltage level network with transformers."""
    print("\n" + "="*60)
    print("Demo 3: Multi-Voltage Network (HV/MV/LV)")
    print("="*60)
    
    builder = TopologyBuilder(network_name="Multi-Voltage Distribution Network")
    net = builder.build_multi_voltage_network(
        hv_buses=1,
        mv_buses=2,
        lv_buses_per_mv=3,
        hv_voltage_kv=110.0,
        mv_voltage_kv=10.0,
        lv_voltage_kv=0.4
    )
    
    summary = builder.get_network_summary()
    print(f"\nNetwork: {summary['name']}")
    print(f"  Buses: {summary['buses']}")
    print(f"  Lines: {summary['lines']}")
    print(f"  Transformers: {summary['transformers']}")
    print(f"  External Grids: {summary['external_grids']}")
    print(f"  Voltage Levels: {summary['voltage_levels']} kV")
    
    # Display voltage level distribution
    print("\nVoltage Level Distribution:")
    for vn_kv in summary['voltage_levels']:
        buses_at_level = net.bus[net.bus['vn_kv'] == vn_kv]
        level_name = "HV" if vn_kv >= 100 else ("MV" if vn_kv >= 1 else "LV")
        print(f"  {level_name} ({vn_kv} kV): {len(buses_at_level)} buses")
    
    # Display transformer connections
    print("\nTransformer Connections:")
    for idx, trafo in net.trafo.iterrows():
        hv_bus = net.bus.loc[trafo['hv_bus'], 'name']
        lv_bus = net.bus.loc[trafo['lv_bus'], 'name']
        hv_voltage = net.bus.loc[trafo['hv_bus'], 'vn_kv']
        lv_voltage = net.bus.loc[trafo['lv_bus'], 'vn_kv']
        print(f"  {trafo['name']}: {hv_bus} ({hv_voltage}kV) → {lv_bus} ({lv_voltage}kV)")
    
    return builder, net


def demo_custom_topology():
    """Demonstrate custom topology building with manual configuration."""
    print("\n" + "="*60)
    print("Demo 4: Custom Topology (Manual Configuration)")
    print("="*60)
    
    from app.adapters.topology_builder import BusConfig, LineConfig, TransformerConfig
    
    builder = TopologyBuilder(network_name="Custom Network")
    builder.create_network()
    
    # Create a small custom network: MV substation → 2 LV networks
    
    # MV substation bus
    builder.add_bus(BusConfig(
        bus_id="MV_Sub",
        voltage_level=VoltageLevel.MV,
        vn_kv=10.0,
        name="MV Substation",
        zone="Substation"
    ))
    builder.add_external_grid("MV_Sub", vm_pu=1.0)
    
    # Two LV networks
    for network_id in [1, 2]:
        # LV head bus
        lv_head_id = f"LV_Head_{network_id}"
        builder.add_bus(BusConfig(
            bus_id=lv_head_id,
            voltage_level=VoltageLevel.LV,
            vn_kv=0.4,
            name=f"LV Head {network_id}",
            zone=f"LV_Network_{network_id}"
        ))
        
        # Add transformer
        builder.add_transformer(TransformerConfig(
            hv_bus_id="MV_Sub",
            lv_bus_id=lv_head_id,
            sn_mva=0.63,  # 630 kVA
            vn_hv_kv=10.0,
            vn_lv_kv=0.4,
            name=f"Trafo_LV{network_id}"
        ))
        
        # Add 3 LV buses downstream
        for i in range(3):
            lv_bus_id = f"LV{network_id}_Bus_{i}"
            builder.add_bus(BusConfig(
                bus_id=lv_bus_id,
                voltage_level=VoltageLevel.LV,
                vn_kv=0.4,
                name=f"LV {network_id}-{i}",
                zone=f"LV_Network_{network_id}"
            ))
            
            # Connect to previous bus
            from_bus = lv_head_id if i == 0 else f"LV{network_id}_Bus_{i-1}"
            builder.add_line(LineConfig(
                from_bus_id=from_bus,
                to_bus_id=lv_bus_id,
                length_km=0.05,
                std_type="NAYY 4x50 SE",
                name=f"LV{network_id}_Line_{i}"
            ))
    
    summary = builder.get_network_summary()
    print(f"\nNetwork: {summary['name']}")
    print(f"  Buses: {summary['buses']}")
    print(f"  Lines: {summary['lines']}")
    print(f"  Transformers: {summary['transformers']}")
    print(f"  External Grids: {summary['external_grids']}")
    print(f"  Voltage Levels: {summary['voltage_levels']} kV")
    
    print("\nBus Mapping:")
    for bus_id, bus_idx in builder.bus_map.items():
        vn_kv = builder.net.bus.loc[bus_idx, 'vn_kv']
        print(f"  {bus_id} → Bus {bus_idx} ({vn_kv} kV)")
    
    return builder, builder.net


def main():
    """Run all topology builder demonstrations."""
    print("="*60)
    print("Topology Builder - Demonstration")
    print("="*60)
    print("\nThis script demonstrates various network topologies that can")
    print("be created using the TopologyBuilder class.")
    
    demos = [
        demo_radial_network,
        demo_feeder_network,
        demo_multi_voltage_network,
        demo_custom_topology,
    ]
    
    results = []
    for demo_func in demos:
        try:
            builder, net = demo_func()
            results.append((demo_func.__name__, builder, net, "✅ Success"))
        except Exception as e:
            print(f"\n❌ Error in {demo_func.__name__}: {e}")
            results.append((demo_func.__name__, None, None, f"❌ Error: {e}"))
    
    # Summary
    print("\n" + "="*60)
    print("Summary")
    print("="*60)
    for name, builder, net, status in results:
        print(f"{name}: {status}")
        if builder and net:
            summary = builder.get_network_summary()
            print(f"  → {summary['buses']} buses, {summary['lines']} lines, "
                  f"{summary['transformers']} transformers")
    
    print("\n✅ All demonstrations complete!")
    print("\nNext steps:")
    print("  1. Integrate TopologyBuilder with PandapowerAdapter")
    print("  2. Add meter placement logic (assign meters to buses)")
    print("  3. Create tests for TopologyBuilder")


if __name__ == "__main__":
    main()
