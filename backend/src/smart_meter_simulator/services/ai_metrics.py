"""
Production-grade metrics for AI forecasting
"""
import time
import logging
from functools import wraps
from typing import Callable, Any
from contextlib import contextmanager

logger = logging.getLogger(__name__)

class AIMetrics:
    """Metrics collector for AI operations"""
    
    def __init__(self):
        self.forecast_count = 0
        self.forecast_errors = 0
        self.constraint_detections = 0
        self.total_forecast_time = 0.0
        self.avg_forecast_time = 0.0
        
    def record_forecast(self, duration_ms: float, constraint_hours: int):
        """Record forecast metrics"""
        self.forecast_count += 1
        self.total_forecast_time += duration_ms
        self.avg_forecast_time = self.total_forecast_time / self.forecast_count
        
        if constraint_hours > 0:
            self.constraint_detections += 1
            
        logger.info(f"Forecast #{self.forecast_count}: {duration_ms:.2f}ms, "
                   f"{constraint_hours} constraint hours")
    
    def record_error(self, error_type: str):
        """Record error"""
        self.forecast_errors += 1
        logger.error(f"Forecast error: {error_type} (total errors: {self.forecast_errors})")
    
    def get_stats(self) -> dict:
        """Get current statistics"""
        return {
            "total_forecasts": self.forecast_count,
            "total_errors": self.forecast_errors,
            "constraint_detections": self.constraint_detections,
            "avg_forecast_time_ms": round(self.avg_forecast_time, 2),
            "error_rate": round(self.forecast_errors / max(1, self.forecast_count), 4)
        }

# Global metrics instance
_metrics = AIMetrics()

def get_metrics() -> AIMetrics:
    """Get global metrics instance"""
    return _metrics

@contextmanager
def track_forecast_time():
    """Context manager to track forecast execution time"""
    start = time.time()
    try:
        yield
    finally:
        duration_ms = (time.time() - start) * 1000
        logger.debug(f"Forecast completed in {duration_ms:.2f}ms")

def track_performance(func: Callable) -> Callable:
    """Decorator to track function performance"""
    @wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        start = time.time()
        try:
            result = func(*args, **kwargs)
            duration_ms = (time.time() - start) * 1000
            
            # Record metrics if result contains constraint info
            if isinstance(result, dict) and "summary" in result:
                constraint_hours = result["summary"].get("constraint_hours", 0)
                _metrics.record_forecast(duration_ms, constraint_hours)
            
            return result
        except Exception as e:
            _metrics.record_error(type(e).__name__)
            raise
    return wrapper
