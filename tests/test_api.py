"""
API Endpoint Tests

Tests for FastAPI REST API endpoints.

Run with:
    uv run pytest tests/test_api.py -v

Fixtures:
    - client: TestClient with mocked engine (from conftest.py)
"""

import pytest
from fastapi.testclient import TestClient


class TestHealthEndpoint:
    """Tests for /health endpoint."""

    def test_health_check(self, client):
        """Verify health endpoint returns OK status."""
        c, _ = client
        response = c.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "timestamp" in data


class TestMeterEndpoints:
    """Tests for meter-related endpoints."""

    def test_list_meters(self, client):
        """Verify meter listing returns configured meters."""
        c, _ = client
        response = c.get("/api/meters")
        assert response.status_code == 200
        data = response.json()
        assert "meters" in data
        assert len(data["meters"]) == 1
        assert data["meters"][0]["meter_id"] == "M1"

    def test_get_meter_details(self, client):
        """Verify individual meter details retrieval."""
        c, mock_engine = client
        response = c.get("/api/meters/M1")
        assert response.status_code == 200
        data = response.json()
        assert data["meter_id"] == "M1"


class TestGridEndpoints:
    """Tests for grid-related endpoints."""

    def test_get_grid_status(self, client):
        """Verify grid status returns topology summary."""
        c, _ = client
        response = c.get("/api/grid/status")
        assert response.status_code == 200
        data = response.json()
        assert "num_buses" in data or "success" in data

    def test_get_grid_topology(self, client):
        """Verify grid topology returns detailed structure."""
        c, _ = client
        response = c.get("/api/grid/topology")
        assert response.status_code == 200
        data = response.json()
        assert "buses" in data or "success" in data

    def test_get_grid_geojson(self, client):
        """Verify GeoJSON topology export."""
        c, _ = client
        response = c.get("/api/grid/geojson")
        assert response.status_code == 200
        data = response.json()
        assert data["type"] == "FeatureCollection"
        assert len(data["features"]) > 0


class TestVPPEndpoints:
    """Tests for VPP-related endpoints."""

    def test_vpp_clusters(self, client):
        """Verify VPP cluster listing."""
        c, mock_engine = client
        mock_engine.vpp.get_all_cluster_statuses.return_value = [
            {"cluster_id": "F1", "total_capacity_kwh": 15.0}
        ]
        response = c.get("/api/vpp/clusters")
        assert response.status_code == 200
        data = response.json()
        assert "clusters" in data
        assert len(data["clusters"]) == 1
        assert data["clusters"][0]["cluster_id"] == "F1"


class TestMarketEndpoints:
    """Tests for market-related endpoints."""

    def test_calculate_p2p_cost(self, client):
        """Verify P2P cost calculation endpoint."""
        c, _ = client
        payload = {
            "buyer_zone_id": 1,
            "seller_zone_id": 2,
            "energy_amount": 10.0,
            "agreed_price": 0.30,
        }
        response = c.post("/api/v1/p2p/calculate-cost", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "total_cost" in data or "success" in data


class TestErrorHandling:
    """Tests for error handling and edge cases."""

    def test_404_handler(self, client):
        """Verify 404 error handling returns UI or error page."""
        c, _ = client
        response = c.get("/api/nonexistent-endpoint")
        # Note: The app returns 200 with UI for SPA routing
        # or 404 if UI dist doesn't exist
        assert response.status_code in [200, 404]

    def test_invalid_meter_id(self, client):
        """Verify handling of invalid meter IDs."""
        c, _ = client
        response = c.get("/api/meters/INVALID_ID")
        # Should return 404 or error response
        assert response.status_code in [404, 422, 500]
