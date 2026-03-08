import asyncio
import httpx
import pytest
from datetime import datetime

BASE_URL = "http://localhost:8082"

@pytest.mark.asyncio
async def test_grid_history_api():
    """Verify that the history API returns data."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        # 1. Check history (might be empty initially if simulator hasn't ticked)
        response = await client.get(f"{BASE_URL}/api/grid/history")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert isinstance(data["history"], list)

@pytest.mark.asyncio
async def test_control_api():
    """Verify that island/reconnect APIs respond correctly."""
    async with httpx.AsyncClient() as client:
        # 1. Test Island
        response = await client.post(f"{BASE_URL}/api/control/island")
        assert response.status_code == 200
        data = response.json()
        assert "success" in data
        
        # 2. Test Reconnect
        response = await client.post(f"{BASE_URL}/api/control/reconnect")
        assert response.status_code == 200
        data = response.json()
        assert "success" in data

if __name__ == "__main__":
    # For manual run
    async def main():
        async with httpx.AsyncClient(timeout=30.0) as client:
            print("Checking Initial Grid History...")
            r = await client.get(f"{BASE_URL}/api/grid/history")
            print(f"Initial History count: {len(r.json().get('history', []))}")
            
            print("\nTriggering Simulation Tick...")
            r = await client.post(f"{BASE_URL}/api/control/tick")
            print(f"Tick: {r.json()}")
            
            # Wait a moment for persistence
            await asyncio.sleep(2)
            
            print("\nChecking Grid History after Tick...")
            r = await client.get(f"{BASE_URL}/api/grid/history")
            history = r.json().get('history', [])
            print(f"New History count: {len(history)}")
            if history:
                print(f"Latest metrics: {history[0]}")
            
            print("\nTesting Island Mode...")
            r = await client.post(f"{BASE_URL}/api/control/island")
            print(f"Island: {r.json()}")
            
            print("\nTesting Reconnection...")
            r = await client.post(f"{BASE_URL}/api/control/reconnect")
            print(f"Reconnect: {r.json()}")
            
    asyncio.run(main())
