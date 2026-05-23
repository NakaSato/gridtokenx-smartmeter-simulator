import json
import logging
from pathlib import Path
from typing import Dict


logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).parent.parent.parent.parent / "data" / "geojson"
CLEANED_DIR = DATA_DIR / "cleaned"
CLEANED_DIR.mkdir(exist_ok=True)


def clean_feature(feature: Dict, file_type: str) -> Dict:
    """Standardize properties and cleanup geometry for a feature."""
    props = feature.get("properties", {})
    geom = feature.get("geometry")
    if not geom:
        return feature

    new_props = {}

    if file_type == "substation":
        new_props = {
            "name": props.get("name_e") or props.get("subname_t"),
            "name_th": props.get("name_t") or props.get("subname_t"),
            "code": props.get("stationid") or f"SUB_{props.get('fid')}",
            "province": props.get("changwat"),
            "district": props.get("amphoe"),
            "subdistrict": props.get("tambol"),
            "status": props.get("status", "EXISTING").lower(),
            "load_mw": props.get("load_2573"),
        }
    elif file_type == "line":
        new_props = {
            "name": props.get("linename") or props.get("uniteng"),
            "code": f"LINE_{props.get('linecode') or props.get('fid')}_{props.get('fid')}",
            "voltage_kv": props.get("voltage") or 115.0,
            "status": "in_service",
        }
    elif file_type == "plant":
        new_props = {
            "name": props.get("sub_en") or "Unknown Plant",
            "name_th": props.get("sub_th"),
            "capacity_mw": props.get("cap_mw", 0.0),
            "status": "operating",
        }
    elif file_type == "tower":
        new_props = {
            "tower_number": props.get("towernum"),
            "line_code": props.get("linecode1"),
            "line_name": props.get("line1"),
        }
    elif file_type == "samui":
        power_type = props.get("power")
        new_props = {
            "name": props.get("name")
            or props.get("name:en")
            or f"Samui_{power_type}_{props.get('osmid')}",
            "type": power_type,
            "voltage": props.get("voltage"),
            "operator": props.get("operator") or "PEA",
            "osmid": props.get("osmid"),
        }
    elif file_type == "zone":
        new_props = {
            "name": props.get("name_e")
            or props.get("sub_en")
            or props.get("prov_namee")
            or f"Zone_{props.get('fid')}",
            "name_th": props.get("name_t")
            or props.get("sub_th")
            or props.get("prov_namt"),
            "province": props.get("changwat") or props.get("prov_namt"),
            "load_mw": props.get("load_2573") or props.get("load_2573_sum"),
        }

    # Preserve FID if present
    if "fid" in props:
        new_props["fid"] = props["fid"]

    return {"type": "Feature", "geometry": geom, "properties": new_props}


def process_file(file_name: str, file_type: str):
    input_path = DATA_DIR / file_name
    output_path = CLEANED_DIR / file_name

    if not input_path.exists():
        logger.warning(f"File not found: {file_name}")
        return

    logger.info(f"Cleaning {file_name}...")

    # For very large files, we might need a streaming approach,
    # but for now we'll load if it fits in memory (<1GB)
    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    features = data.get("features", [])
    cleaned_features = [clean_feature(f, file_type) for f in features]

    output_data = {"type": "FeatureCollection", "features": cleaned_features}

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False)

    logger.info(f"Saved cleaned file to {output_path.name}")


def run_cleanup():
    # Substations
    process_file("egat_substations.geojson", "substation")

    # Power Plants
    process_file("egat_power_plants.geojson", "plant")
    process_file("egat_combined_gen.geojson", "plant")
    process_file("egat_gen_data.geojson", "plant")

    # Lines
    process_file("egat_lines.geojson", "line")
    process_file("egat_combined_lines.geojson", "line")
    for i in range(1, 5):
        process_file(f"egat_lines_section{i}.geojson", "line")

    # Towers
    process_file("egat_combined_towers.geojson", "tower")
    for i in range(1, 5):
        process_file(f"egat_towers_section{i}.geojson", "tower")

    # Zones & Loads
    process_file("egat_gen_zones.geojson", "zone")
    process_file("egat_combined_load.geojson", "zone")
    process_file("egat_district_load.geojson", "zone")
    process_file("pea_nohv_mvcond_merge.geojson", "zone")
    process_file("koh_samui_grid_infrastructure.geojson", "samui")


if __name__ == "__main__":
    run_cleanup()
