import argparse
from pathlib import Path
import pandapower as pp
import pandapower.plotting as pp_plot
import matplotlib.pyplot as plt
import pandas as pd

import pandas as pd

import matplotlib.cm as cm
import matplotlib.colors as mcolors

from smart_meter_simulator.core.topology_factory import load_glm_core_topology
from plot_bus_network import electrical_positions, resolve_symbol_overlaps, rooted_tree

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--glm", type=Path, default=Path("src/smart_meter_simulator/data/grids/grid_bus_network.glm"))
    parser.add_argument("--out-dir", type=Path, default=Path("artifacts"))
    args = parser.parse_args()

    args.out_dir.mkdir(parents=True, exist_ok=True)

    print(f"Loading topology from {args.glm}...")
    topology = load_glm_core_topology(args.glm)
    
    print("Building Pandapower network...")
    net = pp.create_empty_network()
    
    # Create buses
    bus_map = {}
    for bus in topology.buses:
        # Standardize voltage to 0.4 kV
        bus_idx = pp.create_bus(net, name=bus.name, vn_kv=0.4, type="b")
        bus_map[bus.name] = bus_idx
        
    # Create lines
    for line in topology.lines:
        if line.from_bus in bus_map and line.to_bus in bus_map:
            from_idx = bus_map[line.from_bus]
            to_idx = bus_map[line.to_bus]
            
            # Map physical length and impedance
            l_km = line.length / 1000.0 if line.length_unit in ["m", ""] else line.length
            l_km = max(l_km, 0.001)  # Ensure non-zero length
            r = line.resistance_ohm_per_km if line.resistance_ohm_per_km else 0.5
            x = line.reactance_ohm_per_km if line.reactance_ohm_per_km else 0.1
            
            pp.create_line_from_parameters(net, from_idx, to_idx, length_km=l_km, r_ohm_per_km=r, x_ohm_per_km=x, c_nf_per_km=10, max_i_ka=0.2, name=f"{line.from_bus}-{line.to_bus}")
            
    # Add PVs
    for pv in topology.pvs:
        if pv.bus in bus_map:
            bus_idx = bus_map[pv.bus]
            pp.create_sgen(net, bus_idx, p_mw=pv.capacity_kw / 1000.0, name=pv.name)
            
    # Add external grid to root (Slack bus)
    root_bus = topology.get_substation_bus() or topology.buses[0].name
    if root_bus in bus_map:
        pp.create_ext_grid(net, bus_map[root_bus], vm_pu=1.0)
        
    print("Adding physical loads...")
    loads = topology.load_at_bus()
    for bus_name, s_va in loads.items():
        if bus_name in bus_map:
            p_mw = s_va.real / 1e6
            q_mvar = s_va.imag / 1e6
            if p_mw > 0 or q_mvar > 0:
                pp.create_load(net, bus_map[bus_name], p_mw=p_mw, q_mvar=q_mvar, name=f"Load-{bus_name}")

    print("Running AC Power Flow (Newton-Raphson)...")
    try:
        pp.runpp(net)
        print("\n=== Power Flow Results ===")
        print(f"Max Voltage: {net.res_bus.vm_pu.max():.4f} pu")
        print(f"Min Voltage: {net.res_bus.vm_pu.min():.4f} pu")
        print(f"Max Line Loading: {net.res_line.loading_percent.max():.2f}%")
        print("==========================\n")
    except Exception as e:
        print(f"Power flow failed to converge: {e}")

    print("Generating custom coordinates from SVG layout algorithm...")
    root_bus, _, _ = rooted_tree(topology)
    positions = electrical_positions(topology, width=1500, height=1040)
    positions = resolve_symbol_overlaps(positions, fixed_nodes={root_bus} if root_bus else None, min_dx=50.0, min_dy=35.0, iterations=20)
    
    geodata = []
    indices = []
    for bus in topology.buses:
        if bus.name in positions and bus.name in bus_map:
            x, y = positions[bus.name]
            # invert y for matplotlib standard plane
            geodata.append({"x": x, "y": -y})
            indices.append(bus_map[bus.name])
            
    net.bus_geodata = pd.DataFrame(geodata, index=indices)

    # Convert to new geodata format
    try:
        from pandapower.plotting.geo import convert_geodata_to_geojson
        convert_geodata_to_geojson(net)
    except Exception as e:
        print(f"Warning: geodata conversion failed: {e}")

    print("Plotting network using matplotlib collections for high quality...")
    
    # Scale sizes for our 1500x1040 coordinate system
    bus_size = 8.0
    ext_size = 24.0
    line_width = 2.5
    
    # --- Generate Heatmap Colors based on Physics ---
    # Bus Voltage Map (0.9 to 1.1 pu)
    v_norm = mcolors.Normalize(vmin=0.9, vmax=1.1)
    # Use coolwarm (blue for low, red for high, or RdYlBu_r)
    v_cmap = cm.get_cmap("RdYlBu_r") if hasattr(cm, "get_cmap") else plt.colormaps["RdYlBu_r"]
    bus_colors = [v_cmap(v_norm(net.res_bus.vm_pu.at[idx])) if not pd.isna(net.res_bus.vm_pu.at[idx]) else "#334155" for idx in net.bus.index]
    
    # Line Loading Map (0% to 100%)
    l_norm = mcolors.Normalize(vmin=0, vmax=100)
    l_cmap = cm.get_cmap("YlOrRd") if hasattr(cm, "get_cmap") else plt.colormaps["YlOrRd"]
    line_colors = [l_cmap(l_norm(net.res_line.loading_percent.at[idx])) if not pd.isna(net.res_line.loading_percent.at[idx]) else "#94a3b8" for idx in net.line.index]
    
    bc = pp_plot.create_bus_collection(net, size=bus_size, color=bus_colors, zorder=10)
    lc = pp_plot.create_line_collection(net, color=line_colors, linewidths=line_width, use_bus_geodata=True, zorder=5)
    
    collections = [lc, bc]
        
    if not net.sgen.empty:
        pass # Custom PV scatter is handled below
        
    plt.figure(figsize=(16, 12), dpi=300)
    ax = plt.gca()
    
    pp_plot.draw_collections(collections, ax=ax)
    
    # Custom PV Icon using scatter so we can change the icon and offset it
    if not net.sgen.empty:
        pv_x = []
        pv_y = []
        for pv in topology.pvs:
            if pv.bus in positions:
                x, y = positions[pv.bus]
                px = x + 18
                py = -y + 18
                pv_x.append(px)  # offset right
                pv_y.append(py)  # offset up (inverted y)
                # Draw connection line to bus node
                ax.plot([x, px], [-y, py], color="#ca8a04", lw=1.5, zorder=4, linestyle=":")
        ax.scatter(pv_x, pv_y, s=350, c="#eab308", edgecolors="#ca8a04", marker="*", zorder=15, linewidths=1.5)
        
    # Custom External Grid Icon using scatter so we can offset it
    if not net.ext_grid.empty and root_bus in positions:
        x, y = positions[root_bus]
        eg_x = x - 25
        eg_y = -y + 25
        # Draw connection line to root bus
        ax.plot([x, eg_x], [-y, eg_y], color="#ef4444", lw=line_width, zorder=4)
        # Draw external grid substation square
        ax.scatter([eg_x], [eg_y], s=550, c="#ef4444", edgecolors="#991b1b", marker="s", zorder=11, linewidths=1.5)
    
    # Create custom legend
    from matplotlib.lines import Line2D
    legend_elements = [
        Line2D([0], [0], marker='o', color='w', label='Bus', markerfacecolor='#334155', markersize=8),
        Line2D([0], [0], color='#94a3b8', lw=line_width, label='Line'),
        Line2D([0], [0], marker='*', color='w', label='PV Array (Solar)', markerfacecolor='#eab308', markeredgecolor='#ca8a04', markersize=16),
        Line2D([0], [0], marker='s', color='w', label='External Grid (Substation)', markerfacecolor='#ef4444', markeredgecolor='#991b1b', markersize=14)
    ]
    ax.legend(handles=legend_elements, loc='upper right', fontsize=12, frameon=True, shadow=True, borderpad=1.2)
    
    plt.title("80-Bus Rural LV Feeder - AC Power Flow Heatmap", fontsize=20, fontweight='bold', pad=20, color="#0f172a")
    plt.axis('off')
    
    # Add Colorbars
    sm_v = plt.cm.ScalarMappable(cmap=v_cmap, norm=v_norm)
    sm_v.set_array([])
    cbar_v = plt.colorbar(sm_v, ax=ax, orientation='vertical', shrink=0.4, pad=0.02)
    cbar_v.set_label('Voltage (pu)', fontsize=12, fontweight='bold')
    
    sm_l = plt.cm.ScalarMappable(cmap=l_cmap, norm=l_norm)
    sm_l.set_array([])
    cbar_l = plt.colorbar(sm_l, ax=ax, orientation='vertical', shrink=0.4, pad=0.08)
    cbar_l.set_label('Line Loading (%)', fontsize=12, fontweight='bold')
    
    out_png = args.out_dir / "pandapower_network.png"
    plt.savefig(out_png, dpi=300, bbox_inches='tight', facecolor='#f8fafc', edgecolor='none')
    plt.close()
    print(f"Saved high-quality static plot to {out_png}")
    
    print("Plotting network using plotly (interactive)...")
    try:
        import pandapower.plotting.plotly as pp_plotly
        out_html = args.out_dir / "pandapower_network.html"
        pp_plotly.simple_plotly(net, auto_open=False, on_map=False, filename=str(out_html))
        print(f"Saved interactive plotly plot to {out_html}")
    except Exception as e:
        print(f"Failed to generate plotly output: {e}")

if __name__ == "__main__":
    main()
