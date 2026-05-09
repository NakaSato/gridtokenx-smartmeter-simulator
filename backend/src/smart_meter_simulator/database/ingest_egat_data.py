import json
import logging
from datetime import datetime
from pathlib import Path
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
from smart_meter_simulator.database.models import Base, Substation, PowerLine, PowerPlant

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Use sync driver for ingestion script
DATABASE_URL = "postgresql://gridtokenx:gridtokenx_password@127.0.0.1:5433/gridtokenx_gis"

def ingest_data():
    engine = create_engine(DATABASE_URL)
    
    # Ensure grid schema exists
    with engine.begin() as conn:
        conn.execute(text("DROP SCHEMA IF EXISTS grid CASCADE"))
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS grid"))
        Base.metadata.create_all(conn)

    now = datetime.utcnow()

    with Session(engine) as session:
        DATA_DIR = Path(__file__).parent.parent / "data"
        
        # 1. Ingest Substations
        subs_path = DATA_DIR / "egat_substations.json"
        if subs_path.exists():
            logger.info(f"Ingesting substations from {subs_path}")
            with open(subs_path, "r", encoding="utf-8") as f:
                subs_json = json.load(f)
            
            for code, d in subs_json.items():
                stmt = text("""
                    INSERT INTO grid.substations (name, code, voltage_level_kv, operator, type, capacity_mva, province, latitude, longitude, status, created_at, updated_at)
                    VALUES (:name, :code, :voltage_kv, 'EGAT', :type, :capacity_mva, :province, :lat, :lon, 'in_service', :now, :now)
                """)
                session.execute(stmt, {
                    "name": d["name"], "code": code, "voltage_kv": d["voltage_kv"],
                    "type": d["type"], "capacity_mva": d.get("capacity_mva"),
                    "province": d.get("province"), "lon": d["longitude"], "lat": d["latitude"],
                    "now": now
                })
            session.commit()

        # 2. Ingest Lines
        lines_path = DATA_DIR / "egat_lines.json"
        if lines_path.exists():
            logger.info(f"Ingesting lines from {lines_path}")
            with open(lines_path, "r", encoding="utf-8") as f:
                lines_json = json.load(f)
            
            res = session.execute(text("SELECT id, code, name, longitude, latitude FROM grid.substations"))
            sub_data = {row.code: row for row in res}
            
            for idx, d in enumerate(lines_json):
                code = f"EGAT_LINE_{idx:04d}"
                from_sub = sub_data.get(d["from_substation"])
                to_sub = sub_data.get(d["to_substation"])
                
                if from_sub and to_sub:
                    path_json = {
                        "type": "LineString",
                        "coordinates": [[float(from_sub.longitude), float(from_sub.latitude)], [float(to_sub.longitude), float(to_sub.latitude)]]
                    }
                    stmt = text("""
                        INSERT INTO grid.power_lines (name, code, from_substation_id, to_substation_id, voltage_level_kv, line_type, status, path_json, created_at, updated_at)
                        VALUES (:name, :code, :from_id, :to_id, :voltage_kv, 'overhead', 'in_service', :path_json, :now, :now)
                    """)
                    session.execute(stmt, {
                        "name": f"{from_sub.name} - {to_sub.name}", "code": code,
                        "from_id": from_sub.id, "to_id": to_sub.id, "voltage_kv": d["voltage_kv"],
                        "path_json": json.dumps(path_json), "now": now
                    })
            session.commit()
            logger.info("Ingestion complete.")

if __name__ == "__main__":
    ingest_data()

if __name__ == "__main__":
    ingest_data()
