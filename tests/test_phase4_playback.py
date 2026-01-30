import asyncio
import pytest
import pandas as pd
import os
import json
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from app.app import app
from app.core.data_source import ProfileDataSource
from app.core.engine import SimulationMode

client = TestClient(app)

@pytest.fixture
def sample_profile():
    """Create a sample CSV profile for testing."""
    profile_dir = "data/profiles"
    os.makedirs(profile_dir, exist_ok=True)
    
    path = os.path.join(profile_dir, "test_playback.csv")
    
    # Create 4 steps of data (1 hour at 15m intervals)
    now = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
    data = []
    for i in range(4):
        ts = now + timedelta(minutes=15 * i)
        data.append({
            "timestamp": ts.isoformat(),
            "METER_001": 1.5 + (i * 0.1),
            "METER_002_GEN": 2.0 + (i * 0.2),
            "METER_002_CONS": 0.5 + (i * 0.05)
        })
    
    df = pd.DataFrame(data)
    df.to_csv(path, index=False)
    yield "test_playback"
    # Cleanup
    if os.path.exists(path):
        os.remove(path)

def test_profile_data_source_loading(sample_profile):
    """Test that ProfileDataSource can load and retrieve values."""
    ds = ProfileDataSource()
    assert sample_profile in ds.list_profiles()
    
    now = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
    
    # Test METER_001 (Cons only)
    val = ds.get_value(sample_profile, "METER_001", now)
    assert val == 1.5
    
    # Test METER_002 (Gen and Cons)
    gen = ds.get_value(sample_profile, "METER_002_GEN", now)
    cons = ds.get_value(sample_profile, "METER_002_CONS", now)
    assert gen == 2.0
    assert cons == 0.5

def test_playback_api_control(sample_profile):
    """Test switching to playback mode via API."""
    with TestClient(app) as client:
        # 1. Check profiles list
        response = client.get("/api/profiles")
        assert response.status_code == 200
        assert sample_profile in response.json()["profiles"]
        
        # 2. Switch to Playback Mode
        response = client.post("/api/control/mode", json={
            "mode": "playback",
            "profile": sample_profile
        })
        assert response.status_code == 200
        assert response.json()["mode"] == "playback"
        assert response.json()["profile"] == sample_profile
        
        # 3. Verify status reflects mode
        response = client.get("/api/status")
        # Note: We need to check if 'mode' or similar is in status. 
        # Currently app.py status doesn't explicitly return mode, but it uses engine.mode
        pass

@pytest.mark.asyncio
async def test_engine_playback_tick(sample_profile):
    """Test that engine uses playback values during a tick."""
    from app.core.engine import SimulationEngine
    from app.core.meter import SmartMeter
    from app.transport.base import TransportLayer
    from unittest.mock import AsyncMock
    
    # Setup mock transport
    transport = AsyncMock(spec=TransportLayer)
    transport.send_reading.return_value = True
    transport.connect.return_value = None
    transport.send_grid_status.return_value = True
    
    # Create meter matching profile
    meter = SmartMeter({"meter_id": "METER_001", "location": "Test", "meter_type": "Residential", "user_type": "Consumer"})
    engine = SimulationEngine([meter], transport)
    
    # Set to playback mode
    engine.mode = SimulationMode.PLAYBACK
    engine.playback_profile = sample_profile
    
    # Set time to match profile
    now = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
    engine.current_sim_time = now
    
    # Run tick
    await engine.tick()
    
    # Verify reading
    assert meter.last_reading.energy_consumed == 1.5
    assert meter.last_reading.energy_generated == 0.0 # No GEN in profile for METER_001
