import argparse
import pandapower as pp
from smart_meter_simulator.adapters.pandapower_adapter import PandapowerAdapter
import os

def export_to_glm(net, output_path: str):
    """
    Export a basic pandapower network to a GridLAB-D (.glm) file.
    Supports basic mapping of buses, lines, loads, and sgens.
    """
    lines = []
    lines.append("// Generated GridLAB-D model from Pandapower")
    lines.append("module powerflow;")
    lines.append("")
    
    # Export Buses -> Nodes
    for idx, bus in net.bus.iterrows():
        bus_name = bus['name'] if 'name' in bus and pd.notna(bus['name']) else f"Bus_{idx}"
        vn_kv = bus['vn_kv'] * 1000 # Convert to Volts
        lines.append("object node {")
        lines.append(f'    name "{bus_name}";')
        lines.append('    phases ABCN;')
        lines.append(f'    nominal_voltage {vn_kv:.2f};')
        lines.append("}")
        lines.append("")
        
    # Export Lines -> overhead_line
    for idx, line in net.line.iterrows():
        from_bus = net.bus.loc[line.from_bus, 'name']
        if pd.isna(from_bus): from_bus = f"Bus_{line.from_bus}"
        to_bus = net.bus.loc[line.to_bus, 'name']
        if pd.isna(to_bus): to_bus = f"Bus_{line.to_bus}"
        
        lines.append("object overhead_line {")
        lines.append(f'    name "Line_{idx}";')
        lines.append('    phases ABCN;')
        lines.append(f'    from "{from_bus}";')
        lines.append(f'    to "{to_bus}";')
        lines.append(f'    length {line.length_km * 3280.84:.2f}; // km to ft')
        lines.append("}")
        lines.append("")
        
    # Export Loads
    for idx, load in net.load.iterrows():
        bus_name = net.bus.loc[load.bus, 'name']
        if pd.isna(bus_name): bus_name = f"Bus_{load.bus}"
        
        lines.append("object load {")
        lines.append(f'    name "Load_{idx}";')
        lines.append(f'    parent "{bus_name}";')
        lines.append('    phases ABCN;')
        lines.append(f'    constant_power_A {load.p_mw * 1e6}+{(load.q_mvar * 1e6 if pd.notna(load.q_mvar) else 0)}j;')
        lines.append(f'    nominal_voltage {net.bus.loc[load.bus, "vn_kv"] * 1000:.2f};')
        lines.append("}")
        lines.append("")
        
    # Export Generators (sgen)
    if 'sgen' in net and not net.sgen.empty:
        for idx, sgen in net.sgen.iterrows():
            bus_name = net.bus.loc[sgen.bus, 'name']
            if pd.isna(bus_name): bus_name = f"Bus_{sgen.bus}"
            
            lines.append("object load { // Using negative load for sgen")
            lines.append(f'    name "Sgen_{idx}";')
            lines.append(f'    parent "{bus_name}";')
            lines.append('    phases ABCN;')
            # Sgen generates power, so power is negative load
            p_va = -sgen.p_mw * 1e6
            q_var = -sgen.q_mvar * 1e6 if pd.notna(sgen.q_mvar) else 0
            lines.append(f'    constant_power_A {p_va}+{q_var}j;')
            lines.append(f'    nominal_voltage {net.bus.loc[sgen.bus, "vn_kv"] * 1000:.2f};')
            lines.append("}")
            lines.append("")

    with open(output_path, "w") as f:
        f.write("\n".join(lines))
    print(f"Exported {len(net.bus)} buses, {len(net.line)} lines, {len(net.load)} loads to {output_path}")

if __name__ == "__main__":
    import pandas as pd
    os.makedirs("src/smart_meter_simulator/data/grids", exist_ok=True)
    
    adapter = PandapowerAdapter()
    adapter.load_reference_lv_grid("data/80_bus_rural_reference_grid")
    
    output_file = "src/smart_meter_simulator/data/grids/grid_bus_network.glm"
    export_to_glm(adapter.net, output_file)
    print(f"Successfully exported to {output_file}")
