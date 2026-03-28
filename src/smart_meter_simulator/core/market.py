import logging
import random
import math
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

def haversine(lat1, lon1, lat2, lon2):
    """Calculate the great circle distance between two points on the earth (specified in decimal degrees)"""
    # convert decimal degrees to radians 
    lon1, lat1, lon2, lat2 = map(math.radians, [lon1, lat1, lon2, lat2])

    # haversine formula 
    dlon = lon2 - lon1 
    dlat = lat2 - lat1 
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a)) 
    r = 6371 # Radius of earth in kilometers
    return c * r


@dataclass
class CurrentTariff:
    """
    Represents the current grid tariff for a specific interval.
    """
    timestamp: datetime
    tariff_type: str # "TOU", "RTP", "FLAT"
    import_rate: float # Rate for buying from grid (Sol/kWh)
    export_rate: float # Rate for selling to grid (Sol/kWh)
    is_peak: bool
    
class TariffType(Enum):
    FLAT = "Flat"
    TOU = "Time-of-Use"
    RTP = "Real-Time-Pricing"

logger = logging.getLogger(__name__)

@dataclass
class MarketOrder:
    meter_id: str
    is_buy: bool # True for Bid (Buy), False for Ask (Sell)
    amount: float
    price: float
    timestamp: datetime
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    bus_id: Optional[int] = None

@dataclass
class MatchedTrade:
    buyer_id: str
    seller_id: str
    amount: float
    price: float
    timestamp: datetime
    clearing_price: float
    distance_km: float = 0.0
    locational_surcharge: float = 0.0

class MarketManager:
    """
    Simulates a P2P energy market with a clearing mechanism.
    Matches buy and sell orders to determine the market clearing price (MCP).
    """
    
    def __init__(self):
        self.orders: List[MarketOrder] = []
        self.history: List[Dict[str, Any]] = []
        self.trades: List[MatchedTrade] = []
        self.current_mcp = 0.25 # Initial seed price (Sol/kWh)
        self.tariff_manager = TariffManager()
        
    def submit_order(self, order: MarketOrder):
        self.orders.append(order)
        
    def clear_market(self, timestamp: datetime, nodal_prices: Optional[Dict[int, float]] = None) -> Dict[str, Any]:
        """
        Execute the clearing process using a simplified double auction.
        Finds the intersection of supply and demand curves.
        """
        if not self.orders:
            return {"mcp": self.current_mcp, "volume": 0, "matches": 0, "trades": []}
            
        buys = sorted([o for o in self.orders if o.is_buy], key=lambda x: x.price, reverse=True)
        sells = sorted([o for o in self.orders if not o.is_buy], key=lambda x: x.price)
        
        total_buy_vol = sum(o.amount for o in buys)
        total_sell_vol = sum(o.amount for o in sells)
        
        matches = 0
        cleared_volume = 0
        clearing_price = self.current_mcp
        period_trades: List[MatchedTrade] = []
        total_distance_km = 0.0
        
        idx_b = 0
        idx_s = 0
        
        while idx_b < len(buys) and idx_s < len(sells):
            bid = buys[idx_b]
            ask = sells[idx_s]
            
            if bid.price >= ask.price:
                # Match found
                match_vol = min(bid.amount, ask.amount)
                deal_price = (bid.price + ask.price) / 2
                
                # Calculate spatial distance if coordinates are available
                dist = 0.0
                if bid.latitude is not None and bid.longitude is not None and ask.latitude is not None and ask.longitude is not None:
                    dist = haversine(bid.latitude, bid.longitude, ask.latitude, ask.longitude)
                
                cleared_volume += match_vol
                matches += 1
                clearing_price = deal_price
                total_distance_km += dist
                
                # Record trade with locational surcharge
                # Surcharge is the difference in nodal prices (if available)
                surcharge = 0.0
                if nodal_prices and bid.bus_id is not None and ask.bus_id is not None:
                    # If buyer is in a more congested node than seller, they pay more
                    buyer_node_price = nodal_prices.get(bid.bus_id, clearing_price)
                    seller_node_price = nodal_prices.get(ask.bus_id, clearing_price)
                    # The difference reflects the grid stress incurred by the trade
                    surcharge = max(0.0, buyer_node_price - seller_node_price)

                trade = MatchedTrade(
                    buyer_id=bid.meter_id,
                    seller_id=ask.meter_id,
                    amount=match_vol,
                    price=deal_price,
                    timestamp=timestamp,
                    clearing_price=deal_price,
                    distance_km=dist,
                    locational_surcharge=surcharge
                )
                period_trades.append(trade)
                self.trades.append(trade)
                
                # Consume volume
                bid.amount -= match_vol
                ask.amount -= match_vol
                
                if bid.amount <= 1e-6: idx_b += 1
                if ask.amount <= 1e-6: idx_s += 1
            else:
                # No more matches possible with current sorted lists
                break
                
        self.current_mcp = clearing_price
        avg_distance = total_distance_km / matches if matches > 0 else 0.0
        
        result = {
            "timestamp": timestamp.isoformat(),
            "mcp": clearing_price,
            "volume_cleared": cleared_volume,
            "num_matches": matches,
            "total_demand": total_buy_vol,
            "total_supply": total_sell_vol,
            "avg_trade_distance_km": avg_distance,
            "trades": [
                {
                    "buyer": t.buyer_id, 
                    "seller": t.seller_id, 
                    "amount": t.amount, 
                    "price": t.price,
                    "distance_km": t.distance_km,
                    "locational_surcharge": t.locational_surcharge
                } for t in period_trades
            ]
        }
        
        self.history.append(result)
        self.orders = [] # Clear for next interval
        return result

    def get_market_sentiment(self) -> str:
        if not self.history: return "Neutral"
        last = self.history[-1]
        
        demand = last.get("total_demand", 0)
        supply = last.get("total_supply", 0)
        
        if supply == 0: return "Scarcity" if demand > 0 else "Neutral"
        
        ratio = demand / supply
        if ratio > 1.2: return "Bullish (High Demand)"
        if ratio < 0.8: return "Bearish (Over Supply)"
        return "Stable"

class TariffManager:
    """
    Manages dynamic pricing signals for the grid.
    """
    def __init__(self):
        self.current_type = TariffType.TOU
        self.base_import = 0.28
        self.base_export = 0.12
        
    def get_current_tariff(self, timestamp: datetime) -> CurrentTariff:
        """
        Generate tariff for the current timestamp based on active strategy.
        """
        if self.current_type == TariffType.TOU:
            return self._get_tou_tariff(timestamp)
        elif self.current_type == TariffType.RTP:
            return self._get_rtp_tariff(timestamp)
        else:
            return CurrentTariff(
                timestamp=timestamp, 
                tariff_type="FLAT",
                import_rate=self.base_import,
                export_rate=self.base_export,
                is_peak=False
            )
            
    def _get_tou_tariff(self, timestamp: datetime) -> CurrentTariff:
        hour = timestamp.hour
        is_weekday = timestamp.weekday() < 5
        
        # Peak: 17:00 - 21:00 on Weekdays
        # Partial Peak: 07:00 - 10:00 on Weekdays
        # Off Peak: All other times
        
        is_peak = False
        mult = 1.0
        
        if is_weekday:
            if 17 <= hour < 21:
                mult = 2.0 # High Peak
                is_peak = True
            elif 7 <= hour < 10:
                mult = 1.5 # Partial Peak
                
        return CurrentTariff(
            timestamp=timestamp,
            tariff_type="TOU",
            import_rate=self.base_import * mult,
            export_rate=self.base_export * mult, # Feed-in also higher/lower? usually fixed but let's scale
            is_peak=is_peak
        )
        
    def get_forecast(self, start_time: datetime, horizon_steps: int = 24) -> List[float]:
        """
        Get price forecast for the next N steps.
        Returns list of import rates.
        """
        prices = []
        from datetime import timedelta
        temp_time = start_time
        
        for _ in range(horizon_steps):
            tariff = self.get_current_tariff(temp_time)
            prices.append(tariff.import_rate)
            temp_time += timedelta(minutes=15)
            
        return prices
        
    def _get_rtp_tariff(self, timestamp: datetime) -> CurrentTariff:
        # Simulate RTP based on "Wholesale" dynamics + Random fluctuation
        # In real system, this comes from an external API or the Market Clearing Price
        hour = timestamp.hour
        
        # Duck curve shape base
        base_curve = 1.0
        if 10 <= hour <= 15: base_curve = 0.6 # Low price mid-day (Solar)
        if 18 <= hour <= 22: base_curve = 1.8 # High price evening
        
        noise = random.uniform(0.9, 1.1)
        rtp_rate = self.base_import * base_curve * noise
        
        return CurrentTariff(
            timestamp=timestamp,
            tariff_type="RTP",
            import_rate=rtp_rate,
            export_rate=rtp_rate * 0.5, # Export usually lower than import
            is_peak=rtp_rate > (self.base_import * 1.5)
        )
