"""
Price History Tests

Tests for P2P price history storage and analytics:
- PriceHistoryManager class
- Price history API endpoints
- Statistical calculations
- Time-based aggregations

Run with:
    uv run pytest tests/test_price_history.py -v
"""

import pytest
import asyncio
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, patch

from smart_meter_simulator.core.price_history import PriceHistoryManager, PriceRecord
from fastapi.testclient import TestClient
from smart_meter_simulator.app import app


class TestPriceHistoryManager:
    """Tests for PriceHistoryManager class."""

    def test_initialization(self):
        """Test PriceHistoryManager initialization."""
        manager = PriceHistoryManager(
            max_records=1000,
            retention_hours=24,
        )

        assert manager.max_records == 1000
        assert manager.retention_hours == 24
        assert manager.wheeling_cost == 1.76
        assert manager.p2p_discount == 0.10
        assert manager.get_record_count() == 0

    def test_add_price_basic(self):
        """Test adding a price record."""
        manager = PriceHistoryManager()

        record = manager.add_price(supply_kwh=100.0, demand_kwh=100.0)

        assert isinstance(record, PriceRecord)
        assert record.market_clearing_price_baht_kwh > 0
        assert record.buyer_total_baht_kwh > record.market_clearing_price_baht_kwh
        assert record.seller_net_baht_kwh < record.market_clearing_price_baht_kwh
        assert record.supply_kwh == 100.0
        assert record.demand_kwh == 100.0
        assert record.demand_ratio == 1.0
        assert record.market_sentiment == "BALANCED"
        assert record.tou_period in ["on_peak", "off_peak_weekday", "off_peak_weekend"]
        assert record.tou_rate_baht_kwh > 0
        assert record.p2p_discount_percent == 10.0
        assert manager.get_record_count() == 1

    def test_add_price_high_demand(self):
        """Test adding price with high demand."""
        manager = PriceHistoryManager()

        record = manager.add_price(supply_kwh=50.0, demand_kwh=150.0)

        assert record.market_sentiment == "HIGH_DEMAND"
        assert record.demand_ratio == 3.0
        # Price is based on ToU, not demand - just verify it's calculated correctly
        assert record.market_clearing_price_baht_kwh > 0
        # Verify ToU-based pricing: MCP = ToU_Rate * (1 - 0.10)
        expected_mcp = record.tou_rate_baht_kwh * 0.9
        assert record.market_clearing_price_baht_kwh == pytest.approx(expected_mcp, rel=0.01)

    def test_add_price_low_demand(self):
        """Test adding price with low demand."""
        manager = PriceHistoryManager()

        record = manager.add_price(supply_kwh=150.0, demand_kwh=50.0)

        assert record.market_sentiment == "LOW_DEMAND"
        assert record.demand_ratio == pytest.approx(0.333, rel=0.01)

    def test_add_price_custom_timestamp(self):
        """Test adding price with custom timestamp."""
        manager = PriceHistoryManager()
        custom_time = datetime(2026, 1, 15, 10, 30, 0, tzinfo=timezone.utc)
        
        record = manager.add_price(
            supply_kwh=100.0,
            demand_kwh=100.0,
            timestamp=custom_time,
        )
        
        assert "2026-01-15T10:30:00" in record.timestamp

    def test_get_recent_prices(self):
        """Test retrieving recent prices."""
        manager = PriceHistoryManager()
        
        # Add 10 records
        for i in range(10):
            manager.add_price(supply_kwh=100.0 + i, demand_kwh=100.0)
        
        # Get last 5
        records = manager.get_recent_prices(limit=5)
        
        assert len(records) == 5
        # Should be newest first
        assert records[0].supply_kwh > records[-1].supply_kwh

    def test_get_recent_prices_exceeds_count(self):
        """Test getting more records than available."""
        manager = PriceHistoryManager()
        
        # Add 3 records
        for i in range(3):
            manager.add_price(supply_kwh=100.0, demand_kwh=100.0)
        
        # Try to get 100
        records = manager.get_recent_prices(limit=100)
        
        assert len(records) == 3

    def test_max_records_limit(self):
        """Test that max_records limit is enforced."""
        manager = PriceHistoryManager(max_records=50)
        
        # Add 100 records
        for i in range(100):
            manager.add_price(supply_kwh=100.0, demand_kwh=100.0)
        
        # Should only keep last 50
        assert manager.get_record_count() == 50

    def test_get_statistics(self):
        """Test price statistics calculation."""
        manager = PriceHistoryManager()

        # Add records with known prices at different ToU periods
        # ON_PEAK (weekday 10:00) - higher price
        for i in range(5):
            timestamp = datetime(2026, 3, 23, 10, i, tzinfo=timezone.utc)  # Monday
            manager.add_price(supply_kwh=100.0, demand_kwh=100.0, timestamp=timestamp)

        # OFF_PEAK (weekday 23:00) - lower price
        for i in range(5):
            timestamp = datetime(2026, 3, 23, 23, i, tzinfo=timezone.utc)  # Monday
            manager.add_price(supply_kwh=100.0, demand_kwh=100.0, timestamp=timestamp)

        stats = manager.get_statistics(hours=24)

        assert stats["count"] == 10
        assert stats["avg"] is not None
        assert stats["min"] is not None
        assert stats["max"] is not None
        assert stats["std_dev"] is not None
        assert stats["current"] is not None

        # ON_PEAK price should be higher than OFF_PEAK
        # So min < max (different ToU periods)
        assert stats["min"] < stats["max"]

    def test_get_statistics_empty(self):
        """Test statistics with no data."""
        manager = PriceHistoryManager()
        
        stats = manager.get_statistics(hours=24)
        
        assert stats["count"] == 0
        assert stats["avg"] is None
        assert stats["min"] is None
        assert stats["max"] is None

    def test_hourly_summary(self):
        """Test hourly aggregation."""
        manager = PriceHistoryManager()
        
        # Add records across multiple hours
        base_time = datetime.now(timezone.utc)
        for hour in range(3):
            for minute in range(0, 60, 15):
                timestamp = base_time.replace(hour=base_time.hour + hour, minute=minute)
                manager.add_price(
                    supply_kwh=100.0,
                    demand_kwh=100.0,
                    timestamp=timestamp,
                )
        
        summary = manager.get_hourly_summary(hours=24)
        
        # Should have 3 hourly buckets
        assert len(summary) >= 3
        
        # Each bucket should have required fields
        for bucket in summary:
            assert "hour" in bucket
            assert "avg_price" in bucket
            assert "min_price" in bucket
            assert "max_price" in bucket
            assert "record_count" in bucket

    def test_daily_summary(self):
        """Test daily aggregation."""
        manager = PriceHistoryManager()
        
        # Add records across multiple days
        base_time = datetime.now(timezone.utc)
        for day in range(5):
            for hour in range(0, 24, 2):
                timestamp = base_time - timedelta(days=day, hours=hour)
                manager.add_price(
                    supply_kwh=100.0,
                    demand_kwh=100.0,
                    timestamp=timestamp,
                )
        
        summary = manager.get_daily_summary(days=7)
        
        # Should have 5-6 daily buckets (depending on current time)
        assert len(summary) >= 5
        assert len(summary) <= 7
        
        # Each bucket should have required fields
        for bucket in summary:
            assert "date" in bucket
            assert "avg_price" in bucket
            assert "min_price" in bucket
            assert "max_price" in bucket
            assert "record_count" in bucket

    def test_tou_analysis(self):
        """Test TOU period analysis."""
        manager = PriceHistoryManager()

        # Add ON_PEAK records (weekday 10:00)
        for i in range(5):
            timestamp = datetime(2026, 3, 23, 10, 0, tzinfo=timezone.utc)  # Monday
            manager.add_price(supply_kwh=100.0, demand_kwh=100.0, timestamp=timestamp)

        # Add OFF_PEAK records (weekday 23:00)
        for i in range(5):
            timestamp = datetime(2026, 3, 23, 23, 0, tzinfo=timezone.utc)  # Monday
            manager.add_price(supply_kwh=100.0, demand_kwh=100.0, timestamp=timestamp)

        analysis = manager.get_tou_analysis(hours=24)

        assert "on_peak" in analysis
        assert "off_peak" in analysis
        assert "spread" in analysis

        # Verify ON_PEAK has higher prices than OFF_PEAK (ToU-based)
        assert analysis["on_peak"]["count"] == 5
        assert analysis["off_peak"]["count"] == 5
        # ON_PEAK rate (5.7982) should be higher than OFF_PEAK (2.6369)
        assert analysis["on_peak"]["avg"] > analysis["off_peak"]["avg"]
        # Verify spread is positive (ON_PEAK - OFF_PEAK)
        assert analysis["spread"] > 0

    def test_market_sentiment_distribution(self):
        """Test sentiment distribution."""
        manager = PriceHistoryManager()
        
        # Add HIGH_DEMAND records
        for i in range(10):
            manager.add_price(supply_kwh=50.0, demand_kwh=150.0)
        
        # Add BALANCED records
        for i in range(20):
            manager.add_price(supply_kwh=100.0, demand_kwh=100.0)
        
        # Add LOW_DEMAND records
        for i in range(5):
            manager.add_price(supply_kwh=150.0, demand_kwh=50.0)
        
        distribution = manager.get_market_sentiment_distribution(hours=24)
        
        assert distribution["HIGH_DEMAND"] == 10
        assert distribution["BALANCED"] == 20
        assert distribution["LOW_DEMAND"] == 5

    def test_export_to_list(self):
        """Test exporting history to list."""
        manager = PriceHistoryManager()
        
        # Add some records
        for i in range(5):
            manager.add_price(supply_kwh=100.0 + i, demand_kwh=100.0)
        
        exported = manager.export_to_list()
        
        assert len(exported) == 5
        assert isinstance(exported[0], dict)
        assert "timestamp" in exported[0]
        assert "market_clearing_price_baht_kwh" in exported[0]

    def test_clear_history(self):
        """Test clearing history."""
        manager = PriceHistoryManager()
        
        # Add some records
        for i in range(10):
            manager.add_price(supply_kwh=100.0, demand_kwh=100.0)
        
        assert manager.get_record_count() == 10
        
        # Clear
        manager.clear_history()
        
        assert manager.get_record_count() == 0

    @pytest.mark.asyncio
    async def test_start_stop(self):
        """Test starting and stopping manager."""
        manager = PriceHistoryManager()
        
        await manager.start()
        assert manager._cleanup_task is not None
        
        await asyncio.sleep(0.1)
        
        await manager.stop()
        assert manager._cleanup_task.done() or manager._cleanup_task.cancelled()


class TestPriceHistoryAPI:
    """Tests for price history API endpoints."""

    def test_get_price_history(self):
        """Test GET /api/v1/price/history endpoint."""
        client = TestClient(app)
        
        response = client.get("/api/v1/price/history?limit=50")
        
        # Note: This may return 503 if app not fully initialized in test
        # For unit tests, we test the manager directly
        assert response.status_code in [200, 503]

    def test_get_price_statistics(self):
        """Test GET /api/v1/price/history/statistics endpoint."""
        client = TestClient(app)
        
        response = client.get("/api/v1/price/history/statistics?hours=24")
        
        assert response.status_code in [200, 503]

    def test_get_hourly_summary(self):
        """Test GET /api/v1/price/history/hourly endpoint."""
        client = TestClient(app)
        
        response = client.get("/api/v1/price/history/hourly?hours=24")
        
        assert response.status_code in [200, 503]

    def test_get_daily_summary(self):
        """Test GET /api/v1/price/history/daily endpoint."""
        client = TestClient(app)
        
        response = client.get("/api/v1/price/history/daily?days=7")
        
        assert response.status_code in [200, 503]

    def test_get_tou_analysis(self):
        """Test GET /api/v1/price/history/tou-analysis endpoint."""
        client = TestClient(app)
        
        response = client.get("/api/v1/price/history/tou-analysis?hours=24")
        
        assert response.status_code in [200, 503]

    def test_get_market_sentiment(self):
        """Test GET /api/v1/price/history/sentiment endpoint."""
        client = TestClient(app)
        
        response = client.get("/api/v1/price/history/sentiment?hours=24")
        
        assert response.status_code in [200, 503]

    def test_get_history_status(self):
        """Test GET /api/v1/price/history/status endpoint."""
        client = TestClient(app)
        
        response = client.get("/api/v1/price/history/status")
        
        assert response.status_code in [200, 503]

    def test_price_history_validation(self):
        """Test validation for invalid parameters."""
        client = TestClient(app)
        
        # Invalid limit (> 1000)
        response = client.get("/api/v1/price/history?limit=2000")
        
        assert response.status_code == 422
        
        # Invalid hours (> 168)
        response = client.get("/api/v1/price/history/statistics?hours=200")
        
        assert response.status_code == 422


class TestPriceRecord:
    """Tests for PriceRecord dataclass."""

    def test_price_record_creation(self):
        """Test creating a PriceRecord."""
        record = PriceRecord(
            timestamp="2026-03-21T12:00:00Z",
            market_clearing_price_baht_kwh=3.30,
            buyer_total_baht_kwh=4.18,
            seller_net_baht_kwh=2.42,
            supply_kwh=100.0,
            demand_kwh=100.0,
            demand_ratio=1.0,
            market_sentiment="BALANCED",
            tou_period="on_peak",
            tou_rate_baht_kwh=5.7982,
            p2p_discount_percent=10.0,
        )

        assert record.market_clearing_price_baht_kwh == 3.30
        assert record.market_sentiment == "BALANCED"
        assert record.tou_period == "on_peak"
        assert record.tou_rate_baht_kwh == 5.7982
        assert record.p2p_discount_percent == 10.0

    def test_price_record_to_dict(self):
        """Test converting PriceRecord to dict."""
        from dataclasses import asdict

        record = PriceRecord(
            timestamp="2026-03-21T12:00:00Z",
            market_clearing_price_baht_kwh=3.30,
            buyer_total_baht_kwh=4.18,
            seller_net_baht_kwh=2.42,
            supply_kwh=100.0,
            demand_kwh=100.0,
            demand_ratio=1.0,
            market_sentiment="BALANCED",
            tou_period="on_peak",
            tou_rate_baht_kwh=5.7982,
            p2p_discount_percent=10.0,
        )

        record_dict = asdict(record)

        assert isinstance(record_dict, dict)
        assert record_dict["market_clearing_price_baht_kwh"] == 3.30
        assert record_dict["tou_rate_baht_kwh"] == 5.7982
        assert record_dict["p2p_discount_percent"] == 10.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
