import geopandas as gpd
import osmnx as ox
import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
import folium
import random
import json
import os
import shapely.geometry as sg

# ==========================================
# 1. CONFIGURATION (REAL WORLD PARAMETERS)
# ==========================================
CENTER_POINT = (13.780157318353783, 100.56023705120911)
RADIUS_METERS = 400
METERS_PER_TRANSFORMER = 12 
REAL_DATA_ONLY = True      # Strictly use the provided JSON data
PROSUMER_RATIO = 0.35      # 35% of houses have solar
EV_OWNERSHIP_RATIO = 0.10  # 10% of houses have EVs
CRS_UTM = "EPSG:32647"       # UTM Zone 47N
CRS_LATLON = "EPSG:4326"

# Grid Physics
LINE_R_PER_KM = 0.32         # Ohm/km
LINE_X_PER_KM = 0.28         # Ohm/km

# MEA Standard Transformer Sizes (kVA)
TRANSFORMER_SIZES = [50, 100, 160, 250, 315, 500, 1000, 1250, 1500]

# EV Station Config
SYNTHETIC_EV_STATIONS = 3  # Force create this many stations if none found
DC_CHARGER_POWER_KW = 120  # Fast Charger Size

def get_geo_data(center, dist):
    print(f"Loading Map Data...")
    # Fetch Buildings
    tags_b = {'building': True, 'building:levels': True, 'amenity': True, 'shop': True}
    gdf_b = pd.DataFrame() 
    try:
        gdf_b = ox.features_from_point(center, tags=tags_b, dist=dist)
        gdf_b = gdf_b[gdf_b.geometry.type.isin(['Polygon', 'MultiPolygon'])].copy()
        gdf_b = gdf_b.to_crs(CRS_UTM)
    except:
        gdf_b = gpd.GeoDataFrame()
    
    # Fetch Real EV Stations
    tags_ev = {'amenity': 'charging_station'}
    gdf_ev = pd.DataFrame()
    try:
        gdf_ev = ox.features_from_point(center, tags=tags_ev, dist=dist)
        gdf_ev = gdf_ev.to_crs(CRS_UTM)
    except:
        gdf_ev = gpd.GeoDataFrame()
        
    return gdf_b, gdf_ev

# ==========================================
# 2. HELPER LOGIC
# ==========================================
def assign_mea_attributes(row):
    """
    Derived engineering attributes based on MEA standards:
    - Meter Sizes: 5(15)A, 15(45)A, 30(100)A, etc.
    - Tariffs: 1.1 (Small Res), 1.2 (Normal Res), 1.3 (Res TOU), 
              2.1 (Small Gen), 3.1 (Med Gen)
    """
    # 1. Floor Area Calculation
    levels = 1
    if 'building:levels' in row and pd.notnull(row['building:levels']):
        try:
            levels = float(row['building:levels'])
        except: levels = 1
    
    area_sqm = row.geometry.area
    if area_sqm > 200: levels = max(levels, 2)
    total_area = area_sqm * levels

    # 2. Category Determination
    # If usage_type is already set (from injection), respect it
    if 'usage_type' in row and pd.notnull(row['usage_type']):
        usage_type = row['usage_type']
    else:
        is_commercial = ('amenity' in row and pd.notnull(row['amenity'])) or ('shop' in row and pd.notnull(row['shop']))
        usage_type = 'Commercial' if is_commercial else 'Residential'
    
    is_commercial = (usage_type == 'Commercial')
    
    # 3. Meter Size & Load Assignment
    # Standard MEA sizes and their typical peak load (kW)
    meter_size = "15(45) A"
    match_load_kw = 10.0
    phase_conn = "1-Phase"
    tariff_code = "1.2" # Default Normal Res

    if is_commercial:
        if total_area < 200:
            meter_size = "30(100) A"
            match_load_kw = 22.0
            tariff_code = "2.1"
        elif total_area < 1000:
            meter_size = "3-Phase 30(100) A"
            match_load_kw = 66.0
            tariff_code = "3.1"
            phase_conn = "3-Phase"
        else:
            meter_size = "3-Phase / CT"
            match_load_kw = 150.0
            tariff_code = "3.2" # Med Gen TOU
            phase_conn = "3-Phase"
    else:
        # Residential logic
        if total_area < 80:
            meter_size = "5(15) A"
            match_load_kw = 3.3
            tariff_code = "1.1" # Small Res
        elif total_area < 400:
            meter_size = "15(45) A"
            match_load_kw = 10.0
            tariff_code = "1.2"
        else:
            meter_size = "30(100) A"
            match_load_kw = 22.0
            tariff_code = "1.2"
            if random.random() < 0.2: phase_conn = "3-Phase" # Optional for high load res

    # 4. Optional TOU Adoption (1.3 for Res, 2.2 for Small Gen)
    tou_prob = 0.15 # 15% adoption rate for those who can choose
    if tariff_code == "1.2" and random.random() < tou_prob:
        tariff_code = "1.3"
    elif tariff_code == "2.1" and random.random() < tou_prob:
        tariff_code = "2.2"

    # 5. Phase Balancing
    assigned_phase = "ABC"
    if phase_conn == "1-Phase":
        assigned_phase = random.choice(['A', 'B', 'C'])

    # 6. Prosumer & EV Status
    has_solar = random.random() < PROSUMER_RATIO
    solar_kw = (area_sqm * 0.4 * 0.15) if has_solar else 0.0
    
    # EVs typically need 15(45)A or 3-Phase
    capable_of_ev = meter_size not in ["5(15) A"]
    has_ev = (not is_commercial) and capable_of_ev and (random.random() < EV_OWNERSHIP_RATIO)

    return pd.Series([
        usage_type, tariff_code, phase_conn, assigned_phase,
        round(match_load_kw, 2), has_solar, round(solar_kw, 2), has_ev,
        total_area, meter_size
    ])

# ==========================================
# 3. MAIN SIMULATION PROCESS
# ==========================================
print("--- STARTING SIMULATION ---")

# A. Load Data
if REAL_DATA_ONLY:
    print("REAL_DATA_ONLY mode: Skipping OSM fetch.")
    gdf_b = gpd.GeoDataFrame()
    gdf_ev = gpd.GeoDataFrame()
else:
    gdf_b, gdf_ev = get_geo_data(CENTER_POINT, RADIUS_METERS)
    if gdf_b.empty: raise Exception("No Data Found")
    print(f"Found {len(gdf_b)} Buildings and {len(gdf_ev)} Real EV Stations from OSM.")

# B. Enrich and Expand Data (Only if not REAL_DATA_ONLY)
print("Enriching and Expanding Data...")
cols = ['usage_type', 'tariff_code', 'phase_conn', 'phase_id', 'peak_load_kw', 'has_solar', 'solar_kw', 'has_ev', 'total_area', 'meter_size']
gdf_b_expanded = gpd.GeoDataFrame()

if not REAL_DATA_ONLY and not gdf_b.empty:
    expanded_rows = []
    for idx, row in gdf_b.iterrows():
        levels = 1
        if 'building:levels' in row and pd.notnull(row['building:levels']):
            try: levels = int(float(row['building:levels']))
            except: levels = 1
        
        area_sqm = row.geometry.area
        units_per_floor = max(1, int(area_sqm / 300))
        total_units = min(levels * units_per_floor, 5) 
        
        for i in range(total_units):
            expanded_rows.append(row.copy())

    gdf_b_expanded = gpd.GeoDataFrame(expanded_rows, crs=gdf_b.crs)
    gdf_b_expanded[cols] = gdf_b_expanded.apply(assign_mea_attributes, axis=1)
    gdf_b_expanded['node_type'] = 'Building'
if not gdf_ev.empty:
    gdf_ev['node_type'] = 'EV_Station'
    # Default attrs for real EV stations
    gdf_ev['usage_type'] = 'EV_Charging_Station'
    gdf_ev['tariff_code'] = '3.2' # Time of Use 
    gdf_ev['phase_conn'] = '3-Phase' 
    gdf_ev['phase_id'] = 'ABC'
    gdf_ev['peak_load_kw'] = DC_CHARGER_POWER_KW
    gdf_ev['has_solar'] = False
    gdf_ev['solar_kw'] = 0.0
    gdf_ev['has_ev'] = False 
    gdf_ev['total_area'] = 50.0
    gdf_ev['meter_size'] = '3-Phase / CT'

# C. Inject Real UTCC Nodes
print("Injecting Real UTCC Building Nodes...")
real_nodes_file = "utcc_real_data.json"
real_utcc_gdf = gpd.GeoDataFrame()

if os.path.exists(real_nodes_file):
    with open(real_nodes_file, 'r') as f:
        real_data = json.load(f)
    
    rows = []
    for node in real_data.get('meterNodes', []):
        pt = sg.Point(node['longitude'], node['latitude'])
        rows.append({
            'geometry': pt,
            'building_name': node['name'],
            'building_code': node['buildingCode'],
            'node_type': 'Building',
            'usage_type': 'Commercial', # Campus buildings are large commercial/institutional
            'is_real_utcc': True,
            'total_area': 2500.0 # Force large area for high-power meter assignment
        })
    
    real_utcc_gdf = gpd.GeoDataFrame(rows, crs=CRS_LATLON).to_crs(CRS_UTM)
    # Give them a small buffer to act as "building footprints"
    real_utcc_gdf['geometry'] = real_utcc_gdf.geometry.buffer(8) 

# Merge real nodes with expanded OSM data
gdf_b_expanded = pd.concat([gdf_b_expanded, real_utcc_gdf], ignore_index=True)

# Final enrichment for any missing cols
def enrich_row(r):
    if pd.isnull(r.get('peak_load_kw')):
        return assign_mea_attributes(r)
    else:
        # For injected real nodes, ensure we have basic attributes
        # We can still run assignments if we want varied properties, but let's keep it simple for now
        # Actually, let's run assign_mea_attributes on them too to get realistic sizing
        return assign_mea_attributes(r)

# Re-run enrichment to catch injected nodes
gdf_b_expanded[cols] = gdf_b_expanded.apply(assign_mea_attributes, axis=1)

# Merge datasets
gdf_final = pd.concat([gdf_b_expanded, gdf_ev]).reset_index(drop=True)

# Assign IDs
gdf_final['meter_id'] = [f"MEA-{10000+i}" for i in range(len(gdf_final))]
gdf_final['lat'] = gdf_final.geometry.centroid.to_crs(CRS_LATLON).y
gdf_final['lon'] = gdf_final.geometry.centroid.to_crs(CRS_LATLON).x
gdf_final['utm_x'] = gdf_final.geometry.centroid.x
gdf_final['utm_y'] = gdf_final.geometry.centroid.y

# D. Clustering (Topology)
print("Clustering Transformers...")
n_clusters_target = max(1, int(len(gdf_final) / METERS_PER_TRANSFORMER))
kmeans = KMeans(n_clusters=n_clusters_target, random_state=42).fit(gdf_final[['utm_x', 'utm_y']])

# Since KMeans might return fewer clusters than n_clusters_target, 
# re-map the labels to be contiguous 0 to N-1
unique_labels = np.unique(kmeans.labels_)
label_map = {old: new for new, old in enumerate(unique_labels)}
gdf_final['transformer_id'] = [label_map[l] for l in kmeans.labels_]

# Transformer Physics (Centroids & Impedance)
# Use only the centroids that actually have members assigned
trans_centers = kmeans.cluster_centers_[unique_labels]
def calc_impedance(row):
    tx, ty = trans_centers[row['transformer_id']]
    dist_m = np.sqrt((row['utm_x'] - tx)**2 + (row['utm_y'] - ty)**2)
    dist_km = dist_m / 1000.0
    return pd.Series([round(dist_m, 2), round(dist_km * LINE_R_PER_KM, 4), round(dist_km * LINE_X_PER_KM, 4)])

gdf_final[['dist_m', 'line_R', 'line_X']] = gdf_final.apply(calc_impedance, axis=1)

# E. Static Sizing & Electrical Analysis
print("Analyzing Transformer Sizing & Voltage Drop...")
trans_stats = []
COINCIDENCE_FACTOR = 0.7 
V_NOMINAL = 230.0  # Volts (L-N)
PF = 0.9           # Power Factor assumption
TAN_PHI = np.tan(np.arccos(PF))

# 1. Calculate Voltage Drop for each Meter
def calc_voltage_drop(row):
    # P (kW) and Q (kVAR)
    p_kw = row['peak_load_kw']
    q_kvar = p_kw * TAN_PHI
    
    # Approx V_drop = (P*R + Q*X) / V
    # Convert kW to W for math
    v_drop = ( (p_kw * 1000 * row['line_R']) + (q_kvar * 1000 * row['line_X']) ) / V_NOMINAL
    v_actual = V_NOMINAL - v_drop
    v_drop_pct = (v_drop / V_NOMINAL) * 100
    return pd.Series([round(v_actual, 1), round(v_drop_pct, 2)])

gdf_final[['v_actual', 'v_drop_pct']] = gdf_final.apply(calc_voltage_drop, axis=1)

# 2. Aggregated Transformer Stats
for tid, group in gdf_final.groupby('transformer_id'):
    agg_peak_kw = group['peak_load_kw'].sum() * COINCIDENCE_FACTOR
    required_kva = agg_peak_kw / 0.85 
    chosen_kva = next((s for s in TRANSFORMER_SIZES if s >= required_kva), 2000)
    
    # Get Centroid for Database Seeding
    tx, ty = trans_centers[tid]
    # Convert UTM to Lat/Lon for DB
    pt = gpd.points_from_xy([tx], [ty], crs=CRS_UTM).to_crs(CRS_LATLON)
    
    trans_stats.append({
        'transformer_id': tid,
        'lat': pt[0].y,
        'lon': pt[0].x,
        'agg_peak_kw': round(agg_peak_kw, 2),
        'required_kva': round(required_kva, 2),
        'installed_kva': chosen_kva,
        'utilization': round((required_kva/chosen_kva)*100, 1),
        'meter_count': len(group)
    })

df_trans = pd.DataFrame(trans_stats)

# ==========================================
# 4. VISUALIZATION & EXPORT
# ==========================================
print("Exporting Data and Maps...")

# Filter Columns for Clean Export
export_cols = [
    'meter_id', 'lat', 'lon', 'utm_x', 'utm_y',
    'node_type', 'usage_type', 'meter_size',
    'tariff_code', 'phase_conn', 'phase_id',
    'peak_load_kw', 'has_solar', 'solar_kw', 'has_ev',
    'transformer_id', 'dist_m', 'line_R', 'line_X',
    'v_actual', 'v_drop_pct', 'building_name', 'building_code'
]

# Ensure cols exist (in case of synthetic injection anomalies)
final_cols = [c for c in export_cols if c in gdf_final.columns]
df_export = pd.DataFrame(gdf_final[final_cols])

# CSV Exports
df_export.to_csv("dataset_meters.csv", index=False)
df_trans.to_csv("dataset_transformer_sizing.csv", index=False)

# Folium Map
m = folium.Map(location=[CENTER_POINT[0], CENTER_POINT[1]], zoom_start=16, tiles='CartoDB dark_matter')

# Pre-calculate Transformer Coordinates (Lat/Lon)
trans_locs = []
for center in trans_centers:
    pt = gpd.points_from_xy([center[0]], [center[1]], crs=CRS_UTM).to_crs(CRS_LATLON)
    trans_locs.append((pt[0].y, pt[0].x))

# Plot Transformers
for i, (lat, lon) in enumerate(trans_locs):
    folium.Marker(
        [lat, lon], 
        popup=f"Transformer-{i}<br>{df_trans.iloc[i]['installed_kva']}kVA",
        icon=folium.Icon(color="white", icon="bolt", prefix="fa")
    ).add_to(m)

# Plot Meters & Feeder Lines
phase_colors = {'A': 'purple', 'B': 'orange', 'C': 'blue', 'ABC': 'gray'}

for _, row in df_export.iterrows():
    m_lat, m_lon = row['lat'], row['lon']
    t_lat, t_lon = trans_locs[int(row['transformer_id'])]
    
    # 1. Base Phase Color
    p_color = phase_colors.get(row['phase_id'], 'gray')
    
    # 2. Voltage Health Color (for the border/fill)
    # Green > 220V, Yellow 210-220V, Red < 210V
    v_actual = row['v_actual']
    if v_actual > 220:
        v_color = 'green'
    elif v_actual > 210:
        v_color = 'yellow'
    else:
        v_color = 'red'

    radius = 3
    if row['has_solar']: radius = 5
    
    # 3. Feeder Line
    line_popup = f"""
    <b>Feeder Link</b><br>
    Dist: {row['dist_m']}m<br>
    V-Drop: {row['v_drop_pct']}%<br>
    Actual: {row['v_actual']}V
    """
    folium.PolyLine(
        locations=[(m_lat, m_lon), (t_lat, t_lon)],
        color=p_color,
        weight=1.5,
        opacity=0.4,
        popup=line_popup
    ).add_to(m)

    # 4. Meter Marker
    if row['node_type'] == 'EV_Station':
        folium.Marker(
            location=[m_lat, m_lon],
            popup=f"<b>EV STATION</b><br>ID: {row['meter_id']}<br>V: {v_actual}V",
            icon=folium.Icon(color='red', icon='charging-station', prefix='fa')
        ).add_to(m)
        continue 

    popup = f"""
    ID: {row['meter_id']}<br>
    Name: {row.get('building_name', 'N/A')}<br>
    Phase: {row['phase_id']}<br>
    V: <b>{v_actual}V</b><br>
    Load: {row['peak_load_kw']}kW
    """
    folium.CircleMarker(
        location=[m_lat, m_lon],
        radius=radius,
        color=v_color, # Outline shows voltage health
        fill=True,
        fill_color=p_color, # Fill shows phase
        fill_opacity=0.7,
        popup=popup
    ).add_to(m)

m.save("map_bangkok_grid.html")

print("="*40)
print("SUCCESS: Static Grid Dataset Generated")
print(f"1. dataset_bangkok_static.csv ({len(df_export)} meters)")
print(f"2. dataset_transformer_sizing.csv ({len(df_trans)} transformers)")
print(f"3. map_bangkok_grid.html")
print("="*40)
