import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from unittest.mock import patch

from smart_meter_simulator.app import create_app
from smart_meter_simulator.core import app_state
from smart_meter_simulator.core.engine import SimulationEngine
from smart_meter_simulator.devices.ami import SmartMeter
from smart_meter_simulator.transport.base import TransportLayer


class MockTransport(TransportLayer):
    async def connect(self): pass
    async def disconnect(self): pass
    def is_connected(self) -> bool: return True
    async def send_reading(self, reading): pass
    async def send_batch(self, readings): pass
    async def send_grid_status(self, status): pass
    async def send_frequency_event(self, event): pass
    async def send_carbon_intensity(self, ci): pass
    async def send_weather(self, weather): pass
    async def send_simulation_step(self, step): pass
    async def send_alert(self, alert): pass


@pytest.fixture
def mock_engine_with_meters():
    meters = [
        SmartMeter({
            "meter_id": "meter_001",
            "meter_type": "Residential",
            "location": "Samui",
            "base_consumption": 2.0,
            "min_load_kw": 0.1,
            "max_load_kw": 10.0,
        }),
        SmartMeter({
            "meter_id": "meter_002",
            "meter_type": "Residential",
            "location": "Samui",
            "base_consumption": 1.5,
            "min_load_kw": 0.1,
            "max_load_kw": 10.0,
        })
    ]
    transport = MockTransport()
    engine = SimulationEngine(meters, transport)
    engine.interval = 60  # 1 minute ticks
    return engine


def test_loadshed_scenario_service_logic(mock_engine_with_meters):
    """Test loadshed service execution logic directly."""
    engine = mock_engine_with_meters
    service = engine.loadshed_scenario

    scenario = {
        "60": {
            "meter_001": "OUT_OF_SERVICE",
            "meter_002": "OUT_OF_SERVICE"
        },
        "120": {
            "meter_001": "IN_SERVICE"
        }
    }

    # 1. Load scenario
    assert service.load_scenario(scenario) is True
    assert len(service.active_scenario) == 2

    # 2. Start scenario
    start_time = datetime(2026, 5, 31, 12, 0, tzinfo=timezone.utc)
    service.start(start_time)
    assert service.is_active is True

    # 3. Step at 0s (no updates)
    changes = service.update_step(start_time, engine.meters)
    assert len(changes) == 0
    assert engine.meters[0].is_shed is False
    assert engine.meters[1].is_shed is False

    # 4. Step at 60s (both shedded)
    time_60s = datetime(2026, 5, 31, 12, 1, tzinfo=timezone.utc)
    changes = service.update_step(time_60s, engine.meters)
    assert len(changes) == 2
    assert engine.meters[0].is_shed is True
    assert engine.meters[1].is_shed is True

    # 5. Step at 120s (meter_001 restored, meter_002 remains shedded)
    time_120s = datetime(2026, 5, 31, 12, 2, tzinfo=timezone.utc)
    changes = service.update_step(time_120s, engine.meters)
    assert len(changes) == 1
    assert changes[0]["meter_id"] == "meter_001"
    assert changes[0]["is_shed"] is False
    assert engine.meters[0].is_shed is False
    assert engine.meters[1].is_shed is True


def test_loadshed_scenario_api_endpoints(mock_engine_with_meters):
    """Test scenario REST API endpoints via TestClient."""
    app = create_app()
    client = TestClient(app)

    # Patch the global engine state with our mock engine
    with patch.object(app_state, "engine", mock_engine_with_meters):
        # 1. Start check status (should be empty/inactive)
        status_res = client.get("/api/v1/simulation/scenarios/loadshed/status")
        assert status_res.status_code == 200
        assert status_res.json()["is_active"] is False
        assert status_res.json()["scenario_loaded"] is False

        # 2. Try start without loading (should fail)
        start_res = client.post("/api/v1/simulation/scenarios/loadshed/start")
        assert start_res.status_code == 400

        # 3. Load scenario
        scenario_payload = {
            "scenario": {
                "60": {
                    "meter_001": "OUT_OF_SERVICE"
                }
            }
        }
        load_res = client.post("/api/v1/simulation/scenarios/loadshed/load", json=scenario_payload)
        assert load_res.status_code == 200
        assert load_res.json()["success"] is True

        # 4. Start scenario
        start_res = client.post("/api/v1/simulation/scenarios/loadshed/start")
        assert start_res.status_code == 200
        assert start_res.json()["success"] is True

        # 5. Verify status is active
        status_res = client.get("/api/v1/simulation/scenarios/loadshed/status")
        assert status_res.status_code == 200
        assert status_res.json()["is_active"] is True
        assert status_res.json()["scenario_loaded"] is True
        assert status_res.json()["steps_count"] == 1

        # 6. Stop scenario
        stop_res = client.post("/api/v1/simulation/scenarios/loadshed/stop")
        assert stop_res.status_code == 200
        assert stop_res.json()["success"] is True

        status_res = client.get("/api/v1/simulation/scenarios/loadshed/status")
        assert status_res.json()["is_active"] is False


def test_loadshed_scenario_cyber_latency(mock_engine_with_meters):
    """Test scenario execution logic with cyber-communication latency delay modeling."""
    engine = mock_engine_with_meters
    service = engine.loadshed_scenario

    # Mock coordinates on meters
    engine.meters[0].config["latitude"] = 9.5
    engine.meters[0].config["longitude"] = 100.0
    engine.meters[1].config["latitude"] = 9.6
    engine.meters[1].config["longitude"] = 100.1

    scenario = {
        "60": {
            "meter_001": "OUT_OF_SERVICE",
            "meter_002": "OUT_OF_SERVICE"
        }
    }

    # 1. Load scenario with latency enabled (propagation delay: 2.0s per hop)
    assert service.load_scenario(scenario, latency_enabled=True, latency_per_hop_seconds=2.0) is True
    assert service.latency_enabled is True
    assert service.latency_per_hop_seconds == 2.0

    # 2. Start scenario
    start_time = datetime(2026, 5, 31, 12, 0, tzinfo=timezone.utc)
    service.start(start_time)

    # 3. Update at 60s (step triggers, but latency delays actual service status change)
    time_60s = datetime(2026, 5, 31, 12, 1, tzinfo=timezone.utc)
    changes = service.update_step(time_60s, engine.meters)
    # The actions should be queued in pending_actions, not applied immediately because of latency delay
    assert len(changes) == 0
    assert len(service.pending_actions) == 2
    assert engine.meters[0].is_shed is False
    assert engine.meters[1].is_shed is False

    # Hop counts are determined by distance to the virtual substation center
    # Substation center = avg(lat, lon) = (9.55, 100.05)
    # Both meters are equidistant to the center. Since we normalise:
    # dist / max_dist = 1.0 -> hops = int(1.0 * 4) + 1 = 5 hops.
    # delay = 5 hops * 2.0s = 10.0s delay.
    # Therefore, scheduled time is 60s + 10s = 70s.
    assert service.pending_actions[0]["scheduled_time"] == 70
    assert service.pending_actions[1]["scheduled_time"] == 70

    # 4. Update at 65s (delay not completed yet, no updates)
    time_65s = datetime(2026, 5, 31, 12, 1, 5, tzinfo=timezone.utc)
    changes = service.update_step(time_65s, engine.meters)
    assert len(changes) == 0
    assert engine.meters[0].is_shed is False

    # 5. Update at 70s (delay completed, both shedded)
    time_70s = datetime(2026, 5, 31, 12, 1, 10, tzinfo=timezone.utc)
    changes = service.update_step(time_70s, engine.meters)
    assert len(changes) == 2
    assert engine.meters[0].is_shed is True
    assert engine.meters[1].is_shed is True
    assert len(service.pending_actions) == 0

