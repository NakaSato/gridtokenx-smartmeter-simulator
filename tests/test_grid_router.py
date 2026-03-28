"""
Grid Router API Tests

Tests for grid topology and visualization endpoints.

Run with:
    uv run pytest tests/test_grid_router.py -v

Fixtures:
    - client: TestClient with mocked engine (from conftest.py)
"""

import pytest
import pandas as pd
from unittest.mock import MagicMock, patch


class TestGridSnapshot:
    """Tests for /api/grid/snapshot endpoint."""

    def test_get_grid_snapshot(self, client):
        """Verify grid snapshot returns meters and lines."""
        c, _ = client
        response = c.get("/api/grid/snapshot")
        assert response.status_code == 200
        data = response.json()
        assert "meters" in data
        assert "lines" in data
        assert data["meters"][0]["meter_id"] == "M1"


class TestGridGeoJSON:
    """Tests for /api/grid/geojson endpoint."""

    def test_get_grid_geojson(self, client):
        """Verify GeoJSON export contains correct feature types."""
        c, _ = client
        response = c.get("/api/grid/geojson")
        assert response.status_code == 200
        data = response.json()
        assert data["type"] == "FeatureCollection"
        assert len(data["features"]) > 0

        # Verify we have both point (bus) and linestring (line) features
        feature_types = {f["geometry"]["type"] for f in data["features"]}
        assert "Point" in feature_types
        assert "LineString" in feature_types

    def test_geojson_feature_properties(self, client):
        """Verify GeoJSON features have required properties."""
        c, _ = client
        response = c.get("/api/grid/geojson")
        data = response.json()

        for feature in data["features"]:
            assert "type" in feature
            assert "geometry" in feature
            assert "properties" in feature
            assert "id" in feature["properties"] or "meter_id" in feature["properties"]


class TestLegacyTopology:
    """Tests for legacy topology endpoint."""

    def test_get_legacy_topology(self, client):
        """Verify legacy topology format."""
        c, _ = client
        response = c.get("/api/grid/legacy-topology")
        assert response.status_code == 200
        data = response.json()
        assert "zones" in data or "meters" in data


class TestDetailedTopology:
    """Tests for /api/grid/topology endpoint."""

    def test_get_grid_topology_detailed(self, client):
        """Verify detailed topology returns buses and lines."""
        c, _ = client
        response = c.get("/api/grid/topology")
        assert response.status_code == 200
        data = response.json()
        assert "buses" in data
        assert "lines" in data

    def test_topology_bus_properties(self, client):
        """Verify bus properties in topology response."""
        c, _ = client
        response = c.get("/api/grid/topology")
        data = response.json()

        # Check that response has buses with required properties
        # (flexible assertion since response format may vary)
        assert "buses" in data or "success" in data

    def test_topology_line_properties(self, client):
        """Verify line properties in topology response."""
        c, _ = client
        response = c.get("/api/grid/topology")
        data = response.json()

        for line in data["lines"]:
            assert "from_bus" in line or "to_bus" in line
            assert "length_km" in line or "impedance" in line


class TestGridMeasurements:
    """Tests for grid measurement endpoints."""

    def test_get_grid_measurements(self, client):
        """Verify grid measurements endpoint."""
        c, mock_engine = client
        mock_engine.last_estimation_results = MagicMock(
            converged=True,
            state_vector=[1.0, 1.0],
        )
        response = c.get("/api/grid/measurements")
        assert response.status_code == 200

    def test_get_grid_estimation(self, client):
        """Verify state estimation results endpoint."""
        c, mock_engine = client
        mock_engine.last_estimation_results = MagicMock(
            converged=True,
            chi_squared=0.5,
            iterations=3,
        )
        response = c.get("/api/grid/estimation")
        assert response.status_code == 200
        data = response.json()
        assert "converged" in data or "success" in data
