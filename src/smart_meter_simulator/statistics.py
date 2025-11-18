"""
Statistics Module
Handles statistics tracking and reporting
"""

from typing import Dict, Any, Optional


class StatisticsTracker:
    """Tracks and reports simulation statistics"""

    def __init__(self):
        self.stats: Dict[str, int] = {
            'total_readings': 0,
            'kafka_sends': 0,
            'db_stores': 0,
            'file_saves': 0,
            'trading_opportunities': 0,
            'rec_generated': 0,
            'ws_broadcasts': 0,
        }

    def increment(self, key: str, value: int = 1):
        """Increment a statistic"""
        if key in self.stats:
            self.stats[key] += value

    def get(self, key: str) -> int:
        """Get a statistic value"""
        return self.stats.get(key, 0)

    def get_all(self) -> Dict[str, int]:
        """Get all statistics"""
        return self.stats.copy()

    def reset(self):
        """Reset all statistics"""
        for key in self.stats:
            self.stats[key] = 0

    def print_summary(
        self,
        num_meters: int,
        simulation_interval: int,
        current_weather: str,
        standalone_mode: bool,
        ws_info: Optional[Dict[str, Any]] = None
    ):
        """Print comprehensive statistics"""
        print(f"\n{'='*60}")
        print("Smart Meter Simulator Statistics")
        print(f"{'='*60}")

        # Core statistics
        print(
            f"Total Readings Generated: "
            f"{self.stats['total_readings']:,}"
        )
        print(f"Kafka Messages Sent: {self.stats['kafka_sends']:,}")
        print(f"Database Records Stored: {self.stats['db_stores']:,}")
        print(f"Files Saved: {self.stats['file_saves']:,}")
        print(
            f"WebSocket Broadcasts: {self.stats['ws_broadcasts']:,}"
        )
        print(
            f"Trading Opportunities: "
            f"{self.stats['trading_opportunities']:,}"
        )
        print(
            f"REC Certificates Generated: {self.stats['rec_generated']:,}"
        )

        # Configuration
        print(f"Current Weather: {current_weather}")
        print(f"Active Meters: {num_meters}")
        print(f"Simulation Interval: {simulation_interval}s")
        print(
            f"Mode: {'Standalone' if standalone_mode else 'Integrated'}"
        )

        # WebSocket info
        if ws_info:
            print(
                f"WebSocket Server: "
                f"ws://{ws_info['host']}:{ws_info['port']}"
            )
            print(f"Connected Clients: {ws_info['client_count']}")

        print(f"{'='*60}")

    def get_summary_dict(self) -> Dict[str, Any]:
        """Get statistics as dictionary"""
        return {
            'statistics': self.stats,
            'timestamp': self._get_timestamp(),
        }

    @staticmethod
    def _get_timestamp() -> str:
        """Get current timestamp"""
        from datetime import datetime, timezone
        return datetime.now(timezone.utc).isoformat()
