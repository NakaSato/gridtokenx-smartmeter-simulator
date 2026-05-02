import json
import logging
from datetime import datetime
from pathlib import Path
from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import Session
from geoalchemy2.shape import from_shape
from shapely.geometry import Point, LineString, shape, MultiLineString
from smart_meter_simulator.database.models import Base, Substation, PowerLine, PowerPlant

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Use sync driver for ingestion script
DATABASE_URL = "postgresql://gridtokenx:gridtokenx_password@127.0.0.1:5433/gridtokenx_gis"

def ingest_data():
    engine = create_engine(DATABASE_URL)
    
    # Ensure PostGIS and grid schema exist (Resetting for model update)
    with engine.begin() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis"))
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
                    INSERT INTO grid.substations (name, code, voltage_level_kv, operator, type, capacity_mva, province, location, status, created_at, updated_at)
                    VALUES (:name, :code, :voltage_kv, 'EGAT', :type, :capacity_mva, :province, ST_SetSRID(ST_Point(:lon, :lat), 4326), 'in_service', :now, :now)
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
            
            res = session.execute(text("SELECT id, code, name, ST_X(location::geometry) as lon, ST_Y(location::geometry) as lat FROM grid.substations"))
            sub_data = {row.code: row for row in res}
            
            for idx, d in enumerate(lines_json):
                code = f"EGAT_LINE_{idx:04d}"
                from_sub = sub_data.get(d["from_substation"])
                to_sub = sub_data.get(d["to_substation"])
                
                if from_sub and to_sub:
                    wkt = f"MULTILINESTRING(({from_sub.lon} {from_sub.lat}, {to_sub.lon} {to_sub.lat}))"
                    stmt = text("""
                        INSERT INTO grid.power_lines (name, code, from_substation_id, to_substation_id, voltage_level_kv, line_type, circuit_count, conductor_type, status, geom, created_at, updated_at)
                        VALUES (:name, :code, :from_id, :to_id, :voltage_kv, 'overhead', :circuit, :conductor, 'in_service', ST_GeogFromText(:geom), :now, :now)
                    """)
                    session.execute(stmt, {
                        "name": f"{from_sub.name} - {to_sub.name}", "code": code,
                        "from_id": from_sub.id, "to_id": to_sub.id, "voltage_kv": d["voltage_kv"],
                        "circuit": d.get("circuit", 1), "conductor": d.get("conductor"),
                        "geom": f"SRID=4326;{wkt}", "now": now
                    })
            session.commit()

        # 3. Ingest Spotlight GeoJSON
        BACKEND_DATA_DIR = Path(__file__).parent.parent.parent.parent / "data"
        spot_path = BACKEND_DATA_DIR / "geojson" / "spotlight_samui.geojson"
        if not spot_path.exists():
            # Fallback to local data dir
            spot_path = DATA_DIR / "spotlight_samui.geojson"
            
        if spot_path.exists():
            logger.info(f"Ingesting spotlight data from {spot_path}")
            with open(spot_path, "r", encoding="utf-8") as f:
                spot_json = json.load(f)
            
            for idx, feature in enumerate(spot_json["features"]):
                props = feature["properties"]
                ftype = props.get("type")
                geom = feature["geometry"]
                
                if ftype == "substation":
                    # Make code unique by including index
                    code = f"SPOT_SUB_{idx:04d}"
                    lon, lat = geom["coordinates"]
                    stmt = text("""
                        INSERT INTO grid.substations (name, code, voltage_level_kv, operator, type, location, status, created_at, updated_at)
                        VALUES (:name, :code, :voltage_kv, 'PEA', :type, ST_SetSRID(ST_Point(:lon, :lat), 4326), 'in_service', :now, :now)
                    """)
                    session.execute(stmt, {
                        "name": props["name"], "code": code, "voltage_kv": props.get("voltage_kv") or 115.0,
                        "type": props.get("substation_type", "distribution"), "lon": lon, "lat": lat, "now": now
                    })
                
                elif ftype == "plant":
                    code = f"SPOT_PLANT_{idx:04d}"
                    lon, lat = geom["coordinates"]
                    stmt = text("""
                        INSERT INTO grid.power_plants (plant_id, name, plant_type, capacity_mw, status, location, source, created_at, updated_at)
                        VALUES (:plant_id, :name, :plant_type, :capacity_mw, 'operating', ST_SetSRID(ST_Point(:lon, :lat), 4326), :source, :now, :now)
                    """)
                    session.execute(stmt, {
                        "plant_id": code, "name": props["name"],
                        "plant_type": "oil/gas" if "power station" in props["name"].lower() else "solar",
                        "capacity_mw": props.get("capacity_mw", 0.0), "lon": lon, "lat": lat,
                        "source": props.get("source", "Spotlight"), "now": now
                    })

                elif ftype == "transmission":
                    code = f"SPOT_LINE_{idx:04d}"
                    voltage_str = str(props.get("voltage_class", "115000")).split(";")[0]
                    voltage_kv = float(voltage_str) / 1000 if voltage_str.isdigit() else 115.0
                    
                    geom_obj = shape(geom)
                    if geom_obj.geom_type == 'LineString':
                        geom_obj = MultiLineString([geom_obj])
                    
                    wkt = geom_obj.wkt
                    stmt = text("""
                        INSERT INTO grid.power_lines (name, code, voltage_level_kv, line_type, status, geom, created_at, updated_at)
                        VALUES (:name, :code, :voltage_kv, :line_type, 'in_service', ST_GeogFromText(:geom), :now, :now)
                    """)
                    session.execute(stmt, {
                        "name": props["name"], "code": code, "voltage_kv": voltage_kv,
                        "line_type": "submarine" if "Connector" in props["name"] else "overhead",
                        "geom": f"SRID=4326;{wkt}", "now": now
                    })
            session.commit()
            logger.info("Ingestion complete.")

if __name__ == "__main__":
    ingest_data()
