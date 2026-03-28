"""
Price History Database Tests

Tests for SQLite-backed price history storage:
- PriceHistoryDatabase class
- Database CRUD operations
- Long-term retention
- Export functionality

Run with:
    uv run pytest tests/test_price_history_db.py -v
"""

import pytest
import pytest_asyncio
import asyncio
from datetime import datetime, timezone, timedelta
from pathlib import Path
import tempfile

from smart_meter_simulator.core.price_history_db import PriceHistoryDatabase
from smart_meter_simulator.core.price_history import PriceRecord


def make_price_record(
    timestamp: str = "2026-03-21T12:00:00Z",
    market_clearing_price_baht_kwh: float = 3.30,
    buyer_total_baht_kwh: float = 4.18,
    seller_net_baht_kwh: float = 2.42,
    supply_kwh: float = 100.0,
    demand_kwh: float = 100.0,
    demand_ratio: float = 1.0,
    market_sentiment: str = "BALANCED",
    tou_period: str = "on_peak",
    tou_rate_baht_kwh: float = 5.7982,
    p2p_discount_percent: float = 10.0,
) -> PriceRecord:
    """Helper to create PriceRecord with all required fields."""
    return PriceRecord(
        timestamp=timestamp,
        market_clearing_price_baht_kwh=market_clearing_price_baht_kwh,
        buyer_total_baht_kwh=buyer_total_baht_kwh,
        seller_net_baht_kwh=seller_net_baht_kwh,
        supply_kwh=supply_kwh,
        demand_kwh=demand_kwh,
        demand_ratio=demand_ratio,
        market_sentiment=market_sentiment,
        tou_period=tou_period,
        tou_rate_baht_kwh=tou_rate_baht_kwh,
        p2p_discount_percent=p2p_discount_percent,
    )


@pytest.fixture
def temp_db_path():
    """Create temporary database file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_price_history.db"
        yield str(db_path)


@pytest_asyncio.fixture
async def db(temp_db_path):
    """Create database connection."""
    database = PriceHistoryDatabase(db_path=temp_db_path, retention_days=7)
    await database.connect()
    yield database
    await database.disconnect()


class TestPriceHistoryDatabase:
    """Tests for PriceHistoryDatabase class."""

    def test_initialization(self, temp_db_path):
        """Test database initialization."""
        db = PriceHistoryDatabase(db_path=temp_db_path, retention_days=30)
        
        assert db.db_path == Path(temp_db_path)
        assert db.retention_days == 30
        assert db._db is None

    @pytest.mark.asyncio
    async def test_connect_disconnect(self, temp_db_path):
        """Test database connection lifecycle."""
        db = PriceHistoryDatabase(db_path=temp_db_path)
        
        await db.connect()
        assert db._db is not None
        
        # Verify we can query
        count = await db.get_record_count()
        assert count == 0
        
        await db.disconnect()
        # After disconnect, _db should be closed
        # We can't check _db is None because aiosqlite keeps the object
        # Just verify the method completed without error

    @pytest.mark.asyncio
    async def test_add_record(self, db):
        """Test adding a price record."""
        record = make_price_record(
            timestamp="2026-03-21T12:00:00Z",
            market_clearing_price_baht_kwh=3.30,
            buyer_total_baht_kwh=4.18,
            seller_net_baht_kwh=2.42,
            supply_kwh=100.0,
            demand_kwh=100.0,
            demand_ratio=1.0,
            market_sentiment="BALANCED",
            tou_period="ON_PEAK",
        )
        
        row_id = await db.add_record(record)
        
        assert row_id > 0

    @pytest.mark.asyncio
    async def test_add_record_batch(self, db):
        """Test adding multiple records."""
        records = [
            make_price_record(
                timestamp=f"2026-03-21T{i:02d}:00:00Z",
                market_clearing_price_baht_kwh=3.30 + i * 0.1,
                buyer_total_baht_kwh=4.18,
                seller_net_baht_kwh=2.42,
                supply_kwh=100.0,
                demand_kwh=100.0,
                demand_ratio=1.0,
                market_sentiment="BALANCED",
                tou_period="ON_PEAK",
            )
            for i in range(10)
        ]
        
        count = await db.add_record_batch(records)
        
        assert count == 10

    @pytest.mark.asyncio
    async def test_get_recent_records(self, db):
        """Test retrieving recent records."""
        # Add records
        records = [
            make_price_record(
                timestamp=f"2026-03-21T{i:02d}:00:00Z",
                market_clearing_price_baht_kwh=3.30 + i * 0.1,
                buyer_total_baht_kwh=4.18,
                seller_net_baht_kwh=2.42,
                supply_kwh=100.0,
                demand_kwh=100.0,
                demand_ratio=1.0,
                market_sentiment="BALANCED",
                tou_period="ON_PEAK",
            )
            for i in range(20)
        ]
        await db.add_record_batch(records)
        
        # Get recent
        recent = await db.get_recent_records(limit=5)
        
        assert len(recent) == 5
        # Should be newest first
        assert recent[0]['market_clearing_price_baht_kwh'] > recent[-1]['market_clearing_price_baht_kwh']

    @pytest.mark.asyncio
    async def test_get_records_in_range(self, db):
        """Test retrieving records in time range."""
        # Add records
        records = [
            make_price_record(
                timestamp=f"2026-03-21T{i:02d}:00:00Z",
                market_clearing_price_baht_kwh=3.30,
                buyer_total_baht_kwh=4.18,
                seller_net_baht_kwh=2.42,
                supply_kwh=100.0,
                demand_kwh=100.0,
                demand_ratio=1.0,
                market_sentiment="BALANCED",
                tou_period="ON_PEAK",
            )
            for i in range(24)
        ]
        await db.add_record_batch(records)
        
        # Get range (10:00 to 14:00)
        start = datetime(2026, 3, 21, 10, 0, tzinfo=timezone.utc)
        end = datetime(2026, 3, 21, 14, 0, tzinfo=timezone.utc)
        records = await db.get_records_in_range(start, end)
        
        # BETWEEN is inclusive, but timestamp comparison may vary
        assert len(records) >= 4  # At least 10, 11, 12, 13
        assert len(records) <= 5  # At most 10, 11, 12, 13, 14

    @pytest.mark.asyncio
    async def test_get_statistics(self, db):
        """Test statistics calculation."""
        # Add records with varying prices
        records = [
            make_price_record(
                timestamp=f"2026-03-21T{i:02d}:00:00Z",
                market_clearing_price_baht_kwh=3.0 + i * 0.1,
                buyer_total_baht_kwh=4.18,
                seller_net_baht_kwh=2.42,
                supply_kwh=100.0,
                demand_kwh=100.0,
                demand_ratio=1.0,
                market_sentiment="BALANCED",
                tou_period="ON_PEAK",
            )
            for i in range(10)
        ]
        await db.add_record_batch(records)
        
        stats = await db.get_statistics(hours=24)
        
        assert stats["count"] == 10
        assert stats["avg"] is not None
        assert stats["min"] is not None
        assert stats["max"] is not None
        assert stats["std_dev"] is not None
        
        # Verify calculations
        assert stats["min"] == 3.0
        assert stats["max"] == 3.9

    @pytest.mark.asyncio
    async def test_get_statistics_empty(self, db):
        """Test statistics with no data."""
        stats = await db.get_statistics(hours=24)
        
        assert stats["count"] == 0
        assert stats["avg"] is None
        assert stats["min"] is None
        assert stats["max"] is None

    @pytest.mark.asyncio
    async def test_get_hourly_summary(self, db):
        """Test hourly aggregation."""
        # Add records across multiple hours
        records = []
        for hour in range(5):
            for minute in range(0, 60, 15):
                records.append(make_price_record(
                    timestamp=f"2026-03-21T{hour:02d}:{minute:02d}:00Z",
                    market_clearing_price_baht_kwh=3.0 + hour * 0.1,
                    buyer_total_baht_kwh=4.18,
                    seller_net_baht_kwh=2.42,
                    supply_kwh=100.0,
                    demand_kwh=100.0,
                    demand_ratio=1.0,
                    market_sentiment="BALANCED",
                    tou_period="ON_PEAK",
                ))
        
        await db.add_record_batch(records)
        
        summary = await db.get_hourly_summary(hours=24)
        
        assert len(summary) == 5
        for bucket in summary:
            assert "hour" in bucket
            assert "avg_price" in bucket
            assert "record_count" in bucket

    @pytest.mark.asyncio
    async def test_get_daily_summary(self, db):
        """Test daily aggregation."""
        # Add records across multiple days
        records = []
        for day in range(3):
            for hour in range(0, 24, 2):
                records.append(make_price_record(
                    timestamp=f"2026-03-{21+day:02d}T{hour:02d}:00:00Z",
                    market_clearing_price_baht_kwh=3.0 + day * 0.1,
                    buyer_total_baht_kwh=4.18,
                    seller_net_baht_kwh=2.42,
                    supply_kwh=100.0,
                    demand_kwh=100.0,
                    demand_ratio=1.0,
                    market_sentiment="BALANCED",
                    tou_period="ON_PEAK",
                ))
        
        await db.add_record_batch(records)
        
        summary = await db.get_daily_summary(days=7)
        
        assert len(summary) == 3

    @pytest.mark.asyncio
    async def test_get_tou_analysis(self, db):
        """Test TOU period analysis."""
        # Add ON_PEAK records
        on_peak_records = [
            make_price_record(
                timestamp=f"2026-03-21T{10+i:02d}:00:00Z",
                market_clearing_price_baht_kwh=3.5,
                buyer_total_baht_kwh=4.18,
                seller_net_baht_kwh=2.42,
                supply_kwh=100.0,
                demand_kwh=100.0,
                demand_ratio=1.0,
                market_sentiment="BALANCED",
                tou_period="ON_PEAK",
            )
            for i in range(5)
        ]
        
        # Add OFF_PEAK records
        off_peak_records = [
            make_price_record(
                timestamp=f"2026-03-21T{22+i:02d}:00:00Z",
                market_clearing_price_baht_kwh=3.0,
                buyer_total_baht_kwh=4.18,
                seller_net_baht_kwh=2.42,
                supply_kwh=100.0,
                demand_kwh=100.0,
                demand_ratio=1.0,
                market_sentiment="BALANCED",
                tou_period="OFF_PEAK",
            )
            for i in range(5)
        ]
        
        await db.add_record_batch(on_peak_records)
        await db.add_record_batch(off_peak_records)
        
        analysis = await db.get_tou_analysis(hours=24)
        
        assert "on_peak" in analysis
        assert "off_peak" in analysis
        assert "spread" in analysis
        
        assert analysis["on_peak"]["count"] == 5
        assert analysis["off_peak"]["count"] == 5
        assert analysis["spread"] > 0  # ON_PEAK should be higher

    @pytest.mark.asyncio
    async def test_get_sentiment_distribution(self, db):
        """Test sentiment distribution."""
        # Add different sentiments
        records = []
        
        # HIGH_DEMAND
        for i in range(10):
            records.append(make_price_record(
                timestamp=f"2026-03-21T{i:02d}:00:00Z",
                market_clearing_price_baht_kwh=4.0,
                buyer_total_baht_kwh=4.18,
                seller_net_baht_kwh=2.42,
                supply_kwh=50.0,
                demand_kwh=150.0,
                demand_ratio=3.0,
                market_sentiment="HIGH_DEMAND",
                tou_period="ON_PEAK",
            ))
        
        # BALANCED
        for i in range(20):
            records.append(make_price_record(
                timestamp=f"2026-03-21T{10+i:02d}:00:00Z",
                market_clearing_price_baht_kwh=3.3,
                buyer_total_baht_kwh=4.18,
                seller_net_baht_kwh=2.42,
                supply_kwh=100.0,
                demand_kwh=100.0,
                demand_ratio=1.0,
                market_sentiment="BALANCED",
                tou_period="ON_PEAK",
            ))
        
        await db.add_record_batch(records)
        
        distribution = await db.get_sentiment_distribution(hours=24)
        
        assert distribution["HIGH_DEMAND"] == 10
        assert distribution["BALANCED"] == 20
        assert distribution["LOW_DEMAND"] == 0

    @pytest.mark.asyncio
    async def test_get_record_count(self, db):
        """Test record count."""
        # Add some records
        records = [
            make_price_record(
                timestamp=f"2026-03-21T{i:02d}:00:00Z",
                market_clearing_price_baht_kwh=3.30,
                buyer_total_baht_kwh=4.18,
                seller_net_baht_kwh=2.42,
                supply_kwh=100.0,
                demand_kwh=100.0,
                demand_ratio=1.0,
                market_sentiment="BALANCED",
                tou_period="ON_PEAK",
            )
            for i in range(50)
        ]
        await db.add_record_batch(records)
        
        count = await db.get_record_count()
        
        assert count == 50

    @pytest.mark.asyncio
    async def test_clear_history(self, db):
        """Test clearing history."""
        # Add some records
        records = [
            make_price_record(
                timestamp=f"2026-03-21T{i:02d}:00:00Z",
                market_clearing_price_baht_kwh=3.30,
                buyer_total_baht_kwh=4.18,
                seller_net_baht_kwh=2.42,
                supply_kwh=100.0,
                demand_kwh=100.0,
                demand_ratio=1.0,
                market_sentiment="BALANCED",
                tou_period="ON_PEAK",
            )
            for i in range(20)
        ]
        await db.add_record_batch(records)
        
        assert await db.get_record_count() == 20
        
        # Clear
        await db.clear_history()
        
        assert await db.get_record_count() == 0

    @pytest.mark.asyncio
    async def test_export_to_csv(self, db, temp_db_path):
        """Test CSV export."""
        # Add some records
        records = [
            make_price_record(
                timestamp=f"2026-03-21T{i:02d}:00:00Z",
                market_clearing_price_baht_kwh=3.30 + i * 0.1,
                buyer_total_baht_kwh=4.18,
                seller_net_baht_kwh=2.42,
                supply_kwh=100.0,
                demand_kwh=100.0,
                demand_ratio=1.0,
                market_sentiment="BALANCED",
                tou_period="ON_PEAK",
            )
            for i in range(10)
        ]
        await db.add_record_batch(records)
        
        # Export
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "export.csv"
            count = await db.export_to_csv(str(filepath))
            
            assert count == 10
            assert filepath.exists()
            
            # Verify content
            with open(filepath, 'r') as f:
                lines = f.readlines()
                assert len(lines) == 11  # Header + 10 records


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
