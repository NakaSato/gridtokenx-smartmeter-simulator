import json
import logging
import os
import hashlib
from datetime import datetime
from pathlib import Path
from decimal import Decimal
from typing import Dict, List, Any, Optional

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from smart_meter_simulator.database.models import Base, Substation, PowerLine, PowerPlant

from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load .env files
load_dotenv()
load_dotenv(Path(__file__).parent.parent.parent.parent / ".env")
load_dotenv(Path(__file__).parent.parent.parent.parent / ".env.local", override=True)

# Load database URL from environment
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
        coords = geom.get("coordinates", [0, 0])
        
        # Handle Point geometry
        lon, lat = coords if isinstance(coords[0], (int, float)) else coords[0]

        feature_str = json.dumps(coords)
        h = hashlib.md5(f"{file_path.name}_{i}_{feature_str}".encode()).hexdigest()
        code_val = f"SUB_{file_path.stem[:20]}_{h}"[:50]
        
        sub = Substation(
            name=props.get("name") or props.get("name_e") or props.get("subname_t") or f"Substation_{props.get('fid')}",
            code=code_val,
            voltage_level_kv=props.get("voltage") or get_voltage(props),
            operator="EGAT",
            type="transmission",
            province=props.get("province") or props.get("changwat"),
            district=props.get("district") or props.get("amphoe"),
            status=(props.get("status") or "EXISTING").lower(),
            latitude=lat,
            longitude=lon
        )
        session.add(sub)
    session.commit()

def ingest_lines(session: Session, file_path: Path):
    if not file_path.exists():
        return
    
    logger.info(f"Ingesting lines from {file_path.name}")
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    for i, feature in enumerate(data.get("features", [])):
        props = feature["properties"]
        geom = feature["geometry"]
        
        feature_str = json.dumps(geom.get("coordinates", []))
        h = hashlib.md5(f"{file_path.name}_{i}_{feature_str}".encode()).hexdigest()
        code_val = f"LINE_{file_path.stem[:20]}_{h}"[:50]
        
        line = PowerLine(
            name=props.get("name") or props.get("linename") or props.get("uniteng"),
            code=code_val,
            voltage_level_kv=props.get("voltage") or 115.0,
            line_type="overhead",
            status=props.get("status") or "in_service",
            path_json=geom
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
    
    for i, feature in enumerate(data.get("features", [])):
        props = feature["properties"]
        geom = feature["geometry"]
        coords = geom.get("coordinates", [0, 0])
        lon, lat = coords if isinstance(coords[0], (int, float)) else coords[0]
        
        feature_str = json.dumps(coords)
        h = hashlib.md5(f"{file_path.name}_{i}_{feature_str}".encode()).hexdigest()
        plant_id = f"PLANT_{file_path.stem[:20]}_{h}"[:50]
        
        plant = PowerPlant(
            plant_id=plant_id,
            name=props.get("name") or props.get("sub_en") or "Unknown Plant",
            plant_type="oil/gas" if "power station" in (props.get("name") or props.get("sub_en") or "").lower() else "thermal",
            capacity_mw=props.get("capacity_mw") or props.get("cap_mw", 0.0),
            status=props.get("status") or "operating",
            operator="EGAT",
            latitude=lat,
            longitude=lon
        )
        session.add(plant)
    session.commit()

def run_ingestion():
    engine = create_engine(DATABASE_URL)
    
    logger.info("Initializing schema...")
    with engine.begin() as conn:
        conn.execute(text("DROP SCHEMA IF EXISTS grid CASCADE"))
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS grid"))
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
            
        logger.info("Ingestion complete!")

if __name__ == "__main__":
    run_ingestion()
