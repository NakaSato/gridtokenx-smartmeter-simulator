import sqlite3
import os

DB_FILES = ["smart_meter.db", "src/smart_meter.db"]
TARGET_ID = "e039c1f0-242e-4373-b0cd-1ea589ed3fbe"

for db_file in DB_FILES:
    if not os.path.exists(db_file):
        print(f"Skipping {db_file}: Not found.")
        continue

    print(f"\n--- Checking {db_file} ---")
    try:
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()

        cursor.execute("SELECT count(*) FROM meters")
        count = cursor.fetchone()[0]
        print(f"Total Meters: {count}")

        cursor.execute("SELECT meter_id, meter_type, location FROM meters")
        rows = cursor.fetchall()
        found = False

        for row in rows:
            print(f"Meter: {row}")
            if row[0] == TARGET_ID:
                found = True

        if found:
            print(f"SUCCESS: Target meter {TARGET_ID} FOUND in {db_file}.")
        else:
            print(f"FAILURE: Target meter {TARGET_ID} NOT found in {db_file}.")

        conn.close()
    except Exception as e:
        print(f"Error reading {db_file}: {e}")
