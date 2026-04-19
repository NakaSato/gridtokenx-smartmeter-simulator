import asyncio
import os
import datetime
from smart_meter_simulator.core.db import DatabaseManager
from smart_meter_simulator.config import get_config

async def test_etl():
    config = get_config()
    db_url = config.database_url
    print(f"Testing ETL Pipeline. Target: {db_url}")
    
    db = DatabaseManager(db_url)
    initialized = await db.init_db()
    
    if not initialized:
        print("⚠️  PostgreSQL unavailable. Falling back to in-memory SQLite for logic verification...")
        db = DatabaseManager("sqlite+aiosqlite:///:memory:")
        await db.init_db()
    
    # Mock data for ETL
    samui_state = {
        "timestamp": datetime.datetime.now(datetime.timezone.utc),
        "node_id": "koh_samui_hub_1",
        "metrics": {
            "load_demand_mw": 45.2,
            "grid_import_115kv_mw": 40.0,
            "bess_discharge_mw": 5.2,
            "local_gen_diesel_mw": 0.0
        },
        "constraints": {
            "cable_115kv_kmb_utilization_pct": 92.5,
            "bess_soc_pct": 78.0,
            "export_33kv_phangan_mw": 12.4
        },
        "economic_indicators": {
            "marginal_cost_per_mwh": 125.50,
            "carbon_intensity_gco2_kwh": 450
        }
    }
    
    # Save node state
    node_id = await db.save_node_state(samui_state)
    if node_id:
        print(f"✅ Successfully saved Samui node state ID: {node_id}")
    else:
        print("❌ Failed to save node state")
    
    # Retrieve node history
    history = await db.get_node_history("koh_samui_hub_1")
    print(f"Retrieved {len(history)} history records for Samui")
    for s in history:
        print(f"  - {s['timestamp']}: Load={s['metrics']['load_demand_mw']} MW, "
              f"BESS Discharge={s['metrics']['bess_discharge_mw']} MW, "
              f"Utilization={s['constraints']['utilization_pct']}%")
    
    await db.close()

if __name__ == "__main__":
    asyncio.run(test_etl())
