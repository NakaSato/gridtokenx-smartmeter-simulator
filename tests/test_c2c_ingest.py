"""
C2C (Community-to-Community) Data Ingestion Tests

Tests for the C2C live feed ingestion API endpoint.

Run with:
    uv run pytest tests/test_c2c_ingest.py -v
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock, patch

from smart_meter_simulator.config import SimulatorConfig


@pytest.fixture
def mock_app_with_engine():
    """Create mocked app with engine for C2C tests."""
    from smart_meter_simulator.core import app_state

    # Setup mock meter
    mock_meter = MagicMock(spec_name="SmartMeter")
    mock_meter.meter_id = "METER-1234"
    mock_meter.config = {
        "meter_id": "METER-1234",
        "meter_type": "solar_prosumer",
        "bus_id": 1,
        "location": {"lat": 13.0, "lon": 100.0},
        "max_buy_price": 0.35,
        "min_sell_price": 0.15,
    }
    mock_meter.manual_override_cons = 0.0
    mock_meter.manual_override_gen = 0.0

    # Setup mock market
    mock_market = MagicMock()
    mock_market.submit_order = MagicMock()

    # Setup mock engine
    mock_engine = MagicMock()
    mock_engine.meters = [mock_meter]
    mock_engine.market = mock_market
    mock_engine.current_sim_time = MagicMock()
    mock_engine.current_sim_time.isoformat.return_value = "2024-01-01T12:00:00Z"
    mock_engine.interval = 900

    # Setup mock WS manager
    mock_ws = MagicMock()
    mock_ws.broadcast = AsyncMock()

    # Mock the app_state.engine
    with patch.object(app_state, "engine", mock_engine):
        with patch(
            "smart_meter_simulator.routers.control.get_engine",
            return_value=mock_engine,
        ):
            with patch(
                "smart_meter_simulator.routers.control.get_websocket_manager",
                return_value=mock_ws,
            ):
                yield mock_engine


class TestC2CAuthentication:
    """Tests for C2C API authentication."""

    def test_ingest_unauthorized(self):
        """Verify request without API key is rejected."""
        from smart_meter_simulator.app import app

        client = TestClient(app)
        response = client.post(
            "/api/c2c/ingest",
            json={"node_id": "METER-1234", "power_kw": 5.0},
        )
        assert response.status_code == 401

    def test_ingest_invalid_api_key(self):
        """Verify request with invalid API key is rejected."""
        from smart_meter_simulator.app import app

        client = TestClient(app)
        response = client.post(
            "/api/c2c/ingest",
            headers={"X-API-Key": "wrong_key"},
            json={"node_id": "METER-1234", "power_kw": 5.0},
        )
        assert response.status_code == 401


class TestC2CIngestion:
    """Tests for C2C data ingestion."""

    def test_ingest_valid_charging(self, mock_app_with_engine):
        """Verify successful C2C data ingestion for charging."""
        from smart_meter_simulator.app import app

        api_key = getattr(
            SimulatorConfig, "C2C_API_KEY", "gridtokenx_c2c_live_feed"
        )

        client = TestClient(app)
        response = client.post(
            "/api/c2c/ingest",
            headers={"X-API-Key": api_key},
            json={
                "node_id": "METER-1234",
                "power_kw": 12.5,
                "status": "CHARGING",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

        # Verify market order was submitted
        mock_app_with_engine.market.submit_order.assert_called()

    def test_ingest_valid_solar(self, mock_app_with_engine):
        """Verify successful C2C data ingestion for solar generation."""
        from smart_meter_simulator.app import app

        api_key = getattr(
            SimulatorConfig, "C2C_API_KEY", "gridtokenx_c2c_live_feed"
        )

        client = TestClient(app)
        response = client.post(
            "/api/c2c/ingest",
            headers={"X-API-Key": api_key},
            json={
                "node_id": "METER-1234",
                "power_kw": 8.0,
                "status": "GENERATING",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_ingest_unknown_meter(self, mock_app_with_engine):
        """Verify handling of unknown meter IDs."""
        from smart_meter_simulator.app import app

        api_key = getattr(
            SimulatorConfig, "C2C_API_KEY", "gridtokenx_c2c_live_feed"
        )

        client = TestClient(app)
        response = client.post(
            "/api/c2c/ingest",
            headers={"X-API-Key": api_key},
            json={"node_id": "UNKNOWN-0000", "power_kw": 5.0},
        )

        # Should still return success (just no meter action)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True


class TestC2CValidation:
    """Tests for C2C data validation."""

    def test_ingest_missing_fields(self, mock_app_with_engine):
        """Verify handling of missing required fields."""
        from smart_meter_simulator.app import app

        api_key = getattr(
            SimulatorConfig, "C2C_API_KEY", "gridtokenx_c2c_live_feed"
        )

        client = TestClient(app)
        response = client.post(
            "/api/c2c/ingest",
            headers={"X-API-Key": api_key},
            json={"node_id": "METER-1234"},  # Missing power_kw
        )

        # Should return 200 (endpoint handles missing power_kw gracefully)
        assert response.status_code == 200

    def test_ingest_negative_power(self, mock_app_with_engine):
        """Verify handling of negative power values (treated as charging)."""
        from smart_meter_simulator.app import app

        api_key = getattr(
            SimulatorConfig, "C2C_API_KEY", "gridtokenx_c2c_live_feed"
        )

        client = TestClient(app)
        response = client.post(
            "/api/c2c/ingest",
            headers={"X-API-Key": api_key},
            json={"node_id": "METER-1234", "power_kw": -5.0},
        )

        # Negative power is treated as charging
        assert response.status_code == 200
