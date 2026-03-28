"""
Price Provider Abstraction

Provides market clearing prices for P2P energy trading.

Current Implementation:
- ToU-based pricing from Thai market tariffs

Future Implementation:
- API Gateway integration for dynamic prices
"""

import logging
import httpx
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Optional, Dict, Any

from ..config.thai_market import (
    TOU_RATES,
    TOUPeriod,
    get_tou_period,
    RESIDENTIAL_WHEELING_COST_AVG,
)

logger = logging.getLogger(__name__)


class PriceProvider(ABC):
    """
    Abstract base class for price providers.
    
    Implementations:
    - ToUPriceProvider: Local ToU-based pricing (current)
    - APIGatewayPriceProvider: External API Gateway pricing (future)
    """
    
    @abstractmethod
    async def get_current_price(self) -> float:
        """
        Get current market clearing price (Baht/kWh).
        
        Returns:
            Market clearing price in Baht/kWh
        """
        pass
    
    @abstractmethod
    def get_price_sync(self) -> float:
        """
        Get current market clearing price (synchronous).
        
        Returns:
            Market clearing price in Baht/kWh
        """
        pass
    
    @abstractmethod
    def get_tou_period(self, timestamp: Optional[datetime] = None) -> str:
        """
        Get current TOU period.
        
        Args:
            timestamp: Optional timestamp (defaults to now)
            
        Returns:
            TOU period string
        """
        pass


class ToUPriceProvider(PriceProvider):
    """
    Time-of-Use based price provider.
    
    Uses Thai market TOU tariffs:
    - ON_PEAK (Mon-Fri 09:00-22:00): 5.7982 Baht/kWh
    - OFF_PEAK_WEEKDAY (Mon-Fri 22:00-09:00): 2.6369 Baht/kWh
    - OFF_PEAK_WEEKEND (Sat-Sun all day): 2.6369 Baht/kWh
    
    P2P Price = ToU Rate × (1 - discount)
    """
    
    def __init__(self, p2p_discount: float = 0.10):
        """
        Initialize ToU price provider.
        
        Args:
            p2p_discount: P2P discount rate (default 10%)
        """
        self.p2p_discount = p2p_discount
        logger.info(f"ToUPriceProvider initialized (discount={p2p_discount*100}%)")
    
    def get_current_price_sync(self) -> float:
        """
        Get current ToU-based price (synchronous).
        
        Returns:
            P2P market clearing price in Baht/kWh
        """
        now = datetime.now(timezone.utc)
        tou_period = self.get_tou_period(now)
        tou_rate = TOU_RATES[tou_period]
        
        # Apply P2P discount
        p2p_price = tou_rate * (1 - self.p2p_discount)
        
        logger.debug(
            f"ToU Price: {tou_period.value} = {tou_rate:.4f} → "
            f"P2P = {p2p_price:.4f} Baht/kWh"
        )
        
        return p2p_price
    
    async def get_current_price(self) -> float:
        """
        Get current ToU-based price (async).
        
        Returns:
            P2P market clearing price in Baht/kWh
        """
        return self.get_price_sync()
    
    def get_price_sync(self) -> float:
        """
        Get current ToU-based price (synchronous).
        
        Returns:
            P2P market clearing price in Baht/kWh
        """
        return self.get_current_price_sync()
    
    def get_tou_period(self, timestamp: Optional[datetime] = None) -> TOUPeriod:
        """
        Get TOU period for timestamp.
        
        Args:
            timestamp: Optional timestamp (defaults to now)
            
        Returns:
            TOUPeriod enum value
        """
        if timestamp is None:
            timestamp = datetime.now(timezone.utc)
        
        return get_tou_period(
            hour=timestamp.hour,
            is_weekend=timestamp.weekday() >= 5
        )
    
    def get_tou_rate(self, timestamp: Optional[datetime] = None) -> float:
        """
        Get ToU rate for timestamp.
        
        Args:
            timestamp: Optional timestamp (defaults to now)
            
        Returns:
            ToU rate in Baht/kWh
        """
        period = self.get_tou_period(timestamp)
        return TOU_RATES[period]
    
    def get_price_details(self, timestamp: Optional[datetime] = None) -> Dict[str, Any]:
        """
        Get detailed price information.
        
        Args:
            timestamp: Optional timestamp (defaults to now)
            
        Returns:
            Dictionary with price details
        """
        if timestamp is None:
            timestamp = datetime.now(timezone.utc)
        
        tou_period = self.get_tou_period(timestamp)
        tou_rate = TOU_RATES[tou_period]
        p2p_price = tou_rate * (1 - self.p2p_discount)
        
        return {
            "timestamp": timestamp.isoformat(),
            "tou_period": tou_period.value,
            "tou_rate_baht_kwh": round(tou_rate, 4),
            "p2p_discount_percent": round(self.p2p_discount * 100, 2),
            "market_clearing_price_baht_kwh": round(p2p_price, 4),
            "buyer_total_baht_kwh": round(p2p_price + (RESIDENTIAL_WHEELING_COST_AVG * 0.5), 4),
            "seller_net_baht_kwh": round(p2p_price - (RESIDENTIAL_WHEELING_COST_AVG * 0.5), 4),
            "source": "ToU Tariff",
        }


class APIGatewayPriceProvider(PriceProvider):
    """
    API Gateway price provider (FUTURE IMPLEMENTATION).
    
    This class is a placeholder for future integration with the
    GridTokenX API Gateway for dynamic market prices.
    
    TODO: Implement when API Gateway price endpoint is available.
    
    Expected API:
        GET /api/v1/market/price
        Response: {
            "market_clearing_price_baht_kwh": 4.50,
            "timestamp": "2026-03-21T10:00:00Z",
            "tou_period": "on_peak",
            "supply_kwh": 100.0,
            "demand_kwh": 120.0
        }
    """
    
    def __init__(
        self,
        api_gateway_url: str = "http://localhost:8000",
        api_key: Optional[str] = None,
        timeout: float = 10.0,
    ):
        """
        Initialize API Gateway price provider.
        
        Args:
            api_gateway_url: API Gateway base URL
            api_key: Optional API key for authentication
            timeout: Request timeout in seconds
        """
        self.api_gateway_url = api_gateway_url
        self.api_key = api_key
        self.timeout = timeout
        self._http_client: Optional[httpx.AsyncClient] = None
        
        logger.warning(
            "APIGatewayPriceProvider is not yet implemented. "
            "Falling back to ToU pricing."
        )
    
    async def get_current_price(self) -> float:
        """
        Get current price from API Gateway.
        
        TODO: Implement API call when endpoint is available.
        
        Returns:
            Market clearing price in Baht/kWh
            
        Raises:
            NotImplementedError: Always (not yet implemented)
        """
        raise NotImplementedError(
            "APIGatewayPriceProvider is not yet implemented. "
            "Use ToUPriceProvider for now."
        )
    
    def get_price_sync(self) -> float:
        """
        Get current price from API Gateway (synchronous).
        
        TODO: Implement API call when endpoint is available.
        
        Returns:
            Market clearing price in Baht/kWh
            
        Raises:
            NotImplementedError: Always (not yet implemented)
        """
        raise NotImplementedError(
            "APIGatewayPriceProvider is not yet implemented. "
            "Use ToUPriceProvider for now."
        )
    
    def get_tou_period(self, timestamp: Optional[datetime] = None) -> str:
        """
        Get TOU period (fallback to local calculation).
        
        Args:
            timestamp: Optional timestamp (defaults to now)
            
        Returns:
            TOU period string
        """
        if timestamp is None:
            timestamp = datetime.now(timezone.utc)
        
        period = get_tou_period(
            hour=timestamp.hour,
            is_weekend=timestamp.weekday() >= 5
        )
        return period.value


def create_price_provider(
    provider_type: str = "tou",
    p2p_discount: float = 0.10,
    api_gateway_url: Optional[str] = None,
    api_key: Optional[str] = None,
) -> PriceProvider:
    """
    Factory function to create price provider.
    
    Args:
        provider_type: Provider type ("tou" or "api_gateway")
        p2p_discount: P2P discount for ToU provider (default 10%)
        api_gateway_url: API Gateway URL for api_gateway provider
        api_key: API key for api_gateway provider
        
    Returns:
        PriceProvider instance
        
    Example:
        # Use ToU pricing (current)
        provider = create_price_provider(provider_type="tou")
        
        # Use API Gateway pricing (future)
        provider = create_price_provider(
            provider_type="api_gateway",
            api_gateway_url="http://localhost:8000",
            api_key="your-api-key"
        )
    """
    if provider_type == "tou":
        return ToUPriceProvider(p2p_discount=p2p_discount)
    elif provider_type == "api_gateway":
        if not api_gateway_url:
            logger.warning(
                "API Gateway URL not provided, falling back to ToU pricing"
            )
            return ToUPriceProvider(p2p_discount=p2p_discount)
        return APIGatewayPriceProvider(
            api_gateway_url=api_gateway_url,
            api_key=api_key
        )
    else:
        logger.warning(
            f"Unknown provider type '{provider_type}', using ToU pricing"
        )
        return ToUPriceProvider(p2p_discount=p2p_discount)
