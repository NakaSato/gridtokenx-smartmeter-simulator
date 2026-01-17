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
import math

# ==========================================
# WEATHER-BASED SOLAR GENERATION
# ==========================================
def calculate_solar_generation(hour: int, installed_capacity_kw: float, cloud_cover: float = 0.0) -> float:
    """
    Calculate solar power output based on time of day and weather conditions.
    
    Args:
        hour: Hour of day (0-23)
        installed_capacity_kw: Installed solar panel capacity in kW
        cloud_cover: Cloud cover factor (0.0 = clear sky, 1.0 = fully overcast)
    
    Returns:
        Generated power in kW
    
    The function uses a realistic diurnal curve:
    - Peak generation at solar noon (12:00)
    - Zero generation at night (before 6:00 and after 18:00)
    - Gaussian-like curve during daylight hours
    - Cloud cover reduces output proportionally
    """
    if hour < 6 or hour > 18:
        return 0.0
    
    # Solar irradiance curve (Gaussian approximation centered at noon)
    # Peak efficiency at hour 12
    solar_noon = 12.0
    sigma = 2.5  # Spread of the curve
    time_factor = math.exp(-((hour - solar_noon) ** 2) / (2 * sigma ** 2))
    
    # Cloud cover reduction (linear model)
    # 0% cloud = 100% efficiency, 100% cloud = 20% efficiency (diffuse light)
    weather_factor = 1.0 - (cloud_cover * 0.8)
    
    # Temperature derating (simplified - hot weather reduces efficiency slightly)
    # Assuming ~25°C baseline, higher temps reduce by ~0.4%/°C
    temp_factor = 0.95  # Typical 5% loss for Thai conditions
    
    # System losses (inverter, wiring, dust) ~15%
    system_efficiency = 0.85
    
    # Calculate output
    output_kw = installed_capacity_kw * time_factor * weather_factor * temp_factor * system_efficiency
    
    return round(max(0.0, output_kw), 3)


def get_hourly_solar_profile(installed_capacity_kw: float, cloud_cover: float = 0.0) -> list:
    """
    Generate a 24-hour solar generation profile.
    
    Returns a list of 24 values representing power output for each hour.
    """
    return [calculate_solar_generation(hour, installed_capacity_kw, cloud_cover) for hour in range(24)]

# ==========================================
# 1. CONFIGURATION (UTCC SPECIFIC)
# ==========================================
CENTER_POINT = (13.780157318353783, 100.56023705120911)
RADIUS_METERS = 300
METERS_PER_TRANSFORMER = 12 
REAL_DATA_ONLY = False      # Fetch additional OSM buildings to complement real JSON data
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
SYNTHETIC_EV_STATIONS = 1  # For UTCC specifically
DC_CHARGER_POWER_KW = 120  # Fast Charger Size

def get_geo_data(center, dist):
    print(f"Loading Map Data...")
    # Fetch Buildings
    tags_b = {'building': True, 'building:levels': True, 'amenity': True, 'shop': True}
    gdf_b = pd.DataFrame() 
    try:
        gdf_b = ox.features_from_point(center, tags=tags_b, dist=dist)
        if not gdf_b.empty:
            gdf_b = gdf_b[gdf_b.geometry.type.isin(['Polygon', 'MultiPolygon'])].copy()
            gdf_b = gdf_b.to_crs(CRS_UTM)
    except:
        gdf_b = gpd.GeoDataFrame()
    
    # Fetch Real EV Stations
    tags_ev = {'amenity': 'charging_station'}
    gdf_ev = pd.DataFrame()
    try:
        gdf_ev = ox.features_from_point(center, tags=tags_ev, dist=dist)
        if not gdf_ev.empty:
            gdf_ev = gdf_ev.to_crs(CRS_UTM)
    except:
        gdf_ev = gpd.GeoDataFrame()
        
    return gdf_b, gdf_ev

# ==========================================
# 2. HELPER LOGIC
# ==========================================
def assign_mea_attributes(row):
    """
    Derived engineering attributes based on MEA standards for UTCC Campus:
    - Campus buildings are primarily Commercial/Institutional
    """
    # 1. Floor Area Calculation
    levels = 1
    if 'building:levels' in row and pd.notnull(row['building:levels']):
        try:
            levels = float(row['building:levels'])
        except: levels = 1
    
    area_sqm = row.geometry.area
    if area_sqm > 200: levels = max(levels, 3) # UTCC buildings are mostly at least 3 floors
    total_area = area_sqm * levels

    # 2. Category Determination
    usage_type = 'Commercial' # Institutional campus buildings behave like commercial loads
    is_commercial = True
    
    # 3. Meter Size & Load Assignment
    # Standard MEA sizes and their typical peak load (kW)
    meter_size = "3-Phase 30(100) A"
    match_load_kw = 66.0
    phase_conn = "3-Phase"
    tariff_code = "3.1" # Medium Gen

    if total_area > 1000:
        meter_size = "3-Phase / CT"
        match_load_kw = 150.0
        tariff_code = "3.2" # Med Gen TOU
        phase_conn = "3-Phase"
    
    # 5. Phase Balancing (since they are 3-phase, they use ABC)
    assigned_phase = "ABC"

    # 6. Prosumer & EV Status
    has_solar = random.random() < PROSUMER_RATIO
    solar_kw = (area_sqm * 0.4 * 0.15) if has_solar else 0.0
    
    has_ev = False # EVs at UTCC are handled by charging stations

    return pd.Series([
        usage_type, tariff_code, phase_conn, assigned_phase,
        round(match_load_kw, 2), has_solar, round(solar_kw, 2), has_ev,
        total_area, meter_size
    ])

# ==========================================
# 3. MAIN SIMULATION PROCESS
# ==========================================
print("--- STARTING UTCC GRID SIMULATION ---")

# B. Fetch OSM Data (Supplementary)
gdf_osm_b = gpd.GeoDataFrame()
gdf_ev = gpd.GeoDataFrame()

if not REAL_DATA_ONLY:
    gdf_osm_b, gdf_ev = get_geo_data(CENTER_POINT, RADIUS_METERS)
    print(f"Found {len(gdf_osm_b)} additional buildings from OSM.")

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
            'usage_type': 'Commercial',
            'is_real_utcc': True,
            'total_area': 2500.0 
        })
    
    real_utcc_gdf = gpd.GeoDataFrame(rows, crs=CRS_LATLON).to_crs(CRS_UTM)
    # Give them a buffer to act as "building footprints"
    real_utcc_gdf['geometry'] = real_utcc_gdf.geometry.buffer(12) 

# D. Merge and Filter OSM Buildings
# Only keep OSM buildings that don't overlap with our real nodes
if not gdf_osm_b.empty:
    print("Filtering overlapping OSM buildings...")
    # Sjoin to find overlaps
    overlaps = gpd.sjoin(gdf_osm_b, real_utcc_gdf, how='inner', predicate='intersects')
    gdf_osm_b = gdf_osm_b.drop(overlaps.index)
    print(f"Keeping {len(gdf_osm_b)} non-overlapping OSM buildings.")

# Combined Grid Data
gdf_combined = pd.concat([real_utcc_gdf, gdf_osm_b], ignore_index=True)

# E. Enrich and Expand Data
print("Enriching Data...")
cols = ['usage_type', 'tariff_code', 'phase_conn', 'phase_id', 'peak_load_kw', 'has_solar', 'solar_kw', 'has_ev', 'total_area', 'meter_size']

gdf_combined[cols] = gdf_combined.apply(assign_mea_attributes, axis=1)
gdf_combined['node_type'] = 'Building'

# Handle EV Stations if any
if not gdf_ev.empty:
    gdf_ev['node_type'] = 'EV_Station'
    gdf_ev['usage_type'] = 'EV_Charging_Station'
    gdf_ev['tariff_code'] = '3.2' 
    gdf_ev['phase_conn'] = '3-Phase' 
    gdf_ev['phase_id'] = 'ABC'
    gdf_ev['peak_load_kw'] = DC_CHARGER_POWER_KW
    gdf_ev['has_solar'] = False
    gdf_ev['solar_kw'] = 0.0
    gdf_ev['has_ev'] = False 
    gdf_ev['total_area'] = 50.0
    gdf_ev['meter_size'] = '3-Phase / CT'
    gdf_final = pd.concat([gdf_combined, gdf_ev]).reset_index(drop=True)
else:
    gdf_final = gdf_combined.reset_index(drop=True)

# Assign IDs
gdf_final['meter_id'] = [f"UTCC-{1000+i}" for i in range(len(gdf_final))]
gdf_final['lat'] = gdf_final.geometry.centroid.to_crs(CRS_LATLON).y
gdf_final['lon'] = gdf_final.geometry.centroid.to_crs(CRS_LATLON).x
gdf_final['utm_x'] = gdf_final.geometry.centroid.x
gdf_final['utm_y'] = gdf_final.geometry.centroid.y

# D. Clustering (Topology)
print("Clustering Transformers...")
# For UTCC, we likely have few transformers serving the whole campus
n_clusters_target = max(1, int(len(gdf_final) / METERS_PER_TRANSFORMER))
if len(gdf_final) < 2:
    gdf_final['transformer_id'] = 0
    trans_centers = np.array([[gdf_final['utm_x'].mean(), gdf_final['utm_y'].mean()]])
    unique_labels = [0]
else:
    kmeans = KMeans(n_clusters=n_clusters_target, random_state=42).fit(gdf_final[['utm_x', 'utm_y']])
    unique_labels = np.unique(kmeans.labels_)
    label_map = {old: new for new, old in enumerate(unique_labels)}
    gdf_final['transformer_id'] = [label_map[l] for l in kmeans.labels_]
    trans_centers = kmeans.cluster_centers_[unique_labels]

# Transformer Physics (Centroids & Impedance)
def calc_impedance(row):
    tx, ty = trans_centers[row['transformer_id']]
    dist_m = np.sqrt((row['utm_x'] - tx)**2 + (row['utm_y'] - ty)**2)
    dist_km = dist_m / 1000.0
    return pd.Series([round(dist_m, 2), round(dist_km * LINE_R_PER_KM, 4), round(dist_km * LINE_X_PER_KM, 4)])

gdf_final[['dist_m', 'line_R', 'line_X']] = gdf_final.apply(calc_impedance, axis=1)

# E. Static Sizing & Electrical Analysis
print("Analyzing Transformer Sizing & Voltage Drop...")
trans_stats = []
COINCIDENCE_FACTOR = 0.8 # Higher for campus
V_NOMINAL = 230.0  
PF = 0.9           
TAN_PHI = np.tan(np.arccos(PF))

# 1. Calculate Voltage Drop for each Meter
def calc_voltage_drop(row):
    p_kw = row['peak_load_kw']
    q_kvar = p_kw * TAN_PHI
    v_drop = ( (p_kw * 1000 * row['line_R']) + (q_kvar * 1000 * row['line_X']) ) / V_NOMINAL
    v_actual = V_NOMINAL - v_drop
    v_drop_pct = (v_drop / V_NOMINAL) * 100
    return pd.Series([round(v_actual, 1), round(v_drop_pct, 2)])

gdf_final[['v_actual', 'v_drop_pct']] = gdf_final.apply(calc_voltage_drop, axis=1)

# 2. Aggregated Transformer Stats
for tid, group in gdf_final.groupby('transformer_id'):
    agg_peak_kw = group['peak_load_kw'].sum() * COINCIDENCE_FACTOR
    required_kva = agg_peak_kw / 0.85 
    chosen_kva = next((s for s in TRANSFORMER_SIZES if s >= required_kva), 1500)
    
    tx, ty = trans_centers[tid]
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

export_cols = [
    'meter_id', 'lat', 'lon', 'utm_x', 'utm_y',
    'node_type', 'usage_type', 'meter_size',
    'tariff_code', 'phase_conn', 'phase_id',
    'peak_load_kw', 'has_solar', 'solar_kw', 'has_ev',
    'transformer_id', 'dist_m', 'line_R', 'line_X',
    'v_actual', 'v_drop_pct', 'building_name', 'building_code'
]

final_cols = [c for c in export_cols if c in gdf_final.columns]
df_export = pd.DataFrame(gdf_final[final_cols])

# CSV Exports
df_export.to_csv("utcc_dataset_meters.csv", index=False)
df_trans.to_csv("utcc_dataset_transformer_sizing.csv", index=False)

# Folium Map
m = folium.Map(location=[CENTER_POINT[0], CENTER_POINT[1]], zoom_start=17, tiles='CartoDB dark_matter')

# Plot Transformers
trans_loc_map = {}
for i, trans in df_trans.iterrows():
    lat, lon = trans['lat'], trans['lon']
    trans_loc_map[int(trans['transformer_id'])] = (lat, lon)
    folium.Marker(
        [lat, lon], 
        popup=f"Transformer-{int(trans['transformer_id'])}<br>{trans['installed_kva']}kVA",
        icon=folium.Icon(color="white", icon="bolt", prefix="fa")
    ).add_to(m)

# Plot Meters & Feeder Lines
phase_colors = {'A': 'purple', 'B': 'orange', 'C': 'blue', 'ABC': 'gray'}

for _, row in df_export.iterrows():
    m_lat, m_lon = row['lat'], row['lon']
    t_lat, t_lon = trans_loc_map[int(row['transformer_id'])]
    
    p_color = phase_colors.get(row['phase_id'], 'gray')
    
    v_actual = row['v_actual']
    v_color = 'green' if v_actual > 220 else ('yellow' if v_actual > 210 else 'red')

    radius = 5 if row['has_solar'] else 3
    
    folium.PolyLine(
        locations=[(m_lat, m_lon), (t_lat, t_lon)],
        color=p_color,
        weight=1.5,
        opacity=0.4
    ).add_to(m)

    popup = f"""
    ID: {row['meter_id']}<br>
    Name: {row.get('building_name', 'N/A')}<br>
    Load: {row['peak_load_kw']}kW<br>
    V: {v_actual}V
    """
    folium.CircleMarker(
        location=[m_lat, m_lon],
        radius=radius,
        color=v_color,
        fill=True,
        fill_color=p_color,
        fill_opacity=0.7,
        popup=popup
    ).add_to(m)

m.save("map_utcc_grid.html")

print("="*40)
print("SUCCESS: UTCC Static Grid Dataset Generated")
print(f"1. utcc_dataset_meters.csv ({len(df_export)} meters)")
print(f"2. utcc_dataset_transformer_sizing.csv ({len(df_trans)} transformers)")
print(f"3. map_utcc_grid.html")
print("="*40)
