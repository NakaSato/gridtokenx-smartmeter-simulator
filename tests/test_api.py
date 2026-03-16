import pytest
import asyncio
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
from smart_meter_simulator.app import app

@pytest.fixture
def client():
    # Mock config to avoid real DB/Kafka connections during lifespan
    mock_config = MagicMock()
    mock_config.database_url = "postgresql://user:pass@localhost/db"
    mock_config.api_gateway_url = "http://localhost:8080"
    mock_config.api_key = "test_key"
    mock_config.kafka_servers = None
    mock_config.influxdb_token = None
    mock_config.num_meters = 1
    mock_config.autostart_simulation = False
    
    with patch('smart_meter_simulator.app.get_config', return_value=mock_config):
        # Mock engine and other globals
        with patch('smart_meter_simulator.core.app_state.engine') as mock_engine:
            mock_engine.meters = [MagicMock(meter_id="M1", config={"meter_type": "solar", "location": "Zone_1"})]
            mock_engine.running = True
            mock_engine.paused = False
            mock_engine.net = MagicMock()
            mock_engine.market = MagicMock()
            mock_engine.market.current_mcp = 0.25
            mock_engine.market.history = []
            mock_engine.market.tariff_manager.get_current_tariff.return_value = MagicMock(import_rate=0.28, export_rate=0.15)
            mock_engine.last_estimation_results = None
            
            # Patch dependencies to use our mocks
            with patch('smart_meter_simulator.routers.dependencies.app_state', MagicMock(engine=mock_engine)):
                with TestClient(app) as c:
                    yield c, mock_engine

def test_health(client):
    c, _ = client
    response = c.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_list_meters(client):
    c, _ = client
    response = c.get("/api/meters")
    assert response.status_code == 200
    assert len(response.json()["meters"]) == 1
    assert response.json()["meters"][0]["meter_id"] == "M1"

def test_get_grid_status(client):
    c, _ = client
    response = c.get("/api/grid/status")
    assert response.status_code == 200
    assert "num_buses" in response.json()

def test_vpp_clusters(client):
    c, mock_engine = client
    mock_engine.vpp.get_all_cluster_statuses.return_value = [{"cluster_id": "F1"}]
    response = c.get("/api/vpp/clusters")
    assert response.status_code == 200
    assert response.json()["clusters"][0]["cluster_id"] == "F1"

def test_calculate_p2p_cost(client):
    c, _ = client
    data = {
        "buyer_zone_id": 1,
        "seller_zone_id": 2,
        "energy_amount": 10.0,
        "agreed_price": 0.30
    }
    response = c.post("/api/v1/p2p/calculate-cost", json=data)
    assert response.status_code == 200
    assert "total_cost" in response.json()
