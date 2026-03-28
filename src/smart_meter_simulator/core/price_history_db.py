"""
Price History Database Manager

Persistent storage for P2P price history using SQLite.
Provides long-term retention beyond in-memory buffer.
"""

import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional
from pathlib import Path
import aiosqlite

from .price_history import PriceRecord

logger = logging.getLogger(__name__)


class PriceHistoryDatabase:
    """
    SQLite database manager for price history.
    
    Features:
    - Persistent storage beyond in-memory buffer
    - Configurable retention (days/weeks/months)
    - Efficient time-range queries
    - Automatic cleanup of old records
    - Export/import capabilities
    """

    def __init__(
        self,
        db_path: str = "data/price_history.db",
        retention_days: int = 30,
    ):
        self.db_path = Path(db_path)
        self.retention_days = retention_days
        self._db: Optional[aiosqlite.Connection] = None
        self._cleanup_task: Optional[asyncio.Task] = None
        
        # Ensure directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    async def connect(self):
        """Initialize database connection and create tables."""
        self._db = await aiosqlite.connect(str(self.db_path))
        self._db.row_factory = aiosqlite.Row
        
        await self._create_tables()
        await self._create_indexes()
        
        # Start background cleanup
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        
        logger.info(f"PriceHistoryDatabase connected: {self.db_path}")

    async def disconnect(self):
        """Close database connection."""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        
        if self._db:
            await self._db.close()
        
        logger.info("PriceHistoryDatabase disconnected")

    async def _create_tables(self):
        """Create database tables."""
        await self._db.execute("""
            CREATE TABLE IF NOT EXISTS price_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                market_clearing_price_baht_kwh REAL NOT NULL,
                buyer_total_baht_kwh REAL NOT NULL,
                seller_net_baht_kwh REAL NOT NULL,
                supply_kwh REAL NOT NULL,
                demand_kwh REAL NOT NULL,
                demand_ratio REAL NOT NULL,
                market_sentiment TEXT NOT NULL,
                tou_period TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        await self._db.execute("""
            CREATE TABLE IF NOT EXISTS hourly_summary (
                hour TEXT PRIMARY KEY,
                avg_price REAL NOT NULL,
                min_price REAL NOT NULL,
                max_price REAL NOT NULL,
                record_count INTEGER NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        await self._db.execute("""
            CREATE TABLE IF NOT EXISTS daily_summary (
                date TEXT PRIMARY KEY,
                avg_price REAL NOT NULL,
                min_price REAL NOT NULL,
                max_price REAL NOT NULL,
                record_count INTEGER NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        await self._db.commit()
        logger.debug("Database tables created")

    async def _create_indexes(self):
        """Create indexes for efficient queries."""
        await self._db.execute("""
            CREATE INDEX IF NOT EXISTS idx_timestamp 
            ON price_records(timestamp)
        """)
        
        await self._db.execute("""
            CREATE INDEX IF NOT EXISTS idx_sentiment 
            ON price_records(market_sentiment)
        """)
        
        await self._db.execute("""
            CREATE INDEX IF NOT EXISTS idx_tou_period 
            ON price_records(tou_period)
        """)
        
        await self._db.commit()
        logger.debug("Database indexes created")

    async def _cleanup_loop(self):
        """Periodically clean up old records."""
        while True:
            try:
                await asyncio.sleep(3600 * 24)  # Run daily
                await self._cleanup_old_records()
                await self._update_summaries()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}")

    async def add_record(self, record: PriceRecord) -> int:
        """
        Add a price record to the database.
        
        Args:
            record: PriceRecord to store
            
        Returns:
            Database row ID
        """
        cursor = await self._db.execute("""
            INSERT INTO price_records (
                timestamp,
                market_clearing_price_baht_kwh,
                buyer_total_baht_kwh,
                seller_net_baht_kwh,
                supply_kwh,
                demand_kwh,
                demand_ratio,
                market_sentiment,
                tou_period
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            record.timestamp,
            record.market_clearing_price_baht_kwh,
            record.buyer_total_baht_kwh,
            record.seller_net_baht_kwh,
            record.supply_kwh,
            record.demand_kwh,
            record.demand_ratio,
            record.market_sentiment,
            record.tou_period,
        ))
        
        await self._db.commit()
        return cursor.lastrowid

    async def add_record_batch(self, records: List[PriceRecord]) -> int:
        """
        Add multiple records in a single transaction.
        
        Args:
            records: List of PriceRecord to store
            
        Returns:
            Number of records inserted
        """
        data = [
            (
                r.timestamp,
                r.market_clearing_price_baht_kwh,
                r.buyer_total_baht_kwh,
                r.seller_net_baht_kwh,
                r.supply_kwh,
                r.demand_kwh,
                r.demand_ratio,
                r.market_sentiment,
                r.tou_period,
            )
            for r in records
        ]
        
        await self._db.executemany("""
            INSERT INTO price_records (
                timestamp,
                market_clearing_price_baht_kwh,
                buyer_total_baht_kwh,
                seller_net_baht_kwh,
                supply_kwh,
                demand_kwh,
                demand_ratio,
                market_sentiment,
                tou_period
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, data)
        
        await self._db.commit()
        return len(records)

    async def get_recent_records(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get most recent price records.
        
        Args:
            limit: Maximum number of records
            
        Returns:
            List of price records (newest first)
        """
        cursor = await self._db.execute("""
            SELECT * FROM price_records
            ORDER BY timestamp DESC
            LIMIT ?
        """, (limit,))
        
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

    async def get_records_in_range(
        self,
        start_time: datetime,
        end_time: datetime,
    ) -> List[Dict[str, Any]]:
        """
        Get records within a time range.
        
        Args:
            start_time: Start of range
            end_time: End of range
            
        Returns:
            List of price records
        """
        cursor = await self._db.execute("""
            SELECT * FROM price_records
            WHERE timestamp BETWEEN ? AND ?
            ORDER BY timestamp ASC
        """, (
            start_time.isoformat(),
            end_time.isoformat(),
        ))
        
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

    async def get_statistics(
        self,
        hours: int = 24,
    ) -> Dict[str, Any]:
        """
        Calculate statistics for a time period.
        
        Args:
            hours: Time window in hours
            
        Returns:
            Statistical metrics
        """
        cutoff = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()
        
        cursor = await self._db.execute("""
            SELECT 
                COUNT(*) as count,
                AVG(market_clearing_price_baht_kwh) as avg,
                MIN(market_clearing_price_baht_kwh) as min,
                MAX(market_clearing_price_baht_kwh) as max
            FROM price_records
            WHERE timestamp > ?
        """, (cutoff,))
        
        row = await cursor.fetchone()
        
        if row['count'] == 0:
            return {
                "count": 0,
                "avg": None,
                "min": None,
                "max": None,
                "std_dev": None,
            }
        
        # Calculate std dev separately
        cursor = await self._db.execute("""
            SELECT market_clearing_price_baht_kwh
            FROM price_records
            WHERE timestamp > ?
        """, (cutoff,))
        
        prices = [row['market_clearing_price_baht_kwh'] for row in await cursor.fetchall()]
        
        if len(prices) > 1:
            mean = sum(prices) / len(prices)
            variance = sum((x - mean) ** 2 for x in prices) / (len(prices) - 1)
            std_dev = variance ** 0.5
        else:
            std_dev = 0
        
        return {
            "count": row['count'],
            "avg": round(row['avg'], 4) if row['avg'] else None,
            "min": round(row['min'], 4) if row['min'] else None,
            "max": round(row['max'], 4) if row['max'] else None,
            "std_dev": round(std_dev, 4),
        }

    async def get_hourly_summary(self, hours: int = 24) -> List[Dict[str, Any]]:
        """
        Get hourly aggregated data.
        
        Args:
            hours: Number of hours
            
        Returns:
            List of hourly summaries
        """
        # Use pre-computed summary if available
        cursor = await self._db.execute("""
            SELECT * FROM hourly_summary
            ORDER BY hour DESC
            LIMIT ?
        """, (hours,))
        
        rows = await cursor.fetchall()
        
        if rows:
            return [dict(row) for row in rows]
        
        # Calculate on-the-fly if no summary
        cutoff = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()
        
        cursor = await self._db.execute("""
            SELECT 
                strftime('%Y-%m-%d %H:00', timestamp) as hour,
                AVG(market_clearing_price_baht_kwh) as avg_price,
                MIN(market_clearing_price_baht_kwh) as min_price,
                MAX(market_clearing_price_baht_kwh) as max_price,
                COUNT(*) as record_count
            FROM price_records
            WHERE timestamp > ?
            GROUP BY strftime('%Y-%m-%d %H:00', timestamp)
            ORDER BY hour ASC
        """, (cutoff,))
        
        return [dict(row) for row in await cursor.fetchall()]

    async def get_daily_summary(self, days: int = 7) -> List[Dict[str, Any]]:
        """
        Get daily aggregated data.
        
        Args:
            days: Number of days
            
        Returns:
            List of daily summaries
        """
        # Use pre-computed summary if available
        cursor = await self._db.execute("""
            SELECT * FROM daily_summary
            ORDER BY date DESC
            LIMIT ?
        """, (days,))
        
        rows = await cursor.fetchall()
        
        if rows:
            return [dict(row) for row in rows]
        
        # Calculate on-the-fly if no summary
        cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        
        cursor = await self._db.execute("""
            SELECT 
                strftime('%Y-%m-%d', timestamp) as date,
                AVG(market_clearing_price_baht_kwh) as avg_price,
                MIN(market_clearing_price_baht_kwh) as min_price,
                MAX(market_clearing_price_baht_kwh) as max_price,
                COUNT(*) as record_count
            FROM price_records
            WHERE timestamp > ?
            GROUP BY strftime('%Y-%m-%d', timestamp)
            ORDER BY date ASC
        """, (cutoff,))
        
        return [dict(row) for row in await cursor.fetchall()]

    async def get_tou_analysis(self, hours: int = 24) -> Dict[str, Any]:
        """
        Analyze TOU period pricing.
        
        Args:
            hours: Time window in hours
            
        Returns:
            TOU analysis
        """
        cutoff = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()
        
        cursor = await self._db.execute("""
            SELECT 
                tou_period,
                COUNT(*) as count,
                AVG(market_clearing_price_baht_kwh) as avg,
                MIN(market_clearing_price_baht_kwh) as min,
                MAX(market_clearing_price_baht_kwh) as max
            FROM price_records
            WHERE timestamp > ?
            GROUP BY tou_period
        """, (cutoff,))
        
        rows = await cursor.fetchall()
        
        result = {
            "on_peak": None,
            "off_peak": None,
            "spread": None,
        }
        
        for row in rows:
            period = "on_peak" if row['tou_period'] == "ON_PEAK" else "off_peak"
            result[period] = {
                "count": row['count'],
                "avg": round(row['avg'], 4) if row['avg'] else None,
                "min": round(row['min'], 4) if row['min'] else None,
                "max": round(row['max'], 4) if row['max'] else None,
            }
        
        if result["on_peak"] and result["off_peak"]:
            result["spread"] = round(
                result["on_peak"]["avg"] - result["off_peak"]["avg"], 4
            )
        
        return result

    async def get_sentiment_distribution(self, hours: int = 24) -> Dict[str, int]:
        """
        Get market sentiment distribution.
        
        Args:
            hours: Time window in hours
            
        Returns:
            Count per sentiment
        """
        cutoff = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()
        
        cursor = await self._db.execute("""
            SELECT 
                market_sentiment,
                COUNT(*) as count
            FROM price_records
            WHERE timestamp > ?
            GROUP BY market_sentiment
        """, (cutoff,))
        
        rows = await cursor.fetchall()
        
        return {
            "HIGH_DEMAND": 0,
            "BALANCED": 0,
            "LOW_DEMAND": 0,
            **{row['market_sentiment']: row['count'] for row in rows},
        }

    async def _cleanup_old_records(self):
        """Remove records older than retention period."""
        cutoff = (datetime.now(timezone.utc) - timedelta(days=self.retention_days)).isoformat()
        
        cursor = await self._db.execute("""
            DELETE FROM price_records
            WHERE timestamp < ?
        """, (cutoff,))
        
        deleted = cursor.rowcount
        await self._db.commit()
        
        if deleted > 0:
            logger.info(f"Deleted {deleted} old price records")

    async def _update_summaries(self):
        """Update hourly and daily summary tables."""
        # Update hourly summary
        await self._db.execute("""
            INSERT OR REPLACE INTO hourly_summary (hour, avg_price, min_price, max_price, record_count, created_at)
            SELECT 
                strftime('%Y-%m-%d %H:00', timestamp) as hour,
                AVG(market_clearing_price_baht_kwh) as avg_price,
                MIN(market_clearing_price_baht_kwh) as min_price,
                MAX(market_clearing_price_baht_kwh) as max_price,
                COUNT(*) as record_count,
                CURRENT_TIMESTAMP as created_at
            FROM price_records
            GROUP BY strftime('%Y-%m-%d %H:00', timestamp)
        """)
        
        # Update daily summary
        await self._db.execute("""
            INSERT OR REPLACE INTO daily_summary (date, avg_price, min_price, max_price, record_count, created_at)
            SELECT 
                strftime('%Y-%m-%d', timestamp) as date,
                AVG(market_clearing_price_baht_kwh) as avg_price,
                MIN(market_clearing_price_baht_kwh) as min_price,
                MAX(market_clearing_price_baht_kwh) as max_price,
                COUNT(*) as record_count,
                CURRENT_TIMESTAMP as created_at
            FROM price_records
            GROUP BY strftime('%Y-%m-%d', timestamp)
        """)
        
        await self._db.commit()
        logger.debug("Summary tables updated")

    async def get_record_count(self) -> int:
        """Get total number of stored records."""
        cursor = await self._db.execute("SELECT COUNT(*) as count FROM price_records")
        row = await cursor.fetchone()
        return row['count']

    async def clear_history(self):
        """Clear all stored data."""
        await self._db.execute("DELETE FROM price_records")
        await self._db.execute("DELETE FROM hourly_summary")
        await self._db.execute("DELETE FROM daily_summary")
        await self._db.commit()
        logger.info("Price history cleared")

    async def export_to_csv(self, filepath: str) -> int:
        """
        Export price history to CSV file.
        
        Args:
            filepath: Output file path
            
        Returns:
            Number of records exported
        """
        cursor = await self._db.execute("""
            SELECT * FROM price_records
            ORDER BY timestamp ASC
        """)
        
        rows = await cursor.fetchall()
        
        import csv
        with open(filepath, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys() if rows else [])
            writer.writeheader()
            for row in rows:
                writer.writerow(dict(row))
        
        logger.info(f"Exported {len(rows)} records to {filepath}")
        return len(rows)
