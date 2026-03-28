"""
Price History Manager

Stores and retrieves historical P2P market prices for analytics and reporting.
Prices are based on Time-of-Use (ToU) tariffs.
"""

import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional
from collections import deque
from dataclasses import dataclass, asdict

from ..config.thai_market import (
    GRID_BUYBACK_RATE,
    GRID_PURCHASE_RATE_HIGH_TIER,
    TYPICAL_P2P_PRICE,
    RESIDENTIAL_WHEELING_COST_AVG,
    TOU_RATES,
    TOUPeriod,
    get_tou_period,
)

logger = logging.getLogger(__name__)


@dataclass
class PriceRecord:
    """Single price data point."""
    timestamp: str
    market_clearing_price_baht_kwh: float
    buyer_total_baht_kwh: float
    seller_net_baht_kwh: float
    supply_kwh: float
    demand_kwh: float
    demand_ratio: float
    market_sentiment: str
    tou_period: str
    tou_rate_baht_kwh: float
    p2p_discount_percent: float


class PriceHistoryManager:
    """
    Manages historical P2P price data based on ToU tariffs.

    Features:
    - In-memory storage with configurable retention
    - SQLite persistent storage for long-term retention (30 days)
    - Time-series aggregation (hourly, daily summaries)
    - Statistical analytics (avg, min, max, std dev)
    - Export to various formats

    Pricing Model:
    - P2P Price = ToU Rate × (1 - discount)
    - ToU Rates: ON_PEAK=5.7982, OFF_PEAK=2.6369 Baht/kWh
    - Default discount: 10%
    """

    def __init__(
        self,
        max_records: int = 10000,
        retention_hours: int = 24,
        wheeling_cost: float = RESIDENTIAL_WHEELING_COST_AVG,
        p2p_discount: float = 0.10,  # 10% discount vs ToU rate
        use_database: bool = True,
        db_path: str = "data/price_history.db",
        db_retention_days: int = 30,
    ):
        self.max_records = max_records
        self.retention_hours = retention_hours
        self.wheeling_cost = wheeling_cost
        self.p2p_discount = p2p_discount
        self.use_database = use_database

        # In-memory storage (circular buffer for efficiency)
        self._history: deque[PriceRecord] = deque(maxlen=max_records)

        # Database storage
        self._db = None
        if use_database:
            from .price_history_db import PriceHistoryDatabase
            self._db = PriceHistoryDatabase(db_path=db_path, retention_days=db_retention_days)

        # Background cleanup task
        self._cleanup_task: Optional[asyncio.Task] = None

    async def start(self):
        """Start background cleanup task and database connection."""
        if self._db:
            await self._db.connect()
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        logger.info(f"PriceHistoryManager started (retention={self.retention_hours}h, db={self.use_database})")

    async def stop(self):
        """Stop background cleanup task and close database connection."""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        if self._db:
            await self._db.disconnect()
        logger.info("PriceHistoryManager stopped")

    async def _cleanup_loop(self):
        """Periodically clean up old records."""
        while True:
            try:
                await asyncio.sleep(3600)  # Run every hour
                self._cleanup_old_records()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}")

    def add_price(
        self,
        supply_kwh: float,
        demand_kwh: float,
        timestamp: Optional[datetime] = None,
        p2p_discount: Optional[float] = None,
    ) -> PriceRecord:
        """
        Add a new price record to history based on ToU tariff.

        Args:
            supply_kwh: Market supply (kWh)
            demand_kwh: Market demand (kWh)
            timestamp: Record timestamp (defaults to now)
            p2p_discount: P2P discount (defaults to self.p2p_discount)

        Returns:
            The created PriceRecord

        Pricing Formula:
            P2P_Price = ToU_Rate × (1 - discount)
            Buyer_Total = P2P_Price + (wheeling / 2)
            Seller_Net = P2P_Price - (wheeling / 2)
        """
        if timestamp is None:
            timestamp = datetime.now(timezone.utc)

        # Get ToU period and rate
        tou_period = get_tou_period(hour=timestamp.hour, is_weekend=timestamp.weekday() >= 5)
        tou_rate = TOU_RATES[tou_period]
        
        # Apply P2P discount
        discount = p2p_discount if p2p_discount is not None else self.p2p_discount
        mcp = tou_rate * (1 - discount)

        # Calculate buyer/seller rates
        buyer_rate = mcp + (self.wheeling_cost * 0.5)
        seller_net = mcp - (self.wheeling_cost * 0.5)

        # Determine market sentiment
        ratio = demand_kwh / supply_kwh if supply_kwh > 0 else 999
        if ratio > 1.5:
            sentiment = "HIGH_DEMAND"
        elif ratio < 0.7:
            sentiment = "LOW_DEMAND"
        else:
            sentiment = "BALANCED"

        record = PriceRecord(
            timestamp=timestamp.isoformat(),
            market_clearing_price_baht_kwh=round(mcp, 4),
            buyer_total_baht_kwh=round(buyer_rate, 4),
            seller_net_baht_kwh=round(seller_net, 4),
            supply_kwh=round(supply_kwh, 2),
            demand_kwh=round(demand_kwh, 2),
            demand_ratio=round(ratio, 3),
            market_sentiment=sentiment,
            tou_period=tou_period.value,
            tou_rate_baht_kwh=round(tou_rate, 4),
            p2p_discount_percent=round(discount * 100, 2),
        )

        self._history.append(record)
        logger.debug(f"Added price record: {mcp:.4f} Baht/kWh (ToU: {tou_period.value})")

        return record
    
    async def add_price_async(
        self,
        supply_kwh: float,
        demand_kwh: float,
        timestamp: Optional[datetime] = None,
    ) -> PriceRecord:
        """
        Add a new price record to history (async version with database).
        
        Args:
            supply_kwh: Market supply (kWh)
            demand_kwh: Market demand (kWh)
            timestamp: Record timestamp (defaults to now)
        
        Returns:
            The created PriceRecord
        """
        record = self.add_price(supply_kwh, demand_kwh, timestamp)
        
        # Also store in database
        if self._db:
            try:
                await self._db.add_record(record)
            except Exception as e:
                logger.error(f"Failed to store record in database: {e}")
        
        return record

    def _cleanup_old_records(self):
        """Remove records older than retention period."""
        cutoff = datetime.now(timezone.utc) - timedelta(hours=self.retention_hours)
        
        count = 0
        while self._history:
            record = self._history[0]
            record_time = datetime.fromisoformat(record.timestamp)
            if record_time < cutoff:
                self._history.popleft()
                count += 1
            else:
                break
        
        if count > 0:
            logger.info(f"Cleaned up {count} old price records")

    def get_recent_prices(self, limit: int = 100) -> List[PriceRecord]:
        """
        Get most recent price records.
        
        Args:
            limit: Maximum number of records to return
        
        Returns:
            List of PriceRecord, newest first
        """
        records = list(self._history)
        return list(reversed(records[-limit:]))

    def get_prices_in_range(
        self,
        start_time: datetime,
        end_time: datetime,
    ) -> List[PriceRecord]:
        """
        Get prices within a time range.
        
        Args:
            start_time: Start of range
            end_time: End of range
        
        Returns:
            List of PriceRecord within range
        """
        records = []
        for record in self._history:
            record_time = datetime.fromisoformat(record.timestamp)
            if start_time <= record_time <= end_time:
                records.append(record)
        return records

    def get_statistics(
        self,
        hours: int = 24,
    ) -> Dict[str, Any]:
        """
        Calculate price statistics for a time period.
        
        Args:
            hours: Time window in hours
        
        Returns:
            Dictionary with statistical metrics
        """
        # Fallback to in-memory
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        prices = []
        
        for record in self._history:
            record_time = datetime.fromisoformat(record.timestamp)
            if record_time >= cutoff:
                prices.append(record.market_clearing_price_baht_kwh)
        
        if not prices:
            return {
                "count": 0,
                "avg": None,
                "min": None,
                "max": None,
                "std_dev": None,
                "current": None,
            }
        
        import statistics
        
        return {
            "count": len(prices),
            "avg": round(statistics.mean(prices), 4),
            "min": round(min(prices), 4),
            "max": round(max(prices), 4),
            "std_dev": round(statistics.stdev(prices), 4) if len(prices) > 1 else 0,
            "current": prices[-1] if prices else None,
        }

    def get_hourly_summary(self, hours: int = 24) -> List[Dict[str, Any]]:
        """
        Get hourly aggregated price data.
        
        Args:
            hours: Number of hours to summarize
        
        Returns:
            List of hourly summaries
        """
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        hourly_data: Dict[str, List[float]] = {}
        
        for record in self._history:
            record_time = datetime.fromisoformat(record.timestamp)
            if record_time >= cutoff:
                hour_key = record_time.strftime("%Y-%m-%d %H:00")
                if hour_key not in hourly_data:
                    hourly_data[hour_key] = []
                hourly_data[hour_key].append(record.market_clearing_price_baht_kwh)
        
        summaries = []
        for hour_key, prices in sorted(hourly_data.items()):
            summaries.append({
                "hour": hour_key,
                "avg_price": round(sum(prices) / len(prices), 4),
                "min_price": round(min(prices), 4),
                "max_price": round(max(prices), 4),
                "record_count": len(prices),
            })
        
        return summaries

    def get_daily_summary(self, days: int = 7) -> List[Dict[str, Any]]:
        """
        Get daily aggregated price data.
        
        Args:
            days: Number of days to summarize
        
        Returns:
            List of daily summaries
        """
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        daily_data: Dict[str, List[float]] = {}
        
        for record in self._history:
            record_time = datetime.fromisoformat(record.timestamp)
            if record_time >= cutoff:
                day_key = record_time.strftime("%Y-%m-%d")
                if day_key not in daily_data:
                    daily_data[day_key] = []
                daily_data[day_key].append(record.market_clearing_price_baht_kwh)
        
        summaries = []
        for day_key, prices in sorted(daily_data.items()):
            summaries.append({
                "date": day_key,
                "avg_price": round(sum(prices) / len(prices), 4),
                "min_price": round(min(prices), 4),
                "max_price": round(max(prices), 4),
                "record_count": len(prices),
            })
        
        return summaries

    def get_tou_analysis(self, hours: int = 24) -> Dict[str, Any]:
        """
        Analyze price differences between TOU periods.

        Args:
            hours: Time window in hours

        Returns:
            TOU period analysis
        """
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        peak_prices = []
        off_peak_prices = []

        for record in self._history:
            record_time = datetime.fromisoformat(record.timestamp)
            if record_time >= cutoff:
                # TOU periods: "on_peak", "off_peak_weekday", "off_peak_weekend"
                if record.tou_period == "on_peak":
                    peak_prices.append(record.market_clearing_price_baht_kwh)
                else:
                    off_peak_prices.append(record.market_clearing_price_baht_kwh)

        import statistics

        return {
            "on_peak": {
                "count": len(peak_prices),
                "avg": round(statistics.mean(peak_prices), 4) if peak_prices else None,
                "min": round(min(peak_prices), 4) if peak_prices else None,
                "max": round(max(peak_prices), 4) if peak_prices else None,
            },
            "off_peak": {
                "count": len(off_peak_prices),
                "avg": round(statistics.mean(off_peak_prices), 4) if off_peak_prices else None,
                "min": round(min(off_peak_prices), 4) if off_peak_prices else None,
                "max": round(max(off_peak_prices), 4) if off_peak_prices else None,
            },
            "spread": round(
                (statistics.mean(peak_prices) - statistics.mean(off_peak_prices)), 4
            ) if peak_prices and off_peak_prices else None,
        }

    def get_market_sentiment_distribution(self, hours: int = 24) -> Dict[str, int]:
        """
        Get distribution of market sentiment over time.
        
        Args:
            hours: Time window in hours
        
        Returns:
            Count of records per sentiment
        """
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        distribution = {"HIGH_DEMAND": 0, "BALANCED": 0, "LOW_DEMAND": 0}
        
        for record in self._history:
            record_time = datetime.fromisoformat(record.timestamp)
            if record_time >= cutoff:
                distribution[record.market_sentiment] += 1
        
        return distribution

    def export_to_list(self) -> List[Dict[str, Any]]:
        """
        Export all history as a list of dictionaries.
        
        Returns:
            List of price records as dicts
        """
        return [asdict(record) for record in self._history]

    def get_record_count(self) -> int:
        """Get total number of stored records."""
        return len(self._history)

    def clear_history(self):
        """Clear all stored price history."""
        self._history.clear()
        logger.info("Price history cleared")
