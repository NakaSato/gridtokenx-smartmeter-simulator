from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

DATABASE_URL = (
    "postgresql://gridtokenx:gridtokenx_password@127.0.0.1:5433/gridtokenx_gis"
)


def verify():
    engine = create_engine(DATABASE_URL)
    with Session(engine) as session:
        sub_count = session.execute(
            text("SELECT count(*) FROM grid.substations")
        ).scalar()
        line_count = session.execute(
            text("SELECT count(*) FROM grid.power_lines")
        ).scalar()
        plant_count = session.execute(
            text("SELECT count(*) FROM grid.power_plants")
        ).scalar()

        print(f"Substations: {sub_count}")
        print(f"Lines: {line_count}")
        print(f"Power Plants: {plant_count}")

        # Check some Koh Samui data
        samui_lines = session.execute(
            text("SELECT name FROM grid.power_lines WHERE name LIKE '%Samui%'")
        ).fetchall()
        print(f"Samui Lines: {[line[0] for line in samui_lines]}")


if __name__ == "__main__":
    verify()
