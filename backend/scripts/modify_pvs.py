import re
import random

glm_path = 'src/smart_meter_simulator/data/grids/grid_bus_network.glm'
with open(glm_path, 'r') as f:
    content = f.read()

bus_names = re.findall(r'name "PV_Inverter_(ref_lv_bus_\d+)";', content)
print(f"Found {len(bus_names)} PVs")

keep_count = int(80 * 0.15)
keep_buses = set(random.sample(bus_names, keep_count))
print(f"Keeping {keep_count} PVs: {keep_buses}")

for bus in bus_names:
    if bus not in keep_buses:
        # replace inverter block
        inverter_pattern = r'object inverter \{\n    name "PV_Inverter_' + bus + r'";.*?\n\}\n\n*'
        content = re.sub(inverter_pattern, '', content, flags=re.DOTALL)
        
        # replace solar block
        solar_pattern = r'object solar \{\n    name "PV_' + bus + r'";.*?\n\}\n\n*'
        content = re.sub(solar_pattern, '', content, flags=re.DOTALL)

with open(glm_path, 'w') as f:
    f.write(content)
print("Updated GLM")
