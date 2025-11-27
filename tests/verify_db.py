import sqlite3
import time
import os


def verify_database():
    db_path = "smart_meter.db"

    if not os.path.exists(db_path):
        print(f"Database file {db_path} not found.")
        return

    print(f"Checking database at {db_path}...")

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Check schema
        cursor.execute("PRAGMA table_info(readings)")
        columns = [info[1] for info in cursor.fetchall()]
        print(f"Columns in readings table: {columns}")

        if "net_emission" in columns:
            print("SUCCESS: net_emission column exists.")
        else:
            print("FAILURE: net_emission column MISSING.")

        # Check data
        cursor.execute("SELECT COUNT(*) FROM readings")
        count = cursor.fetchone()[0]
        print(f"Total readings: {count}")

        if count > 0:
            cursor.execute(
                "SELECT id, timestamp, net_emission FROM readings ORDER BY id DESC LIMIT 5"
            )
            rows = cursor.fetchall()
            print("Last 5 readings:")
            for row in rows:
                print(f"ID: {row[0]}, Time: {row[1]}, Net Emission: {row[2]}")
        else:
            print("No readings found yet.")

        conn.close()

    except Exception as e:
        print(f"Error verifying database: {e}")


if __name__ == "__main__":
    # Wait a bit for server to start and generate data
    print("Waiting 5 seconds for server to generate data...")
    time.sleep(5)
    verify_database()
