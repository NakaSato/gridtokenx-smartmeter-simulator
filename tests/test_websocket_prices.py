"""
WebSocket Price Streaming Tests

Tests for real-time P2P price streaming via WebSocket:
- WebSocket connection and initial price update
- Continuous price updates
- Price formula verification
- Market dynamics simulation

Run with:
    uv run pytest tests/test_websocket_prices.py -v
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch
from datetime import datetime, timezone

from fastapi.testclient import TestClient
from smart_meter_simulator.app import app
from smart_meter_simulator.core.price_streamer import PriceStreamer
from smart_meter_simulator.transport.websocket import WebSocketManager


class TestPriceStreamer:
    """Tests for PriceStreamer class."""

    def test_price_streamer_initialization(self):
        """Test PriceStreamer initialization."""
        manager = WebSocketManager()
        streamer = PriceStreamer(manager)

        assert streamer.websocket_manager is manager
        assert streamer.broadcast_interval == 5.0
        assert streamer.wheeling_cost == 1.76  # RESIDENTIAL_WHEELING_COST_AVG
        assert streamer.p2p_discount == 0.10
        assert streamer._running is False
        assert streamer._task is None

    def test_calculate_price_basic(self):
        """Test basic price calculation."""
        manager = WebSocketManager()
        streamer = PriceStreamer(manager)

        # Set known supply/demand
        streamer.current_supply = 100.0
        streamer.current_demand = 100.0

        price_data = streamer._calculate_price()

        # Verify structure
        assert price_data["type"] == "price_update"
        assert "timestamp" in price_data
        assert "data" in price_data
        assert "pricing" in price_data
        assert "comparison" in price_data

        # Verify data fields
        data = price_data["data"]
        assert "market_clearing_price_baht_kwh" in data
        assert "buyer_total_baht_kwh" in data
        assert "seller_net_baht_kwh" in data
        assert "market_sentiment" in data
        assert "tou_period" in data
        assert "tou_rate_baht_kwh" in data
        assert "p2p_discount_percent" in data

        # Verify pricing info (ToU-based)
        pricing = price_data["pricing"]
        assert pricing["source"] == "ToU Tariff"
        assert "tou_period" in pricing
        assert "tou_rate_baht_kwh" in pricing
        assert pricing["formula"] == "P2P_Price = ToU_Rate × (1 - discount)"
        assert "note" in pricing  # API Gateway note

        # Verify comparison
        comparison = price_data["comparison"]
        assert "p2p_savings_percent" in comparison
        assert "seller_premium_percent" in comparison
        assert "utility_retail_rate_baht_kwh" in comparison

    def test_calculate_price_high_demand(self):
        """Test price calculation with high demand."""
        manager = WebSocketManager()
        streamer = PriceStreamer(manager)

        # High demand scenario
        streamer.current_supply = 50.0
        streamer.current_demand = 150.0

        price_data = streamer._calculate_price()
        data = price_data["data"]

        # Price is based on ToU, not demand - verify sentiment
        assert data["market_sentiment"] == "HIGH_DEMAND"
        assert data["demand_ratio"] == 3.0
        # Verify ToU-based pricing
        assert data["tou_rate_baht_kwh"] > 0
        assert data["p2p_discount_percent"] == 10.0

    def test_calculate_price_low_demand(self):
        """Test price calculation with low demand."""
        manager = WebSocketManager()
        streamer = PriceStreamer(manager)

        # Low demand scenario
        streamer.current_supply = 150.0
        streamer.current_demand = 50.0

        price_data = streamer._calculate_price()
        data = price_data["data"]

        # Verify sentiment (price is ToU-based, not demand-based)
        assert data["market_sentiment"] == "LOW_DEMAND"
        assert data["demand_ratio"] == pytest.approx(0.333, rel=0.01)
        assert data["tou_period"] in ["on_peak", "off_peak_weekday", "off_peak_weekend"]

    def test_calculate_price_balanced(self):
        """Test price calculation with balanced market."""
        manager = WebSocketManager()
        streamer = PriceStreamer(manager)
        
        # Balanced scenario
        streamer.current_supply = 100.0
        streamer.current_demand = 100.0
        
        price_data = streamer._calculate_price()
        data = price_data["data"]
        
        # Should be balanced
        assert data["market_sentiment"] == "BALANCED"
        assert 0.9 <= data["demand_ratio"] <= 1.1

    def test_simulate_market_dynamics(self):
        """Test market dynamics simulation."""
        manager = WebSocketManager()
        streamer = PriceStreamer(manager)
        
        initial_supply = streamer.current_supply
        initial_demand = streamer.current_demand
        
        # Simulate should change values
        streamer._simulate_market_dynamics()
        
        # Values should have changed (with random component)
        assert streamer.current_supply > 0
        assert streamer.current_demand > 0

    def test_update_market_state(self):
        """Test manual market state update."""
        manager = WebSocketManager()
        streamer = PriceStreamer(manager)
        
        streamer.update_market_state(supply_kwh=200.0, demand_kwh=100.0)
        
        assert streamer.current_supply == 200.0
        assert streamer.current_demand == 100.0

    @pytest.mark.asyncio
    async def test_price_streamer_start_stop(self):
        """Test starting and stopping PriceStreamer."""
        manager = WebSocketManager()
        streamer = PriceStreamer(manager, broadcast_interval=0.1)
        
        # Start
        await streamer.start()
        assert streamer._running is True
        assert streamer._task is not None
        
        # Let it run briefly
        await asyncio.sleep(0.3)
        
        # Stop
        await streamer.stop()
        assert streamer._running is False


class TestWebSocketPriceEndpoint:
    """Tests for WebSocket price endpoint."""

    def test_websocket_price_connection(self):
        """Test WebSocket connection to price endpoint."""
        client = TestClient(app)
        
        with client.websocket_connect("/ws/prices") as websocket:
            # Should receive initial price update
            data = websocket.receive_json()
            
            assert data["type"] == "price_update"
            assert "timestamp" in data
            assert "data" in data
            
            # Verify price data structure
            price_data = data["data"]
            assert "market_clearing_price_baht_kwh" in price_data
            assert "buyer_total_baht_kwh" in price_data
            assert "seller_net_baht_kwh" in price_data

    def test_websocket_price_format(self):
        """Test WebSocket price message format."""
        client = TestClient(app)

        with client.websocket_connect("/ws/prices") as websocket:
            data = websocket.receive_json()

            # Verify top-level structure
            assert data["type"] == "price_update"
            assert "timestamp" in data
            assert "data" in data
            assert "pricing" in data
            assert "comparison" in data

            # Verify data fields
            price = data["data"]
            assert isinstance(price["market_clearing_price_baht_kwh"], float)
            assert isinstance(price["buyer_total_baht_kwh"], float)
            assert isinstance(price["seller_net_baht_kwh"], float)
            assert price["market_sentiment"] in ["HIGH_DEMAND", "LOW_DEMAND", "BALANCED"]
            assert price["tou_period"] in ["on_peak", "off_peak_weekday", "off_peak_weekend"]
            assert "tou_rate_baht_kwh" in price
            assert "p2p_discount_percent" in price

            # Verify pricing info (ToU-based)
            pricing = data["pricing"]
            assert pricing["source"] == "ToU Tariff"
            assert "tou_period" in pricing
            assert "tou_rate_baht_kwh" in pricing
            assert pricing["formula"] == "P2P_Price = ToU_Rate × (1 - discount)"
            assert "note" in pricing  # API Gateway note

            # Verify comparison
            comparison = data["comparison"]
            assert "utility_retail_rate_baht_kwh" in comparison
            assert "utility_buyback_rate_baht_kwh" in comparison
            assert "p2p_savings_percent" in comparison
            assert "seller_premium_percent" in comparison

    def test_websocket_price_range(self):
        """Test that prices are within reasonable range."""
        client = TestClient(app)
        
        with client.websocket_connect("/ws/prices") as websocket:
            data = websocket.receive_json()
            price = data["data"]
            
            # Price should be positive
            assert price["market_clearing_price_baht_kwh"] > 0
            
            # Buyer rate should be higher than MCP (includes wheeling)
            assert price["buyer_total_baht_kwh"] > price["market_clearing_price_baht_kwh"]
            
            # Seller net should be lower than MCP (includes wheeling)
            assert price["seller_net_baht_kwh"] < price["market_clearing_price_baht_kwh"]
            
            # Wheeling cost should be positive
            assert price["wheeling_cost_baht_kwh"] > 0


class TestPriceStreamingIntegration:
    """Integration tests for price streaming."""

    def test_multiple_websocket_clients(self):
        """Test multiple clients receiving price updates."""
        client = TestClient(app)
        
        # Connect multiple clients
        with client.websocket_connect("/ws/prices") as ws1, \
             client.websocket_connect("/ws/prices") as ws2:
            
            # Both should receive initial update
            data1 = ws1.receive_json()
            data2 = ws2.receive_json()
            
            # Both should receive same type of data
            assert data1["type"] == data2["type"] == "price_update"
            
            # Prices should be similar (same market conditions)
            price1 = data1["data"]["market_clearing_price_baht_kwh"]
            price2 = data2["data"]["market_clearing_price_baht_kwh"]
            
            # Prices should be very close (same calculation)
            assert abs(price1 - price2) < 0.01

    def test_price_update_timestamp(self):
        """Test that price updates have valid timestamps."""
        client = TestClient(app)
        
        with client.websocket_connect("/ws/prices") as websocket:
            data = websocket.receive_json()
            
            timestamp_str = data["timestamp"]
            assert timestamp_str is not None
            
            # Should be valid ISO format
            from datetime import datetime
            try:
                datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            except ValueError:
                pytest.fail("Timestamp is not valid ISO format")

    def test_price_formula_components(self):
        """Test that ToU pricing components are correctly calculated."""
        client = TestClient(app)

        with client.websocket_connect("/ws/prices") as websocket:
            data = websocket.receive_json()

            pricing = data["pricing"]
            price_data = data["data"]

            # Verify pricing source
            assert pricing["source"] == "ToU Tariff"
            assert "note" in pricing  # API Gateway integration note

            # Verify ToU period matches the rate
            tou_period = pricing["tou_period"]
            tou_rate = pricing["tou_rate_baht_kwh"]
            
            # ToU rates: ON_PEAK=5.7982, OFF_PEAK=2.6369
            if tou_period == "on_peak":
                assert tou_rate == pytest.approx(5.7982, rel=0.01)
            else:  # off_peak_weekday or off_peak_weekend
                assert tou_rate == pytest.approx(2.6369, rel=0.01)

            # Verify P2P discount is applied correctly
            discount = pricing["p2p_discount_percent"] / 100.0
            expected_mcp = tou_rate * (1 - discount)
            assert price_data["market_clearing_price_baht_kwh"] == pytest.approx(expected_mcp, rel=0.01)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
