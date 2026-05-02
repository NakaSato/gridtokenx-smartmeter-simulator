import json
import hashlib
from pathlib import Path

file_path = Path("data/geojson/cleaned/egat_combined_load.geojson")
with open(file_path, "r") as f:
    data = json.load(f)

codes = set()
for i, feature in enumerate(data.get("features", [])):
    props = feature["properties"]
    geom = feature["geometry"]
    fallback_hash = hashlib.md5(str(geom["coordinates"]).encode()).hexdigest()[:6]
    base_code = f"{props.get('code')}_{props.get('fid')}" if props.get('code') and props.get('fid') else props.get("code") or props.get("stationid") or props.get("sub_code") or f"Z_{props.get('fid')}"
    code_val = f"{base_code}_{file_path.stem}_{i}_{fallback_hash}"[:50]
    
    if code_val in codes:
        print(f"DUPLICATE GENERATED CODE FOUND: {code_val} at index {i}")
    codes.add(code_val)
    if code_val == "Z_None_egat_combined_load_700_f32652":
        print(f"Found exactly at index {i}")

print("Total features:", len(data.get("features", [])))
print("Total unique codes:", len(codes))
