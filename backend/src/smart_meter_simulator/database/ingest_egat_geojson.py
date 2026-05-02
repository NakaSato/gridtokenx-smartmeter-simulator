import json
import logging
import os
from datetime import datetime
import hashlib
from pathlib import Path
from decimal import Decimal
from typing import Dict, List, Any, Optional

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
from geoalchemy2.shape import from_shape
from shapely.geometry import shape, Point, MultiPoint, LineString, MultiLineString, Polygon, MultiPolygon

from smart_meter_simulator.database.models import Base, Substation, PowerLine, PowerPlant, Tower, Zone

from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load .env files
load_dotenv()
load_dotenv(Path(__file__).parent.parent.parent.parent / ".env")
load_dotenv(Path(__file__).parent.parent.parent.parent / ".env.local", override=True)

# Load database URL from environment - Prefer GIS_DATABASE_URL for this script
DATABASE_URL = os.getenv("GIS_DATABASE_URL") or os.getenv("DATABASE_URL")
if not DATABASE_URL:
    DATABASE_URL = "postgresql://gridtokenx:gridtokenx_password@127.0.0.1:5433/gridtokenx_gis"

DATA_DIR = Path(__file__).parent.parent.parent.parent / "data" / "geojson" / "cleaned"

# Ensure we use a synchronous driver for this script
if "+asyncpg" in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.replace("+asyncpg", "")

def get_voltage(props: Dict) -> float:
    """Extract highest voltage level from substation properties."""
    voltages = []
    for v in ["voltage500", "voltage230", "voltage132", "voltage115", "voltage69"]:
        val = str(props.get(v, "")).strip()
        if val and val.replace('.', '', 1).isdigit():
            voltages.append(float(val))
    return max(voltages) if voltages else 115.0

def clean_geometry(geom: Dict) -> Any:
    """Convert GeoJSON geometry to Shapely object and handle Multi-types."""
    obj = shape(geom)
    # Ensure Multi-types for models that expect them
    if isinstance(obj, LineString):
        return MultiLineString([obj])
    if isinstance(obj, Polygon):
        return MultiPolygon([obj])
    return obj

def ingest_substations(session: Session, file_path: Path):
    if not file_path.exists():
        logger.warning(f"File not found: {file_path}")
        return
    
    logger.info(f"Ingesting substations from {file_path.name}")
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    for i, feature in enumerate(data.get("features", [])):
        props = feature["properties"]
        geom = feature["geometry"]
        feature_str = json.dumps(geom.get("coordinates", []))
        h = hashlib.md5(f"{file_path.name}_{i}_{feature_str}".encode()).hexdigest()
        code_val = f"SUB_{file_path.stem[:20]}_{h}"[:50]
        
        sub = Substation(
            name=props.get("name") or props.get("name_e") or props.get("subname_t") or f"Substation_{props.get('fid')}",
            name_th=props.get("name_th") or props.get("name_t") or props.get("subname_t"),
            code=code_val,
            voltage_level_kv=props.get("voltage") or get_voltage(props),
            operator="EGAT",
            type="transmission",
            load_mw=props.get("load_mw") or props.get("load_2573"),
            province=props.get("province") or props.get("changwat"),
            district=props.get("district") or props.get("amphoe"),
            subdistrict=props.get("subdistrict") or props.get("tambol"),
            status=(props.get("status") or "EXISTING").lower(),
            location=from_shape(shape(geom).centroid, srid=4326)
        )
        session.add(sub)
    session.commit()

def ingest_lines(session: Session, file_path: Path):
    if not file_path.exists():
        return
    
    logger.info(f"Ingesting lines from {file_path.name}")
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    import hashlib
    for i, feature in enumerate(data.get("features", [])):
        props = feature["properties"]
        geom = feature["geometry"]
        
        feature_str = json.dumps(geom.get("coordinates", []))
        h = hashlib.md5(f"{file_path.name}_{i}_{feature_str}".encode()).hexdigest()
        code_val = f"LINE_{file_path.stem[:20]}_{h}"[:50]
        
        line = PowerLine(
            name=props.get("name") or props.get("linename") or props.get("uniteng"),
            code=code_val,
            voltage_level_kv=props.get("voltage") or props.get("voltage") or 115.0,
            line_type="overhead",
            status=props.get("status") or "in_service",
            geom=from_shape(clean_geometry(geom), srid=4326)
        )
        session.add(line)
        if len(session.new) > 500:
            session.commit()
    session.commit()

def ingest_plants(session: Session, file_path: Path):
    if not file_path.exists():
        return
    
    logger.info(f"Ingesting plants from {file_path.name}")
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    import hashlib
    
    for i, feature in enumerate(data.get("features", [])):
        props = feature["properties"]
        geom = feature["geometry"]
        
        feature_str = json.dumps(geom.get("coordinates", []))
        h = hashlib.md5(f"{file_path.name}_{i}_{feature_str}".encode()).hexdigest()
        plant_id = f"PLANT_{file_path.stem[:20]}_{h}"[:50]
        
        plant = PowerPlant(
            plant_id=plant_id,
            name=props.get("name") or props.get("sub_en") or "Unknown Plant",
            name_th=props.get("name_th") or props.get("sub_th"),
            plant_type="oil/gas" if "power station" in (props.get("name") or props.get("sub_en") or "").lower() else "thermal",
            capacity_mw=props.get("capacity_mw") or props.get("cap_mw", 0.0),
            status=props.get("status") or "operating",
            operator="EGAT",
            location=from_shape(shape(geom).centroid, srid=4326),
            source="EGAT Data"
        )
        session.add(plant)
    session.commit()


def ingest_towers(session: Session, file_path: Path):
    if not file_path.exists():
        return
    
    logger.info(f"Ingesting towers from {file_path.name}")
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    for feature in data.get("features", []):
        props = feature["properties"]
        geom = feature["geometry"]
        
        tower = Tower(
            tower_number=props.get("tower_number") or props.get("towernum"),
            line_code=props.get("line_code") or props.get("linecode1"),
            line_name_1=props.get("line_name") or props.get("line1"),
            line_name_2=props.get("line2"),
            type=props.get("type"),
            location=from_shape(shape(geom).centroid, srid=4326)
        )
        session.add(tower)
        if len(session.new) > 1000:
            session.commit()
    session.commit()

def ingest_zones(session: Session, file_path: Path):
    if not file_path.exists():
        return
    
    logger.info(f"Ingesting zones from {file_path.name}")
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    import hashlib
    for i, feature in enumerate(data.get("features", [])):
        props = feature["properties"]
        geom = feature["geometry"]
        
        feature_str = json.dumps(geom.get("coordinates", []))
        h = hashlib.md5(f"{file_path.name}_{i}_{feature_str}".encode()).hexdigest()
        code_val = f"ZONE_{file_path.stem[:20]}_{h}"[:50]
        
        zone = Zone(
            name=props.get("name") or props.get("name_e") or props.get("sub_en") or props.get("prov_namee") or f"Zone_{props.get('fid')}",
            name_th=props.get("name_th") or props.get("name_t") or props.get("sub_th") or props.get("prov_namt"),
            code=code_val,
            zone_type="district" if "district" in file_path.name else "area",
            operator="EGAT",
            load_mw=props.get("load_mw") or props.get("load_2573") or props.get("load_2573_sum"),
            province=props.get("province") or props.get("changwat") or props.get("prov_namt"),
            geom=from_shape(clean_geometry(geom), srid=4326)
        )
        session.add(zone)
        if len(session.new) >= 5:
            try:
                session.commit()
            except Exception as e:
                logger.error(f"Error committing batch in {file_path.name}: {e}")
                session.rollback()
    try:
        session.commit()
    except Exception as e:
        logger.error(f"Error committing final batch in {file_path.name}: {e}")
        session.rollback()

def ingest_samui(session: Session, file_path: Path):
    if not file_path.exists():
        return
    
    logger.info(f"Ingesting Samui infrastructure from {file_path.name}")
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    for feature in data.get("features", []):
        props = feature["properties"]
        geom = feature["geometry"]
        power_type = props.get("type")
        
        if power_type == "generator":
            obj = PowerPlant(
                plant_id=f"SAMUI_GEN_{props.get('osmid')}",
                name=props.get("name"),
                plant_type="renewable",
                capacity_mw=0.0,
                status="operating",
                operator=props.get("operator"),
                location=from_shape(shape(geom).centroid, srid=4326),
                source="OSM/Samui Data"
            )
        elif power_type == "substation":
            obj = Substation(
                name=props.get("name"),
                code=f"SAMUI_SUB_{props.get('osmid')}",
                voltage_level_kv=115.0,
                operator=props.get("operator"),
                location=from_shape(clean_geometry(geom).centroid, srid=4326)
            )
        elif power_type in ["minor_line", "line", "cable"]:
            raw_volt = props.get("voltage", "")
            volt_kv = 22.0
            if raw_volt:
                first_volt = str(raw_volt).split(";")[0].strip()
                if first_volt.replace('.', '', 1).isdigit():
                    v = float(first_volt)
                    volt_kv = v / 1000.0 if v > 1000 else v
                    
            obj = PowerLine(
                name=props.get("name") or f"Samui Line {props.get('osmid')}",
                code=f"SAMUI_LINE_{props.get('osmid')}",
                voltage_level_kv=volt_kv,
                line_type="underground" if power_type == "cable" else "overhead",
                geom=from_shape(clean_geometry(geom), srid=4326)
            )
        else:
            continue
            
        session.add(obj)
    session.commit()

def run_ingestion():
    engine = create_engine(DATABASE_URL)
    
    # Initialize Schema (Resetting as per previous script behavior)
    logger.info("Initializing schema...")
    with engine.begin() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis"))
        conn.execute(text("DROP SCHEMA IF EXISTS grid CASCADE"))
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS grid"))
        # Ensure PostGIS types are available for the 'grid' schema
        conn.execute(text("ALTER USER gridtokenx SET search_path TO grid, public"))
        conn.execute(text("SET search_path TO grid, public"))
        Base.metadata.create_all(conn)

    with Session(engine) as session:
        # 1. Substations
        ingest_substations(session, DATA_DIR / "egat_substations.geojson")
        
        # 2. Power Plants
        ingest_plants(session, DATA_DIR / "egat_power_plants.geojson")
        ingest_plants(session, DATA_DIR / "egat_combined_gen.geojson")
        ingest_plants(session, DATA_DIR / "egat_gen_data.geojson")
        
        # 3. Lines
        ingest_lines(session, DATA_DIR / "egat_lines.geojson")
        ingest_lines(session, DATA_DIR / "egat_combined_lines.geojson")
        for i in range(1, 5):
            ingest_lines(session, DATA_DIR / f"egat_lines_section{i}.geojson")
            
        # 4. Towers
        ingest_towers(session, DATA_DIR / "egat_combined_towers.geojson")
        for i in range(1, 5):
            ingest_towers(session, DATA_DIR / f"egat_towers_section{i}.geojson")
            
        # 5. Zones & Loads
        ingest_zones(session, DATA_DIR / "egat_gen_zones.geojson")
        ingest_zones(session, DATA_DIR / "egat_combined_load.geojson")
        ingest_zones(session, DATA_DIR / "egat_district_load.geojson")
        ingest_zones(session, DATA_DIR / "pea_nohv_mvcond_merge.geojson")
        
        # 6. Koh Samui Infrastructure
        ingest_samui(session, DATA_DIR / "koh_samui_grid_infrastructure.geojson")
        
        logger.info("Ingestion complete!")

if __name__ == "__main__":
    run_ingestion()
