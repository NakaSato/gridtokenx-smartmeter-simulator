import pytest
import pandas as pd
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch, AsyncMock
from smart_meter_simulator.app import app

@pytest.fixture
def client():
    mock_config = MagicMock()
    mock_config.database_url = "postgresql://user:pass@localhost/db"
    mock_config.api_gateway_url = "http://localhost:8080"
    mock_config.api_key = "test_key"
    mock_config.kafka_servers = None
    mock_config.influxdb_token = None
    mock_config.num_meters = 1
    mock_config.autostart_simulation = False
    
    with patch('smart_meter_simulator.app.get_config', return_value=mock_config):
        with patch('smart_meter_simulator.core.app_state.engine') as mock_engine:
            # Setup mock engine
            mock_engine.meters = [MagicMock(meter_id="M1", battery_level=5.0, config={"meter_type": "Residential", "location": "Zone_1", "phase": "A"})]
            mock_engine.meter_to_bus = {"M1": 0}
            mock_engine.current_sim_time = pd.Timestamp.now()
            mock_engine.market = MagicMock()
            mock_engine.market.current_mcp = 0.25
            mock_engine.market.get_market_sentiment.return_value = "Bullish"
            mock_engine.market.history = []
            
            # Setup mock net
            net = MagicMock()
            net.bus = pd.DataFrame({
                "name": ["Bus 0", "Bus 1"],
                "vn_kv": [0.4, 0.4],
                "type": ["b", "b"]
            }, index=[0, 1])
            
            net.line = pd.DataFrame({
                "name": ["Line 0"],
                "from_bus": [0],
                "to_bus": [1],
                "length_km": [0.1],
                "max_i_ka": [0.2],
                "vn_kv": [0.4]
            }, index=[0])
            
            net.load = pd.DataFrame({"bus": [0]}, index=[0])
            net.sgen = pd.DataFrame({"bus": [1]}, index=[0])
            net.ext_grid = pd.DataFrame({"bus": [0]}, index=[0])
            
            net.res_bus = pd.DataFrame({"vm_pu": [1.0, 1.0]}, index=[0, 1])
            net.res_line = pd.DataFrame({"loading_percent": [10.0], "i_ka": [0.01]}, index=[0])
            
            net.bus_geocoord = pd.DataFrame({"x": [100.6, 100.7], "y": [13.7, 13.8]}, index=[0, 1])
            
            mock_engine.net = net
            
            # Mock mapbox_matcher
            mock_matcher = AsyncMock()
            mock_matcher.match_route.return_value = ([[100.6, 13.7], [100.7, 13.8]], 15000.0)
            
            with patch('smart_meter_simulator.routers.dependencies.app_state', MagicMock(engine=mock_engine)):
                with patch('smart_meter_simulator.app.mapbox_matcher', mock_matcher, create=True):
                    with TestClient(app) as c:
                        yield c, mock_engine

def test_get_grid_snapshot(client):
    c, _ = client
    response = c.get("/api/grid/snapshot")
    assert response.status_code == 200
    data = response.json()
    assert "meters" in data
    assert "lines" in data
    assert data["meters"][0]["meter_id"] == "M1"

def test_get_grid_geojson(client):
    c, _ = client
    response = c.get("/api/grid/geojson")
    assert response.status_code == 200
    data = response.json()
    assert data["type"] == "FeatureCollection"
    assert len(data["features"]) > 0
    # Verify we have both point (bus) and linestring (line)
    types = [f["geometry"]["type"] for f in data["features"]]
    assert "Point" in types
    assert "LineString" in types

def test_get_legacy_topology(client):
    c, _ = client
    response = c.get("/api/grid/legacy-topology")
    assert response.status_code == 200
    data = response.json()
    assert "zones" in data
    assert "meters" in data

def test_get_grid_topology_detailed(client):
    c, _ = client
    response = c.get("/api/grid/topology")
    assert response.status_code == 200
    data = response.json()
    assert "buses" in data
    assert "lines" in data
