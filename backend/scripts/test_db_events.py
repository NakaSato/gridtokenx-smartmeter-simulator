import asyncio
import os
from smart_meter_simulator.core.db import DatabaseManager
from smart_meter_simulator.config import get_config

async def test_db():
    config = get_config()
    db_url = config.database_url
    print(f"Testing DB at {db_url}")
    
    db = DatabaseManager(db_url)
    await db.init_db()
    
    # Save an event
    event_id = await db.save_grid_event(
        event_type="bottleneck",
        severity="warning",
        message="Test bottleneck event",
        metadata={"line": "Test Line", "loading": 95.0}
    )
    print(f"Saved event ID: {event_id}")
    
    # Retrieve events
    events = await db.get_grid_events()
    print(f"Retrieved {len(events)} events")
    for e in events:
        print(f"- {e['timestamp']}: {e['message']} (Metadata: {e['metadata']})")
    
    await db.close()

if __name__ == "__main__":
    asyncio.run(test_db())
