import asyncio
from smart_meter_simulator.core.engine import SimulationEngine
from smart_meter_simulator.core.meter import SmartMeter
from smart_meter_simulator.app import app, engine, delete_meter
from fastapi.testclient import TestClient


# Mock engine for testing
class MockEngine:
    def __init__(self):
        self.meters = []
        self.running = False


async def test_remove_meter():
    print("Testing Remove Meter Functionality...")

    # Setup
    global engine
    engine = MockEngine()

    # Create a meter
    meter_config = {
        "meter_id": "test-meter-remove",
        "meter_type": "Solar_Prosumer",
        "location": "Test Location",
    }
    meter = SmartMeter(meter_config)
    engine.meters.append(meter)

    print(f"Initial meters: {len(engine.meters)}")
    assert len(engine.meters) == 1

    # Test delete
    # Note: We need to inject the mock engine into the app module or mock the global variable
    # Since we can't easily inject into the running app module from here without patching,
    # we will test the logic by calling the function directly if possible, or mocking app.engine

    # Let's try to patch the engine in app module
    import smart_meter_simulator.app as app_module

    app_module.engine = engine

    # Call delete_meter directly (it's an async function)
    result = await app_module.delete_meter("test-meter-remove")

    print(f"Delete result: {result}")

    assert result["success"] is True
    assert len(engine.meters) == 0

    print("Remove Meter test passed.")


if __name__ == "__main__":
    asyncio.run(test_remove_meter())
