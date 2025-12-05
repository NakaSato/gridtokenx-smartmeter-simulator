import psycopg2
import os
from datetime import datetime

# DB Config
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "gridtokenx"
DB_USER = "gridtokenx_user"
DB_PASS = "gridtokenx_password"

try:
    conn = psycopg2.connect(
        host=DB_HOST, port=DB_PORT, dbname=DB_NAME, user=DB_USER, password=DB_PASS
    )
    cur = conn.cursor()

    print("--- Checking Row Counts ---")

    # Insert or Update Simulator User
    sim_user_id = "63c1d015-6765-4843-9ca3-5ba21ee54d7e"
    cur.execute("SELECT count(*) FROM users WHERE id = %s", (sim_user_id,))
    if cur.fetchone()[0] == 0:
        print(f"Inserting Simulator User: {sim_user_id}")
    else:
        print(f"Updating Simulator User: {sim_user_id}")
    cur.execute(
        """
        INSERT INTO users (id, email, username, password_hash, wallet_address, role, created_at, updated_at)
        VALUES (%s, 'simulator@gridtokenx.com', 'simulator_user', 'hash', 'AmeT4PvH96gx8AiuLkpjsX9ExA21oH2HtthgbvzDgnD3', 'user'::user_role, NOW(), NOW())
        ON CONFLICT (id) DO UPDATE SET wallet_address = EXCLUDED.wallet_address, updated_at = NOW();
    """,
        (sim_user_id,),
    )
    conn.commit()

    cur.execute("SELECT count(*) FROM meter_readings")
    print(f"Meter Readings Count: {cur.fetchone()[0]}")

    cur.execute("SELECT count(*) FROM users")
    print(f"Users Count: {cur.fetchone()[0]}")

    print("\n--- Listing Users ---")
    cur.execute("SELECT id, email, role FROM users LIMIT 5")
    for row in cur.fetchall():
        print(f"User: {row[0]}, {row[1]}, {row[2]}")

    print("\n--- Checking Minted Readings ---")
    cur.execute("SELECT count(*) FROM meter_readings WHERE minted = true")
    print(f"Minted Count: {cur.fetchone()[0]}")

    cur.execute("""
        SELECT id, kwh_amount, minted, mint_tx_signature, created_at
        FROM meter_readings
        WHERE minted = true
        LIMIT 5
    """)
    for row in cur.fetchall():
        print(f"Minted Reading: {row}")

    print("\n--- Checking Specific Reading 9d381c91... ---")
    cur.execute("""
        SELECT id, kwh_amount, minted, mint_tx_signature, created_at, verification_status
        FROM meter_readings
        WHERE id = '9d381c91-1f5c-4d20-b287-5028850f7a8e'
    """)
    row = cur.fetchone()
    if row:
        print(f"Reading: {row}")
    else:
        print("Reading not found.")
    print("\n--- Clearing Meter Readings ---")
    # cur.execute("DELETE FROM meter_readings")
    # conn.commit()
    # print("All meter readings deleted.")

    print("\n--- Checking Migrations ---")
    cur.execute(
        "SELECT version, description, success FROM _sqlx_migrations ORDER BY version DESC LIMIT 5"
    )
    rows = cur.fetchall()
    for row in rows:
        print(f"Migration: {row}")

    print("\n--- Checking user_role Type ---")
    cur.execute("SELECT typname FROM pg_type WHERE typname = 'user_role'")
    rows = cur.fetchall()
    if rows:
        print(f"Type found: {rows[0][0]}")
    else:
        print("Type 'user_role' NOT found.")

    cur.close()
    conn.close()

except Exception as e:
    print(f"Error: {e}")
