from typing import Optional
from smart_meter_simulator.core.engine import SimulationEngine
from smart_meter_simulator.transport.websocket import WebSocketManager
from smart_meter_simulator.utils.mapbox_matcher import MapboxMatcher
from smart_meter_simulator.core.price_streamer import PriceStreamer
from smart_meter_simulator.core.price_history import PriceHistoryManager

# Global state
engine: Optional[SimulationEngine] = None
websocket_manager = WebSocketManager()
mapbox_matcher = MapboxMatcher()
price_streamer: Optional[PriceStreamer] = None
price_history: Optional[PriceHistoryManager] = None


def get_simulation_engine() -> Optional[SimulationEngine]:
    """Get the current simulation engine instance"""
    return engine
