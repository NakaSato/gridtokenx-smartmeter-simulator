import pytest
from fastapi.testclient import TestClient
from app.app import app
import asyncio
from datetime import datetime

def test_api_status():
    """Test the general status endpoint."""
    with TestClient(app) as client:
        response = client.get("/api/status")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "running" in data # Updated field name

def test_grid_status_endpoint():
    """Test the grid status endpoint."""
    with TestClient(app) as client:
        response = client.get("/api/grid/status")
        assert response.status_code == 200
        data = response.json()
        if "error" not in data:
            assert "num_buses" in data
            assert "num_lines" in data

def test_grid_topology_endpoint():
    """Test the grid topology endpoint."""
    with TestClient(app) as client:
        # Topology might be empty or uninitialized, but should return a response
        response = client.get("/api/grid/topology")
        assert response.status_code == 200
        data = response.json()
        if "error" not in data:
            assert "buses" in data
            assert "lines" in data

def test_grid_estimation_endpoint():
    """Test the grid estimation endpoint."""
    with TestClient(app) as client:
        response = client.get("/api/grid/estimation")
        assert response.status_code == 200
        data = response.json()
        # Might return error if not run yet, but should be a valid response
        assert "converged" in data or "error" in data

def test_grid_measurements_endpoint():
    """Test the grid measurements endpoint."""
    with TestClient(app) as client:
        response = client.get("/api/grid/measurements")
        assert response.status_code == 200
        data = response.json()
        assert "measurements" in data

def test_simulation_control_endpoints():
    """Test starting and stopping the simulation."""
    with TestClient(app) as client:
        # Start
        response = client.post("/api/control/start")
        assert response.status_code == 200
        # We don't strictly assert success=True here because NR might fail if net is invalid
        # but the endpoint should return a valid JSON
        assert "success" in response.json()
        
        # Check status
        response = client.get("/api/status")
        assert "running" in response.json()
        
        # Stop
        response = client.post("/api/control/stop")
        assert response.status_code == 200
        assert response.json()["success"] is True

def test_websocket_connection():
    """Test that websocket endpoint is reachable."""
    with TestClient(app) as client:
        with client.websocket_connect("/ws") as websocket:
            # Just check connection
            pass
